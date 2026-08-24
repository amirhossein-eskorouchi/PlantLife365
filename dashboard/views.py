from .data_services import (
    get_daily_statistics,
    get_history,
    get_latest_reading,
    get_readings_for_date,
    get_user_device_ids,
)
from django.shortcuts import render, redirect # type: ignore
from django.http import StreamingHttpResponse # type: ignore
from .utils import get_sensor_reading, get_camera_frame # type: ignore
from django.http import JsonResponse # type: ignore
from .models import SensorReading, SystemLog, UserProfile, HardwareDevice, UserSubscription
from django.contrib.auth import authenticate, login, logout # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
import os
import io
from PIL import Image, ImageDraw, ImageFont
from django.views.decorators.csrf import csrf_exempt # type: ignore
from django.views.decorators.http import require_POST # type: ignore
from django.db import transaction # type: ignore
from .device_ingestion import (
    DevicePayloadError,
    parse_sensor_payload,
    validate_image_upload,
)
from django.core.files.storage import default_storage # type: ignore
from django.core.files.base import ContentFile  # type: ignore
import json
from django.contrib.sites.shortcuts import get_current_site # type: ignore
from django.utils.encoding import force_bytes, force_str # type: ignore
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode # type: ignore
from django.template.loader import render_to_string # type: ignore
from django.core.mail import EmailMessage # type: ignore
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator # type: ignore
from django.db.models import Min, Max, Avg
from django.utils import timezone
from datetime import timedelta
import datetime
import uuid
import logging
import base64

# ML Imports (Top-level)
try:
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    import seaborn as sns
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.svm import SVR
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.preprocessing import StandardScaler
    HAS_ML_LIBRARIES = True
except ImportError:
    HAS_ML_LIBRARIES = False

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    ''' this will render the dashboard homepge '''
    return render(request, 'dashboard/index.html')

def video_feed(request):
    ''' this will render the video feed page 
    StreamingHttpResponse keeps the connection open to send continuous data '''
    return StreamingHttpResponse(get_camera_frame(), content_type='multipart/x-mixed-replace; boundary=frame')

@login_required(login_url='login')
def sensor_api(request):
    """
    Return the latest telemetry belonging to the authenticated user.

    Prediction fields are retained as null placeholders for dashboard
    compatibility and will be implemented cleanly in Batch 5.
    """

    latest = get_latest_reading(
        request.user
    )

    if latest is None:
        return JsonResponse(
            {
                'status': 'offline',
                'temperature': '--',
                'humidity': '--',
                'light': '--',
                'water_level': '--',
                'gas': '--',
                'predicted_temp': None,
                'predicted_humid': None,
                'predicted_light': None,
                'predicted_water': None,
                'predicted_gas': None,
                'predicted_date': None,
                'prediction_status': (
                    'deferred_to_batch_5'
                ),
                'message': (
                    'No active device telemetry available'
                ),
            }
        )

    return JsonResponse(
        {
            'status': 'online',
            'device_id': latest.device_id,
            'temperature': latest.temperature,
            'humidity': latest.humidity,
            'light': latest.light,
            'water_level': latest.water_level,
            'gas': latest.gas,
            'predicted_temp': None,
            'predicted_humid': None,
            'predicted_light': None,
            'predicted_water': None,
            'predicted_gas': None,
            'predicted_date': None,
            'prediction_status': (
                'deferred_to_batch_5'
            ),
            'timestamp': latest.timestamp.isoformat(),
        }
    )

