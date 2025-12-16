
"""Forms for user registration and profile management.

This module defines the forms used for creating and updating user accounts,
including:
- PassengerCreationForm: For registering new passengers.
- EmailAuthenticationForm: For logging in with email.
- UserUpdateForm & ProfileUpdateForm: For updating user details.
"""


from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import PassengerProfile
from datetime import date

import re


class PassengerCreationForm(UserCreationForm):
    """Form for creating new Passenger accounts and profiles.

    Inherits from UserCreationForm and adds fields for PassengerProfile.
    """

    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))

    passport = forms.CharField(max_length=9, required=False)
    phone_number = forms.CharField(max_length=10, required=False)
    nationality = forms.CharField(max_length=10, required=False)

    class Meta(UserCreationForm.Meta):
        """Meta options for PassengerCreationForm."""
        model = User
        fields = ('email', 'first_name', 'last_name')


    def __init__(self, *args, **kwargs):
        """Initializes the form and applies Bootstrap styling."""
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():

            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label or field_name
            })

        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})



    def clean_email(self):
        """Validates that the email is not already registered.

        Returns:
            str: The validated email address.

        Raises:
            ValidationError: If a user with this email already exists.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered. Please login instead.")
        return email
    
    def clean_nationality(self):
        """Validates that the nationality (ID) is exactly 10 digits.

        Returns:
            str: The validated nationality ID.

        Raises:
            ValidationError: If the ID format is invalid.
        """
        nid = self.cleaned_data.get('nationality')

        if not re.match(r'^\d{10}$', nid):
            raise forms.ValidationError("National ID must be exactly 10 numbers.")
        return nid

    def clean_passport(self):
        """Validates that the passport number is 9 alphanumeric characters.

        Returns:
            str: The validated passport number.

        Raises:
            ValidationError: If the passport format is invalid.
        """
        passport = self.cleaned_data.get('passport')
        if passport:

            if not re.match(r'^[A-Za-z0-9]{9}$', passport):
                raise forms.ValidationError("Passport must be exactly 9 alphanumeric characters.")
        return passport

    def clean_date_of_birth(self):
        """Validates that the passenger is at least 18 years old.

        Returns:
            date: The validated date of birth.

        Raises:
            ValidationError: If the user is under 18.
        """

        dob = self.cleaned_data.get('date_of_birth')

        if dob:
            today = date.today()

            cutoff_date = today.replace(year=today.year - 18)

            if dob > cutoff_date:
                raise forms.ValidationError("Sorry. You must be at least 18 years old to be able to register!")
            
        return dob
    
    def clean_phone_number(self):
        """Validates that the phone number is exactly 10 digits.

        Returns:
            str: The validated phone number.

        Raises:
            ValidationError: If the phone number format is invalid.
        """
        phone = self.cleaned_data.get('phone_number')
        if phone and not re.match(r'^\d{10}$', phone):
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        
        return phone

    def save(self, commit=True):
        """Saves the User and PassengerProfile.

        Args:
            commit (bool): Whether to save to the database.

        Returns:
            User: The created User instance.
        """

        user = super().save(commit=False)


        user.username = self.cleaned_data.get('email')

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
    """Authentication form using email instead of username."""
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def clean(self):
        """Validates the email and password against the database.

        Returns:
            dict: The cleaned data.

        Raises:
            ValidationError: If the email/password combination is invalid.
        """
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email__iexact=email)
                self.user_cache = user
            except User.DoesNotExist:
                self.add_error('username', 'Invalid email or password.')
        
        return self.cleaned_data


class UserUpdateForm(forms.ModelForm):
    """Form for updating basic user information (first name, last name, email).
    
    This form is used by both passengers and admins to update their core
    user account details.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating passenger profile details.
    
    Allows passengers to update their specific profile information such as
    phone number, date of birth, nationality, and passport number.
    """
    class Meta:
        model = PassengerProfile
        fields = ['phone_number', 'date_of_birth', 'nationality', 'passport']
        labels = {
            'nationality': 'National ID / Iqama',
            'passport': 'Passport Number',
            'date_of_birth': 'Date of Birth',
            'phone_number': 'Phone Number'
        }
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05XXXXXXXX'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit ID'}),
            'passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9-char alphanumeric'}),
        }



    def clean_phone_number(self):
        """Validates that the phone number is exactly 10 digits.

        Returns:
            str: The validated phone number.
        """
        phone = self.cleaned_data.get('phone_number')
        if phone and not re.match(r'^\d{10}$', phone):
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return phone

    def clean_nationality(self):
        """Validates that the nationality (ID) is exactly 10 digits.

        Returns:
            str: The validated nationality ID.
        """
        nid = self.cleaned_data.get('nationality')

        if nid and not re.match(r'^\d{10}$', nid):
            raise forms.ValidationError("National ID must be exactly 10 numbers.")
        return nid

    def clean_passport(self):
        """Validates that the passport number is 9 alphanumeric characters.

        Returns:
            str: The validated passport number.
        """
        passport = self.cleaned_data.get('passport')
        if passport and not re.match(r'^[A-Za-z0-9]{9}$', passport):
            raise forms.ValidationError("Passport must be exactly 9 alphanumeric characters.")
        return passport

    def clean_date_of_birth(self):
        """Validates the date of birth.

        Ensures the date is not in the future and the user is at least 18 years old.

        Returns:
            date: The validated date of birth.

        Raises:
            ValidationError: If the date is invalid or user is underage.
        """
        dob = self.cleaned_data.get('date_of_birth')
        if dob:

            if dob > date.today():
                raise forms.ValidationError("Date of birth cannot be in the future.")
            

            today = date.today()
            cutoff_date = today.replace(year=today.year - 18)
            if dob > cutoff_date:
                raise forms.ValidationError("You must be at least 18 years old.")
            
                
        return dob