from .assistant_service import (
    AssistantServiceError,
    generate_assistant_reply,
)
from .ml_services import (
    MLServiceError,
    run_regression_analysis,
)
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
@require_POST
def ml_analyze(request):
    """
    Run bounded exploratory regression analysis on one uploaded
    CSV/Excel dataset.
    """

    subscription, _ = UserSubscription.objects.get_or_create(
        user=request.user
    )

    if subscription.tier == 'STD':

        return JsonResponse(
            {
                'error': (
                    'Researcher or Premium access is required '
                    'for exploratory ML analytics.'
                )
            },
            status=403,
        )

    upload = request.FILES.get(
        'datafile'
    )

    if upload is None:

        return JsonResponse(
            {
                'error': (
                    'No data file was uploaded.'
                )
            },
            status=400,
        )

    options_raw = request.POST.get(
        'options',
        '{}',
    )

    try:
        options = json.loads(
            options_raw
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'error': (
                    'Analysis options must be valid JSON.'
                )
            },
            status=400,
        )

    try:

        analysis = run_regression_analysis(
            upload,
            options,
        )

    except MLServiceError as exc:

        return JsonResponse(
            {
                'error': str(exc)
            },
            status=400,
        )

    except Exception:

        logger.exception(
            'Unexpected ML-analysis failure'
        )

        return JsonResponse(
            {
                'error': (
                    'The analysis could not be completed.'
                )
            },
            status=500,
        )

    report_html = render_to_string(
        'dashboard/partials/ml_report.html',
        {
            'analysis': analysis
        },
        request=request,
    )

    return JsonResponse(
        {
            'status': 'success',
            'report_html': report_html,
            'analysis_summary': {
                'response': analysis[
                    'response'
                ],
                'features': analysis[
                    'features'
                ],
                'clean_rows': analysis[
                    'clean_rows'
                ],
                'train_rows': analysis[
                    'train_rows'
                ],
                'test_rows': analysis[
                    'test_rows'
                ],
            },
        }
    )

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
@require_POST
def chatbot_response(request):
    """
    Send one authenticated question to the configured local
    PlantLife365 assistant service.
    """

    try:
        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'error': (
                    'Invalid JSON payload.'
                )
            },
            status=400,
        )

    message = str(
        payload.get(
            'message',
            '',
        )
    ).strip()

    if not message:

        return JsonResponse(
            {
                'error': (
                    'Message is required.'
                )
            },
            status=400,
        )

    try:

        reply = generate_assistant_reply(
            request.user,
            message,
        )

    except AssistantServiceError as exc:

        logger.warning(
            'PlantLife365 assistant unavailable: %s',
            exc,
        )

        return JsonResponse(
            {
                'error': str(exc)
            },
            status=503,
        )

    except Exception:

        logger.exception(
            'Unexpected PlantLife365 assistant failure'
        )

        return JsonResponse(
            {
                'error': (
                    'The local AI assistant could not '
                    'complete the request.'
                )
            },
            status=500,
        )

    return JsonResponse(
        {
            'reply': reply
        }
    )

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
    """
    Preserve the historical subscription-tier UI without presenting
    it as a completed billing or checkout system.
    """

    from django.contrib import messages

    valid_tiers = {
        'STD',
        'RES',
        'PRM',
    }

    if tier not in valid_tiers:

        messages.error(
            request,
            'Unknown subscription tier.'
        )

        return redirect(
            'subscriptions'
        )

    messages.info(
        request,
        (
            'Subscription checkout is a prototype feature '
            'and is disabled in the maintained repository.'
        ),
    )

    return redirect(
        'subscriptions'
    )

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