@csrf_exempt
@require_POST
def receive_esp32_data(request):
    """
    Authenticated PlantLife365 device-ingestion endpoint.

    Expected request:
    - multipart/form-data
    - JSON telemetry in the ``data`` field
    - optional JPEG in the ``image`` field
    - per-device secret in X-PlantLife365-Token
    """

    try:
        payload = parse_sensor_payload(
            request.POST.get('data')
        )

    except DevicePayloadError as exc:
        return JsonResponse(
            {
                'status': 'error',
                'message': str(exc),
            },
            status=400,
        )

    device_id = payload['device_id']

    try:
        hardware_device = HardwareDevice.objects.get(
            device_id=device_id,
            is_active=True,
        )

    except HardwareDevice.DoesNotExist:
        logger.warning(
            'Rejected telemetry from unknown or inactive '
            'device_id=%s',
            device_id,
        )

        return JsonResponse(
            {
                'status': 'error',
                'message': 'Device authentication failed',
            },
            status=403,
        )

    device_token = request.headers.get(
        'X-PlantLife365-Token',
        '',
    ).strip()

    if not hardware_device.check_secret_pin(
        device_token
    ):
        logger.warning(
            'Rejected telemetry authentication for '
            'device_id=%s',
            device_id,
        )

        return JsonResponse(
            {
                'status': 'error',
                'message': 'Device authentication failed',
            },
            status=403,
        )

    if hardware_device.upgrade_legacy_secret_pin(
        device_token
    ):
        hardware_device.save(
            update_fields=[
                'secret_pin'
            ]
        )

    image_file = request.FILES.get(
        'image'
    )

    try:
        validate_image_upload(
            image_file
        )

    except DevicePayloadError as exc:
        return JsonResponse(
            {
                'status': 'error',
                'message': str(exc),
            },
            status=400,
        )

    live_image_bytes = None

    if image_file is not None:

        try:
            image_file.seek(0)
            live_image_bytes = image_file.read()
            image_file.seek(0)

        except Exception:
            logger.exception(
                'Could not read validated device image'
            )

            return JsonResponse(
                {
                    'status': 'error',
                    'message': (
                        'Could not process device image'
                    ),
                },
                status=400,
            )

    try:

        with transaction.atomic():

            reading = SensorReading.objects.create(
                temperature=payload['temp'],
                humidity=payload['humidity'],
                light=payload['light'],
                water_level=payload[
                    'water_level'
                ],
                gas=payload['gas'],
                device_id=hardware_device.device_id,
                image=image_file,
            )

        if live_image_bytes is not None:

            if default_storage.exists(
                'live_feed.jpg'
            ):
                default_storage.delete(
                    'live_feed.jpg'
                )

            default_storage.save(
                'live_feed.jpg',
                ContentFile(
                    live_image_bytes
                ),
            )

        return JsonResponse(
            {
                'status': 'success',
                'id': reading.id,
                'device_id': hardware_device.device_id,
            },
            status=201,
        )

    except Exception:
        logger.exception(
            'Unexpected telemetry-ingestion failure '
            'for device_id=%s',
            device_id,
        )

        return JsonResponse(
            {
                'status': 'error',
                'message': (
                    'Server could not process telemetry'
                ),
            },
            status=500,
        )

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error_message = None
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            # Check or create UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            if not profile.has_seen_intro:
                return redirect('intro')
            return redirect('dashboard')
        else:
            error_message = "Invalid username or password."
            
    return render(request, 'dashboard/login.html', {'error': error_message})

@login_required(login_url='login')
def intro_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
        
    if request.method == 'POST':
        # User clicked proceed
        profile.has_seen_intro = True
        profile.save()
        
        # Check if they have devices, if not guide them to add_device, else return to dashboard
        has_devices = HardwareDevice.objects.filter(owner=request.user).exists()
        if has_devices:
            return redirect('dashboard')
        return redirect('add_device')
        
    return render(request, 'dashboard/intro.html')

