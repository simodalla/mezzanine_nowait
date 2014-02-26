# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.contrib.admin import AdminSite
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import timedelta, now, datetime
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import patch, Mock

from ..admin import SlotTimeAdmin, CalendarAdmin, SlotTimesGenerationAdmin
from ..models import SlotTime, Calendar, SlotTimesGeneration
from .factories import BookingTypeF


class CalendarAdminTest(TestCase):

    def test_booking_type_links_callable(self):
        bookingtypes = [BookingTypeF() for i in range(0, 3)]
        calendar = bookingtypes[0].calendar
        calendaradmin = CalendarAdmin(Calendar, AdminSite)
        result = '<br >'.join(
            ['<a href="{0}?id={1}">{2}</a>'.format(reverse(
                'admin:nowait_bookingtype_changelist'), bt.pk, bt.title)
             for bt in calendar.bookingtype_set.order_by('title')])
        self.assertEqual(calendaradmin.booking_type_links(calendar), result)


class SlotTimeAdminTest(TestCase):

    def test_get_calendar_link_callable(self):
        bookingtype = BookingTypeF()
        start = now()
        end = start + timedelta(minutes=30)
        obj = SlotTime.objects.create(booking_type=bookingtype,
                                      start=start, end=end)
        slottimeadmin = SlotTimeAdmin(SlotTime, AdminSite)
        self.assertEqual(
            slottimeadmin.calendar_link(obj),
            '<a href="{url}?id={calendar.pk}">{calendar.name}</a>'.format(
                url=reverse('admin:nowait_calendar_changelist'),
                calendar=bookingtype.calendar))


class BookingTypeAdminTest(TestCase):
    pass


class SlotTimesGenerationAdminTest(TestCase):

    def test_slottimes_lt_callble_without_related_slottime(self):
        slottimegeneration = Mock()
        slottimegeneration.slottime_set.count.return_value = 0
        stgadmin = SlotTimesGenerationAdmin(SlotTimesGeneration, AdminSite)
        self.assertEqual(stgadmin.slottimes_lt(slottimegeneration), '0')

    def test_slottimes_lt_callble_with_related_slottime(self):
        slottimegeneration = Mock()
        slottimes = 10
        slottimegeneration.pk = 5
        slottimegeneration.slottime_set.count.return_value = slottimes
        stgadmin = SlotTimesGenerationAdmin(SlotTimesGeneration, AdminSite)
        self.assertEqual(
            stgadmin.slottimes_lt(slottimegeneration),
            '<a href="{url}?generation={stg.pk}">{count}</a>'.format(
                url=reverse('admin:nowait_slottime_changelist'),
                stg=slottimegeneration, count=slottimes))

