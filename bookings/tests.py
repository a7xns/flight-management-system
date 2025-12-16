from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError

from bookings.models import Booking, Ticket
from bookings.forms import TicketForm
from users.models import PassengerProfile
from flights.models import Flight, Aircraft, Airport

class BookingModelTests(TestCase):
    """Tests for the Booking and Ticket models."""

    def setUp(self):
        """Sets up the test environment with airports, aircraft, flight, user, and profile."""
        # 1. Create Airports (Required for Flight)
        self.origin = Airport.objects.create(
            airport_code="DMM", 
            airport_name="King Fahd International", 
            city="Dammam", 
            country="Saudi Arabia"
        )
        self.destination = Airport.objects.create(
            airport_code="JED", 
            airport_name="King Abdulaziz International", 
            city="Jeddah", 
            country="Saudi Arabia"
        )

        # 2. Create Aircraft
        self.aircraft = Aircraft.objects.create(
            model="Boeing 777",
            first_class=10,
            business_class=20,
            economy_class=100
        )
        
        # 3. Create Flight with correct Foreign Keys
        self.flight = Flight.objects.create(
            flight_number="SV101",
            aircraft=self.aircraft,
            economy_price=Decimal("100.00"),
            business_price=Decimal("200.00"),
            first_class_price=Decimal("300.00"),
            departure_datetime=timezone.now() + timedelta(days=5),
            arrival_datetime=timezone.now() + timedelta(days=5, hours=4),
            departure_airport=self.origin, # Object
            arrival_airport=self.destination
        )

        self.user = User.objects.create_user(username='tester', password='password')
        self.profile = PassengerProfile.objects.create(user=self.user)

    def test_booking_total_price_calculation(self):
        """Tests the calculation of the total booking price.

        Verifies that the total price is correctly calculated based on the seat class
        and number of passengers (e.g., 2 Business class seats at 200.00 each = 400.00).
        """
        booking = Booking.objects.create(
            flight=self.flight,
            passenger=self.profile,
            seat_class='Business',
            number_of_passengers=2,
            status='Confirmed'
        )
        # 2 * 200.00 = 400.00 --> will pass if it's correctly 400
        self.assertEqual(booking.total_price(), Decimal("400.00"))

    def test_ticket_seat_format(self):
        """Tests that the ticket seat number is correctly saved."""
        booking = Booking.objects.create(flight=self.flight, passenger=self.profile)
        ticket = Ticket.objects.create(
            booking=booking,
            seat_number="12A",
            passenger_name="Abdullah Mohammed",
            passport="A12345678",
            nationality="1234567890",
            passenger_dob=date(1990, 1, 1)
        )
        self.assertEqual(ticket.seat_number, "12A")

    def test_ticket_seat_format_validation(self):
        """Tests the RegexValidator on seat_number.

        Verifies that a ValidationError is raised if the seat number contains only digits.
        """
        booking = Booking.objects.create(flight=self.flight, passenger=self.profile)
        ticket = Ticket(
            booking=booking,
            seat_number="123", # This should be invalid because it needs start with letter
            passenger_name="Bad Seat Test",
            passport="A12345678",
            nationality="1010101010",
            passenger_dob=date(1990, 1, 1)
        )
        with self.assertRaises(ValidationError):
            ticket.full_clean()

    def test_passenger_count_validation(self):
        """Tests the check_number_of_passenger validation method.

        Verifies that a ValidationError is raised if the number of passengers is 0.
        """
        booking = Booking(
            flight=self.flight,
            passenger=self.profile,
            seat_class='Economy',
            number_of_passengers=0
        )
        with self.assertRaises(ValidationError):
            booking.check_number_of_passenger()


