from django.db import models
from django.core.exceptions import ValidationError

class Airport(models.Model):
    airport_code = models.CharField(primary_key=True, max_length=3)
    airport_name = models.CharField(max_length=100, null=False)
    city = models.CharField(max_length=50, null=False)
    country = models.CharField(max_length=50, null=False)

    def __str__(self):
        return f"{self.airport_name} ({self.airport_code})"

    class Meta:
        db_table = 'Airport'


class Aircraft(models.Model):
    aircraft_id = models.AutoField(primary_key=True)
    model = models.CharField(max_length=50, null=False)
    economy_class = models.PositiveIntegerField(default=150)
    business_class = models.PositiveIntegerField(default=16)
    first_class = models.PositiveIntegerField(default=8)

    def __str__(self):
        return self.model

    class Meta:
        db_table = 'Aircraft'


class Flight(models.Model):
    flight_number = models.CharField(primary_key=True, max_length=10)
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()
    economy_price = models.DecimalField(max_digits=10, decimal_places=2, default=300.00)
    business_price = models.DecimalField(max_digits=10, decimal_places=2, default=800.00)
    first_class_price = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00)
    departure_airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='departing_flights')
    arrival_airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='arriving_flights')
    aircraft = models.ForeignKey(Aircraft, on_delete=models.PROTECT)

    def available_seats_dynamic(self):
        from bookings.models import Booking
        booked_economy = Booking.objects.filter(flight=self, seat_class='Economy').count()
        booked_business = Booking.objects.filter(flight=self, seat_class='Business').count()
        booked_first_class = Booking.objects.filter(flight=self, seat_class='First').count()
        total_seats = self.aircraft.economy_class + self.aircraft.business_class + self.aircraft.first_class
        booked_seats = booked_economy + booked_business + booked_first_class
        return total_seats - booked_seats

    def flight_time(self):
        if self.departure_datetime and self.arrival_datetime:
            diff = self.arrival_datetime - self.departure_datetime
            total_seconds = diff.total_seconds()
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{int(hours)} hours and {int(minutes)} minutes"
        return None

    def check_flight(self):
        if self.departure_datetime >= self.arrival_datetime:
            raise ValidationError("Departure time must be before arrival time.")
        if self.departure_airport == self.arrival_airport:
            raise ValidationError("Departure and arrival airports cannot be the same.")
        if any(p < 0 for p in [self.economy_price, self.business_price, self.first_class_price]):
            raise ValidationError("Prices must be positive.")

    def __str__(self):
        return f"{self.flight_number}"

    class Meta:
        db_table = 'Flight'
