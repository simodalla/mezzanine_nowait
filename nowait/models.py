# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
try:
    from django.db.transaction import atomic
except ImportError:
    from django.db.transaction import commit_on_success as atomic
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import (datetime, timedelta, make_aware,
                                   get_current_timezone)

from mezzanine.core.fields import RichTextField
from mezzanine.pages.models import Displayable, Link
from mezzanine.utils.email import send_mail_template, subject_template

from model_utils import Choices
from model_utils.models import TimeStampedModel, StatusField

from .core import get_range_days, get_week_map_by_weekday
from .utils import get_root_app_page


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
    gsummary = models.CharField(_('google summary'), max_length=300,
                                blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('calendar')
        verbose_name_plural = _('calendars')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Email(TimeStampedModel):
    email = models.EmailField(_('email'), unique=True)
    notes = models.CharField(_('notes'), max_length=300, blank=True)

    class Meta:
        ordering = ['email']
        verbose_name = _('email')
        verbose_name_plural = _('emails')

    def __str__(self):
        return self.email


@python_2_unicode_compatible
class BookingType(Displayable):
    slot_length = models.PositiveIntegerField(
        _('slot length'), default=30,
        help_text=_('Length in minutes of slot time.'))
    intro = RichTextField(_('intro'), blank=True)
    calendar = models.ForeignKey(Calendar, verbose_name=_('calendar'),
                                 blank=True, null=True)
    informations = RichTextField(_('informations'), blank=True)
    operators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        verbose_name=_('operators'))
    notification_emails_enable = models.BooleanField(
        _('Enable email notifications'), default=True)
    notification_emails = models.ManyToManyField(
        Email, blank=True, null=True, verbose_name=_('Emails to notify'))
    raw_location = models.CharField(_('Location (raw)'), max_length=500,
                                    blank=True)
    link = models.ForeignKey(Link, blank=True, null=True, editable=False)

    class Meta:
        ordering = ['title']
        verbose_name = _('booking type')
        verbose_name_plural = _('booking types')
        unique_together = ('calendar', 'title')

    def __str__(self):
        return '%s %s' % (self._meta.verbose_name, self.title)

    def get_absolute_url(self):
        return reverse('nowait:bookingtype_detail',
                       kwargs={'slug': self.slug})

    def get_or_create_link(self):
        try:
            root_page = get_root_app_page(self._meta.app_label)
        except ImproperlyConfigured as e:
            raise e
        link, created = Link.objects.get_or_create(
            slug=self.get_absolute_url().rstrip('/').lstrip('/'),
            parent=root_page,
            defaults={'title': self.title})
        if self.link != link:
            old_link = self.link
            self.link = link
            self.save()
            if old_link:
                old_link.delete()
        return link, created

    def get_notification_emails(self):
        """
        Return list of email addresses from email of self.operators and from
        self.notification_emails

        :return: list of email address
        :rtype: list of string
        """
        emails = [operator.email for operator in self.operators.all()]
        emails += [email.email for email in self.notification_emails.all()]
        return emails


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

    def create_slot_times(self):
        try:
            days = get_week_map_by_weekday(
                get_range_days(self.start_date, self.end_date))
        except Exception as e:
            raise e

        if self.booking_type.dailyslottimepattern_set.count() == 0:
            raise ValueError("{title} has no related DailySlotTimePattern "
                             "objects".format(title=self.booking_type.title))

        count = 0
        for pattern in self.booking_type.dailyslottimepattern_set.all():
            for day in days[str(pattern.day)]:
                cache_start_datetime = make_aware(
                    datetime.combine(day, pattern.start_time),
                    get_current_timezone())
                end_datetime = make_aware(
                    datetime.combine(day, pattern.end_time),
                    get_current_timezone())
                while (((end_datetime - cache_start_datetime).seconds / 60)
                        >= pattern.booking_type.slot_length):
                    start_slot = cache_start_datetime
                    end_slot = cache_start_datetime + timedelta(
                        minutes=pattern.booking_type.slot_length)
                    try:
                        slot, created = (
                            self.slottime_set.get_or_create(
                                booking_type=pattern.booking_type,
                                start=start_slot,
                                end=end_slot,
                                user=self.user))
                        if created:
                            count += 1
                    except ValidationError:
                        pass
                    cache_start_datetime = end_slot
        return count,


