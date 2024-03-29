import datetime
from datetimewidget.widgets import DateTimeWidget
from .models import Appointment, Doctor
from django import forms


class AppointmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].label = 'Begin time'
        self.fields['end_date'].label = 'End time'
        self.fields['patients_remarks'].label = 'Remarks'

        self.fields['start_date'].widget.attrs.update({
            'class': 'uk-width-auto uk-input'
        })
        self.fields['end_date'].widget.attrs.update({
            'class': 'uk-width-auto uk-input'
        })
        self.fields['patients_remarks'].widget.attrs.update({
            'class': 'uk-width-auto uk-input'
        })

    class Meta:
        model = Appointment
        fields = {'patients_remarks', 'start_date', 'end_date'}
        dateTimeOptions = {
            'autoclose': True,
            'startDate': str(datetime.datetime.today().date()),
            'endDate': str(datetime.datetime.today().date() + datetime.timedelta(1)),
            'format': 'mm/dd/yyyy hh:ii',
        }
        widgets = {
            'start_date': DateTimeWidget(options=dateTimeOptions),
            'end_date': DateTimeWidget(options=dateTimeOptions),
        }


class InviteDocForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(InviteDocForm, self).__init__(*args, **kwargs)
        self.fields['user'].label = 'User'
        self.fields['user'].widget.attrs.update({
            'class': 'uk-width-auto uk-input'
        })

        self.fields['name'].label = 'Name'
        self.fields['name'].widget.attrs.update({
            'class': 'uk-width-auto uk-input'
        })
    class Meta:
        model = Doctor
        fields = {'user', 'name'}