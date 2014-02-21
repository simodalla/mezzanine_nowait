# -*- coding: iso-8859-1 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.shortcuts import redirect

from .core import BOOKME_GROUP_ADMINS
from .models import (BookingType, Calendar, DailySlotTimePattern, SlotTime,
                     SlotTimesGeneration, Booking)


class MixinCheckOperatorAdminView(object):
    def change_view(self, request, object_id, form_url='', extra_context=None):
        user = request.user
        if user.is_superuser or (
                BOOKME_GROUP_ADMINS in user.groups.values_list('name',
                                                               flat=True)):
            return super(MixinCheckOperatorAdminView, self).change_view(
                request, object_id, form_url=form_url,
                extra_context=extra_context)
        self.message_user(
            request,
            _("You do not have permission to modify this object type."),
            level=messages.ERROR)
        return redirect('admin:bookme_{}_changelist'.format(
            self.model.__name__.lower()))


class BookingTypeInline(admin.TabularInline):
    extra = 1
    model = BookingType
    ordering = ['name']


class DailySlotTimePatternInline(admin.TabularInline):
    extra = 1
    model = DailySlotTimePattern
    ordering = ['day', 'start_time', 'end_time']


class BookingTypeAdmin(MixinCheckOperatorAdminView, admin.ModelAdmin):
    inlines = [DailySlotTimePatternInline]
    list_display = ['name', 'calendar', 'slot_length', 'description', 'notes',
                    'admin_cms_page']
    list_per_page = 20
    prepopulated_fields = {'slug': ('name',)}

    def save_model(self, request, obj, form, change):
        obj.save()
        try:
            from mezzanine_bookme.models import BookingTypePage
            if not change:
                page, created = BookingTypePage.make_page_from_booking_type(obj)
                if created:
                    self.message_user(
                        request,
                        _('Page of title "%(title)s" with slug "%(slug)s" is'
                          ' succesfully created.') % {'title': page.title,
                                                      'slug': page.slug})
        except ImportError:
            if 'mezzanine' in [app.slipt('.')[0] for app
                               in settings.INSTALLED_APPS]:
                self.message_user(
                    request,
                    _('App {} not in INSTALLED_APPS setting'.format(
                        'mezzanine_bookme')),
                    level=messages.ERROR)


class CalendarAdmin(MixinCheckOperatorAdminView, admin.ModelAdmin):
    list_display = ['name', 'owner', 'gid', 'get_booking_types']
    list_per_page = 20

    def get_booking_types(self, obj):
        return u'<br >'.join(
            [u'<a href="{}?id={}">{}</a>'.format(
                reverse('admin:bookme_bookingtype_changelist'), bt.pk, bt.name)
             for bt in obj.bookingtype_set.all()])
    get_booking_types.short_description = _('booking types')
    get_booking_types.allow_tags = True


class SlotTimesGenerationAdmin(MixinCheckOperatorAdminView, admin.ModelAdmin):
    actions = ['create_slottimes']
    list_display = ['pk', 'booking_type', 'start_date',
                    'end_date', 'user', 'created', 'slottimes_lt']
    list_per_page = 20

    def save_model(self, request, obj, form, change):
        obj.user = obj.save()
        obj.save()

    def slottimes_lt(self, obj):
        slottimes_count = obj.slottime_set.count()
        if slottimes_count:
            url = reverse('admin:{}_{}_changelist'.format(
                SlotTime._meta.app_label,
                SlotTime._meta.module_name))
            return '<a href="{}?generation={}">{} {}</a>'.format(
                url, obj.pk, slottimes_count, _('slottimes generated'))
    slottimes_lt.short_description = _('slottimes generated')
    slottimes_lt.allow_tags = True

    def create_slottimes(self, request, queryset):
        for obj in queryset:
            obj.create_slot_times()
    create_slottimes.short_description = (
        _("Create slottimes from generation"))


class SlotTimeAdmin(MixinCheckOperatorAdminView, admin.ModelAdmin):
    date_hierarchy = 'start'
    list_display = ['pk', 'admin_calendar', 'booking_type', 'start', 'end',
                    'status', 'generation']
    list_filter = ['calendar', 'booking_type', 'status']
    list_per_page = 20
    ordering = ['booking_type', 'start', 'end']


class BookingAdmin(MixinCheckOperatorAdminView, admin.ModelAdmin):
    list_display = ['pk', 'user', 'admin_day', 'admin_start', 'admin_end',
                    'notes', 'telephone']
    list_per_page = 20
    search_fields = ['id', 'user__username', 'user__last_name',
                     'user__first_name', 'slottime__booking_type__name']


admin.site.register(Booking, BookingAdmin)
admin.site.register(BookingType, BookingTypeAdmin)
admin.site.register(Calendar, CalendarAdmin)
admin.site.register(SlotTime, SlotTimeAdmin)
admin.site.register(SlotTimesGeneration, SlotTimesGenerationAdmin)
