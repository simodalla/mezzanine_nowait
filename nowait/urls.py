# -*- coding: iso-8859-1 -*-
from __future__ import unicode_literals, absolute_import
from django.conf.urls import patterns, url

from .views import BookingTypeDetailView

urlpatterns = patterns(
    'nowait.views',
    url(r'bookingtype/(?P<slug>[-_\w]+)/$', BookingTypeDetailView.as_view(),
    # url(r'bookingtype/(?P<slug>[-_\w]+)/$', 'aaa',
        name='bookingtype_detail'),
    # url(r'^(?P<slug>[-_\w]+)/slottime/select/$', 'None',
    #     name='slottime_select'),
)
