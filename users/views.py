from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from .forms import PassengerCreationForm


# Create your views here.

def passenger_register(request: HttpRequest) -> HttpResponse:
    """
    Handles the public passenger registration page.

    - If the request is GET:
      Displays a new, empty PassengerCreationForm.
    - If the request is POST (form submission):
      Validates the form. If valid, it saves the new passenger user
      (with 'is_staff=False') and their profile, then redirects to login.
    """


    if request.method == 'POST':

        form = PassengerCreationForm(request.POST)

        if form.is_valid():

            user = form.save()

            messages.success(request, "Registeration successful. Please log in.")

            return redirect('user_login')
        else:
            messages.error(request, "Please correct the errors below")

    else:
        form = PassengerCreationForm()


    return render(request, 'users/passenger_register.html', {'form': form})


def user_login(request: HttpRequest) -> HttpResponse:
    """
    Handles the user login page.
    Redirects Admins to an admin page and Passengers to a passenger page.
    """

    if request.method == 'POST':

        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username=username, password=password)

            if user is not None:
                
                login(request, user)

                if user.is_staff: # means he/she is an admin
                    
                    return redirect('admin:index')
                else:
                    return redirect('passenger_dashboard')

            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Invalid username or password")
    
    else: # means a GET request
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})
            
@login_required
def passenger_dashboard(request):
    return render(request, 'users/passenger_dashboard.html')



