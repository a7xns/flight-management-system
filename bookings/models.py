from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class Booking(models.Model):
    """Represents a flight booking made by passenger.
    
    Attributes:
        booking_id: The unique identifier for the booking.
        booking_date: The date and time when the booking was created.
        status: The current status of the booking (e.g., 'Confirmed', 'Pending', 'Cancelled').
        number_of_passengers: The number of passengers included in the booking.
        seat_class: The class of seats booked (e.g., 'Economy', 'Business', 'First').
        passenger: The passenger profile associated with the booking.
        flight: The flight associated with the booking.
    """
    
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
        """Calculates the total price of the booking based on seat class and passenger count.

        Returns:
            The calculated total price.

        Raises:
            ValidationError: If the seat class is invalid.
        """
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
        """Validates that the number of passengers is greater than zero.

        Raises:
            ValidationError: If the number of passengers is zero or negative.
        """
        if self.number_of_passengers <= 0:
            raise ValidationError("Number of passengers must be greater than zero.")

    def __str__(self):
        """Returns the string representation of the booking.

        Returns:
            str: The string representation of the booking.
        """
        return f"Booking {self.booking_id}"

    class Meta:
        db_table = 'Booking'

class Ticket(models.Model):
    """Represents a specific ticket for a seat within a booking.

    Attributes:
        ticket_id: The unique identifier for the ticket.
        seat_number: The seat number assigned to the ticket.
        passenger_name: The name of the passenger holding the ticket.
        passport: The passport number of the passenger.
        passenger_dob: The date of birth of the passenger.
        nationality: The nationality of the passenger.
        booking: The booking associated with this ticket.
    """
    ticket_id = models.AutoField(primary_key=True)
    seat_number = models.CharField(
        max_length=10, 
        validators=[RegexValidator(r'^\d+[A-Za-z]+$', 'Invalid seat number format')]
    )
    passenger_name = models.CharField(max_length=100)
    passport = models.CharField(max_length=20)
    passenger_dob = models.DateField()
    nationality = models.CharField(max_length=50)
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='tickets')

    def __str__(self):
        """Returns the string representation of the ticket.

        Returns:
            str: The string representation of the ticket.
        """
        return f"Ticket {self.ticket_id} - {self.seat_number} for {self.passenger_name}"

    class Meta:
        db_table = 'Ticket'

