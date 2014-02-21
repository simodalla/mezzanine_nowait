# -*- coding: iso-8859-1 -*-

import factory

from django.contrib.auth.models import User, Permission, Group

from .. import models
from ..core import BOOKME_GROUP_ADMINS, BOOKME_GROUP_OPERATORS

DOMAIN = 'comune.zolapredosa.bo.it'


class BookmeOperatorsGroupFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Group

    name = BOOKME_GROUP_OPERATORS

    @classmethod
    def _prepare(cls, create, **kwargs):
        group = super(BookmeOperatorsGroupFactory, cls)._prepare(create,
                                                                 **kwargs)
        group.permissions.add(
            *Permission.objects.filter(content_type__app_label='bookme',
                                       codename__startswith='change'))
        return group


class BookmeAdminsGroupFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Group

    name = BOOKME_GROUP_OPERATORS

    @classmethod
    def _prepare(cls, create, **kwargs):
        group = super(BookmeAdminsGroupFactory, cls)._prepare(create, **kwargs)
        group.permissions.add(
            *Permission.objects.filter(content_type__app_label='bookme'))
        return group


class UserFactory(factory.DjangoModelFactory):
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
        user = super(UserFactory, cls)._prepare(create, **kwargs)
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


class AdminFactory(UserFactory):
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


class BookingTypeF(factory.DjangoModelFactory):
    FACTORY_FOR = models.BookingType
    FACTORY_DJANGO_GET_OR_CREATE = ('title', 'calendar',)

    calendar = factory.SubFactory(CalendarPatternsFactory)
    title = factory.Sequence(lambda n: 'bookingtype_%s' % n)
    info = factory.LazyAttribute(lambda a: 'info on {0}'.format(a.title))


class BookingType30F(BookingTypeF):
    title = 'booking type 30'
    slot_length = 30


class BookingType45F(BookingTypeF):
    title = 'booking type 45'
    slot_length = 45
