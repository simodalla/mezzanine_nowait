# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.messages import SUCCESS
from django.core.exceptions import ImproperlyConfigured
from django.forms import ModelMultipleChoiceField

from mezzanine.conf import settings
from mezzanine.pages.models import Page


class PageContextTitleMixin(object):
    """
    Provides update of response context data with variable "title"
    valorized with value of attribute "page_title".
    """
    page_title = None

    def get_page_title(self):
        """
        Returns the attribute "page_title".
        """
        return self.page_title

    def get_context_data(self, **kwargs):
        """
        Update of response context data with variable "title" valorized with
        value of attribute "page_title".
        """
        context = super(PageContextTitleMixin, self).get_context_data(**kwargs)
        context.update({"title": self.get_page_title()})
        return context


class RequestMessagesTestMixin(object):

    def assert_in_messages(self, response, msg, level=SUCCESS, verbose=False):
        if not 'messages' in response.context:
            self.fail('"messages" not in response.context')
        messages = [(m.message, m.tags) for m in response.context['messages']]
        if verbose:
            print("messages in response: {}".format(messages))
        self.assertIn((msg, level), messages)


class UserChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        label = ''
        if obj.last_name:
            label += '%s ' % obj.last_name
        if obj.first_name:
            label += '%s' % obj.first_name
        label = label if label else obj.username
        label += ' [{}]'.format(obj.email) if obj.email else ''
        return label.strip()


def get_app_setting(app_label, setting):
    settings.use_editable()
    setting_root_slug_key = '{0}_{1}'.format(app_label.upper(),
                                             setting.upper())
    slug = getattr(settings, setting_root_slug_key, None)
    if not slug:
        raise ImproperlyConfigured("The {0} setting must not be empty.".format(
            setting_root_slug_key))
    return slug


def get_or_create_root_app_page(model_page, app_label, **defaults):
    if 'slug' in defaults:
        del defaults['slug']
    slug = get_app_setting(app_label, 'ROOT_SLUG')
    if slug != '/':
        slug = slug.lstrip('/').rstrip('/')
    root_page, created = model_page.objects.get_or_create(
        slug=slug, defaults=defaults)
    return root_page, created


def get_root_app_page(app_label):
    slug = get_app_setting(app_label, 'ROOT_SLUG')
    try:
        return Page.objects.get(slug=slug)
    except Page.DoesNotExist:
        raise ImproperlyConfigured('No page with slug "{0}" was found'.format(
            slug))
