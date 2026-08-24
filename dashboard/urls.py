from django.urls import path # type: ignore
from django.contrib.auth import views as auth_views # type: ignore
from . import views
from django.conf import settings # type: ignore
from django.conf.urls.static import static # type: ignore

urlpatterns = [
    # when the user goes to http://website.com/ -> run views.index
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='dashboard/password_reset.html',
        email_template_name='dashboard/password_reset_email.html',
        subject_template_name='dashboard/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='dashboard/password_reset_done.html'), name='password_reset_done'),
    path('reset/<str:uidb64>/<str:token>/', auth_views.PasswordResetConfirmView.as_view(template_name='dashboard/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='dashboard/password_reset_complete.html'), name='password_reset_complete'),
    path('intro/', views.intro_view, name='intro'),
    path('add-device/', views.add_device_view, name='add_device'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/edit/<int:device_id>/', views.edit_device, name='edit_device'),
    path('settings/delete/<int:device_id>/', views.delete_device, name='delete_device'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('ml-tool/', views.ml_tool, name='ml_tool'),
    path('pretrained-model/', views.pretrained_model, name='pretrained_model'),
    path('ml_analyze/', views.ml_analyze, name='ml_analyze'),
    path('ml_custom_code/', views.ml_custom_code, name='ml_custom_code'),
    path('api/data/', views.sensor_api, name='sensor_api'),
    path('api/sensor-history/', views.sensor_history_api, name='sensor_history_api'),
    path('api/logs/', views.logs_api, name='logs_api'),
    path('api/logs/read/<int:log_id>/', views.mark_log_read, name='mark_log_read'),
    path('api/logs/delete/<int:log_id>/', views.delete_log, name='delete_log'),
    path('api/logs/delete_all/', views.delete_all_logs, name='delete_all_logs'),
    path('api/logs/create/', views.create_log, name='create_log'),
    path('upload', views.receive_esp32_data, name='receive_esp32_data'),
    path('api/export-csv/', views.export_csv_by_date, name='export_csv_by_date'),
    path('api/daily-stats/', views.daily_sensor_stats_api, name='daily_sensor_stats_api'),
    path('api/chat/', views.chatbot_response, name='chatbot_response'),
    path('subscriptions/', views.subscriptions_view, name='subscriptions'),
    path('subscriptions/upgrade/<str:tier>/', views.upgrade_subscription, name='upgrade_subscription'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