class FreeSlotTimeManager(models.Manager):
    def get_query_set(self):
        return super(FreeSlotTimeManager, self).get_query_set().filter(
            status=SlotTime.STATUS.free)

    def get_for_booking(self, booking_type, start, days_start=1, days_end=95):
        qs = self.get_query_set()
        return qs.filter(
            booking_type=booking_type,
            start__gt=start + timedelta(days=days_start),
            end__lt=start + timedelta(days=days_end)).order_by('start')


class TakenSlotTimeManager(models.Manager):
    def get_query_set(self):
        return super(TakenSlotTimeManager, self).get_query_set().filter(
            status=SlotTime.STATUS.taken)


@python_2_unicode_compatible
class SlotTime(TimeStampedModel):
    STATUS = Choices(('free', _('free')), ('taken', _('taken')))
    generation = models.ForeignKey(SlotTimesGeneration, blank=True, null=True,
                                   verbose_name=_('generation'))
    booking_type = models.ForeignKey(BookingType,
                                     verbose_name=_('booking type'))
    start = models.DateTimeField(_('start'))
    end = models.DateTimeField(_('end'))
    status = StatusField(_('status'), default=STATUS.free)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                             verbose_name=_('user'))

    objects = models.Manager()
    free = FreeSlotTimeManager()
    taken = TakenSlotTimeManager()

    class Meta:
        verbose_name = _('slot time')
        verbose_name_plural = _('slot times')
        ordering = ['booking_type', 'start', 'end']

    def __str__(self):
        return ('{self._meta.verbose_name} {self.start:%A %d %B %Y %H:%M}'
                ' - {self.end:%A %d %B %Y %H:%M}'.format(self=self))

    def clean(self):
        if SlotTime.objects.exclude(pk=self.pk).filter(
                start__lte=self.start, end__gt=self.start).count() > 0:
            raise ValidationError(
                "Tring to insert an %s object that"
                " overlaps with other." % self._meta.verbose_name.capitalize())

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.clean()
        return super(SlotTime, self).save(
            force_insert=force_insert, force_update=force_update, using=using,
            update_fields=update_fields)


@python_2_unicode_compatible
class Booking(TimeStampedModel):
    booker = models.ForeignKey(settings.AUTH_USER_MODEL,
                               verbose_name=_('booker'))
    slottime = models.OneToOneField(SlotTime, verbose_name=_('slot time'))
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

    @atomic
    def save_and_take_slottime(self, slottime, request):
        self.slottime = slottime
        self.booker = request.user
        self.save()
        self.slottime.status = SlotTime.STATUS.taken
        self.slottime.save()

    @property
    def success_message_on_creation(self):
        title = self.slottime.booking_type.title
        message = (
            _('Your booking for "%(booking_type)s" is succesfully created with'
              ' id: %(pk)s') % {'booking_type': title, 'pk': self.pk})
        return message

    def send_emails_on_creation(self, request):
        for template, addr_to in [
            ('booking_created_booker', self.booker.email),
            ('booking_created_operator',
             self.slottime.booking_type.get_notification_emails())]:
            try:
                send_mail_template(
                    subject_template(
                        'nowait/email/subject/{}.txt'.format(template), None),
                    'nowait/email/{}'.format(template), settings.SERVER_EMAIL,
                    addr_to, context={'booking': self,
                                      'request': request})
            except SMTPException as e:
                logger = logging.getLogger('django.request')
                logger.error(
                    'Internal Server Error: %s', request.path,
                    exc_info=str(e),
                    extra={'status_code': 500, 'request': request})
