from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking

def delete_expired_bookings():
    """
    Finds bookings that have been 'Pending' for more than 10 minutes
    and cancels them to release the seats.
    """
    cutoff_time = timezone.now() - timedelta(minutes=5)
    
    expired_bookings = Booking.objects.filter(
        status='Pending',
        booking_date__lt=cutoff_time
    )
    
    count = expired_bookings.count()
    
    if count > 0:
        # Update status to Cancelled
        expired_bookings.update(status='Cancelled')
        print(f"[Auto-Scheduler] Cancelled {count} expired bookings. Seats released.")
    else:
        # Optional: Print this to prove it's working (remove later to keep logs clean)
        print("[Auto-Scheduler] No expired bookings found.")