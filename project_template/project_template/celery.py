# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

from celery import Celery

from django.conf import settings

sys.path.insert(1, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../..")))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_template.settings')

print(sys.path)

app = Celery('project_template')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