class TicketFormTests(TestCase):
    """Tests the validations in TicketForm (forms.py) independent of database models."""

    def test_valid_ticket_form(self):
        """Tests that a form with valid data is considered valid."""
        form_data = {
            'passenger_name': 'Sarah Connor',
            'passport': 'A12345678', 
            'nationality': '1020304050',
            'passenger_dob': date(1985, 5, 20)
        }
        form = TicketForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_nationality_length(self):
        """Tests validation for nationality length.

        Verifies that the form is invalid if the nationality is not exactly 10 characters.
        """
        form_data = {
            'passenger_name': 'Valid Name',
            'passport': 'A12345678',
            'nationality': '123', # short nationality
            'passenger_dob': date(1990, 1, 1)
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("National ID must be exactly 10 numbers", form.errors['nationality'][0])

    def test_invalid_passport_format(self):
        """Tests validation for passport format.

        Verifies that the form is invalid if the passport starts with a number.
        """
        form_data = {
            'passenger_name': 'Valid Name',
            'passport': '123456789', # Starts with number then should be Fail
            'nationality': '1020304050',
            'passenger_dob': date(1990, 1, 1)
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Passport must be exactly 9 alphanumeric characters", form.errors['passport'][0])

    def test_future_dob(self):
        """Tests validation for future date of birth.

        Verifies that the form is invalid if the passenger_dob Date of Birth is in the future.
        """
        future_date = date.today() + timedelta(days=1)
        form_data = {
            'passenger_name': 'Time Traveler Test',
            'passport': 'A12345678',
            'nationality': '1020304050',
            'passenger_dob': future_date
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Date of birth cannot be in the future", form.errors['passenger_dob'][0])


class BookingFlowTests(TestCase):
    """Tests for the booking flow views and interactions."""

    def setUp(self):
        """Sets up the test (user, airports, aircraft, and flight)."""
        self.client = Client()
        
        # Setup User
        self.user = User.objects.create_user(username='flyer', password='password123')
        self.profile = PassengerProfile.objects.create(user=self.user)
        self.client.login(username='flyer', password='password123')

        # Setup Airports
        self.origin = Airport.objects.create(
            airport_code="RUH", airport_name="Riyadh Airbase", city="Riyadh", country="KSA"
        )
        self.dest = Airport.objects.create(
            airport_code="DXB", airport_name="Dubai Intl", city="Dubai", country="UAE"
        )

        # Setup Flight
        self.aircraft = Aircraft.objects.create(
            model="Airbus A320",
            first_class=6,
            business_class=12,
            economy_class=60
        )
        self.flight = Flight.objects.create(
            flight_number="SV202",
            aircraft=self.aircraft,
            economy_price=Decimal("100.00"),
            business_price=Decimal("250.00"),
            first_class_price=Decimal("500.00"),
            departure_datetime=timezone.now() + timedelta(days=10),
            arrival_datetime=timezone.now() + timedelta(days=10, hours=2),
            departure_airport=self.origin,
            arrival_airport=self.dest
        )

    def test_seat_selection_view(self):
        """Tests the seat selection view.

        Verifies that the view returns a 200 status code and contains the expected context.
        """
        url = reverse('seat_selection', args=[self.flight.flight_number, 'Economy'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['eco_range'])

    def test_create_booking_process(self):
        """Tests the process of creating a booking.

        Verifies that a booking and its associated ticket are created successfully, and the user is redirected.
        """
        url = reverse('create_booking')
        post_data = {
            'flight_id': self.flight.flight_number,
            'seats_str': '12A',
            'seat_class': 'Economy',
            '12A-passenger_name': 'Test Passenger',
            '12A-passport': 'P12345678',
            '12A-nationality': '1010101010',
            '12A-passenger_dob': '1990-01-01'
        }
        response = self.client.post(url, post_data)
        
        # Expect redirect (Success)
        self.assertEqual(response.status_code, 302) 
        
        # Checking database
        booking = Booking.objects.last()
        self.assertEqual(booking.tickets.count(), 1)
        self.assertEqual(booking.tickets.first().seat_number, '12A')

    def test_cancel_ticket(self):
        """Tests cancelling a single ticket.

        Verifies that the ticket is removed and the user is redirected to the booking details.
        """
        booking = Booking.objects.create(
            flight=self.flight, passenger=self.profile, seat_class='Economy', number_of_passengers=2
        )
        t1 = Ticket.objects.create(
            booking=booking, seat_number="1A", passenger_name="P1",
            passport="A11111111", nationality="1111111111", passenger_dob=date(2000,1,1)
        )
        t2 = Ticket.objects.create(
            booking=booking, seat_number="1B", passenger_name="P2",
            passport="B22222222", nationality="2222222222", passenger_dob=date(2000,1,1)
        )

        url = reverse('cancel_ticket', args=[t1.ticket_id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('booking_details', args=[booking.booking_id]))
        self.assertFalse(Ticket.objects.filter(ticket_id=t1.ticket_id).exists())

    def test_cancel_last_ticket_cancels_booking(self):
        """Tests that cancelling the last ticket also cancels the booking.

        Verifies that if a booking has only one ticket and it is cancelled, the booking
        status is updated to 'Cancelled'.
        """
        booking = Booking.objects.create(
            flight=self.flight, passenger=self.profile, seat_class='Economy', number_of_passengers=1
        )
        t1 = Ticket.objects.create(
            booking=booking, seat_number="1A", passenger_name="Single",
            passport="A11111111", nationality="1111111111", passenger_dob=date(2000,1,1)
        )

        url = reverse('cancel_ticket', args=[t1.ticket_id])
        response = self.client.post(url)
        
        # Should Redirect to my_bookings means and status should be cancelled
        self.assertRedirects(response, reverse('my_bookings'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'Cancelled')

    def test_access_other_user_booking(self):
        """Tests that users cannot access other people's bookings."""
        other_user = User.objects.create_user(username='other', password='password')
        other_profile = PassengerProfile.objects.create(user=other_user)
        other_booking = Booking.objects.create(
            flight=self.flight, passenger=other_profile, seat_class='Economy'
        )
        
        url = reverse('booking_details', args=[other_booking.booking_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


    def test_cancel_ticket_past_flight(self):
        """Tests tickets for past flights cannot be cancelled.

        Verifies that attempting to cancel a ticket for a past flight redirects back to
        booking details and does not delete the ticket.
        """
        past_flight = Flight.objects.create(
            flight_number="OLD999",
            aircraft=self.aircraft,
            economy_price=100, business_price=200, first_class_price=300,
            departure_datetime=timezone.now() - timedelta(days=1),
            arrival_datetime=timezone.now() - timedelta(hours=20),
            departure_airport=self.origin, arrival_airport=self.dest
        )
        booking = Booking.objects.create(flight=past_flight, passenger=self.profile)
        ticket = Ticket.objects.create(
            booking=booking, seat_number="1A", passenger_name="Late",
            passport="L12345678", nationality="1111111111", passenger_dob=date(2000,1,1)
        )
        
        url = reverse('cancel_ticket', args=[ticket.ticket_id])
        response = self.client.post(url)
        
        # redirect back to booking details
        self.assertRedirects(response, reverse('booking_details', args=[booking.booking_id]))
        self.assertTrue(Ticket.objects.filter(ticket_id=ticket.ticket_id).exists())

    def test_download_ticket_pdf(self):
        """Tests the download_ticket_pdf view.

        Verifies that the view returns a PDF response.
        """
        booking = Booking.objects.create(flight=self.flight, passenger=self.profile, status='Confirmed')
        url = reverse('download_ticket_pdf', args=[booking.booking_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(f'filename="ticket_{booking.booking_id}.pdf"', response['Content-Disposition'])

    def test_create_booking_no_profile(self):
        """Tests booking creation behavior for a user without a profile.

        Verifies that an exception is raised when a user without a profile tries to create a booking
        (due to database integrity constraints).
        """
        user_no_prof = User.objects.create_user(username='noprof', password='password')
        self.client.login(username='noprof', password='password')
        
        url = reverse('create_booking')
        post_data = {
            'flight_id': self.flight.flight_number,
            'seats_str': '12A',
            'seat_class': 'Economy',
            '12A-passenger_name': 'Ghost',
            '12A-passport': 'P00000000',
            '12A-nationality': '1010101010',
            '12A-passenger_dob': '1990-01-01'
        }
        # should handle strictly/fail. 
        # currently the code tries to insert passenger=None which violates DB constraint.
        # We assert it raises an Exception (IntegrityError usually)
        with self.assertRaises(Exception): 
            self.client.post(url, post_data)