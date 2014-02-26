# -*- coding: iso-8859-1 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.shortcuts import redirect

from .defaults import NOWAIT_GROUP_ADMINS
from .models import (BookingType, Calendar, DailySlotTimePattern, SlotTime,
                     SlotTimesGeneration, Booking)


class MixinCheckOperatorAdminView(object):
    def change_view(self, request, object_id, form_url='', extra_context=None):
        user = request.user
        if user.is_superuser or (
                NOWAIT_GROUP_ADMINS in user.groups.values_list('name',
                                                               flat=True)):
            return super(MixinCheckOperatorAdminView, self).change_view(
                request, object_id, form_url=form_url,
                extra_context=extra_context)
        self.message_user(
            request,
            _("You do not have permission to modify this object type."),
            level=messages.ERROR)
        return redirect(admin_urlname(self.model._meta, 'changelist'))


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

    # def save_model(self, request, obj, form, change):
    #     obj.save()
    #     try:
    #         from mezzanine_bookme.models import BookingTypePage
    #         if not change:
    #             page, created = BookingTypePage.make_page_from_booking_type(obj)
    #             if created:
    #                 self.message_user(
    #                     request,
    #                     _('Page of title "%(title)s" with slug "%(slug)s" is'
    #                       ' succesfully created.') % {'title': page.title,
    #                                                   'slug': page.slug})
    #     except ImportError:
    #         if 'mezzanine' in [app.slipt('.')[0] for app
    #                            in settings.INSTALLED_APPS]:
    #             self.message_user(
    #                 request,
    #                 _('App {} not in INSTALLED_APPS setting'.format(
    #                     'mezzanine_bookme')),
    #                 level=messages.ERROR)


class CalendarAdmin(MixinCheckOperatorAdminView, admin.ModelAdmin):
    list_display = ['name', 'owner', 'gid', 'booking_type_links']
    list_per_page = 20

    def booking_type_links(self, obj):
        link_tpl = '<a href="{url}?id={bookinktype.pk}">{bookinktype.title}</a>'
        return '<br >'.join([
            link_tpl.format(
                url=reverse(admin_urlname(bt._meta, 'changelist')),
                bookinktype=bt)
            for bt in obj.bookingtype_set.order_by('title')])
    booking_type_links.short_description = _('booking types')
    booking_type_links.allow_tags = True


class SlotTimesGenerationAdmin(MixinCheckOperatorAdminView, admin.ModelAdmin):
    actions = ['create_slottimes']
    list_display = ['pk', 'booking_type', 'start_date',
                    'end_date', 'user', 'created', 'slottimes_lt']
    list_per_page = 20

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def slottimes_lt(self, obj):
        slottimes_count = obj.slottime_set.count()
        if slottimes_count >= 1:
            url = reverse(admin_urlname(SlotTime._meta, 'changelist'))
            return '<a href="{0}?generation={1}">{2}</a>'.format(
                url, obj.pk, slottimes_count)
        return str(slottimes_count)
    slottimes_lt.short_description = _('slottimes generated')
    slottimes_lt.allow_tags = True

    def create_slottimes(self, request, queryset):
        for obj in queryset:
            obj.create_slot_times()
    create_slottimes.short_description = (
        _("Create slottimes from generation"))


class SlotTimeAdmin(MixinCheckOperatorAdminView, admin.ModelAdmin):
    date_hierarchy = 'start'
    list_display = ['pk', 'calendar_lt', 'booking_type', 'start', 'end',
                    'status', 'generation']
    list_filter = ['calendar', 'booking_type', 'status']
    list_per_page = 20
    ordering = ['booking_type', 'start', 'end']

    def calendar_link(self, obj):
        return '<a href="{url}?id={calendar.pk}">{calendar.name}</a>'.format(
            url=reverse(admin_urlname(obj.booking_type.calendar._meta,
                                      'changelist')),
            calendar=obj.booking_type.calendar)
    calendar_link.allow_tags = True
    calendar_link.short_description = _('calendar')


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