@login_required(login_url='login')
def add_device_view(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    user_sub, _ = UserSubscription.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        action = request.POST.get(
            'action'
        )

        if action == 'skip':
            return redirect(
                'dashboard'
            )

        current_devices = HardwareDevice.objects.filter(
            owner=request.user
        ).count()

        if current_devices >= user_sub.max_devices:

            from django.contrib import messages

            messages.error(
                request,
                (
                    f"Device limit reached "
                    f"({user_sub.max_devices}). "
                    f"Please upgrade your subscription "
                    f"to add more devices."
                ),
            )

            return redirect(
                'subscriptions'
            )

        device_id = (
            request.POST.get(
                'device_id'
            )
            or ''
        ).strip()

        secret_pin = (
            request.POST.get(
                'secret_pin'
            )
            or ''
        ).strip()

        if not device_id or not secret_pin:

            return render(
                request,
                'dashboard/add_device.html',
                {
                    'error': (
                        'Please enter both Device ID '
                        'and Secret PIN.'
                    )
                },
            )

        is_active = (
            request.POST.get(
                'is_active',
                'on',
            )
            == 'on'
        )

        try:

            device = HardwareDevice.objects.get(
                device_id=device_id
            )

            if not device.check_secret_pin(
                secret_pin
            ):

                return render(
                    request,
                    'dashboard/add_device.html',
                    {
                        'error': (
                            'Invalid Device ID or '
                            'Device Password.'
                        )
                    },
                )

            if device.upgrade_legacy_secret_pin(
                secret_pin
            ):

                device.save(
                    update_fields=[
                        'secret_pin'
                    ]
                )

            if device.owner is not None:

                if device.owner != request.user:

                    return render(
                        request,
                        'dashboard/add_device.html',
                        {
                            'error': (
                                'This device is already claimed '
                                'by another user.'
                            )
                        },
                    )

            device.owner = request.user
            device.is_active = is_active

            device.save(
                update_fields=[
                    'owner',
                    'is_active',
                ]
            )

            return redirect(
                'dashboard'
            )

        except HardwareDevice.DoesNotExist:

            device = HardwareDevice(
                device_id=device_id,
                owner=request.user,
                is_active=is_active,
            )

            device.set_secret_pin(
                secret_pin
            )

            device.save()

            return redirect(
                'dashboard'
            )

    return render(
        request,
        'dashboard/add_device.html'
    )

def logout_view(request):
    logout(request)
    return redirect('login')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error_message = None
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        confirm_p = request.POST.get('confirm_password')
        
        from django.contrib.auth.models import User # type: ignore
        
        if not u or not e or not p or not confirm_p:
            error_message = "All fields are required."
        elif p != confirm_p:
            error_message = "Passwords do not match."
        elif User.objects.filter(username=u).exists():
            error_message = "Username already exists."
        elif User.objects.filter(email=e).exists():
            error_message = "Email already exists."
        else:
            # Create user
            user = User.objects.create_user(username=u, email=e, password=p)
            user.is_active = False # Require email activation
            user.save()
            # Create profile
            UserProfile.objects.create(user=user, has_seen_intro=False)
            
            # Send verification email
            current_site = get_current_site(request)
            mail_subject = 'Activate your PlantLife365 account.'
            message = render_to_string('dashboard/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            from_email = settings.DEFAULT_FROM_EMAIL if getattr(settings, 'DEFAULT_FROM_EMAIL', '') else 'noreply@localhost'
            email = EmailMessage(
                        mail_subject, message, from_email, [e]
            )
            email.send(fail_silently=False)
            
            # Redirect to login with a special success parameter (usually passed via messages framework, but using query params or context since no messages framework active here)
            return render(request, 'dashboard/login.html', {'success': 'Please confirm your email address to complete the registration. Check your spam folder if you do not see it.'})
            
    return render(request, 'dashboard/signup.html', {'error': error_message})

def activate(request, uidb64, token):
    from django.contrib.auth.models import User # type: ignore
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'dashboard/login.html', {'success': 'Thank you for your email confirmation. Now you can login to your account.'})
    else:
        return render(request, 'dashboard/login.html', {'error': 'Activation link is invalid!'})


@login_required(login_url='login')
def dashboard(request):
    # Check if user needs to see intro first
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    # Ensure subscription exists
    UserSubscription.objects.get_or_create(user=request.user)
    
    if not profile.has_seen_intro:
        return redirect('intro')
    return render(request, 'dashboard/index.html')


@login_required(login_url='login')
def ml_tool(request):
    """Render the ML exploratory tool page."""
    # Check subscription tier
    sub, _ = UserSubscription.objects.get_or_create(user=request.user)
    if sub.tier == 'STD':
        return redirect('subscriptions')
        
    return render(request, 'dashboard/ml_tool.html')


@login_required(login_url='login')
def ml_analyze(request):
    """Receive uploaded dataset and options, run basic regression models and return a small HTML report.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    # Check subscription tier
    sub, _ = UserSubscription.objects.get_or_create(user=request.user)
    if sub.tier == 'STD':
        return JsonResponse({'error': 'Subscription upgrade required to use ML tools.'}, status=403)

    if not HAS_ML_LIBRARIES:
        return JsonResponse({
            'error': 'Required packages missing (pandas, scikit-learn, etc.)',
            'details': 'Contact administrator to install ML dependencies.'
        }, status=500)

    if 'datafile' not in request.FILES:
        return JsonResponse({'error': 'No datafile uploaded'}, status=400)

    f = request.FILES['datafile']
    name = f.name.lower()
    try:
        if name.endswith('.csv'):
            df = pd.read_csv(f)
        else:
            df = pd.read_excel(f)
    except Exception as e:
        return JsonResponse({'error': 'Failed to read uploaded file', 'details': str(e)}, status=400)

    options_raw = request.POST.get('options', '{}')
    try:
        opts = json.loads(options_raw)
    except Exception:
        opts = {}

    response_col = opts.get('response')
    features = opts.get('features', [])
    train_pct = int(opts.get('train_pct', 80))
    random_seed = int(opts.get('random_seed', 42))
    models_to_run = opts.get('models', [])

    if not response_col or not features:
        return JsonResponse({'error': 'Response and features are required in options'}, status=400)

    # Filter numeric values and drop NaNs
    try:
        relevant_cols = [response_col] + features
        missing = [c for c in relevant_cols if c not in df.columns]
        if missing:
            return JsonResponse({'error': 'Missing columns in datafile', 'missing': missing}, status=400)

        sub = df[relevant_cols].copy()
        for c in sub.columns:
            sub[c] = pd.to_numeric(sub[c], errors='coerce')
        sub = sub.dropna()
        
        if sub.empty:
            return JsonResponse({'error': 'No usable numeric data found after cleaning.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Data preprocessing failed', 'details': str(e)}, status=400)

    X = sub[features].values
    y = sub[response_col].values
    test_size = 1 - (train_pct / 100.0)
    
    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_seed)
        
        # Scaling Features (Crucial for SVR, KNN, and Linear models)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        
    except Exception as e:
        return JsonResponse({'error': 'Train/test split failed', 'details': str(e)}, status=400)


    results = []
    
    for m_key in models_to_run:
        for i, feat_name in enumerate(features):
            try:
                if m_key == 'linear':
                    model = LinearRegression()
                    display_name = 'Linear Regression'
                elif m_key == 'random_forest':
                    model = RandomForestRegressor(n_estimators=100, random_state=random_seed)
                    display_name = 'Random Forest'
                elif m_key == 'gbm':
                    model = GradientBoostingRegressor(n_estimators=100, random_state=random_seed)
                    display_name = 'Gradient Boosting'
                elif m_key == 'svr':
                    model = SVR()
                    display_name = 'Support Vector Regression'
                elif m_key == 'knn':
                    model = KNeighborsRegressor()
                    display_name = 'K-Nearest Neighbors'
                else:
                    continue

                # Use only the specified 1D feature
                X_train_1d = X_train[:, i].reshape(-1, 1)
                X_test_1d = X_test[:, i].reshape(-1, 1)

                model.fit(X_train_1d, y_train)
                preds = model.predict(X_test_1d)
                rmse = mean_squared_error(y_test, preds)
                r2 = r2_score(y_test, preds)
                
                # Capture hyperparameters
                params = model.get_params()
                important_keys = ['n_estimators', 'max_depth', 'learning_rate', 'C', 'kernel', 'n_neighbors', 'alpha', 'l1_ratio']
                clean_params = {k: v for k, v in params.items() if k in important_keys or (v is not None and not isinstance(v, (dict, list)))}
                
                # Generate Plots for THIS 1D model
                fit_link = ""
                full_name = f"{display_name} ({feat_name})"
                
                try:
                    # Plot: Y-axis vs X-axis with Fitted Line
                    fig3 = Figure(figsize=(5, 4))
                    ax3 = fig3.add_subplot(111)
                    
                    X_test_unscaled = scaler.inverse_transform(X_test)
                    x_feat = X_test_unscaled[:, i]
                    
                    sort_idx = np.argsort(x_feat)
                    x_sorted = x_feat[sort_idx]
                    preds_sorted = preds[sort_idx]
                    
                    ax3.scatter(x_feat, y_test, color='#3498db', alpha=0.5, s=30, label='Actual')
                    ax3.plot(x_sorted, preds_sorted, color='red', linewidth=1.5, label='Fitted Line')
                    ax3.set_title(f"{response_col} vs {feat_name}\n({display_name})", fontsize=11, fontweight='bold')
                    ax3.set_xlabel(feat_name, fontsize=10)
                    ax3.set_ylabel(response_col, fontsize=10)
                    
                    # Add R^2 value within the plot
                    bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
                    ax3.text(0.05, 0.95, f"RÃƒâ€šÃ‚Â² = {r2:.4f}", transform=ax3.transAxes, fontsize=10,
                             verticalalignment='top', bbox=bbox_props)
                    
                    ax3.tick_params(labelsize=9)
                    ax3.legend(prop={'size': 9})
                    ax3.grid(True, alpha=0.3)
                    fig3.tight_layout()
                    buf3 = io.BytesIO()
                    fig3.savefig(buf3, format='png', dpi=110)
                    fit_link = f"data:image/png;base64,{base64.b64encode(buf3.getvalue()).decode()}"

                except Exception as plot_e:
                    logger.error(f"Plotting failed for {full_name}: {plot_e}")

                results.append({
                    'model': full_name, 
                    'rmse': float(rmse), 
                    'r2': float(r2),
                    'params': clean_params,
                    'fit_plot': fit_link,
                    'feature': feat_name,
                    'preds': preds.tolist()
                })

            except Exception as e:
                results.append({'model': f"{m_key} ({feat_name})", 'error': str(e)})

    # Sort results by R^2 descending (best to worst), with errored outcomes at the bottom
    results.sort(key=lambda x: (0 if 'error' in x else 1, x.get('r2', -float('inf'))), reverse=True)

    valid_results = [r for r in results if 'error' not in r]

    # --- Stats table rows (all results including errors) ---
    stats_rows = ""
    for i, r in enumerate(results):
        bg = "#f9fafb" if i % 2 == 0 else "#ffffff"
        if 'error' in r:
            stats_rows += f"<tr style='background:{bg}'><td style='padding:8px 10px;font-weight:600;border:1px solid #e5e7eb;'>{r['model']}</td><td colspan='3' style='color:red;padding:8px 10px;border:1px solid #e5e7eb;'>{r['error']}</td></tr>"
        else:
            param_str = " &nbsp;|&nbsp; ".join([f"<b>{k}</b>={v}" for k, v in list(r['params'].items())[:4]])
            stats_rows += f"""<tr style='background:{bg}'>
                <td style='padding:8px 10px;font-weight:600;border:1px solid #e5e7eb;font-size:13px;'>{r['model']}</td>
                <td style='padding:8px 10px;font-weight:700;color:#16a34a;border:1px solid #e5e7eb;font-size:14px;'>{r['rmse']:.4f}</td>
                <td style='padding:8px 10px;font-weight:700;color:#2563eb;border:1px solid #e5e7eb;font-size:14px;'>{r['r2']:.4f}</td>
                <td style='padding:8px 10px;font-size:11px;color:#555;border:1px solid #e5e7eb;'>{param_str}</td>
            </tr>"""

    sh = "font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#1e293b;background:#e2e8f0;padding:7px 12px;margin-bottom:10px;border-radius:3px;"
    
    plots_html = ""
    if valid_results:
        for feat_name in features:
            feat_results = [r for r in valid_results if r['feature'] == feat_name]
            if not feat_results:
                continue
                
            n_models = max(len(feat_results), 1)
            plot_w_pct = int(100 / n_models)
            
            fit_cells = "".join([
                f"<td style='width:{plot_w_pct}%;text-align:center;padding:6px;vertical-align:top;'>"
                f"<img src='{r['fit_plot']}' style='width:100%;display:block;border-radius:4px;border:1px solid #e2e8f0;'/>"
                f"</td>"
                for r in feat_results
            ])
            
            plots_html += f"""
            <div style='margin-bottom:24px; border: 1px solid #cbd5e1; border-radius: 6px; padding: 16px; background: #f8fafc;'>
                <div style='font-size:14px;font-weight:700;margin-bottom:14px;color:#0f172a; border-bottom: 2px solid #27ae60; padding-bottom: 6px;'>
                    <span style='color:#27ae60;'>&#9632;</span> Analysis for Feature: {feat_name}
                </div>
                <div style='margin-bottom:18px'>
                    <div style='{sh}'>{response_col} vs {feat_name} [Fitted Line]</div>
                    <table style='width:100%;border-collapse:collapse;table-layout:fixed'><tr>{fit_cells}</tr></table>
                </div>
            </div>
            """

    report_html = f"""
    <div style='padding:22px 26px;background:#fff;color:#111;font-family:Arial,Helvetica,sans-serif;width:100%;box-sizing:border-box;font-size:14px;line-height:1.6;'>

      <!-- Header Banner -->
      <div style='background:linear-gradient(135deg,#1a3c2e 0%,#27ae60 100%);color:#fff;padding:16px 20px;border-radius:6px;margin-bottom:20px;'>
        <div style='font-size:20px;font-weight:700;letter-spacing:0.3px;'>PlantLife365 &mdash; ML Analysis Report</div>
        <div style='font-size:11px;opacity:0.85;margin-top:5px;'>
            Generated: {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')} &nbsp;&bull;&nbsp; Random Seed: {random_seed} &nbsp;&bull;&nbsp; All features standard scaled
        </div>
      </div>

      <!-- Performance Section -->
      <div style='margin-bottom:20px;'>
        <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#fff;background:#1e293b;padding:7px 12px;border-radius:3px;margin-bottom:10px;'>&#9632;&nbsp; Model Performance Comparison</div>
        <table style='width:100%;border-collapse:collapse;font-size:13px;'>
          <thead>
            <tr style='background:#1e293b;color:#fff;'>
              <th style='padding:9px 12px;text-align:left;border:1px solid #334155;'>Model</th>
              <th style='padding:9px 12px;text-align:left;border:1px solid #334155;'>RMSE &darr;</th>
              <th style='padding:9px 12px;text-align:left;border:1px solid #334155;'>R&sup2; Score &uarr;</th>
              <th style='padding:9px 12px;text-align:left;border:1px solid #334155;'>Key Hyperparameters</th>
            </tr>
          </thead>
          <tbody>{stats_rows}</tbody>
        </table>
      </div>

      <!-- Plots -->
      {plots_html}

      <!-- Footer -->
      <div style='border-top:1px solid #e5e7eb;padding-top:8px;margin-top:8px;font-size:10px;color:#9ca3af;text-align:center;'>
        PlantLife365 Agriculture Monitoring System &mdash; ML Exploratory Tool
      </div>
    </div>
    """

    return JsonResponse({'report_html': report_html})

@login_required(login_url='login')
def logs_api(request):
    """
    Return the authenticated user's most recent alerts/logs.
    """

    logs = (
        SystemLog.objects
        .filter(
            owner=request.user
        )
        .order_by(
            '-timestamp'
        )[:20]
    )

    unread_count = (
        SystemLog.objects
        .filter(
            owner=request.user,
            is_read=False,
        )
        .count()
    )

    data = []

    for log in logs:

        data.append(
            {
                'id': log.id,
                'level': log.level,
                'message': log.message,
                'device_id': log.device_id,
                'timestamp': log.timestamp.strftime(
                    '%b %d, %Y %I:%M %p'
                ),
                'is_read': log.is_read,
            }
        )

    return JsonResponse(
        {
            'status': 'success',
            'logs': data,
            'unread_count': unread_count,
        }
    )


@login_required(login_url='login')
@require_POST
def mark_log_read(
    request,
    log_id,
):
    try:

        log = SystemLog.objects.get(
            id=log_id,
            owner=request.user,
        )

    except SystemLog.DoesNotExist:

        return JsonResponse(
            {
                'status': 'error',
                'message': 'Log not found',
            },
            status=404,
        )

    log.is_read = True

    log.save(
        update_fields=[
            'is_read'
        ]
    )

    return JsonResponse(
        {
            'status': 'success'
        }
    )


@login_required(login_url='login')
@require_POST
def delete_log(
    request,
    log_id,
):
    try:

        log = SystemLog.objects.get(
            id=log_id,
            owner=request.user,
        )

    except SystemLog.DoesNotExist:

        return JsonResponse(
            {
                'status': 'error',
                'message': 'Log not found',
            },
            status=404,
        )

    log.delete()

    return JsonResponse(
        {
            'status': 'success'
        }
    )


@login_required(login_url='login')
@require_POST
def delete_all_logs(request):

    deleted_count, _ = (
        SystemLog.objects
        .filter(
            owner=request.user
        )
        .delete()
    )

    return JsonResponse(
        {
            'status': 'success',
            'deleted_count': deleted_count,
        }
    )


@login_required(login_url='login')
@require_POST
def create_log(request):
    """
    Create one user-owned dashboard alert.

    The current dashboard generates threshold alerts client-side. This
    endpoint validates and stores those alerts without allowing one user
    to create or modify another user's log records.
    """

    try:
        data = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'status': 'error',
                'message': 'Invalid JSON payload',
            },
            status=400,
        )

    level = str(
        data.get(
            'level',
            'INFO',
        )
    ).upper()

    allowed_levels = {
        'INFO',
        'WARNING',
        'CRITICAL',
    }

    if level not in allowed_levels:

        return JsonResponse(
            {
                'status': 'error',
                'message': 'Invalid log level',
            },
            status=400,
        )

    message = str(
        data.get(
            'message',
            '',
        )
    ).strip()

    if not message:

        return JsonResponse(
            {
                'status': 'error',
                'message': 'Message is required',
            },
            status=400,
        )

    if len(message) > 1000:

        return JsonResponse(
            {
                'status': 'error',
                'message': (
                    'Message exceeds 1000 characters'
                ),
            },
            status=400,
        )

    device_id = str(
        data.get(
            'device_id',
            '',
        )
    ).strip()

    if device_id:

        device_owned = HardwareDevice.objects.filter(
            owner=request.user,
            device_id=device_id,
        ).exists()

        if not device_owned:

            return JsonResponse(
                {
                    'status': 'error',
                    'message': (
                        'Unknown device for current user'
                    ),
                },
                status=400,
            )

    else:
        device_id = None

    log = SystemLog.objects.create(
        owner=request.user,
        device_id=device_id,
        level=level,
        message=message,
    )

    return JsonResponse(
        {
            'status': 'success',
            'id': log.id,
        },
        status=201,
    )

@login_required(login_url='login')
def export_csv_by_date(request):
    """
    Export the authenticated user's telemetry for one calendar date.
    """

    import csv
    from datetime import datetime

    from django.http import HttpResponse

    date_str = (
        request.GET.get(
            'date'
        )
        or ''
    ).strip()

    if not date_str:

        return JsonResponse(
            {
                'error': (
                    'Date parameter is required.'
                )
            },
            status=400,
        )

    try:

        date_value = datetime.strptime(
            date_str,
            '%Y-%m-%d',
        ).date()

    except ValueError:

        return JsonResponse(
            {
                'error': (
                    'Invalid date format. '
                    'Use YYYY-MM-DD.'
                )
            },
            status=400,
        )

    readings = get_readings_for_date(
        request.user,
        date_value,
    )

    if not readings.exists():

        return JsonResponse(
            {
                'error': (
                    'No data available for '
                    'the selected date.'
                )
            },
            status=404,
        )

    response = HttpResponse(
        content_type='text/csv'
    )

    response['Content-Disposition'] = (
        'attachment; '
        f'filename="PlantLife365_Data_{date_str}.csv"'
    )

    writer = csv.writer(
        response
    )

    writer.writerow(
        [
            'Timestamp',
            'Device ID',
            'Temperature (C)',
            'Humidity (%)',
            'Water Level (%)',
            'Light (%)',
            'Gas (%)',
        ]
    )

    for reading in readings:

        writer.writerow(
            [
                reading.timestamp.isoformat(),
                reading.device_id or '',
                reading.temperature,
                reading.humidity,
                reading.water_level,
                reading.light,
                reading.gas,
            ]
        )

    return response

from django.contrib import messages # type: ignore

@login_required(login_url='login')
def settings_view(request):
    devices = HardwareDevice.objects.filter(owner=request.user)
    return render(request, 'dashboard/settings.html', {'devices': devices})

@login_required(login_url='login')
def edit_device(request, device_id):
    if request.method == 'POST':
        try:
            device = HardwareDevice.objects.get(id=device_id, owner=request.user)
            device.name = request.POST.get('name', '')
            device.is_active = request.POST.get('is_active') == 'on'
            device.save()
            messages.success(request, f"Device settings updated successfully.")
        except HardwareDevice.DoesNotExist:
            messages.error(request, "Device not found.")
    return redirect('settings')

@login_required(login_url='login')
def delete_device(request, device_id):
    if request.method == 'POST':
        try:
            device = HardwareDevice.objects.get(id=device_id, owner=request.user)
            device.owner = None
            device.save()
            messages.success(request, f"Device unpaired successfully.")
        except HardwareDevice.DoesNotExist:
            messages.error(request, "Device not found.")
    return redirect('settings')

@login_required(login_url='login')
def sensor_history_api(request):
    """
    Return bounded historical telemetry for the authenticated user.
    """

    period = (
        request.GET.get(
            'period',
            'live',
        )
        or 'live'
    ).strip()

    if period == 'live':

        return JsonResponse(
            {
                'status': 'online',
                'data': [],
            }
        )

    allowed_periods = {
        '1h',
        '1d',
        '1w',
    }

    if period not in allowed_periods:

        return JsonResponse(
            {
                'status': 'error',
                'message': (
                    'Unsupported history period'
                ),
            },
            status=400,
        )

    readings = get_history(
        request.user,
        period,
        max_points=100,
    )

    if not readings:

        return JsonResponse(
            {
                'status': 'offline',
                'data': [],
            }
        )

    data = []

    for reading in readings:

        if period == '1h':

            display_time = (
                reading.timestamp.strftime(
                    '%H:%M:%S'
                )
            )

        else:

            display_time = (
                reading.timestamp.strftime(
                    '%m/%d %H:%M'
                )
            )

        data.append(
            {
                'device_id': reading.device_id,
                't': reading.temperature,
                'h': reading.humidity,
                'w': reading.water_level,
                'l': reading.light,
                'g': reading.gas,
                'time': display_time,
                'timestamp': (
                    reading.timestamp.isoformat()
                ),
            }
        )

    return JsonResponse(
        {
            'status': 'online',
            'period': period,
            'points': len(data),
            'data': data,
        }
    )


@login_required(login_url='login')
def daily_sensor_stats_api(request):
    """
    Return rolling 24-hour telemetry statistics for the authenticated
    user's active devices.
    """

    stats = get_daily_statistics(
        request.user,
        hours=24,
    )

    if stats is None:

        return JsonResponse(
            {
                'status': 'offline',
                'stats': {},
            }
        )

    return JsonResponse(
        {
            'status': 'online',
            'window_hours': 24,
            'stats': stats,
        }
    )

@login_required(login_url='login')
def ml_custom_code(request):
    """
    Disabled in the maintained repository pending an isolated
    execution design.
    """
    return JsonResponse(
        {
            'error': (
                'Custom server-side Python execution is disabled in the '
                'maintained PlantLife365 repository.'
            )
        },
        status=403,
    )


import urllib.request
import urllib.error

@csrf_exempt
def chatbot_response(request):
    """
    Receives a POST request with {'message': 'user message text'} 
    and forwards it to the local Ollama API, enriched with real-time farm data and project knowledge.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_msg = data.get('message', '')
            
            if not user_msg:
                return JsonResponse({'error': 'Message is required'}, status=400)

            # --- Context Enrichment ---
            # 1. General Project Knowledge (Fixed Knowledge Base)
            project_kb = (
                "Knowledge Base: PlantLife365 is an agriculture monitoring system. "
                "Features include: \n"
                "- A Dashboard showing real-time sensor metrics and a live video feed from ESP32 cameras.\n"
                "- Device Management for pairing and unpairing hardware using unique IDs and secret PINs.\n"
                "- An ML Tool for uploaded tabular data and regression-based exploratory analysis.\n"
                "- Data Exporting to CSV by specific dates.\n"
                "- System Logs for tracking alerts (INFO, WARNING, CRITICAL).\n"
                "Architecture: It uses a Django backend, SQLite database, and ESP32 edge devices running MicroPython."
            )

            context = f"You are the PlantLife365 AI Assistant. {project_kb} "
            
            if request.user.is_authenticated:
                user_devices = HardwareDevice.objects.filter(owner=request.user, is_active=True).values_list('device_id', flat=True)
                
                # 2. Fetch Latest Sensor Data
                sensor_info = "No real-time sensor data available."
                try:
                    latest = SensorReading.objects.filter(device_id__in=user_devices).latest('timestamp')
                    sensor_info = (
                        f"Current Sensor Data (as of {latest.timestamp.strftime('%H:%M:%S')}):\n"
                        f"- Temperature: {latest.temperature}Ãƒâ€šÃ‚Â°C\n"
                        f"- Humidity: {latest.humidity}%\n"
                        f"- Soil Moisture: {latest.water_level}%\n"
                        f"- Light Level: {latest.light}%\n"
                        f"- Gas/Air Quality: {latest.gas}%"
                    )
                except SensorReading.DoesNotExist:
                    pass
                
                # 3. Fetch Recent Logs
                logs = SystemLog.objects.filter(owner=request.user).order_by('-timestamp')[:5]
                log_info = "Recent System Logs:\n" + "\n".join([f"- [{l.level}] {l.timestamp.strftime('%H:%M')}: {l.message}" for l in logs])
                
                # 4. Fetch User Info
                try:
                    sub = request.user.subscription
                    sub_info = f"Subscription Tier: {sub.get_tier_display()} (Max Devices: {sub.max_devices})"
                except:
                    sub_info = "Subscription: Standard"
                
                device_count = user_devices.count()
                
                context += (
                    f"\n\nUser Context:\n- Username: {request.user.username}\n- {sub_info}\n- Active Devices: {device_count}\n\n"
                    f"Here is the real-time status of the user's farm:\n{sensor_info}\n\n"
                    f"{log_info}\n\n"
                    "Use this information to answer the user's question precisely. "
                )
            else:
                context += "The user is not logged in, so you don't have access to their specific device data."

            full_prompt = f"{context}\nUser Question: {user_msg}\n\nAssistant Response:"
            # --------------------------
            
            # Prepare request to local Ollama instance
            ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
            payload = {
                "model": os.environ.get("OLLAMA_MODEL", "phi3"),
                "prompt": full_prompt,
                "stream": False
            }
            
            req = urllib.request.Request(
                ollama_url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers={'Content-Type': 'application/json'}
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    ollama_res = json.loads(response.read().decode('utf-8'))
                    ai_text = ollama_res.get('response', "I couldn't generate a response.")
                    return JsonResponse({'reply': ai_text})
            except urllib.error.URLError as e:
                logger.error(f"Ollama connection error: {e}")
                return JsonResponse({
                    'reply': "Error: Could not connect to the local AI. Please make sure Ollama is installed and running (`ollama serve`)."
                })
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            logger.error(f"Chatbot error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required(login_url='login')
def subscriptions_view(request):
    user_sub, created = UserSubscription.objects.get_or_create(user=request.user)
    current_devices = HardwareDevice.objects.filter(owner=request.user).count()
    
    # Pre-format the display for the current subscription
    max_devices_display = 'Unlimited' if user_sub.max_devices > 100 else str(user_sub.max_devices)
    
    # Define limits for each tier to show in the pricing cards
    tier_limits = {
        'STD': '1',
        'RES': '2',
        'PRM': 'Unlimited'
    }
    
    return render(request, 'dashboard/subscriptions.html', {
        'subscription': user_sub,
        'current_devices': current_devices,
        'max_devices_display': max_devices_display,
        'tier_limits': tier_limits
    })

@login_required(login_url='login')
def upgrade_subscription(request, tier):
    # Mocking stripe checkout for now
    user_sub, created = UserSubscription.objects.get_or_create(user=request.user)
    
    from django.contrib import messages
    if tier == 'PRM':
        user_sub.tier = 'PRM'
        user_sub.max_devices = 999
        user_sub.save()
        messages.success(request, "Successfully upgraded to Premium Tier!")
    elif tier == 'RES':
        user_sub.tier = 'RES'
        user_sub.max_devices = 2
        user_sub.save()
        messages.success(request, "Successfully upgraded to Researcher Tier!")
    elif tier == 'STD':
        user_sub.tier = 'STD'
        user_sub.max_devices = 1
        user_sub.save()
        messages.success(request, "Switched to Standard Tier.")
        
    return redirect('subscriptions')

@login_required(login_url='login')
def pretrained_model(request):
    """
    Historical reference-dataset demonstration disabled until
    its data source and prediction semantics are packaged
    reproducibly.
    """
    return render(
        request,
        'dashboard/pretrained_model.html',
        {
            'error': (
                'The historical reference-dataset demonstration is '
                'disabled until its data source and prediction semantics '
                'are packaged reproducibly.'
            )
        },
    )
