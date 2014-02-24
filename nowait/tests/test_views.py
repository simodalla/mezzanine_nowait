# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase

from .factories import BookingType30F, UserF, RootNowaitPageF
from ..defaults import NOWAIT_ROOT_SLUG


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
        response = self.client.get(self.url.format(slug=self.booking_type.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('title' in response.context)
        self.assertEqual(response.context['title'],
                         'Select day and slot time')

    # def test_
        # print(response.context['slottimes'])

