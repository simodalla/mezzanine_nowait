# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from mezzanine.conf import settings


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


def root_app_page_get_or_create(model, slug, title, **defaults):
    settings.use_editable()
    root_slug = settings.NOWAIT_ROOT_SLUG.lstrip('/').rstrip('/')
    root_page, create = model.objects.get_or_create(slug=slug, title=title,
                                                    defaults=defaults)
    return root_page, create

