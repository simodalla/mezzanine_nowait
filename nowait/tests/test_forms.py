# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.test import TestCase
from django.utils.timezone import now, timedelta

from .factories import BookingType30F, UserF
from ..models import Booking, SlotTime
from ..forms import BookingCreateForm


class BookingCreateFormTest(TestCase):

    def setUp(self):
        start = now()
        self.booking_type = BookingType30F()
        self.slottime = SlotTime.objects.create(
            booking_type=self.booking_type,
            start=start,
            end=start + timedelta(minutes=self.booking_type.slot_length))
        self.booker = UserF()
        self.client.login(username=self.booker.username,
                          password=self.booker.username)
        self.data = {'slottime': self.slottime.pk,
                     'notes': 'notes on booking',
                     'telephone': '+399900990'}

    def test_form_is_not_valid(self):
        """
        Test that clean method raise ValidationError if slottime pk passed in
        form is already linked to Booking object.
        """
        Booking.objects.create(booker=self.booker, slottime=self.slottime)
        form = BookingCreateForm(self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(form.errors['__all__'][0],
                         'Slot time selected is already assigned')

    def test_form_is_valid(self):
        form = BookingCreateForm(self.data)
        self.assertTrue(form.is_valid())
