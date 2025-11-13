from django import forms
from .models import Appointment, Service
from datetime import date, timedelta

class AppointmentForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True),
        empty_label="Select a service"
    )
    appointment_date = forms.DateField(
        widget=forms.SelectDateWidget(),
        initial=date.today() + timedelta(days=1)  # Can't book for today
    )
    
    class Meta:
        model = Appointment
        fields = ['client_name', 'client_email', 'client_phone', 'service', 
                 'appointment_date', 'appointment_time', 'special_requests']
        widgets = {
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
            'special_requests': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Any special requests or design ideas...'}),
        }
    
    def clean_appointment_date(self):
        appointment_date = self.cleaned_data['appointment_date']
        if appointment_date < date.today():
            raise forms.ValidationError("You cannot book an appointment in the past.")
        return appointment_date