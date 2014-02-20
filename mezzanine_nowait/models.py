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
