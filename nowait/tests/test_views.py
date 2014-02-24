# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
# from django.test.utils import Rq
# from dj

from ..utils import setup_cbview
from .factories import BookingType30F


class BookingTypeDetailViewTest(TestCase):

    def setUp(self):
        print(1)
        self.booking_type = BookingType30F()
        self.url = '/nowait/bookingtype/{booking_type.slug}/'.format(
            booking_type=self.booking_type)
        print(2)

    def test_get_page_title(self):
        print(3)
        response = self.client.get(self.url)
        print(4)
        self.assertEqual(response.status_code, 200)
        print(5)
        self.assertIn('title', response.context)
        self.assertEqual(response.context['title'],
                         self.booking_type.title.title())
        print(6)

