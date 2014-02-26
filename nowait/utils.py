# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured

from mezzanine.conf import settings
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED


class PageContextTitleMixin(object):
    """
    Provides update of response context data with variable "title"
    valorized with value of attribute "page_title".
    """
    page_title = None

    def get_page_title(self):
        """
        Returns the attribute "page_title".
        """
        return self.page_title

    def get_context_data(self, **kwargs):
        """
        Update of response context data with variable "title" valorized with
        value of attribute "page_title".
        """
        context = super(PageContextTitleMixin, self).get_context_data(**kwargs)
        context.update({"title": self.get_page_title()})
        return context


def root_app_page_get_or_create(model_page, app_label, **defaults):
    settings.use_editable()
    setting_root_slug_key = '{0}_ROOT_SLUG'.format(app_label.upper())
    slug = getattr(settings, setting_root_slug_key, None)
    if not slug:
        raise ImproperlyConfigured("The {0} setting must not be empty.".format(
            setting_root_slug_key))
    if slug != '/':
        slug = slug.lstrip('/').rstrip('/')
    root_page, create = model_page.objects.get_or_create(
        slug=slug, defaults=defaults)
    return root_page, create

