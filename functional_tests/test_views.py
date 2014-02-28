# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, timedelta
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import patch, Mock

from django.core.urlresolvers import reverse
from django.template.defaultfilters import striptags
from django.test import TestCase
from django.utils import timezone

from nowait.tests.factories import AdminF, BookingType30F, UserF
from .base import FunctionalTest


class BookingTypeDetailViewTest(FunctionalTest):

    def setUp(self):
        super(BookingTypeDetailViewTest, self).setUp()
        self.bookingtype = BookingType30F()
        self.bookingtype.intro = "<p><i>intro</i></p>"
        self.bookingtype.informations = (
            'Lorem ipsum dolor sit amet, consectetuer adipiscing elit.'
            ' Aenean commodo ligula eget dolor. Aenean massa. Cum sociis'
            ' natoque penatibus et magnis dis parturient montes, nascetur'
            ' ridiculus mus. Donec quam felis,')
        self.bookingtype.save()

    def tearDown(self):
        super(BookingTypeDetailViewTest, self).tearDown()

    def test_title_block(self):
        self.browser.get(self.get_url(self.bookingtype.get_absolute_url()))
        div_title = self.browser.find_element_by_id('bookingtype_title')
        self.assertIn('jumbotron', div_title.get_attribute('class'))
        div_title_h1 = div_title.find_element_by_tag_name('h1')
        self.assertEqual(div_title_h1.text, self.bookingtype.title)
        div_intro = div_title.find_element_by_css_selector(
            'div#bookingtype_intro')
        self.assertEqual(div_intro.text, striptags(self.bookingtype.intro))
        link = div_title.find_element_by_partial_link_text(
            'Make your reservation')
        self.assertEqual(
            link.get_attribute('href'),
            self.get_url(reverse('nowait:slottime_select',
                                 kwargs={'slug': self.bookingtype.slug})))

    def test_content_block(self):
        self.browser.get(self.get_url(self.bookingtype.get_absolute_url()))
        div_info = self.browser.find_element_by_id('bookingtype_informations')
        self.assertEqual(div_info.text.strip('\n'),
                         striptags(self.bookingtype.informations))


class SlottimeSelectViewTest(FunctionalTest):
    def setUp(self):
        super(SlottimeSelectViewTest, self).setUp()
        self.admin = AdminF()
        self.create_pre_authenticated_session(self.admin)
        self.today = date(2013, 9, 9) - timedelta(days=2) # Monday
        start_10 = date(2013, 10, 07)
        start_11 = date(2013, 11, 04)
        print("TODAY:", self.today)
        self.bookingtype = BookingType30F()
        self.bookingtype.dailyslottimepattern_set.create(
            day=0, start_time='9:00', end_time='13:00')
        self.bookingtype.slottimesgeneration_set.create(
            start_date='{:%Y-%m-%d}'.format(self.today),
            end_date='{:%Y-%m-%d}'.format(self.today + timedelta(days=7)))  #
        self.bookingtype.slottimesgeneration_set.create(
            start_date='{:%Y-%m-%d}'.format(start_10),
            end_date='{:%Y-%m-%d}'.format(start_10 + timedelta(days=7)))
        self.bookingtype.slottimesgeneration_set.create(
            start_date='{:%Y-%m-%d}'.format(start_11),
            end_date='{:%Y-%m-%d}'.format(start_11 + timedelta(days=7)))
        # print(self.bookingtype.dailyslottimepattern_set.all())
        # print(self.bookingtype.slottimesgeneration_set.all())
        for dstp in self.bookingtype.slottimesgeneration_set.all():
            dstp.create_slot_times()
        # print(self.bookingtype.slottime_set.all())
        # print(timezone.datetime.today())
        # with patch('functional_tests.test_views.timezone') as mock_tz:
        #     print(mock_tz.datetime.today())
        # print(timezone.datetime.today())

    @patch('nowait.views.timezone.now')
    def test_view(self, mock_now):
        mock_now.return_value = self.today
        self.browser.get(self.get_url(
            reverse('nowait:slottime_select',
                    kwargs={'slug': self.bookingtype.slug})))
        import ipdb; ipdb.set_trace()
