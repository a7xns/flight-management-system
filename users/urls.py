from django.urls import path
from . import views
from django.views.generic import RedirectView

from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', RedirectView.as_view(url='login/', permanent=False)),
    path('passenger-register/', views.passenger_register, name='passenger_register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),

    path('passenger-dashboard/', views.passenger_dashboard, name='passenger_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('profile/', views.profile, name='profile'),

    path(
        'reset-password/', 
        auth_views.PasswordResetView.as_view(template_name='users/forgot_password.html'), 
        name='reset_password'
    ),
    path(
        'reset-password-sent/', 
        auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), 
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(template_name="users/password_reset_confirm.html"), 
        name="password_reset_confirm"
    ),
    path(
        'reset_password_complete/', 
        auth_views.PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"), 
        name="password_reset_complete"
    ),
]