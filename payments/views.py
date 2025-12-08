from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import *
from bookings.models import Booking



# Create your views here.

@login_required
def process_payment(request, booking_id):  

    booking = get_object_or_404(Booking, booking_id=booking_id, passenger__user=request.user)
    

    if booking.status == 'Confirmed':
        messages.info(request, "This booking is already confirmed.")
        return redirect('booking_details', booking_id=booking.booking_id)

    if request.method == 'POST':
        
        Payment.objects.create(
            booking=booking,
            payment_method='Credit Card',
        )
        
        booking.status = 'Confirmed'
        booking.save()
        
        messages.success(request, "Payment successful! Your flight is booked.")
        return redirect('booking_details', booking_id=booking.booking_id)

    return render(request, 'payments/process_payment.html', {'booking': booking})