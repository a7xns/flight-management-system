from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Payment
from bookings.models import Booking
from flights.models import Flight, Airport, Aircraft
from users.models import PassengerProfile

class PaymentTests(TestCase):
    """Tests for Payment model and views."""

    def setUp(self):
        """Sets up the test for the user, flight, booking, and passenger."""
        self.client = Client()

        self.user = get_user_model().objects.create_user(username='testuser', password='password')
        self.other_user = get_user_model().objects.create_user(username='tester', password='password')
        self.client.login(username='testuser', password='password')

        self.airport = Airport.objects.create(airport_code="DXB", airport_name="Dubai Int", city="Dubai", country="UAE")
        self.aircraft = Aircraft.objects.create(model="A380")
        self.flight = Flight.objects.create(
            flight_number="EK101",
            departure_datetime=timezone.now() + timedelta(days=1),
            arrival_datetime=timezone.now() + timedelta(days=1, hours=8),
            economy_price=100.00,
            business_price=500.00,
            first_class_price=1000.00,
            departure_airport=self.airport,
            arrival_airport=self.airport,
            aircraft=self.aircraft
        )
        self.passenger = PassengerProfile.objects.create(user=self.user)
        
        self.booking = Booking.objects.create(
            flight=self.flight,
            passenger=self.passenger,
            seat_class='Economy',
            number_of_passengers=2,
            status='Pending'
        )

    def test_get_amount_economy(self):
        """Tests that the correct payment amount is calculated for Economy class."""
        payment = Payment(booking=self.booking)
        self.assertEqual(payment.get_amount(), 200.00)

    def test_payment_page_load(self):
        """Tests that the payment page loads successfully."""
        url = reverse('process_payment', args=[self.booking.booking_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_process_payment_success(self):
        """Tests successful payment processing and booking status update."""
        url = reverse('process_payment', args=[self.booking.booking_id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Payment.objects.filter(booking=self.booking).exists())
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'Confirmed')

    def test_redirect_if_already_confirmed(self):
        """Tests that users are redirected if the booking is confirmed."""
        self.booking.status = 'Confirmed'
        self.booking.save()
        url = reverse('process_payment', args=[self.booking.booking_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_cannot_pay_others_booking(self):
        """Tests that a user cannot access the payment page for another user's booking."""
        self.client.login(username='tester', password='password')
        url = reverse('process_payment', args=[self.booking.booking_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_amount_business_class(self):
        """Tests that the correct payment amount is calculated for Business class."""
        biz_booking = Booking.objects.create(
            flight=self.flight, passenger=self.passenger, seat_class='Business', number_of_passengers=1
        )
        payment = Payment(booking=biz_booking)

        self.assertEqual(payment.get_amount(), 500.00)

    def test_get_amount_first_class(self):
        """Tests that the correct payment amount is calculated for First class."""
        first_booking = Booking.objects.create(
            flight=self.flight, passenger=self.passenger, seat_class='First', number_of_passengers=3
        )
        payment = Payment(booking=first_booking)

        self.assertEqual(payment.get_amount(), 3000.00)

    def test_get_amount_invalid_class_returns_zero(self):
        """Tests that an invalid seat class returns a payment amount of 0."""
        bad_booking = Booking.objects.create(
            flight=self.flight, passenger=self.passenger, seat_class='Invalid', number_of_passengers=1
        )
        payment = Payment(booking=bad_booking)
        self.assertEqual(payment.get_amount(), 0)



    def test_payment_creation_sets_date(self):
        """Tests that creating a payment automatically sets the payment date."""
        payment = Payment.objects.create(booking=self.booking, payment_method='Cash')
        self.assertIsNotNone(payment.payment_date)
        self.assertAlmostEqual(payment.payment_date, timezone.now(), delta=timedelta(seconds=10))

    def test_pay_for_cancelled_booking_fails(self):
        """Tests that payment cannot be processed for a cancelled booking."""
        self.booking.status = 'Cancelled'
        self.booking.save()
        url = reverse('process_payment', args=[self.booking.booking_id])
        
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302) 

    def test_payment_method_choices(self):
        """Tests that 'Wallet' is a valid payment method choice."""
        payment = Payment(booking=self.booking, payment_method='Wallet')

        self.assertIn('Wallet', dict(Payment.METHOD_CHOICES))

    def test_payment_updates_related_booking_only(self):
        """Tests that payment updates only the related booking's status."""
        booking_b = Booking.objects.create(flight=self.flight, passenger=self.passenger, status='Pending')
        
        url = reverse('process_payment', args=[self.booking.booking_id])
        self.client.post(url)
        
        booking_b.refresh_from_db()
        self.assertEqual(booking_b.status, 'Pending')

    def test_unauthenticated_user_access(self):
        """Tests that unauthenticated users are redirected to login."""
        self.client.logout()
        url = reverse('process_payment', args=[self.booking.booking_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_post_payment_idempotency(self):
        """Tests that submitting payment multiple times does not create duplicate payments."""
        url = reverse('process_payment', args=[self.booking.booking_id])
        self.client.post(url)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Payment.objects.filter(booking=self.booking).count(), 1)