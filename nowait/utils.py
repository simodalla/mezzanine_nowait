# -*- coding: utf-8 -*-
from __future__ import unicode_literals


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


def setup_cbview(view, request, *args, **kwargs):
    view.request = request
    view.args = args
    view.kwargs = kwargs

