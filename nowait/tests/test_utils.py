# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from mezzanine.pages.models import RichTextPage

from ..utils import root_app_page_get_or_create


class RootAppPageCreationTest(TestCase):

    def setUp(self):
        pass

    def test_create_root_page_return_page(self):
        title = 'Nowait Root Page'
        slug = 'nowait-root-page'
        page, create = root_app_page_get_or_create(RichTextPage, slug, title)

