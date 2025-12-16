from django.apps import AppConfig

class BookingsConfig(AppConfig):
    """Configuration for the Bookings application"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'

    def ready(self):
        """Initializes application-specific logic when the app is ready.

        Starts the background updater for handling expired bookings.
        """

        from . import updater
        updater.start()