# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, timedelta
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from nowait.tests.factories import UserF, BookingType30F, RootNowaitPageF
from .base import FunctionalTest


class UserCreateBookingTest(FunctionalTest):
    def setUp(self):
        super(UserCreateBookingTest, self).setUp()
        self.user = UserF()
        self.root = RootNowaitPageF()
        # self.create_pre_authenticated_session(self.admin)
        # 2013-9-9 is a Monday
        start = date(2013, 9, 9)
        self.today = start - timedelta(days=2)
        self.start_dates = [start, date(2013, 10, 7), date(2013, 11, 4)]
        self.bookingtype = BookingType30F()
        self.bookingtype.get_or_create_link()
        self.bookingtype.dailyslottimepattern_set.create(
            day=0, start_time='9:00', end_time='13:00')
        for start_date in self.start_dates:
            self.bookingtype.slottimesgeneration_set.create(
                start_date='{0:%Y-%m-%d}'.format(start_date),
                end_date='{0:%Y-%m-%d}'.format(start_date + timedelta(days=7)))
        for dstp in self.bookingtype.slottimesgeneration_set.all():
            dstp.create_slot_times()

    @patch('nowait.views.timezone.now')
    def test_user_choose_slottime_make_login_and_create_booking(
            self, mock_now):
        mock_now.return_value = self.today
        # user go to home page "/"
        self.browser.get(self.get_url('/'))
        # user click on link of root nowait page from left panel tree
        left_panel_tree = self.get_left_panel_tree()
        left_panel_tree.find_element_by_link_text(self.root.title).click()
        # user click on link of choosen booking type from left panel tree
        import ipdb
        ipdb.set_trace()
        left_panel_tree = self.get_left_panel_tree()
        left_panel_tree.find_element_by_link_text(
            self.bookingtype.title).click()
        # user click on link "Make your reservation"
        self.browser.find_element_by_partial_link_text(
            'Make your reservation').click()
        slottime_selected = self.browser.find_elements_by_css_selector(
            '.tab-content .active a.thumbnail')[0]
        slottime_selected_id = slottime_selected.get_attribute('id')
        slottime_selected.click()
        # user is redirected to login page and now insert his credentials
        self.browser.find_element_by_id('id_username').send_keys(
            self.user.username)
        self.browser.find_element_by_id('id_password').send_keys(
            self.user.username)
        self.browser.find_element_by_css_selector(
            '.form-actions input').click()
        # print(slottime_selected_id)