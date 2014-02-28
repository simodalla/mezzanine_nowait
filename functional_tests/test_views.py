# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.template.defaultfilters import striptags

from nowait.tests.factories import BookingType30F
from .base import FunctionalTest


class BookingTypeDetailViewTest(FunctionalTest):

    def setUp(self):
        super(BookingTypeDetailViewTest, self).setUp()
        self.bookingtype = BookingType30F()
        self.bookingtype.intro = "<p><i>intro</i></p>"
        self.bookingtype.info = """
Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo
ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis
dis parturient montes, nascetur ridiculus mus. Donec quam felis,"""
        self.bookingtype.save()

    def tearDown(self):

        super(BookingTypeDetailViewTest, self).tearDown()

    def test_title_block(self):
        self.browser.get(self.get_url(self.bookingtype.get_absolute_url()))
        div_title = self.browser.find_element_by_id('bookingtype_title')
        self.assertIn('jumbotron', div_title.get_attribute('class'))
        div_title_h1 = div_title.find_element_by_tag_name('h1')
        self.assertEqual(div_title_h1.text, self.bookingtype.title)
        div_info = div_title.find_element_by_css_selector(
            'div#bookingtype_intro')
        self.assertEqual(div_info.text, striptags(self.bookingtype.info))
        link = div_title.find_element_by_partial_link_text(
            'Make your reservation')
        self.assertEqual(
            link.get_attribute('href'),
            self.get_url(reverse('nowait:slottime_select',
                                 kwargs={'slug': self.bookingtype.slug})))

    # def test_content_block(self):
