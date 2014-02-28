# -*- coding: iso-8859-1 -*-
from __future__ import unicode_literals, absolute_import
from datetime import date, timedelta
from django.test import TestCase
from ..core import get_range_days, get_week_map_by_weekday


class GetRangeDaysTest(TestCase):

    def setUp(self):
        self.start_date = date(2013, 5, 6)
        self.end_date = date(2013, 6, 22)

    def test_create_slot_times_method_wrong_parameter_type(self):
        self.assertRaises(TypeError, get_range_days, 'a', 'b')

    def test_create_slot_times_method_wrong_parameter_values(self):
        self.assertRaises(ValueError, get_range_days,
                          date.today() + timedelta(days=2),
                          date.today())
        self.assertRaises(ValueError, get_range_days,
                          date.today(),
                          date.today() + timedelta(days=500))

    def test_create_slot_times_call_with_same_day_same_month(self):
        """
        Test the correct returned list from create_slot_times with the same
        date.
        """
        days = get_range_days(self.start_date, self.start_date)
        self.assertEqual(len(days), 1)
        self.assertListEqual(days, [self.start_date])

    def test_create_slot_times_call_with_one_day_same_month(self):
        """
        Test the correct returned list from create_slot_times with two dates
        with timedelta of 1 day and the same month
        """
        end_date = self.start_date + timedelta(days=1)
        days = get_range_days(self.start_date, end_date)
        self.assertEqual(len(days), 2)
        self.assertListEqual(days, [self.start_date, end_date])

    def test_create_slot_times_call_with_five_day_same_month(self):
        """
        Test the correct returned list from create_slot_times with two dates
        with timedelta of 1 day and the same month
        """
        range_days = 5
        end_date = self.start_date + timedelta(days=range_days)
        days = get_range_days(self.start_date, end_date)
        self.assertEqual(len(days), range_days + 1)
        self.assertListEqual(
            days,
            [date(self.start_date.year, self.start_date.month, day)
             for day in range(self.start_date.day,
                              self.start_date.day + range_days + 1)])


class GetWeekMapByWeekdayTest(TestCase):

    def setUp(self):
        self.start_date = date(2013, 5, 6)
        self.end_date = date(2013, 6, 22)

    def test_get_week_map_by_weekday_method_wrong_parameter_type(self):
        self.assertRaises(ValueError, get_week_map_by_weekday, 777)

    def test_get_week_map_by_weekday_call(self):
        get_week_map_by_weekday(get_range_days(self.start_date,
                                               self.end_date))
