# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.timezone import now, timedelta
from django.test import TestCase

from .factories import BookingType30F, UserF, RootNowaitPageF
from ..defaults import NOWAIT_ROOT_SLUG
from ..models import SlotTime, Booking
from ..utils import RequestMessagesTestMixin


class BookingTypeDetailViewTest(TestCase):

    def setUp(self):
        self.booking_type = BookingType30F()
        self.url = '/nowait/{booking_type.slug}/'.format(
            booking_type=self.booking_type)

    def test_get_page_title(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('title' in response.context)
        self.assertEqual(response.context['title'],
                         self.booking_type.title.title())


class SlottimeSelectViewTest(TestCase):

    def setUp(self):
        self.booking_type = BookingType30F()
        self.user = UserF()
        self.url = '/nowait/{slug}/slottime/select/'
        self.client.login(username=self.user.username,
                          password=self.user.username)
        self.root = RootNowaitPageF()

    def test_get_view_with_wrong_booking_type_slug(self):
        response = self.client.get(self.url.format(slug='fake-slug'))
        self.assertRedirects(response, '/%s/' % NOWAIT_ROOT_SLUG)

    def test_get_page_title(self):
        response = self.client.get(
            self.url.format(slug=self.booking_type.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('title' in response.context)
        self.assertEqual(response.context['title'],
                         'Select day and slot time')


class BookingCreateViewTest(RequestMessagesTestMixin, TestCase):
    def setUp(self):
        start = now()
        self.root = RootNowaitPageF()
        self.booking_type = BookingType30F()
        self.slottime = SlotTime.objects.create(
            booking_type=self.booking_type,
            start=start,
            end=start + timedelta(minutes=self.booking_type.slot_length))
        self.booker = UserF()
        self.url = reverse('nowait:booking_create',
                           kwargs={'slottime_pk': self.slottime.pk})
        self.client.login(username=self.booker.username,
                          password=self.booker.username)
        self.data = {'slottime': self.slottime.pk,
                     'notes': 'notes on booking',
                     'telephone': '+399900990'}

    def test_redirect_in_dispacth(self):
        """
        Test if dispacth method redirect to other page if slottime doesn't
        exist.
        """
        response = self.client.get(reverse('nowait:booking_create',
                                           kwargs={'slottime_pk': 999}))
        self.assertRedirects(
            response, '/{page.slug}/'.format(page=self.root))

    def test_slottime_object_is_in_context_data(self):
        """
        Test that slottime object is in view context with key 'slottime'.
        """
        response = self.client.get(self.url)
        self.assertIn('slottime', response.context)
        self.assertEqual(response.context['slottime'], self.slottime)

    def test_slottime_in_form_and_has_initial_value(self):
        """
        Test that 'slottime' is a field in form and is in form initial data
        with rigth value.
        """
        response = self.client.get(self.url)
        form = response.context['form']
        self.assertIn('slottime', form.fields)
        self.assertIn('slottime', form.initial)
        self.assertEqual(form.initial['slottime'], self.slottime.pk)

    def test_on_form_valid_create_new_booking_with_data(self):
        """
        Test valid creation of new booking object and correct setting of
        slottime, notes, booker, telephone fields.
        """
        self.client.post(self.url, self.data)
        booking = Booking.objects.get(slottime=self.slottime)
        booking.booker = self.booker
        booking.notes = self.data['notes']
        booking.telephone = self.data['telephone']

    def test_on_form_valid_set_slottime_to_taken_status(self):
        """
        Test valid creation of new booking object and setting of status to
        take of slottime relative to new booking created
        """
        self.client.post(self.url, self.data)
        booking = Booking.objects.get(slottime=self.slottime)
        self.assertEqual(booking.slottime.status, SlotTime.STATUS.taken)

    def test_on_form_valid_set_message_success(self):
        """
        Test valid creation of new booking object and setting of status to
        take of slottime relative to new booking created
        """
        response = self.client.post(self.url, self.data, follow=True)
        booking = Booking.objects.get(slottime=self.slottime)
        self.assert_in_messages(
            response, booking.get_success_message_on_creation(),
            level=messages.SUCCESS, verbose=True)
