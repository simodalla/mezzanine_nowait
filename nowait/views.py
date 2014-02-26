# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from datetime import datetime

from django.core.urlresolvers import reverse, NoReverseMatch
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import FormView

from mezzanine.conf import settings

from braces.views import LoginRequiredMixin, GroupRequiredMixin

from .utils import PageContextTitleMixin
from .models import BookingType, SlotTime


class BookingTypeDetailView(PageContextTitleMixin, DetailView):
    model = BookingType

    def get_page_title(self):
        return _('%(title)s') % {'title': self.object.title.title()}


class SlottimeSelectView(PageContextTitleMixin, LoginRequiredMixin,
                         TemplateView):

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
            else ((start.month + i) % 12, start.year + 1) for i in range(0, 3)]:
            qs = slottimes.filter(start__month=month, start__year=year)
            if len(qs) > 0:
                context['slottimes'].append(
                    ('{:%B}'.format(qs[0].start), year, qs))
        return context


class BookingCreateView(LoginRequiredMixin, PageContextTitleMixin, FormView):
    form_class = BookingCreateForm
    page_title = 'Conferma Prenotazione'
    template_name = 'bookme/booking_create.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            self.slottime = SlotTime.objects.get(
                pk=kwargs['slottime_pk'])
        except SlotTime.DoesNotExist:
            return redirect('bookme:slottime_select')
        return super(BookingCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BookingCreateView, self).get_context_data(**kwargs)
        context.update({'slottime': self.slottime})
        return context

    def get_initial(self):
        return {'slottime': self.slottime.pk}

    def get_success_url(self):
        return reverse('bookme:booking_list')

    @transaction.commit_manually
    def form_valid(self, form):
        result = super(BookingCreateView, self).form_valid(form)
        try:
            booking = form.instance
            booking.slottime = self.slottime
            booking.user = self.request.user
            booking.save()
            booking.slottime.status = SlotTime.STATUS.taken
            booking.slottime.save()
            # if 'djcelery' in settings.INSTALLED_APPS:
            #     from .tasks import create_calendar_event
            #     create_calendar_event.delay(booking)
            messages.success(
                self.request,
                _('Your booking for "%(booking_type)s" is succesfully created'
                  ' with id: %(pk)s') %
                  {'booking_type': booking.slottime.booking_type.name,
                   'pk': '<b>{}</b>'.format(booking.pk)},
                extra_tags='safe')
        except:
            transaction.rollback()
            # TODO: fare errore e mandare mail con eccezzione
        else:
            transaction.commit()
            for template, addr_to in [
                    ('booking_created', booking.user.email),
                    ('booking_created_operator',
                     booking.slottime.booking_type.get_operator_emails())]:
                send_mail_template('bookme/email/{}'.format(template),
                                   settings.SERVER_EMAIL,
                                   addr_to,
                                   context={'booking': booking,
                                            'request': self.request})
        return result

    def form_invalid(self, form):
        return super(BookingCreateView, self).form_invalid(form)
