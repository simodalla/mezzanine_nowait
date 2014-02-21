# -*- coding: iso-8859-1 -*-
from __future__ import unicode_literals, absolute_import
from django.conf.urls import patterns, url

# from .views import (BookingTypeListView, BookingCreateView, SlottimeSelectView,
#                     BookingTypeDetailView, BookingListView, BookingDetailView,
#                     CalendarGoogleConnectFormView, AdminHomeView)

urlpatterns = patterns(
    'nowait.views',
    url(r'bookingtype/(?P<slug>[-_\w]+)/$', 'bookingtype_detail',
        name='bookingtype_detail'),
)
