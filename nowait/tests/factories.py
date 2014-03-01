# -*- coding: iso-8859-1 -*-

import factory
from django.contrib.auth.models import User, Permission, Group
from mezzanine.pages.models import RichTextPage
from .. import models
from ..defaults import (NOWAIT_ROOT_SLUG, NOWAIT_GROUP_ADMINS,
                        NOWAIT_GROUP_OPERATORS)

DOMAIN = 'example.com'


class NowaitGOperatorsF(factory.DjangoModelFactory):
    FACTORY_FOR = Group

    name = NOWAIT_GROUP_OPERATORS

    @classmethod
    def _prepare(cls, create, **kwargs):
        group = super(NowaitGOperatorsF, cls)._prepare(create, **kwargs)
        group.permissions.add(
            *Permission.objects.filter(content_type__app_label='bookme',
                                       codename__startswith='change'))
        return group


class NowaitGAdminsF(factory.DjangoModelFactory):
    FACTORY_FOR = Group

    name = NOWAIT_GROUP_ADMINS

    @classmethod
    def _prepare(cls, create, **kwargs):
        group = super(NowaitGAdminsF, cls)._prepare(create, **kwargs)
        group.permissions.add(
            *Permission.objects.filter(content_type__app_label='bookme'))
        return group


class UserF(factory.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: 'user_%s' % n)
    password = factory.Sequence(lambda n: 'user_%s' % n)
    email = factory.LazyAttribute(
        lambda o: '{0}@{1}'.format(o.username, DOMAIN))
    is_staff = True
    is_active = True

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserF, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for group in extracted:
                self.groups.add(group)


class AdminF(UserF):
    FACTORY_FOR = User

    username = 'admin'
    password = 'admin'
    email = 'admin@{0}'.format(DOMAIN)
    is_superuser = True


class DailySlotTimePatternFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DailySlotTimePattern
    FACTORY_DJANGO_GET_OR_CREATE = ('booking_type', 'day', 'start_time')


class CalendarPatternsFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Calendar
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = 'demo calendar with pattern'
    description = factory.LazyAttribute(
        lambda obj: 'description of {0}'.format(obj.name))


class RichTextPageF(factory.DjangoModelFactory):
    FACTORY_FOR = RichTextPage

    title = factory.Sequence(lambda n: 'RichTextPage n. %s' % n)
    content = factory.LazyAttribute(lambda a: '<p>Content of %s</p>' % a.title)


class RootNowaitPageF(RichTextPageF):
    title = 'Root Page of NoWait'
    slug = NOWAIT_ROOT_SLUG


class BookingTypeF(factory.DjangoModelFactory):
    FACTORY_FOR = models.BookingType
    FACTORY_DJANGO_GET_OR_CREATE = ('title', 'calendar',)

    calendar = factory.SubFactory(CalendarPatternsFactory)
    title = factory.Sequence(lambda n: 'bookingtype_%s' % n)
    intro = factory.LazyAttribute(lambda a: 'intro on {0}'.format(a.title))
    slug = factory.LazyAttribute(lambda a: '-'.join(a.title.split(' ')))


class BookingType30F(BookingTypeF):
    title = 'booking type 30'
    slot_length = 30


class BookingType45F(BookingTypeF):
    title = 'booking type 45'
    slot_length = 45
