from apscheduler.schedulers.background import BackgroundScheduler
from .tasks import delete_expired_bookings

def start():
    scheduler = BackgroundScheduler()
    
    # Run the job every 1 minute
    scheduler.add_job(delete_expired_bookings, 'interval', minutes=1)

    scheduler.start()