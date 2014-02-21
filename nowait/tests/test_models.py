# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import datetime
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import (timedelta, make_aware, get_current_timezone,
                                   now)
from ..models import (DAYS, Calendar, Email, BookingType, DailySlotTimePattern,
                      SlotTimesGeneration, SlotTime, Booking)
from .factories import (BookingType30F, BookingType45F, BookingTypeF,
                        UserFactory, AdminFactory)


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

    def setUp(self):
        self.booking_type_30 = BookingType30F()
        self.booking_type_45 = BookingType45F()
        self.user = UserFactory()
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
            "{} has no related DailySlotTimePattern objects".format(
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

        # self.st_generation.booking_type = self.booking_type_45
        # self.st_generation.save()
        # self.booking_type_45.dailyslottimepattern_set.create(
        #     day=self.start_date.weekday() + 1, start_time='11:00',
        #     end_time='12:30')
        # result, = self.st_generation.create_slot_times()
        # self.assertEqual(result, 0)
        # self.assertEqual(self.booking_type_30.slottime_set.count(), 8)
        # self.assertEqual(self.booking_type_45.slottime_set.count(), 0)
        # for bt in [self.booking_type_30, self.booking_type_45]:
        #     for slottime in bt.slottime_set.all():
        #         slottime.status = SlotTime.STATUS.free
        #         slottime.generation = self.st_generation
        #         slottime.calendar = bt.calendar
        #         slottime.booking_type = bt
        #         slottime.user = self.user
        #
        # SlotTime.objects.all().delete()
        # self.booking_type_45.dailyslottimepattern_set.create(
        #     day=self.start_date.weekday() + 1, start_time='14:00',
        #     end_time='15:30')
        # result, = self.st_generation.create_slot_times()
        # self.assertEqual(result, 4)
        # self.assertEqual(self.booking_type_30.slottime_set.count(), 0)
        # self.assertEqual(self.booking_type_45.slottime_set.count(), 4)
        # for bt in [self.booking_type_30, self.booking_type_45]:
        #     for slottime in bt.slottime_set.all():
        #         slottime.status = SlotTime.STATUS.free
        #         slottime.generation = self.st_generation
        #         slottime.calendar = bt.calendar
        #         slottime.booking_type = bt
        #         slottime.user = self.user


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

    def test_st_method(self):
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

    def test_admin_calendar_method(self):
        bookingtype = BookingTypeF()
        start = now()
        end = start + timedelta(minutes=30)
        slottime = SlotTime.objects.create(booking_type=bookingtype,
                                           start=start, end=end)
        self.assertEqual(
            slottime.admin_calendar(),
            '<a href="{url}?id={calendar.pk}>{calendar.name}"'.format(
                url=reverse('admin:nowait_calendar_changelist'),
                calendar=bookingtype.calendar))



class SlotTimeManagersTest(TestCase):
    def setUp(self):
        self.booking_types = {}
        self.user = UserFactory()
        self.admin = AdminFactory()
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
                start_time='{}:{}'.format(start.hour, start.minute),
                end_time='{}:{}'.format(end.hour, end.minute), )
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


class BookingModelTest(TestCase):

    def test_str(self):
        obj = Booking.objects.create()
        self.assertEqual(obj.__str__(),
                         '%s n.%s' % (obj._meta.verbose_name, obj.pk))


