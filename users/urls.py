from django.urls import path
from . import views

from django.views.generic import RedirectView


urlpatterns = [
    path('', RedirectView.as_view(url='login/', permanent=False)),
    path('passenger-register/', views.passenger_register, name='passenger_register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('passenger-dashboard/', views.passenger_dashboard, name='passenger_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/', views.profile, name='profile'),
]