# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import datetime
from smtplib import SMTPException

try:
    from unittest.mock import Mock, patch, ANY, call
except ImportError:
    from mock import Mock, patch, ANY, call

from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.test import TestCase, TransactionTestCase, RequestFactory
from django.test.utils import override_settings
from django.utils.timezone import (timedelta, make_aware, get_current_timezone,
                                   now)

from mezzanine.conf import settings
from mezzanine.pages.models import Link, RichTextPage

from ..models import (DAYS, Calendar, Email, BookingType, DailySlotTimePattern,
                      SlotTimesGeneration, SlotTime, Booking)
from .factories import (BookingType30F, BookingType45F, BookingTypeF,
                        UserF, AdminF)
from ..utils import get_or_create_root_app_page


class CalendarModelTest(TestCase):

    def test_str(self):
        name = 'calendar name'
        obj = Calendar.objects.create(name=name)
        self.assertEqual(obj.__str__(), name)


class EmailModelTest(TestCase):

    def test_str(self):
        email = 'demo@example.com'
        obj = Email.objects.create(email=email)
        self.assertEqual(obj.__str__(), email)


class BookingTypeModelTest(TestCase):

    def setUp(self):
        self.title = 'bookingtype xxx'
        self.slug = '-'.join(self.title.split(' '))

    def test_str(self):
        obj = BookingType.objects.create(title=self.title)
        self.assertEqual(obj.__str__(),
                         '%s %s' % (obj._meta.verbose_name, self.title))

    def test_get_absolute_url(self):
        obj = BookingType.objects.create(title=self.title)
        self.assertEqual(obj.slug, self.slug)
        self.assertEqual(obj.get_absolute_url(),
                         '/nowait/%s/' % self.slug)

    def test_get_or_create_link_raise_exception_if_no_root_page(self):
        obj = BookingType.objects.create(title=self.title, slug=self.slug)
        self.assertRaises(ImproperlyConfigured, obj.get_or_create_link)

    def test_create_link_with_get_or_create_link_method(self):
        obj = BookingType.objects.create(title=self.title, slug=self.slug)
        get_or_create_root_app_page(RichTextPage, obj._meta.app_label)
        link, created = obj.get_or_create_link()
        self.assertTrue(isinstance(link, Link))
        self.assertTrue(created)
        self.assertEqual(link, obj.link)
        self.assertEqual(link.slug, obj.get_absolute_url())
        self.assertEqual(link.title, obj.title)

    def test_get_or_create_link_delete_old_link(self):
        root_page, created = get_or_create_root_app_page(RichTextPage,
                                                         'nowait')
        old_wrong_link = Link.objects.create(slug='wrong-slug',
                                             parent=root_page)
        old_wrong_link.delete = Mock()
        obj = BookingType.objects.create(title=self.title, slug=self.slug,
                                         link=old_wrong_link)
        self.assertTrue(obj.link, old_wrong_link)
        link, created = obj.get_or_create_link()
        self.assertTrue(isinstance(link, Link))
        self.assertTrue(created)
        self.assertEqual(link, obj.link)
        self.assertEqual(link.slug, obj.get_absolute_url())
        self.assertEqual(link.title, obj.title)
        old_wrong_link.delete.assert_called_once_with()


class DailySlotTimePatternModelTest(TestCase):

    def test_str(self):
        booking_type = BookingType.objects.create(title='bookingtype xxx')
        day = DAYS.mo
        start_time = '11:00'
        end_time = '11:00'
        obj = DailySlotTimePattern.objects.create(
            booking_type=booking_type, day=day,
            start_time=start_time, end_time=end_time)
        self.assertEqual(
            obj.__str__(),
            '%s: %s, %s-%s' % (obj._meta.verbose_name, obj.get_day_display(),
                               obj.start_time, obj.end_time))


