from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.user_login, name='user_login'),
    path('passenger-register/', views.passenger_register, name='passenger_register'),
    path('passenger-dashboard/', views.passenger_dashboard, name='passenger_dashboard'),
    path('profile/', views.view_profile, name='view_profile'),
    path('booked_flights/', views.view_booked_flights, name='view_booked_flights'),
    
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_manage_users, name='admin_manage_users'),
    path('admin/settings/', views.admin_site_settings, name='admin_site_settings'),
    path('admin/reports/', views.admin_view_reports, name='admin_view_reports')
]