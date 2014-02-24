# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import FormView
from braces.views import LoginRequiredMixin, GroupRequiredMixin

# from .utils import PageContextTitleMixin
from .models import BookingType


def aaa(request, slug):
    from django.http import HttpResponse
    return HttpResponse('ciao')


# class BookingTypeDetailView(PageContextTitleMixin, DetailView):
class BookingTypeDetailView(DetailView):
    model = BookingType

    def get_context_data(self, **kwargs):
        print(10)
        context = super(BookingTypeDetailView, self).get_context_data(**kwargs)
        print(11)
        return context

    # def get_page_title(self):
    #     return _('%(title)s') % {'title': self.object.title.title()}