class SlotTimesGenerationModelTest(TestCase):

    def setUp(self):
        self.booking_type_30 = BookingType30F()
        self.booking_type_45 = BookingType45F()
        self.user = UserF()
        # 6 may of 2013 is a monday
        self.start_date = make_aware(datetime.datetime(2013, 5, 6, 10, 0),
                                     get_current_timezone())
        self.n_slot = 3
        assert self.start_date.weekday() == 0
        self.st_generation = SlotTimesGeneration.objects.create(
            booking_type=self.booking_type_30, start_date=self.start_date,
            end_date=self.start_date, user=self.user)

    def test_str(self):
        booking_type = BookingType.objects.create(title='bookingtype xxx')
        today = datetime.date.today()
        obj = SlotTimesGeneration.objects.create(
            booking_type=booking_type, start_date=today,
            end_date=today + datetime.timedelta(days=10))
        self.assertEqual(obj.__str__(), '%s n.%s' % (obj._meta.verbose_name,
                                                     obj.pk))

    def test_create_slot_times_method_with_wrong_start_and_end_date(self):
        self.st_generation.end_date = self.start_date - timedelta(days=2)
        self.st_generation.save()
        self.assertRaises(ValueError, self.st_generation.create_slot_times)
        self.st_generation.end_date = self.start_date + timedelta(days=500)
        self.st_generation.save()
        self.assertRaises(ValueError, self.st_generation.create_slot_times)

    def test_create_slot_times_method_without_related_pattern(self):
        """
        Test that the call of method 'create_slot_times' on one Calendar
        without related DailySlotTimePattern raise a ValueError exception
        """
        self.booking_type_30.dailyslottimepattern_set.all().delete()
        self.assertRaisesMessage(
            ValueError,
            "{0} has no related DailySlotTimePattern objects".format(
                self.booking_type_30.title),
            self.st_generation.create_slot_times)

    def test_create_slot_times_method_with_same_day_and_no_dstp(self):
        """
        Test that the call of method 'create_slot_times' on SlotTimesGeneration
        with the same 'start_date' and 'end_date' fields. The same date
        'start_date' and 'end_date' is a weekday that not in
        DailySlotTimePattern day.
        """
        self.booking_type_30.dailyslottimepattern_set.create(
            day=self.start_date.weekday() + 1, start_time='9:00',
            end_time='11:00')
        result, = self.st_generation.create_slot_times()
        self.assertEqual(result, 0)
        self.assertEqual(self.booking_type_30.slottime_set.count(), 0)

    def test_create_slot_times_method_with_same_day(self):
        self.booking_type_30.dailyslottimepattern_set.create(
            day=self.start_date.weekday(), start_time='9:00',
            end_time='11:00')
        result, = self.st_generation.create_slot_times()
        self.assertEqual(result, 4)
        self.assertEqual(self.booking_type_30.slottime_set.count(), 4)
        for slottime in self.booking_type_30.slottime_set.all():
            slottime.status = SlotTime.STATUS.free
            slottime.generation = self.st_generation
            slottime.calendar = self.booking_type_30.calendar
            slottime.booking_type = self.booking_type_30
            slottime.user = self.user

    def test_create_slot_times_method_with_same_day_two_dstp(self):
        self.booking_type_30.dailyslottimepattern_set.create(
            day=self.start_date.weekday(), start_time='9:00',
            end_time='11:00')
        self.booking_type_30.dailyslottimepattern_set.create(
            day=self.start_date.weekday() + 1, start_time='9:00',
            end_time='11:00')
        result, = self.st_generation.create_slot_times()
        self.assertEqual(result, 4)
        self.assertEqual(self.booking_type_30.slottime_set.count(), 4)
        for slottime in self.booking_type_30.slottime_set.all():
            slottime.status = SlotTime.STATUS.free
            slottime.generation = self.st_generation
            slottime.calendar = self.booking_type_30.calendar
            slottime.booking_type = self.booking_type_30
            slottime.user = self.user

    def test_create_slot_times_method_with_more_day(self):
        self.st_generation.end_date = self.start_date + timedelta(days=1)
        self.st_generation.save()
        self.booking_type_30.dailyslottimepattern_set.create(
            day=self.start_date.weekday(), start_time='9:00',
            end_time='11:00')
        self.booking_type_30.dailyslottimepattern_set.create(
            day=self.start_date.weekday() + 1, start_time='11:00',
            end_time='13:00')
        result, = self.st_generation.create_slot_times()
        self.assertEqual(result, 8)
        self.assertEqual(self.booking_type_30.slottime_set.count(), 8)
        for slottime in self.booking_type_30.slottime_set.all():
            slottime.status = SlotTime.STATUS.free
            slottime.generation = self.st_generation
            slottime.calendar = self.booking_type_30.calendar
            slottime.booking_type = self.booking_type_30
            slottime.user = self.user


