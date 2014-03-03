# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from unittest.mock import Mock, patch, ANY
except ImportError:
    from mock import Mock, patch, ANY

from django.core import mail
from django.core.urlresolvers import reverse
from django.utils.timezone import now, timedelta
from django.test import TestCase, RequestFactory
from .factories import BookingType30F, UserF, RootNowaitPageF
from ..defaults import NOWAIT_ROOT_SLUG
from ..models import SlotTime
from ..utils import RequestMessagesTestMixin
from ..views import BookingCreateView


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
        self.mock_instance = Mock()
        self.mock_instance._meta.fields = []

    def tearDown(self):
        self.mock_instance.reset_mock()

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

    @patch('nowait.views.messages')
    @patch('django.forms.models.construct_instance', spec=True)
    def test_on_form_valid_call_method_save_and_take_slottime(
            self, mock_construct_instance, mock_messages):
        """
        Test that call save_and_take_slottime on Booking object on form_valid
        """
        factory = RequestFactory()
        request = factory.post(self.url, self.data)
        request.user = self.booker
        mock_construct_instance.return_value = self.mock_instance
        BookingCreateView.as_view()(
            request, **{'slottime_pk': self.slottime.pk})
        self.mock_instance.save_and_take_slottime.assert_called_once_with(
            self.slottime, request)

    @patch('nowait.views.messages')
    @patch('django.forms.models.construct_instance', spec=True)
    def test_on_form_valid_call_message_success(
            self, mock_construct_instance, mock_messages):
        """
        Test that call message.success on form_valid
        """
        factory = RequestFactory()
        request = factory.post(self.url, self.data)
        request.user = self.booker
        mock_construct_instance.return_value = self.mock_instance
        BookingCreateView.as_view()(
            request, **{'slottime_pk': self.slottime.pk})
        mock_messages.success.assert_called_once_with(
            request, self.mock_instance.get_success_message_on_creation(),
            extra_tags='safe')

    @patch('nowait.views.messages')
    @patch('django.forms.models.construct_instance', spec=True)
    def test_on_form_valid_call_method_for_send_emais(
            self, mock_construct_instance, mock_messages):
        """
        Test that call message.success on form_valid
        """
        factory = RequestFactory()
        request = factory.post(self.url, self.data)
        request.user = self.booker
        mock_construct_instance.return_value = self.mock_instance
        BookingCreateView.as_view()(
            request, **{'slottime_pk': self.slottime.pk})
        self.mock_instance.send_emails_on_creation.assert_called_once_with(
            request)

    @patch('nowait.views.messages')
    @patch('django.forms.models.construct_instance', spec=True)
    def test_in_on_form_occurs_exception_and_message_error_is_called(
            self, mock_construct_instance, mock_messages):
        """
        Test that message.error is called if booking.save_and_take_slottime
        raise an exception.
        """
        self.mock_instance.save_and_take_slottime.side_effect = Exception('Boom!')
        factory = RequestFactory()
        request = factory.post(self.url, self.data)
        request.user = self.booker
        mock_construct_instance.return_value = self.mock_instance
        BookingCreateView.as_view()(
            request, **{'slottime_pk': self.slottime.pk})
        mock_messages.error.assert_called_once_with(request, ANY)

    @patch('nowait.views.logging.getLogger')
    @patch('nowait.views.messages')
    @patch('django.forms.models.construct_instance', spec=True)
    def test_in_on_form_occurs_exception_and_logging_is_called(
            self, mock_construct_instance, mock_messages, mock_get_logger):
        """
        Test that logger 'django.request' is called if
        booking.save_and_take_slottime raise an exception.
        """
        exception = Exception('Boom!')
        self.mock_instance.save_and_take_slottime.side_effect = exception
        factory = RequestFactory()
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        request = factory.post(self.url, self.data)
        request.user = self.booker
        mock_construct_instance.return_value = self.mock_instance
        BookingCreateView.as_view()(
            request, **{'slottime_pk': self.slottime.pk})
        mock_get_logger.assert_called_once_with('django.request')
        mock_logger.error.assert_called_once_with(
            ANY, request.path, exc_info=str(exception),
            extra={'status_code': 500, 'request': request})

    @patch('nowait.views.messages')
    @patch('django.forms.models.construct_instance', spec=True)
    def test_in_on_form_occurs_exception_and_redirect_in_same_path(
            self, mock_construct_instance, mock_messages):
        """
        Test that message.error is called if booking.save_and_take_slottime
        raise an exception.
        """
        self.mock_instance.save_and_take_slottime.side_effect = Exception('Boom!')
        factory = RequestFactory()
        request = factory.post(self.url, self.data)
        request.user = self.booker
        mock_construct_instance.return_value = self.mock_instance
        response = BookingCreateView.as_view()(
            request, **{'slottime_pk': self.slottime.pk})
        self.assertEqual(response.url, '.')
