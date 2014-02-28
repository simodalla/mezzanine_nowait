# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys

from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase

from django.conf import settings
from django.contrib.auth import (BACKEND_SESSION_KEY, SESSION_KEY,
                                 get_user_model)
User = get_user_model()
from django.contrib.sessions.backends.db import SessionStore

from selenium import webdriver


class FunctionalTest(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        for arg in sys.argv:
            if 'liveserver' in arg:
                cls.server_url = 'http://' + arg.split('=')[1]
                return
        LiveServerTestCase.setUpClass()
        cls.server_url = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        if cls.server_url == cls.live_server_url:
            LiveServerTestCase.tearDownClass()

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)

    def tearDown(self):
        self.browser.quit()

    def get_url(self, url, args=None, kwargs=None):
        if url.startswith('/'):
            return '%s%s/' % (self.live_server_url, url.rstrip('/'))
        return '%s%s' % (self.live_server_url,
                         reverse(url, args=args, kwargs=kwargs))

    def create_pre_authenticated_session(self, user):
        session = SessionStore()
        session[SESSION_KEY] = user.pk
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session.save()
        ## to set a cookie we need fo first visit the domain.
        ## 404 pages load the quicktest!
        self.browser.get('{0}/404_no_such_url/'.format(self.server_url))
        self.browser.add_cookie(dict(
            name=settings.SESSION_COOKIE_NAME,
            value=session.session_key,
            path='/',
        ))
        return session.session_key

    def login(self, username, password, url, submit_id=None,
              submit_css_selector=None):
        self.browser.get('%s%s' % (self.live_server_url, url))
        username_input = self.browser.find_element_by_name('username')
        username_input.send_keys(username)
        password_input = self.browser.find_element_by_name('password')
        password_input.send_keys(password)
        if submit_css_selector:
            self.browser.find_element_by_css_selector(
                submit_css_selector).click()
            return True
        elif submit_id:
            self.browser.find_element_by_id(submit_id).click()
            return True
        return False

    # def admin_login(self, username, password, url):
    #     self.login(username, password, '/admin/login/')
