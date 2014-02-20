# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import datetime
from django.test import TestCase
from django.utils import timezone
from ..models import (DAYS, Calendar, Email, BookingType, DailySlotTimePattern,
                      SlotTimesGeneration, SlotTime, Booking)


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

    def test_str(self):
        title = 'booking xxx'
        obj = BookingType.objects.create(title=title)
        self.assertEqual(obj.__str__(),
                         '%s %s' % (obj._meta.verbose_name, title))

    def test_get_absolute_url(self):
        title = 'bookingtype xxx'
        slug = '-'.join(title.split(' '))
        obj = BookingType.objects.create(title=title)
        self.assertEqual(obj.slug, slug)
        self.assertEqual(obj.get_absolute_url(),
                         '/nowait/bookingtype/%s/' % slug)


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

    def test_str(self):
        booking_type = BookingType.objects.create(title='bookingtype xxx')
        today = datetime.date.today()
        obj = SlotTimesGeneration.objects.create(
            booking_type=booking_type, start_date=today,
            end_date=today + datetime.timedelta(days=10))
        self.assertEqual(obj.__str__(), '%s n.%s' % (obj._meta.verbose_name,
                                                     obj.pk))


class SlotTimeModelTest(TestCase):

    def test_str(self):
        booking_type = BookingType.objects.create(title='bookingtype xxx')
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)
        obj = SlotTime.objects.create(booking_type=booking_type,
                                      start=start, end=end)
        self.assertEqual(
            obj.__str__(),
            '{obj._meta.verbose_name} {obj.start:%A %d %B %Y %H:%M} -'
            ' {obj.end:%A %d %B %Y %H:%M}'.format(obj=obj))


class BookingModelTest(TestCase):

    def test_str(self):
        obj = Booking.objects.create()
        self.assertEqual(obj.__str__(),
                         '%s n.%s' % (obj._meta.verbose_name, obj.pk))


