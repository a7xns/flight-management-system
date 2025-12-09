from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from bookings.models import *
from flights.models import Flight
from users.models import PassengerProfile
from .forms import *
from django.template.loader import get_template

from xhtml2pdf import pisa


# Create your views here.

@login_required
def my_bookings(request):

    user_bookings = Booking.objects.filter(passenger__user=request.user).order_by('-booking_date')

    return render(request, 'bookings/my_bookings.html', {'bookings': user_bookings})


@login_required
def seat_selection(request):

    flight_id = request.GET.get('flight_id')


    if not flight_id:
        return redirect('passenger-dashboard')
    

    try:

        adult = int(request.GET.get('adults', 1))
        children = int(request.GET.get('children', 0))
    except ValueError:
        adult = 10
        children = 2

    total_passengers = adult + children


    flight = get_object_or_404(Flight, flight_number=flight_id)

    taken_seats_list = list(
        Ticket.objects.filter(booking__flight=flight)
        .exclude(booking__status='Cancelled')
        .values_list('seat_number', flat=True)
    )


    context = {
        'flight': flight,
        'total_passengers': total_passengers,
        'taken_seats': taken_seats_list,
        'row_range': range(1, 21)
    }

    return render(request, 'bookings/seat_selection.html', context)


@login_required
def passenger_details(request):
    """
    Display a TicketForm for EACH selected seat.
    """
    if request.method == 'POST':

        flight_id = request.POST.get('flight_id')
        seats_str = request.POST.get('selected_seats')
        
        if not flight_id or not seats_str:
            messages.error(request, "Please select seats first!")
            
        flight = get_object_or_404(Flight, flight_number=flight_id)
        seats_list = seats_str.split(',')
        
        
        forms_list = []
        for seat in seats_list:

            # prefix=seat ensures the HTML inputs will be unique (e.g. name="1A-passenger_name")
            form = TicketForm(prefix=seat)
        
            forms_list.append((seat, form))
            
        context = {
            'flight': flight,
            'forms_list': forms_list, 
            'seats_str': seats_str
        }
        
        return render(request, 'bookings/passenger_details.html', context)
    
    return redirect('passenger_dashboard')


@login_required
def create_booking(request):
    """
    Validate ALL forms and save data.
    """
    if request.method == 'POST':
        flight_id = request.POST.get('flight_id')
        seats_str = request.POST.get('seats_str')
        seats_list = seats_str.split(',')

        flight = get_object_or_404(Flight, flight_number=flight_id)
        
        valid_forms = []
        all_valid = True
        
        forms_list_for_template = []
        
        for seat in seats_list:

            form = TicketForm(request.POST, prefix=seat)
            
            forms_list_for_template.append((seat, form))
            
            if form.is_valid():

                valid_forms.append((seat, form))
            else:
                all_valid = False
        

        if not all_valid:
            messages.error(request, "Please correct the errors below.")

            return render(request, 'bookings/passenger_details.html', {
                'flight': flight,
                'forms_list': forms_list_for_template, 
                'seats_str': seats_str
            })


        try:
            profile = request.user.passenger_profile
        except PassengerProfile.DoesNotExist:
            profile = None

        booking = Booking.objects.create(
            flight=flight,
            status='Pending',
            number_of_passengers=len(seats_list),
            seat_class='Economy', 
            passenger=profile
        )

        for seat, form in valid_forms:

            ticket = form.save(commit=False) 
            
            ticket.booking = booking         
            ticket.seat_number = seat        
            ticket.seat_class = 'Economy'
            ticket.price = flight.economy_price
            
            ticket.save()                    
            
        messages.success(request, "Booking created! Redirecting to payment...")
        return redirect('process_payment', booking_id=booking.booking_id)
    
    return redirect('passenger_dashboard')


@login_required
def booking_details(request, booking_id):
    """
    Displays the final Booking Confirmation / Receipt.
    This is where the user lands after a successful payment.
    """

    booking = get_object_or_404(Booking, booking_id=booking_id, passenger__user=request.user)
    
    return render(request, 'bookings/booking_details.html', {'booking': booking})

@login_required
def download_ticket_pdf(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger__user=request.user)
    
    # It just looks for this file name.
    # As long as you updated the content of this file, the new design will show up.
    template_path = 'bookings/ticket_pdf.html' 
    
    context = {'booking': booking}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{booking.booking_id}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
        
    return response

