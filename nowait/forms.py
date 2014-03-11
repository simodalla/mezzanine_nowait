# -*- coding: iso-8859-1 -*-

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelMultipleChoiceField
from django.utils.translation import ugettext as _

from mezzanine.utils.models import get_user_model

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Field, Fieldset
from crispy_forms.bootstrap import FormActions , Alert

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
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        booking_type_info = _('Booking type selected')
        slottime_info = _('Slot time selected')
        from_txt = _('from')
        to_txt = _('to')
        change_label = _('Change it')
        self.helper.layout = Layout(
            Fieldset(
                '',
                HTML('<div class="alert alert-info text-center">'
                     '%s:&nbsp;<strong>'
                     '{{ slottime.booking_type.title }}</strong>'
                     '</div>' % booking_type_info),
                HTML('<div class="alert alert-info text-center">'
                     '%(slottime_info)s:&nbsp;<strong>'
                     '{{ slottime.start|date:"l j F Y" }}&nbsp;%(from)s'
                     ' {{ slottime.start|date:"H:i" }}&nbsp;%(to)s'
                     ' {{ slottime.end|date:"H:i" }}</strong>'
                     '&nbsp;&nbsp;&nbsp;<a role="button"'
                     ' href="' % {'slottime_info': slottime_info,
                                  'from': from_txt, 'to': to_txt} +
                     '{% url \'nowait:slottime_select\' slottime.booking_type.'
                     'slug %}' + '" class="btn btn-primary">%s '
                                 '&raquo;</a></div>' % change_label),
                'slottime',
                'notes',
                'telephone'
            ),

            FormActions(
                HTML('<div class="col-lg-offset-2 col-lg-8">'),
                Submit('create_booking', _('Booking Confirmation'),
                       css_class='btn-large'),
                HTML('</div>')
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
