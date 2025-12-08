
"""
This file defines the forms used for user registration.
It includes:
- AdminCreationForm: A form for creating new Admin users (is_staff=True).
- PassengerCreationForm: A form for creating new Passenger users (is_staff=False)
  and their associated PassengerProfile.
"""


from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import PassengerProfile
from datetime import date

import re


class PassengerCreationForm(UserCreationForm):
    """
    A form for creating new Passenger accounts.

    Inherits from UserCreationForm and adds extra fields for the
    PassengerProfile. Overrides the save() method to create both
    the User and the linked PassengerProfile.
    """

    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))

    passport = forms.CharField(max_length=7, required=False)
    phone_number = forms.CharField(max_length=10, required=False)
    nationality = forms.CharField(max_length=10, required=False)

    class Meta(UserCreationForm.Meta):
        """
        Configuration class for the PassengerCreationForm.
        """
        model = User
        fields = ('email', 'first_name', 'last_name')


    def __init__(self, *args, **kwargs):
        """
        This adds Bootstrap styling 'form-control' class
        to all fields to render correctly
        """
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():

            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label or field_name
            })

        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

    def clean_nationality(self):

        nid = self.cleaned_data.get('nationality')

        if not re.match(r'^\d{10}$', nid):
            raise forms.ValidationError("National ID must be exactly 10 numbers.")
        return nid

    def clean_passport(self):
        passport = self.cleaned_data.get('passport')
        if passport:

            if not re.match(r'^[A-Za-z0-9]{9}$', passport):
                raise forms.ValidationError("Passport must be exactly 9 alphanumeric characters.")
        return passport

    def clean_date_of_birth(self):
        """
        A custom validation method that checks if the user is aged 18 or above.
        Automatically called when form.is_valid() is invoked.
        """

        dob = self.cleaned_data.get('date_of_birth')

        if dob:
            today = date.today()

            cutoff_date = today.replace(year=today.year - 18)

            if dob > cutoff_date:
                raise forms.ValidationError("Sorry. You must be at least 18 years old to be able to register!")
            
        return dob

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


        user.username = self.cleaned_data.get('email')

        # very important. This ensures this user is not an admin
        user.is_staff = False

        if commit:
            user.save()


            PassengerProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number') or None,
                passport=self.cleaned_data.get('passport') or None,
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                nationality=self.cleaned_data.get('nationality') or None
            )

        return user


class EmailAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that uses email address of user.
    """
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                self.user_cache = user
            except User.DoesNotExist:
                self.add_error('username', 'Invalid email or password.')
        
        return self.cleaned_data
