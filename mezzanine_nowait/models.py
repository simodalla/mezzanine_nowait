# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import warnings

from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.timezone import (datetime, timedelta, make_aware,
                                   get_current_timezone, now)
from mezzanine.core.fields import RichTextField
from mezzanine.pages.models import Displayable
from model_utils import Choices
from model_utils.models import TimeStampedModel, StatusField
#
# from .core import get_range_days, get_week_map_by_weekday

try:
    #noinspection PyUnresolvedReferences
    from djga.models import Credential
except ImportError:
    import warnings


DAYS = Choices((0, 'mo', _('monday')), (1, 'tu', _('tuesday')),
               (2, 'we', _('wednesday')), (3, 'th', _('thursday')),
               (4, 'fr', _('friday')), (5, 'sa', _('saturday')),
               (6, 'su', _('sunday')), )


@python_2_unicode_compatible
class Calendar(TimeStampedModel):
    name = models.CharField(_('name'), max_length=300, unique=True)
    description = models.TextField(_('description'), blank=True, default='')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                              verbose_name=_('owner'))
    gid = models.CharField(_('google id'), max_length=300, blank=True,
                           unique=True)
    gsummary = models.CharField(_('google summary'), max_length=300, blank=True)

    class Meta:
        verbose_name = _('calendar')
        verbose_name_plural = _('calendars')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Email(TimeStampedModel):
    email = models.EmailField(_('email'))
    notes = models.TextField(_('notes'), max_length=300, blank=True)

    def __str__(self):
        return self.email


@python_2_unicode_compatible
class BookingType(Displayable):
    slot_length = models.PositiveIntegerField(
        _('slot length'), default=30,
        help_text=_('Length in minutes of slot time.'))
    info = RichTextField(_('info'), blank=True)
    calendar = models.ForeignKey(Calendar, verbose_name=_('calendar'),
                                 blank=True, null=True)
    notes = RichTextField(_('notes'), blank=True)
    operators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        verbose_name=_('operators'))
    notifications_email_enable = models.BooleanField(
        _('Enable email notifications'), default=True)
    notifications_emails = models.ManyToManyField(
        Email, blank=True, null=True, verbose_name=_('Emails to notify'))
    raw_location = models.CharField(_('Location (raw)'), max_length=500)

    class Meta:
        ordering = ['title']
        verbose_name = _('booking type')
        verbose_name_plural = _('booking types')
        unique_together = ('calendar', 'title')

    def __str__(self):
        return '%s %s' % (self._meta.verbose_name, self.title)

    def get_absolute_url(self):
        return reverse('mezzanine_nowait:bookingtype_detail',
                       kwargs={'slug': self.slug})


@python_2_unicode_compatible
class DailySlotTimePattern(TimeStampedModel):
    booking_type = models.ForeignKey(BookingType)
    day = models.IntegerField(_('day'), choices=DAYS, default=DAYS.mo)
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))

    class Meta:
        verbose_name = _('daily slot time pattern')
        verbose_name_plural = _('daily slot time patterns')
        unique_together = ('booking_type', 'day', 'start_time')

    def __str__(self):
        return '%s: %s, %s-%s' % (self._meta.verbose_name,
                                  self.get_day_display(),
                                  self.start_time, self.end_time)


@python_2_unicode_compatible
class SlotTimesGeneration(TimeStampedModel):
    booking_type = models.ForeignKey(BookingType)
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                             editable=False, verbose_name=_('user'))

    class Meta:
        verbose_name = _('slot times generation')
        verbose_name_plural = _('slot times generations')

    def __str__(self):
        return '%s n.%s' % (self._meta.verbose_name, self.pk)

    #noinspection PyTypeChecker,PyTypeChecker
    # def create_slot_times(self):
    #     try:
    #         days = get_week_map_by_weekday(
    #             get_range_days(self.start_date, self.end_date))
    #     except Exception as e:
    #         raise e
    #
    #     if self.booking_type.dailyslottimepattern_set.count() == 0:
    #         raise ValueError("{} has no related DailySlotTimePattern "
    #                          "objects".format(self.booking_type.name))
    #
    #     count = 0
    #     for pattern in self.booking_type.dailyslottimepattern_set.all():
    #         for day in days[str(pattern.day)]:
    #             cache_start_datetime = make_aware(
    #                 datetime.combine(day, pattern.start_time),
    #                 get_current_timezone())
    #             end_datetime = make_aware(
    #                 datetime.combine(day, pattern.end_time),
    #                 get_current_timezone())
    #             while (((end_datetime - cache_start_datetime).seconds / 60)
    #                        >= pattern.booking_type.slot_length):
    #                 start_slot = cache_start_datetime
    #                 end_slot = cache_start_datetime + timedelta(
    #                     minutes=pattern.booking_type.slot_length)
    #                 try:
    #                     slot, created = (
    #                         self.slottime_set.get_or_create(
    #                             booking_type=pattern.booking_type,
    #                             calendar=pattern.booking_type.calendar,
    #                             start=start_slot,
    #                             end=end_slot,
    #                             user=self.user))
    #                     if created:
    #                         count += 1
    #                 except ValidationError:
    #                     pass
    #                 cache_start_datetime = end_slot
    #     return count,


@python_2_unicode_compatible
class SlotTime(TimeStampedModel):
    STATUS = Choices(('free', _('free')), ('taken', _('taken')))
    generation = models.ForeignKey(SlotTimesGeneration, blank=True, null=True,
                                   verbose_name=_('generation'))
    booking_type = models.ForeignKey(BookingType,
                                     verbose_name=_('booking type'))
    calendar = models.ForeignKey(Calendar, blank=True, null=True,
                                 verbose_name=_('calendar'))
    start = models.DateTimeField(_('start'))
    end = models.DateTimeField(_('end'))
    status = StatusField(_('status'), default=STATUS.free)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                             verbose_name=_('user'))

    objects = models.Manager()
    # free = FreeSlotTimeManager()
    # taken = TakenSlotTimeManager()

    class Meta:
        verbose_name = _('slot time')
        verbose_name_plural = _('slot times')
        ordering = ['booking_type', 'start', 'end']

    def __str__(self):
        return ('{self._meta.verbose_name} {self.start:%A %d %B %Y %H:%M}'
                ' - {self.end:%A %d %B %Y %H:%M}'.format(self=self))


@python_2_unicode_compatible
class Booking(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'),
                             blank=True, null=True)
    slottime = models.OneToOneField(SlotTime, verbose_name=_('slot time'),
                                    blank=True, null=True)
    notes = models.TextField(
        _('notes'), blank=True,
        help_text=_('add notes to communicate to the  person in charge of '
                    'booking (this field is not required)'))
    telephone = models.CharField(
        _('telephone'), max_length=30, blank=True,
        help_text=_('enter an alternate phone number to the one entered during'
                    ' registration (this field is not required)'))

    class Meta:
        verbose_name = _('booking')
        verbose_name_plural = _('bookings')

    def __str__(self):
        return '%s n.%s' % (self._meta.verbose_name, self.pk)
