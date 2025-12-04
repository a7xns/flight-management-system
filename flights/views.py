from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import NewFlightForm
from .models import Flight, Airport
from datetime import datetime

# Create your views here.

@login_required
def admin_view_reports(request):

    return render(request, 'flights/reports.html')

@login_required
def add_new_flight(request):


    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page !')
        return redirect('passenger_dashboard')
    
    
    if request.method == 'POST':
        
        flight_form = NewFlightForm(request.POST)

        if flight_form.is_valid():
            flight_form.save()

            messages.success(request, 'Flight has been created successfully.')
        else:
            messages.error(request, 'Please check the error below !')

    else:
        flight_form = NewFlightForm()



    return render(request, 'flights/add_new_flight.html', context={'form': flight_form})

@login_required
def view_flights(request):
        
    flights = Flight.objects.all().order_by('departure_datetime')
    return render(request, 'flights/view_flights.html', {'flights': flights})

@login_required
def delete_flight(request, flight_id):

    if not request.user.is_staff:
        messages.error(request, 'Access denied')
        return redirect('passenger_dashboard')
    
    flight = get_object_or_404(Flight, flight_number=flight_id)

    if request.method == 'POST':
        flight.delete()

        messages.success(request, 'Flight deleted successfully')

    return redirect('view_flights')

@login_required
def flight_management(request):

    return render(request, 'flights/flights_management.html')


@login_required
def search_flight(request):

    departure_code = request.GET.get('origin')
    destination_code = request.GET.get('destination')
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')

    cabin_class = request.GET.get('cabin_class', 'economy')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')


    flights = []

    departure_city = 'Unknown'
    destination_city = 'Unknown'


    if departure_code and destination_code and date_from_str and date_to_str:

        try:
            search_date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            search_date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()

            flights = Flight.objects.filter(
                departure_airport__airport_code=departure_code,
                arrival_airport__airport_code=destination_code,
                departure_datetime__date__range=[search_date_from, search_date_to]
            )


            if min_price:
                if cabin_class == 'business':
                    flights = flights.filter(business_price__gte = min_price)

                elif cabin_class == 'first':
                    flights = flights.filter(first_class_price__gte = min_price)

                else:
                    flights = flights.filter(economy_price__gte=min_price)

            if max_price:
                if cabin_class == 'business':
                    flights = flights.filter(business_price__lte = max_price)

                elif cabin_class == 'first':
                    flights = flights.filter(first_class_price__lte = max_price)

                else:
                    flights = flights.filter(economy_price__lte=max_price)


            flights = flights.order_by('departure_datetime')

            if flights.exists():
                departure_city = flights[0].departure_airport.city
                destination_city = flights[0].arrival_airport.city
            else:

                try:
                    departure_city = Airport.objects.get(airport_code=departure_code).city
                    destination_city = Airport.objects.get(airport_code=destination_code).city
                
                except Airport.DoesNotExist:
                    pass

        except ValueError:
            pass


    context = {
        'flights': flights,
        'departure_code': departure_code,
        'destination_code': destination_code,
        'cabin_class': cabin_class,
        'min_price': min_price,
        'max_price': max_price,
        'departure_city': departure_city,
        'destination_city': destination_city,
        'date_from': date_from_str,
        'date_to': date_to_str,
        'result_count': len(flights)
    }


    return render(request, 'flights/search_flight.html', context)