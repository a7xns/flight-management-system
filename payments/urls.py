from django.urls import path
from . import views


urlpatterns = [
    path('process-payment/<int:booking_id>', views.process_payment, name='process_payment'),
]