from django import forms
from .models import Ticket
from datetime import date
import re

class TicketForm(forms.ModelForm):

    class Meta:
        model = Ticket

        fields = ['passenger_name', 'passport', 'nationality', 'passenger_dob']
        labels = {
            'nationality': 'National ID / Iqama',
            'passenger_name': 'Full Name'
        }
        widgets = {
            'passenger_dob': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


    def clean_nationality(self):
        nid = self.cleaned_data.get('nationality')

        if not re.match(r'^\d{10}$', nid):
            raise forms.ValidationError("National ID must be exactly 10 numbers.")
        return nid

    def clean_passport(self):
        passport = self.cleaned_data.get('passport')

        if not re.match(r'^[A-Za-z]{1}[A-Za-z0-9]{8}$', passport):
            raise forms.ValidationError("Passport must be exactly 9 alphanumeric characters and starts with a letter!")
        return passport

    def clean_passenger_dob(self):
        dob = self.cleaned_data.get('passenger_dob')
        if dob:
            if dob > date.today():
                raise forms.ValidationError("Date of birth cannot be in the future.")

        return dob

    def clean_passenger_name(self):
        name = self.cleaned_data.get('passenger_name')
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise forms.ValidationError("Name must contain only letters (no numbers or symbols).")
        return name