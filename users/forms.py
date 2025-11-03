
"""
This file defines the forms used for user registration.
It includes:
- AdminCreationForm: A form for creating new Admin users (is_staff=True).
- PassengerCreationForm: A form for creating new Passenger users (is_staff=False)
  and their associated PassengerProfile.
"""


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import PassengerProfile


class PassengerCreationForm(UserCreationForm):
    """
    A form for creating new Passenger accounts.

    Inherits from UserCreationForm and adds extra fields for the
    PassengerProfile. Overrides the save() method to create both
    the User and the linked PassengerProfile.
    """

    phone_number = forms.CharField(max_length=20, required=False)
    passport_number = forms.CharField(max_length=50, required=False)

    class Meta(UserCreationForm.Meta):
        """
        Configuration class for the PassengerCreationForm.
        """
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def save(self, commit=True):
        """
        Saves the new User instance, ensures they are not staff,
        and creates their linked PassengerProfile.

        Args:
            commit (bool): If True (default), save the user and profile
                           to the database.

        Returns:
            django.contrib.auth.models.User: The newly created passenger user object.
        """

        user = super().save(commit=False)

        # very important. This ensures this user is not an admin
        user.is_staff = False

        if commit:
            user.save()

            PassengerProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number'),
                passport_number=self.cleaned_data.get('passport_number')
            )

        return user
    
