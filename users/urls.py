from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.user_login, name='user_login'),
    path('passenger-register/', views.passenger_register, name='passenger_register'),
    path('passenger-dashboard/', views.passenger_dashboard, name='passenger_dashboard')
]