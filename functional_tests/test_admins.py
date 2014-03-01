# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from unittest import skip
from django.contrib.admin.templatetags.admin_urls import admin_urlname

from .base import FunctionalTest
from nowait.tests.factories import AdminF
from nowait.models import BookingType


@skip
class AdminTest(FunctionalTest):
    def setUp(self):
        super(AdminTest, self).setUp()
        self.admin = AdminF()
        self.create_pre_authenticated_session(self.admin)

    def test_add_booking_type(self):
        self.browser.get(
            self.get_url(admin_urlname(BookingType._meta, 'changelist')))
