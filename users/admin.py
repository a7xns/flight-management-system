from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PassengerProfile, Admin

# Register your models here.



class PassengerProfileInline(admin.StackedInline):
    """
    This class defines how to show the PassengerProfile *inside* the User admin page.
    'admin.StackedInline' means the fields will be stacked vertically.
    """

    model = PassengerProfile
    can_delete = False

    verbose_name_plural = 'Passenger Profile'




class UserAdmin(BaseUserAdmin):
    """
    This creates our *new* custom admin page for the User model.
    It inherits all the features of the default admin page ('BaseUserAdmin').
    """

    # to install the 'PassengerProfileInline' plugin
    inlines = (PassengerProfileInline,)



admin.site.unregister(User)
admin.site.register(User, UserAdmin)