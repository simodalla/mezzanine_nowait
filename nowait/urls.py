# -*- coding: iso-8859-1 -*-
from __future__ import unicode_literals, absolute_import
from django.conf.urls import patterns, url

from .views import BookingTypeDetailView, SlottimeSelectView

urlpatterns = patterns(
    'nowait.views',
    # url(r'^$', BookingTypeListView.as_view(), name='home'),
    url(r'^(?P<slug>[-_\w]+)/$', BookingTypeDetailView.as_view(),
        name='bookingtype_detail'),
    url(r'^(?P<slug>[-_\w]+)/slottime/select/$', SlottimeSelectView.as_view(),
        name='slottime_select'),
)