class SlotTimeModelTest(TestCase):

    def setUp(self):
        self.booking_type_30 = BookingType30F()
        self.booking_type_45 = BookingType45F()
        # 6 may of 2013 is a monday
        self.start_date = make_aware(
            datetime.datetime(2013, 5, 6, 10, 0),
            get_current_timezone())
        self.n_slot = 3
        assert self.start_date.weekday() == 0
        DailySlotTimePattern.objects.create(
            booking_type=self.booking_type_30, day=DAYS.mo,
            start_time=self.start_date,
            end_time=self.start_date + timedelta(
                minutes=self.booking_type_30.slot_length*self.n_slot))

    def test_str_method(self):
        bookingtype = BookingType.objects.create(title='bookingtype xxx')
        start = now()
        end = start + timedelta(minutes=30)
        obj = SlotTime.objects.create(booking_type=bookingtype,
                                      start=start, end=end)
        self.assertEqual(
            obj.__str__(),
            '{obj._meta.verbose_name} {obj.start:%A %d %B %Y %H:%M} -'
            ' {obj.end:%A %d %B %Y %H:%M}'.format(obj=obj))

    def test_clean_method(self):
        bookingtype = BookingTypeF()
        start = now()
        end = start + timedelta(minutes=30)
        slottime = SlotTime.objects.create(booking_type=bookingtype,
                                           start=start, end=end)
        slottime_over = SlotTime()
        slottime_over.start = slottime.start + timedelta(minutes=15)
        slottime_over.end = slottime.end + timedelta(minutes=15)
        self.assertRaises(ValidationError, slottime_over.clean)

    def test_save_method(self):
        bookingtype = BookingTypeF()
        start = now()
        end = start + timedelta(minutes=30)
        slottime = SlotTime.objects.create(booking_type=bookingtype,
                                           start=start, end=end)
        slottime_over = SlotTime()
        slottime_over.start = slottime.start + timedelta(minutes=15)
        slottime_over.end = slottime.end + timedelta(minutes=15)
        self.assertRaises(ValidationError, slottime_over.save)

    # def test_admin_calendar_method(self):
    #     bookingtype = BookingTypeF()
    #     start = now()
    #     end = start + timedelta(minutes=30)
    #     slottime = SlotTime.objects.create(booking_type=bookingtype,
    #                                        start=start, end=end)
    #     self.assertEqual(
    #         slottime.admin_calendar(),
    #         '<a href="{url}?id={calendar.pk}">{calendar.name}</a>'.format(
    #             url=reverse('admin:nowait_calendar_changelist'),
    #             calendar=bookingtype.calendar))


# @skipIf(datetime.date.today().isoweekday() == 7, "On Sunday this test fail")
class SlotTimeManagersTest(TestCase):
    def setUp(self):
        self.booking_types = {}
        self.user = UserF()
        self.admin = AdminF()
        self.start_date = now()
        self.n_slot = 2
        self.start_hour = 9
        count = 0
        self.n_pre_slottimes = 0
        for btf in [BookingType30F(), BookingType45F()]:
            start = datetime.datetime.combine(datetime.date.today(),
                                              datetime.time(
                                                  self.start_hour))
            end = start + datetime.timedelta(
                minutes=(self.n_slot * btf.slot_length))
            DailySlotTimePattern.objects.create(
                booking_type=btf,
                day=self.start_date.weekday() + count,
                start_time='{0}:{1}'.format(start.hour, start.minute),
                end_time='{0}:{1}'.format(end.hour, end.minute), )
            st_generation = SlotTimesGeneration.objects.create(
                booking_type=btf,
                start_date=self.start_date - timedelta(days=1),
                end_date=self.start_date + timedelta(days=30),
                user=self.admin)
            result, = st_generation.create_slot_times()
            count += 1
            self.n_pre_slottimes += result
            self.booking_types.update(
                {str(btf.slot_length): (btf, result)})

    def test_free_manager(self):
        self.assertEqual(SlotTime.free.count(), self.n_pre_slottimes)
        st_taken = SlotTime.objects.all()[0]
        st_taken.status = SlotTime.STATUS.taken
        st_taken.save()
        self.assertEqual(SlotTime.free.count(),
                         self.n_pre_slottimes - 1)
        self.assertEqual(SlotTime.taken.count(), 1)


