from django import forms
from .models import Flight
from django.core.exceptions import ValidationError


class NewFlightForm(forms.ModelForm):

    class Meta:

        model = Flight
        fields = [
            'flight_number',
            'departure_datetime',
            'arrival_datetime',
            'economy_price',
            'business_price',
            'first_class_price',
            'departure_airport',
            'arrival_airport',
            'aircraft'
        ]

        widgets = {
            'departure_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'arrival_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name ,field in self.fields.items():

            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label
            })

            self.fields['aircraft'].widget.attrs.update({'class': 'form-select'})
            self.fields['departure_airport'].widget.attrs.update({'class': 'form-select'})
            self.fields['arrival_airport'].widget.attrs.update({'class': 'form-select'})

            self.fields['aircraft'].empty_label = 'Select Aircraft Type'
            self.fields['departure_airport'].empty_label = 'Select Departure Airport'
            self.fields['arrival_airport'].empty_label = 'Select Destination Airport'

    
    def clean(self):
        """
        Override clean() method to validate model
        """

        cleaned_data = super().clean()
        flight = Flight(**cleaned_data)

        try:
            flight.check_flight()
        except ValidationError as e:
            raise forms.ValidationError(e.message)
        
        return cleaned_data
    

class FlightForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = [
            'flight_number', 'aircraft', 'departure_airport', 'arrival_airport',
            'departure_datetime', 'arrival_datetime', 'economy_price',
            'business_price', 'first_class_price', 'status'
        ]
        widgets = {
            'departure_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'arrival_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'flight_number': forms.TextInput(attrs={'class': 'form-control'}),
            'economy_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'business_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'first_class_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'aircraft': forms.Select(attrs={'class': 'form-select'}),
            'departure_airport': forms.Select(attrs={'class': 'form-select'}),
            'arrival_airport': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        dep = cleaned_data.get('departure_datetime')
        arr = cleaned_data.get('arrival_datetime')
        dep_airport = cleaned_data.get('departure_airport')
        arr_airport = cleaned_data.get('arrival_airport')

        if dep and arr and arr < dep:
            raise forms.ValidationError("Arrival time cannot be before departure time.")
            
        if dep_airport and arr_airport and dep_airport == arr_airport:
            raise forms.ValidationError("Departure and Arrival airports cannot be the same.")
            
        return cleaned_data