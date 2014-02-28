# -*- coding: iso-8859-1 -*-
from __future__ import unicode_literals

from copy import deepcopy

from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext, ugettext_lazy as _
from django.shortcuts import redirect

# don't delete next two lines before DisplayableAdmin because
# raise more error in testing
from django.contrib.auth import get_user_model
User = get_user_model()
from mezzanine.core.admin import DisplayableAdmin, TabularDynamicInlineAdmin

from .defaults import NOWAIT_GROUP_ADMINS
from .models import (Booking, BookingType, Calendar, DailySlotTimePattern,
                     Email, SlotTime, SlotTimesGeneration)
from .forms import BookingTypeAdminForm


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


class DailySlotTimePatternInline(TabularDynamicInlineAdmin):
    extra = 1
    model = DailySlotTimePattern
    ordering = ['day', 'start_time', 'end_time']


class EmailAdmin(admin.ModelAdmin):
    list_display = ['pk', 'email', 'notes']
    list_editable = ['email', 'notes']
    list_per_page = 20
    search_fields = ('email',)


class BookingTypeAdmin(MixinCheckOperatorAdminView, DisplayableAdmin):
    _booking_type_fieldset = (
        _('Booking type data'),
        {'fields': ('title', 'slot_length', 'calendar', 'intro',
                    'informations', 'operators', 'notifications_email_enable',
                    'notifications_emails', 'raw_location')})
    form = BookingTypeAdminForm
    inlines = [DailySlotTimePatternInline]
    list_display = ('title', 'status', 'admin_link', 'calendar', 'slot_length',
                    'informations', 'link',)
    list_per_page = 20
    radio_fields = {'calendar': admin.VERTICAL}

    def save_model(self, request, obj, form, change):
        obj.save()
        try:
            link, created = obj.get_or_create_link()
            if created:
                msg = _('Link to "%(url)s" successfully created') % {
                    'url': link.slug}
                self.message_user(request, msg, level=messages.SUCCESS)
        except ImproperlyConfigured as e:
            msg = 'Error on Link creation: {error_message}'.format(
                error_message=str(e))
            self.message_user(request, msg, level=messages.ERROR)

    def get_fieldsets(self, request, obj=None):
        """
        Merge original DisplayableAdmin with fields of BookingType model.
        """
        displayable_fieldset = list(deepcopy(
            super(BookingTypeAdmin, self).get_fieldsets(request, obj=obj)))
        if displayable_fieldset[0][1]['fields'][0] == 'title':
            displayable_fieldset[0][1]['fields'].pop(0)
            displayable_fieldset[0][1].update(
                {'classes': (u'collapse-closed',)})
            displayable_fieldset[0] = list(displayable_fieldset[0])
            displayable_fieldset[0][0] = _('Publication data')
            displayable_fieldset[0] = tuple(displayable_fieldset[0])
            displayable_fieldset.insert(0, self._booking_type_fieldset)
        else:
            displayable_fieldset += self._booking_type_fieldset
            msg = _('Wrong form for "%(model)s" creation, please contact'
                    ' site administrator.') % {
                'model': self.model._meta.verbose_name}
            self.message_user(request, msg, level=messages.ERROR)
        return tuple(displayable_fieldset)


class CalendarAdmin(MixinCheckOperatorAdminView, admin.ModelAdmin):
    list_display = ['name', 'owner', 'gid', 'booking_type_links']
    list_per_page = 20

    def booking_type_links(self, obj):
        link_tpl = ('<a href="{url}?id={bookinktype.pk}">{bookinktype.title}'
                    '</a>')
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
    list_display = ['pk', 'calendar_link', 'booking_type', 'start', 'end',
                    'status', 'generation']
    list_filter = ['booking_type', 'status']
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
    list_display = ['pk', 'user', 'formatted_day', 'formatted_start',
                    'formatted_end', 'informations', 'telephone']
    list_per_page = 20
    search_fields = ['id', 'user__username', 'user__last_name',
                     'user__first_name', 'slottime__booking_type__name']

    def formatted_day(self):
        result = u'{} {} {} {}'.format(
            ugettext(self.slottime.start.strftime('%A')).capitalize(),
            self.slottime.start.day,
            ugettext(self.slottime.start.strftime('%B')).capitalize(),
            self.slottime.start.year)
        return result
    formatted_day.admin_order_field = 'slottime__start'
    formatted_day.short_description = _('day')

    def formatted_start(self):
        return self.slottime.start.strftime('%H:%M')
    formatted_start.short_description = _('Start Time')

    def formatted_end(self):
        return self.slottime.end.strftime('%H:%M')
    formatted_end.short_description = _('End Time')


admin.site.register(Booking, BookingAdmin)
admin.site.register(BookingType, BookingTypeAdmin)
admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Email, EmailAdmin)
admin.site.register(SlotTime, SlotTimeAdmin)
admin.site.register(SlotTimesGeneration, SlotTimesGenerationAdmin)
