# -*- coding: iso-8859-1 -*-

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelMultipleChoiceField
from django.utils.translation import ugettext as _

from mezzanine.utils.models import get_user_model

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Field, Fieldset
from crispy_forms.bootstrap import FormActions

from .models import Booking, BookingType, Email
from .utils import UserChoiceField


class BookingCreateForm(forms.ModelForm):
    class Meta:
        model = Booking
        exclude = ('booker',)

    slottime = forms.CharField(widget=forms.HiddenInput, required=True)

    def __init__(self, *args, **kwargs):
        super(BookingCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'form_create_booking'
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Fieldset(
                '',
                HTML('<div class="alert alert-info text-center">'
                     'Tipo di pratica selezionata: <strong>'
                     ' {{ slottime.booking_type.name }}</strong></div>'),
                HTML('<div class="alert alert-info text-center">'
                     'Fascia oraria selezionata: <strong>'
                     '{{ slottime.start|date:"l j F Y" }} dalle'
                     ' {{ slottime.start|date:"H:i" }} alle'
                     ' {{ slottime.end|date:"H:i" }}</strong>'
                     '&nbsp;&nbsp;&nbsp;<a href="'
                     '{% url \'nowait:slottime_select\''
                     ' slottime.booking_type.slug %}" class="btn btn-small'
                     ' btn-inverse">Cambiala &raquo;</a></div>'),
                'slottime',
                Field('notes', css_class="input-xlarge"),
                Field('telephone', css_class="input-xlarge"),
            ),
            FormActions(
                Submit('booking', _('Booking Confirmation'),
                       css_class='btn-large')
            )
        )

    def clean(self):
        cleaned_data = super(BookingCreateForm, self).clean()
        slottime_pk = cleaned_data.get('slottime')
        try:
            Booking.objects.get(slottime_id=slottime_pk)
            raise forms.ValidationError(_('Slot time selected is already'
                                          ' assigned'))
        except Booking.DoesNotExist:
            pass
        return cleaned_data


class CalendarGoogleConnectForm(forms.Form):
    google_calendar = forms.ChoiceField(widget=forms.Select,
                                        required=True, choices=[])

    def __init__(self, calendars=None, *args, **kwargs):
        super(CalendarGoogleConnectForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'join_calendar_form'
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Fieldset(
                '',
                Field('google_calendar'),
            ),
            FormActions(
                Submit('booking', _('Connect'), css_class='btn-large')
            )
        )

        if calendars:
            self.fields['google_calendar'].choices = calendars


class BookingTypeAdminForm(forms.ModelForm):
    operators = UserChoiceField(
        queryset=get_user_model().objects.order_by(
            'last_name', 'first_name', 'username'),
        required=False,
        widget=FilteredSelectMultiple(_('operators'), False))
    notifications_emails = ModelMultipleChoiceField(
        queryset=Email.objects.order_by('email'),
        required=False,
        widget=FilteredSelectMultiple(_('Emails to notify'), False))

    class Meta:
        model = BookingType