SERVER_EMAIL = 'serveremail@example.com'


class BookingModelTest(TestCase):

    def setUp(self):
        start = now()
        booking_type = BookingType30F()
        self.slottime = SlotTime.objects.create(
            booking_type=booking_type,
            start=start,
            end=start + timedelta(minutes=booking_type.slot_length),
            status=SlotTime.STATUS.taken)
        self.booker = UserF()

    def test_str(self):
        booking = Booking.objects.create(slottime=self.slottime,
                                         booker=self.booker)
        self.assertEqual(booking.__str__(),
                         '%s n.%s' % (booking._meta.verbose_name, booking.pk))

    def test_property_success_message_on_creation(self):
        booking = Booking()
        booking.booker = self.booker
        booking.slottime = self.slottime
        booking.save()
        self.assertEqual(
            booking.success_message_on_creation,
            'Your booking for "{}" is succesfully created with'
            ' id: <b>{}</b>'.format(self.slottime.booking_type.title,
                                    booking.pk))

    @override_settings(SERVER_EMAIL=SERVER_EMAIL)
    @patch('nowait.models.send_mail_template')
    def test_send_emails_on_creation_without_errors(
            self, mock_send_mail_template):
        emails = ['mail1@example.com', 'mail2@example.com']
        mock_emails = Mock()
        mock_emails.return_value = emails
        self.slottime.booking_type.get_notification_email = mock_emails
        request = RequestFactory().get('/fake')
        booking = Booking()
        booking.booker = self.booker
        booking.slottime = self.slottime
        booking.save()
        booking.send_emails_on_creation(request)
        context = {'booking': booking, 'request': request}
        calls = [call(ANY, settings.SERVER_EMAIL, self.booker.email,
                      context=context),
                 call(ANY, settings.SERVER_EMAIL, emails, context=context)]
        mock_send_mail_template.has_calls(calls)

    @override_settings(SERVER_EMAIL=SERVER_EMAIL)
    @patch('nowait.views.logging.getLogger')
    @patch('nowait.models.send_mail_template')
    def test_send_emails_on_creation_raise_exception(
            self, mock_send_mail_template, mock_get_logger):
        exception = SMTPException('Boom!')
        self.slottime.booking_type.get_notification_email = (
            Mock(return_value=[]))
        mock_send_mail_template.side_effect = exception
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        request = RequestFactory().get('/fake')
        booking = Booking()
        booking.booker = self.booker
        booking.slottime = self.slottime
        booking.save()
        booking.send_emails_on_creation(request)
        mock_get_logger.has_calls(call('django.request'),
                                  call('django.request'))
        log_call = call(ANY, request.path, exc_info=str(exception),
                        extra={'status_code': 500, 'request': request})
        mock_logger.error.has_calls(log_call, log_call)


class BookingModelWithTransTest(TransactionTestCase):
    def setUp(self):
        start = now()
        self.booking_type = BookingType30F()
        self.slottime = SlotTime.objects.create(
            booking_type=self.booking_type,
            start=start,
            end=start + timedelta(minutes=self.booking_type.slot_length))
        self.booker = UserF()
        self.request = RequestFactory().get('/fake')
        self.request.user = self.booker

    def test_save_and_take_slottime_method_ok(self):
        booking = Booking()
        booking.telephone = '3339988999'
        booking.notes = 'bla bla bla'
        booking.save_and_take_slottime(self.slottime, self.request)
        self.assertIsNotNone(booking.pk)
        self.assertEqual(booking.booker, self.request.user)
        self.assertEqual(booking.slottime, self.slottime)
        self.assertEqual(booking.slottime.status, SlotTime.STATUS.taken)
