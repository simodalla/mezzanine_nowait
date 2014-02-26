# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings

from mezzanine.conf import settings
from mezzanine.pages.models import RichTextPage, Link

from ..utils import root_app_page_get_or_create

NOWAIT_ROOT_SLUG = 'nowait-root-page'


@override_settings(NOWAIT_ROOT_SLUG=NOWAIT_ROOT_SLUG)
class RootAppPageCreationTest(TestCase):

    def setUp(self):
        self.defaults = {'title': 'Nowait Root Page',
                         'content': '<p>Content</p>'}

    def test_call_root_app_page_get_or_create_without_no_wait_slug_setting(
            self):
        with override_settings(NOWAIT_ROOT_SLUG=None):
            self.assertRaises(
                ImproperlyConfigured,
                root_app_page_get_or_create,
                RichTextPage, 'nowait', **self.defaults)

    def test_strip_border_slashes(self):
        with override_settings(NOWAIT_ROOT_SLUG='/%s/' % NOWAIT_ROOT_SLUG):
            page, created = root_app_page_get_or_create(
                RichTextPage, 'nowait', **self.defaults)
            self.assertEqual(page.slug, NOWAIT_ROOT_SLUG)

    def test_no_strip_border_slashes_if_slug_is_root_slash(self):
        with override_settings(NOWAIT_ROOT_SLUG='/'):
            page, created = root_app_page_get_or_create(
                RichTextPage, 'nowait', **self.defaults)
            self.assertEqual(page.slug, '/')

    def test_create_root_page_return_page(self):
        page, created = root_app_page_get_or_create(
            RichTextPage, 'nowait', **self.defaults)
        self.assertTrue(isinstance(page, RichTextPage))
        self.assertTrue(created)
        self.assertEqual(page.slug, settings.NOWAIT_ROOT_SLUG)
        for field in self.defaults:
            self.assertEqual(getattr(page, field), self.defaults[field])

    def test_get_root_page_with_more_pages_with_same_slug(self):
        already_root_page = RichTextPage.objects.create(
            slug=NOWAIT_ROOT_SLUG, **self.defaults)
        self.assertEqual(RichTextPage.objects.count(), 1)
        page, created = root_app_page_get_or_create(
            RichTextPage, 'nowait', **self.defaults)
        self.assertEqual(RichTextPage.objects.count(), 1)
        self.assertFalse(created)
        self.assertEqual(already_root_page.pk, page.pk)
        self.assertEqual(page.slug, settings.NOWAIT_ROOT_SLUG)
        for field in self.defaults:
            self.assertEqual(getattr(page, field), self.defaults[field])




