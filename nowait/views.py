# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from datetime import datetime

from django import get_version
from django.contrib import messages
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core import exceptions
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, DetailView
from django.views.generic.edit import FormView

from mezzanine.conf import settings

from braces.views import LoginRequiredMixin

from .utils import PageContextTitleMixin, get_root_app_page
from .models import BookingType, SlotTime
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
        # return reverse('nowait:booking_list')
        return '/'

    @transaction.commit_manually
    def form_valid(self, form):
        result = super(BookingCreateView, self).form_valid(form)

        try:
            if
            booking = form.instance
            booking.slottime = self.slottime
            booking.user = self.request.user
            booking.save()
            booking.slottime.status = SlotTime.STATUS.taken
            booking.slottime.save()
    #         # if 'djcelery' in settings.INSTALLED_APPS:
    #         #     from .tasks import create_calendar_event
    #         #     create_calendar_event.delay(booking)
        except Exception as e:
            transaction.rollback()
            # import ipdb
            # ipdb.set_trace()
            print("**************")
            # TODO: fare errore e mandare mail con eccezzione
        else:
            transaction.commit()
            messages.success(self.request,
                             booking.get_success_message_on_creation(),
                             extra_tags='safe')
            booking.send_emails_on_creation(self.request)
        finally:
            return result
    #
    # def form_invalid(self, form):
    #     return super(BookingCreateView, self).form_invalid(form)
