from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from .models import Flight, Airport, Aircraft
from bookings.models import Booking, Ticket
from users.models import PassengerProfile

class FlightTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='user', password='password')
        self.admin = get_user_model().objects.create_user(username='admin', password='password', is_staff=True, is_superuser=True)
        
        self.airport1 = Airport.objects.create(airport_code="JFK", airport_name="JFK", city="NYC", country="USA")
        self.airport2 = Airport.objects.create(airport_code="LHR", airport_name="LHR", city="London", country="UK")
        self.aircraft = Aircraft.objects.create(model="B777", economy_class=100)

        self.flight = Flight.objects.create(
            flight_number="SV2020",
            departure_datetime=timezone.now() + timedelta(days=1),
            arrival_datetime=timezone.now() + timedelta(days=1, hours=8),
            economy_price=100.00, business_price=200.00, first_class_price=300.00,
            departure_airport=self.airport1, arrival_airport=self.airport2, aircraft=self.aircraft,
            status='Scheduled'
        )

    # --- ORIGINAL TESTS ---
    def test_flight_model_logic(self):
        # Total = 100 (Eco set in setup) + 16 (Biz Default) + 8 (First Default) = 124
        # We expect 124 available seats initially
        self.assertEqual(self.flight.available_seats_dynamic(), 124)

    def test_view_flights_public(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('view_flights'))
        self.assertEqual(response.status_code, 200)

    def test_add_flight_permission(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('add_new_flight'))
        self.assertEqual(response.status_code, 302)

    def test_manifest_permission(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('flight_manifest', args=['SV2020']))
        self.assertEqual(response.status_code, 302) # Redirect due to messages/check

    @patch('flights.views.pisa.CreatePDF')
    def test_generate_report(self, mock_pdf):
        mock_pdf.return_value.err = 0
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('generate_report_pdf'))
        self.assertEqual(response.status_code, 200)

    # --- 10 NEW TESTS ---

    def test_delete_flight_logic(self):
        self.client.login(username='admin', password='password')
        url = reverse('delete_flight', args=['SV2020'])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Flight.objects.filter(flight_number='SV2020').exists())

    def test_delete_flight_permission_denied(self):
        self.client.login(username='user', password='password')
        url = reverse('delete_flight', args=['SV2020'])
        response = self.client.post(url)
        # Should redirect or error, flight should still exist
        self.assertTrue(Flight.objects.filter(flight_number='SV2020').exists())

    def test_search_flight_no_results(self):
        self.client.login(username='user', password='password')
        data = {'origin': 'JFK', 'destination': 'JFK', 'date_from': '2025-01-01', 'date_to': '2025-01-02'}
        response = self.client.get(reverse('search_flight'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['flights']), 0)

    def test_search_flight_price_filter(self):
        self.client.login(username='user', password='password')
        # Filter max price 50 (flight is 100) -> Should return 0
        date_str = (timezone.now() + timedelta(days=0)).strftime('%Y-%m-%d')
        data = {
            'origin': 'JFK', 'destination': 'LHR', 
            'date_from': date_str, 'date_to': date_str,
            'max_price': 50
        }
        response = self.client.get(reverse('search_flight'), data)
        self.assertEqual(len(response.context['flights']), 0)

    def test_flight_details_view(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('flight_details', args=['SV2020']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SV2020')

    def test_edit_flight_get(self):
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('edit_flight', args=['SV2020']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flights/edit_flight.html')

    def test_edit_flight_post_update(self):
        self.client.login(username='admin', password='password')
        url = reverse('edit_flight', args=['SV2020'])
        
        # Update price to 999
        data = {
            'flight_number': 'SV2020',
            'aircraft': self.aircraft.aircraft_id,
            'departure_airport': self.airport1.airport_code,
            'arrival_airport': self.airport2.airport_code,
            'departure_datetime': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'arrival_datetime': (timezone.now() + timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M'),
            'economy_price': 999.00,
            'business_price': 200.00, 'first_class_price': 300.00,
            'status': 'Delayed'
        }
        self.client.post(url, data)
        
        self.flight.refresh_from_db()
        self.assertEqual(self.flight.economy_price, 999.00)
        self.assertEqual(self.flight.status, 'Delayed')

    def test_flight_str_representation(self):
        self.assertEqual(str(self.flight), "SV2020")

    def test_remove_passenger_cancel_booking_logic(self):
        # Setup: Booking with 1 passenger
        self.client.login(username='admin', password='password')
        prof = PassengerProfile.objects.create(user=self.user)
        bk = Booking.objects.create(flight=self.flight, passenger=prof, status='Confirmed')
        tk = Ticket.objects.create(booking=bk, seat_number='1A', passenger_name='T', passport='P', passenger_dob='2000-01-01', nationality='N')
        
        # Action: Remove the ONLY passenger
        self.client.post(reverse('remove_passenger', args=[tk.ticket_id]))
        
        # Result: Booking should be Cancelled because no passengers left
        bk.refresh_from_db()
        self.assertEqual(bk.status, 'Cancelled')

    def test_admin_reports_view_loads(self):
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('admin_view_reports'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'flights/reports.html')