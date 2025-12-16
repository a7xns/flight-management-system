"""Views for the users app.

This module contains the view functions for user registration, authentication,
dashboard access (for both passengers and admins), and profile management.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import *
from .models import PassengerProfile, Admin
from flights.models import Airport, Flight
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking



def passenger_register(request: HttpRequest) -> HttpResponse:
    """Handles the registration of new passengers.
    
    Processes the PassengerCreationForm. If valid, creates a new user and
    redirects to the login page. If invalid, re-renders the form with errors.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered registration page or a redirect to login.
    """

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
    """Handles user authentication and login.
    
    Authenticates the user using email and password. Redirects to the appropriate
    dashboard (Admin or Passenger) upon successful login.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered login page or a redirect to the dashboard.
    """


    if request.method == 'POST':

        form = EmailAuthenticationForm(request, data=request.POST)

        if form.is_valid():

            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            try:
                user = User.objects.get(email__iexact=email)
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
    """Logs out the current user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A redirect to the login page.
    """

    logout(request)
    messages.success(request, 'You have been logged out successfully')

    return redirect('user_login')

@login_required
def passenger_dashboard(request):
    """Renders the passenger dashboard with flight search and upcoming bookings.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered passenger dashboard.
    """
    
    airports = Airport.objects.all().order_by('city')

    now = timezone.now()
    
    upcoming_bookings = Booking.objects.filter(
        passenger__user=request.user,     
        flight__departure_datetime__gt=now  
    ).exclude(
        status='Cancelled'                  
    ).order_by('flight__departure_datetime')[:3] 

    context = {
        'airports': airports,
        'upcoming_bookings': upcoming_bookings
    }

    return render(request, 'users/passenger_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Renders the admin dashboard with statistics on flights and bookings.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered admin dashboard.
    """

    if not request.user.is_staff:
        messages.error(request, 'Sorry. You are not authorized to view that page!')
        return redirect('passenger_dashboard')


    duration = request.GET.get('duration', 'year')
    now = timezone.now()


    if duration == 'day':
        start_date = now - timedelta(days=1)
    elif duration == 'week':
        start_date = now - timedelta(weeks=1)
    elif duration == 'month':
        start_date = now - timedelta(days=30)
    elif duration == '3month':
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=365)



    total_flights = Flight.objects.filter(departure_datetime__gte=start_date).count()
    total_bookings = Booking.objects.filter(booking_date__gte=start_date).count()

    cancellations = Booking.objects.filter(status='Cancelled', booking_date__gte=start_date).count()


    context = {
        'total_flights': total_flights,
        'total_bookings': total_bookings,
        'cancellations': cancellations,
        'selected_duration': duration
    }

    return render(request, 'users/admin_dashboard.html', context)

@login_required
def view_profile(request):
    """Displays the current user's profile information.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered profile view page.
    """
    
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
    """Displays a list of flights booked by the passenger.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered booked flights page.
    """
    passenger = request.user.passenger_profile
    bookings = Booking.objects.filter(passenger=passenger)
    return render(request, 'users/view_booked_flights.html', {'bookings': bookings})

@login_required
def admin_manage_users(request):
    """Renders the user management dashboard page.

    This view is a placeholder for the user management interface where admins
    can view and modify user accounts.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered user management page.
    """
    return render(request, 'users/admin_manage_users.html')


@login_required
def admin_site_settings(request):
    """Renders the site settings configuration page.

    This view is a placeholder for global site settings management.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered site settings page.
    """
    return render(request, 'users/admin_site_settings.html')

@login_required
def profile(request):
    """Handles profile updates for both admins and passengers.

    Displays the appropriate profile form (Admin or Passenger) based on the user's
    status. Handles form submission to update user and profile details.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered profile edit page (users/profile.html).
    """

    user = request.user

    if user.is_staff:

        admin_profile, created = Admin.objects.get_or_create(user=user)
        
        if request.method == 'POST':

            u_form = UserUpdateForm(request.POST, instance=user)
            
            if u_form.is_valid():
                u_form.save()
                messages.success(request, 'Admin profile updated successfully!')
                return redirect('profile')
        else:
            u_form = UserUpdateForm(instance=user)
        
        p_form = None 
        profile_data = admin_profile


    else:

        passenger_profile, created = PassengerProfile.objects.get_or_create(user=user)

        if request.method == 'POST':
            u_form = UserUpdateForm(request.POST, instance=user)
            p_form = ProfileUpdateForm(request.POST, instance=passenger_profile)

            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Passenger profile updated successfully!')
                return redirect('profile')
        else:
            u_form = UserUpdateForm(instance=user)
            p_form = ProfileUpdateForm(instance=passenger_profile)
            
        profile_data = passenger_profile

    context = {
        'u_form': u_form,
        'p_form': p_form,       
        'profile': profile_data 
    }

    return render(request, 'users/profile.html', context)
