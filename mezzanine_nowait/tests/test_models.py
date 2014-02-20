# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from django.core.urlresolvers import reverse
from django.test import TestCase
from ..models import Calendar, Email, BookingType


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
        title = 'booking xxx'
        slug = '-'.join(title.split(' '))
        obj = BookingType.objects.create(title=title)
        self.assertEqual(obj.slug, slug)
        self.assertEqual(obj.get_absolute_url(),
                         '/nowait/bookingtype/%s/' % slug)
