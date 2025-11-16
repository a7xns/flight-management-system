from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Pending', 'Pending'),
        ('Cancelled', 'Cancelled'),
    ]

    SEAT_CLASS_CHOICES = [
        ('Economy', 'Economy'),
        ('Business', 'Business'),
        ('First', 'First'),
    ]
    
    booking_id = models.AutoField(primary_key=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    number_of_passengers = models.PositiveIntegerField(default=1)
    seat_class = models.CharField(max_length=20, choices=SEAT_CLASS_CHOICES, default='Economy')
    passenger = models.ForeignKey('users.PassengerProfile', on_delete=models.RESTRICT)
    flight = models.ForeignKey('flights.Flight', on_delete=models.RESTRICT)

    def total_price(self):
        seat_prices = {
            'Economy': self.flight.economy_price,
            'Business': self.flight.business_price,
            'First': self.flight.first_class_price,
        }
        price = seat_prices.get(self.seat_class)
        if price is None:
            raise ValidationError("Invalid seat class")
        return price * self.number_of_passengers

    def check_number_of_passenger(self):
        if self.number_of_passengers <= 0:
            raise ValidationError("Number of passengers must be greater than zero.")

    def __str__(self):
        return f"Booking {self.booking_id}"

    class Meta:
        db_table = 'Booking'

class Ticket(models.Model):
    ticket_id = models.AutoField(primary_key=True)
    seat_number = models.CharField(
        max_length=10, 
        validators=[RegexValidator(r'^\d+[A-Za-z]+$', 'Invalid seat number format')]
    )
    passenger_name = models.CharField(max_length=100)
    passport = models.CharField(max_length=20, unique=True)
    passenger_dob = models.DateField()
    nationality = models.CharField(max_length=50)
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='tickets')

    def __str__(self):
        return f"Ticket {self.ticket_id} - {self.seat_number} for {self.passenger_name}"

    class Meta:
        db_table = 'Ticket'

