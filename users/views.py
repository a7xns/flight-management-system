from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import PassengerCreationForm, EmailAuthenticationForm
from .models import PassengerProfile
from bookings.models import Booking

def passenger_register(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = PassengerCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('user_login')
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = PassengerCreationForm()

    return render(request, 'users/passenger_register.html', {'form': form})


def user_login(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    login(request, user)
                    if user.is_staff:
                        return redirect('admin:index')
                    else:
                        return redirect('passenger_dashboard')
                else:
                    messages.error(request, "Invalid email or password")
            except User.DoesNotExist:
                messages.error(request, "Invalid email or password")
        else:
            messages.error(request, "Invalid email or password")
    else:
        form = EmailAuthenticationForm()

    return render(request, 'users/login.html', {'form': form})
            

@login_required
def passenger_dashboard(request):
    passenger = None
    bookings = None

    if request.method == 'POST':
        passport = request.POST.get('passport_number')
        try:
            passenger = PassengerProfile.objects.get(passport=passport, user=request.user)
            bookings = Booking.objects.filter(passenger=passenger)
        except PassengerProfile.DoesNotExist:
            passenger = None
            bookings = None

    return render(request, 'users/passenger_dashboard.html', {
        'passenger': passenger,
        'bookings': bookings,
    })

@login_required
def view_profile(request):
    passenger = request.user.passenger_profile
    return render(request, 'users/view_profile.html', {'passenger': passenger})

@login_required
def view_booked_flights(request):
    passenger = request.user.passenger_profile
    bookings = Booking.objects.filter(passenger=passenger)
    return render(request, 'users/view_booked_flights.html', {'bookings': bookings})

@login_required
def admin_dashboard(request):
    if request.method == 'POST':
        destination = request.POST.get('destination')
        if destination == 'manage_users':
            return redirect('admin_manage_users') 
        elif destination == 'view_reports':
            return redirect('admin_view_reports') 
        elif destination == 'site_settings':
            return redirect('admin_site_settings')

    context = {
        'page_title': 'Admin Control Panel'
    }
    return render(request, 'users/admin_dashboard.html', context)

@login_required
def admin_manage_users(request):
    return render(request, 'users/admin_manage_users.html')

@login_required
def admin_view_reports(request):
    return render(request, 'users/admin_view_reports.html')

@login_required
def admin_site_settings(request):
    return render(request, 'users/admin_site_settings.html')
