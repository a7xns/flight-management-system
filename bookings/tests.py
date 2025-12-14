from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Booking, Ticket
from users.models import PassengerProfile
from flights.models import Flight, Airport, Aircraft

class BookingTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

        self.profile = PassengerProfile.objects.create(user=self.user, phone_number='1234567890')
        self.airport = Airport.objects.create(airport_code="JFK", airport_name="JFK", city="NYC", country="USA")
        self.aircraft = Aircraft.objects.create(model="B777")
        self.flight = Flight.objects.create(
            flight_number="TS123",
            departure_datetime=timezone.now() + timedelta(days=1),
            arrival_datetime=timezone.now() + timedelta(days=1, hours=8),
            economy_price=100.00, business_price=200.00, first_class_price=300.00,
            departure_airport=self.airport, arrival_airport=self.airport, aircraft=self.aircraft
        )
        self.booking = Booking.objects.create(
            flight=self.flight, passenger=self.profile, seat_class='Economy', number_of_passengers=1, status='Pending'
        )

    # --- ORIGINAL TESTS ---
    def test_my_bookings_view(self):
        response = self.client.get(reverse('my_bookings'))
        self.assertEqual(response.status_code, 200)

    def test_seat_selection_view(self):
        response = self.client.get(reverse('seat_selection'), {'flight_id': 'TS123'})
        self.assertEqual(response.status_code, 200)

    def test_passenger_details_post(self):
        data = {'flight_id': 'TS123', 'selected_seats': '1A', 'seat_class': 'Economy'}
        response = self.client.post(reverse('passenger_details'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_price'], 100.00)

    def test_create_booking_success(self):
        data = {
            'flight_id': 'TS123', 'seats_str': '1A', 'seat_class': 'Economy',
            '1A-passenger_name': 'John', '1A-passport': 'A12345678',
            '1A-nationality': '1112223334', '1A-passenger_dob': '1990-01-01', '1A-seat_number': '1A'
        }
        response = self.client.post(reverse('create_booking'), data)
        self.assertEqual(response.status_code, 302)

    def test_download_ticket_pdf(self):
        response = self.client.get(reverse('download_ticket_pdf', args=[self.booking.booking_id]))
        self.assertEqual(response.status_code, 200)

    # --- 10 NEW TESTS ---

    def test_booking_model_total_price_logic(self):
        # Test model method directly
        self.booking.number_of_passengers = 3
        self.assertEqual(self.booking.total_price(), 300.00) # 3 * 100

    def test_booking_model_invalid_seat_class(self):
        self.booking.seat_class = 'Space'
        # total_price should raise error or return None/fail based on your logic
        # Your model raises ValidationError
        with self.assertRaises(ValidationError):
            self.booking.total_price()

    def test_booking_passenger_validation(self):
        # Number of passengers must be > 0
        self.booking.number_of_passengers = 0
        with self.assertRaises(ValidationError):
            self.booking.check_number_of_passenger()

    def test_ticket_seat_format_validation(self):
        # Regex check: '1A' is valid, 'ABC' might be invalid depending on regex
        ticket = Ticket(booking=self.booking, seat_number='!!', passenger_name='Test', passport='A12345678', passenger_dob='1990-01-01', nationality='USA')
        # We need to call full_clean() to trigger validators
        with self.assertRaises(ValidationError):
            ticket.full_clean()

    def test_create_booking_missing_fields_fails(self):
        # Submitting form without passport
        data = {
            'flight_id': 'TS123', 'seats_str': '1A', 'seat_class': 'Economy',
            '1A-passenger_name': 'John', 
            # Missing Passport
            '1A-nationality': '1112223334', '1A-passenger_dob': '1990-01-01'
        }
        response = self.client.post(reverse('create_booking'), data)
        # Should re-render page (200) with errors, not redirect (302)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/passenger_details.html')

    def test_booking_details_404_for_other_user(self):
        other_user = get_user_model().objects.create_user(username='other', password='pw')
        self.client.login(username='other', password='pw')
        
        url = reverse('booking_details', args=[self.booking.booking_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_seat_selection_invalid_flight(self):
        # Accessing seat map for fake flight
        response = self.client.get(reverse('seat_selection'), {'flight_id': 'FAKE999'})
        # View uses get_object_or_404 -> 404
        self.assertEqual(response.status_code, 404)

    def test_create_booking_business_price(self):
        # Simulate booking business class via POST
        data = {
            'flight_id': 'TS123', 'seats_str': '1A', 'seat_class': 'Business',
            '1A-passenger_name': 'John', '1A-passport': 'A12345678',
            '1A-nationality': '1112223334', '1A-passenger_dob': '1990-01-01', '1A-seat_number': '1A'
        }
        self.client.post(reverse('create_booking'), data)
        
        # Check DB
        new_booking = Booking.objects.last()
        self.assertEqual(new_booking.seat_class, 'Business')

    def test_download_ticket_access_denied(self):
        # Logged out user
        self.client.logout()
        url = reverse('download_ticket_pdf', args=[self.booking.booking_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Redirect to login

    def test_booking_defaults(self):
        # Test default values in model
        b = Booking.objects.create(flight=self.flight, passenger=self.profile)
        self.assertEqual(b.status, 'Pending')
        self.assertEqual(b.seat_class, 'Economy')