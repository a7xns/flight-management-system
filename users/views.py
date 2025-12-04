from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import PassengerCreationForm, EmailAuthenticationForm
from .models import PassengerProfile, Admin
from flights.models import Airport



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
                        return redirect('admin_dashboard')
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
def user_logout(request: HttpRequest) -> HttpResponse:

    logout(request)
    messages.success(request, 'You have been logged out successfully')

    return redirect('user_login')

@login_required
def passenger_dashboard(request):
    passenger = None
    bookings = None

    airports = Airport.objects.all().order_by('city')

    return render(request, 'users/passenger_dashboard.html', context={'airports': airports})


@login_required
def admin_dashboard(request):

    if not request.user.is_staff:
        messages.error(request, 'Sorry. You are not authorized to view that page!')
        return redirect('passenger_dashboard')

    return render(request, 'users/admin_dashboard.html')



@login_required
def view_profile(request):
    
    user = request.user
    profile_data = None
    user_type = None


    if user.is_staff:
        user_type = 'admin'

        try:
            profile_data = user.admin_profile
        except Admin.DoesNotExist:
            profile_data = None
    else:
        user_type = 'passenger'

        try:
            profile_data = user.passenger_profile
        except PassengerProfile.DoesNotExist:
            profile_data = None
    
    context = {
        'user_obj': user,
        'user_type': user_type,
        'profile': profile_data
    }

    return render(request, 'users/profile.html', context)


@login_required
def view_booked_flights(request):
    passenger = request.user.passenger_profile
    bookings = Booking.objects.filter(passenger=passenger)
    return render(request, 'users/view_booked_flights.html', {'bookings': bookings})


    context = {
        'page_title': 'Admin Control Panel'
    }
    return render(request, 'users/admin_dashboard.html', context)

@login_required
def admin_manage_users(request):
    return render(request, 'users/admin_manage_users.html')


@login_required
def admin_site_settings(request):
    return render(request, 'users/admin_site_settings.html')
