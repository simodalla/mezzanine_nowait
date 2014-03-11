# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import logging
from datetime import datetime

from django.contrib import messages
from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView

from mezzanine.conf import settings

from braces.views import LoginRequiredMixin

from .utils import PageContextTitleMixin, get_root_app_page
from .models import Booking, BookingType, SlotTime
from .forms import BookingCreateForm


class BookingTypeDetailView(PageContextTitleMixin, DetailView):
    model = BookingType

    def get_page_title(self):
        return _('%(title)s') % {'title': self.object.title.title()}


class SlottimeSelectView(PageContextTitleMixin, TemplateView):
    template_name = 'nowait/slottime_select.html'
    page_title = _('Select day and slot time')
    booking_type = None

    def get(self, request, *args, **kwargs):
        try:
            self.booking_type = BookingType.objects.get(
                slug=kwargs['slug'])
        except BookingType.DoesNotExist:
            try:
                url_to_return = reverse('nowait:home')
            except NoReverseMatch:
                settings.use_editable()
                url_to_return = '/{slug}/'.format(
                    slug=settings.NOWAIT_ROOT_SLUG.lstrip('/').rstrip('/'))
            return redirect(url_to_return)
        return super(SlottimeSelectView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SlottimeSelectView, self).get_context_data(**kwargs)
        now = timezone.now()
        start = timezone.make_aware(
            datetime(now.year, now.month, now.day, 0, 1),
            timezone.get_current_timezone())
        slottimes = SlotTime.free.get_for_booking(self.booking_type,
                                                  start=start)
        context['slottimes'] = []
        for month, year in [
            (start.month + i, start.year) if start.month + i <= 12
            else ((start.month + i) % 12, start.year + 1) for i in range(0,
                                                                         3)]:
            qs = slottimes.filter(start__month=month, start__year=year)
            if len(qs) > 0:
                context['slottimes'].append(
                    ('{0:%B}'.format(qs[0].start), year, qs))
        return context


class BookingCreateView(LoginRequiredMixin, PageContextTitleMixin, FormView):
    form_class = BookingCreateForm
    http_method_names = ['get', 'post']
    page_title = _('Confirmation of booking')
    slottime = None
    template_name = 'nowait/booking_create.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            self.slottime = SlotTime.objects.get(
                pk=kwargs['slottime_pk'])
            return super(BookingCreateView, self).dispatch(
                request, *args, **kwargs)
        except SlotTime.DoesNotExist:
            return redirect('/{page.slug}/'.format(
                page=get_root_app_page(SlotTime._meta.app_label)))

    def get_context_data(self, **kwargs):
        context = super(BookingCreateView, self).get_context_data(**kwargs)
        context.update({'slottime': self.slottime})
        return context

    def get_initial(self):
        return {'slottime': self.slottime.pk}

    def get_success_url(self):
        return reverse('nowait:booking_list')

    def form_valid(self, form):
        result = super(BookingCreateView, self).form_valid(form)
        booking = form.instance
        try:
            booking.save_and_take_slottime(self.slottime, self.request)
        except Exception as e:
            msg_on_error = _('Sorry. An error is occured. Please try again'
                             ' later.')
            messages.error(self.request, msg_on_error)
            logger = logging.getLogger('django.request')
            logger.error(
                'Internal Server Error: %s', self.request.path,
                exc_info=str(e), extra={'status_code': 500,
                                        'request': self.request})
            return redirect('.')
        else:
            messages.success(self.request,
                             booking.success_message_on_creation)
            booking.send_emails_on_creation(self.request)
        return result


class BookingListView(PageContextTitleMixin, LoginRequiredMixin, ListView):
    context_object_name = 'booking_list'
    page_title = _('My Booking')

    def get_queryset(self):
        return Booking.objects.filter(
            booker=self.request.user.pk).order_by('created')

    def get_context_data(self, **kwargs):
        context = super(BookingListView, self).get_context_data(**kwargs)
        context.update({'order': self.request.GET.get('order', None)})
        return context


class BookingDetailView(PageContextTitleMixin, LoginRequiredMixin,
                        DetailView):
    model = Booking

    def get_page_title(self):
        return _('Details of booking %(pk)s') % {'pk': self.object.pk}

    def get_queryset(self):
        return super(BookingDetailView, self).get_queryset().filter(
            booker=self.request.user)
