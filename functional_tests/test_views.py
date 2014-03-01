# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, timedelta
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from django.core.urlresolvers import reverse
from django.template.defaultfilters import striptags

from nowait.tests.factories import AdminF, BookingType30F
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
        # 2013-9-9 is a Monday
        start = date(2013, 9, 9)
        self.today = start - timedelta(days=2)
        self.start_dates = [start, date(2013, 10, 7), date(2013, 11, 4)]
        self.bookingtype = BookingType30F()
        self.bookingtype.dailyslottimepattern_set.create(
            day=0, start_time='9:00', end_time='13:00')
        for start_date in self.start_dates:
            self.bookingtype.slottimesgeneration_set.create(
                start_date='{0:%Y-%m-%d}'.format(start_date),
                end_date='{0:%Y-%m-%d}'.format(start_date + timedelta(days=7)))
        for dstp in self.bookingtype.slottimesgeneration_set.all():
            dstp.create_slot_times()

    @patch('nowait.views.timezone.now')
    def test_visible_slottimes(self, mock_now):
        mock_now.return_value = self.today
        self.browser.get(self.get_url(
            reverse('nowait:slottime_select',
                    kwargs={'slug': self.bookingtype.slug})))
        for start_date in self.start_dates:
            slottimes = self.bookingtype.slottime_set.filter(
                start__range=(start_date, start_date + timedelta(days=8)))
            tab_pane = self.browser.find_element_by_css_selector(
                '.tab-content #{month}'.format(
                    month=('{0:%B}'.format(start_date)).lower()))
            thumbs = tab_pane.find_elements_by_css_selector('a.thumbnail')
            self.assertEqual(len(thumbs), len(slottimes))



