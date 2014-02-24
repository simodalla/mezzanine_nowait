# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext as _

from mezzanine.conf import register_setting

NOWAIT_APP_NAME = _('NoWait')
NOWAIT_GROUP_ADMINS = ('nowait_admins', '*')
NOWAIT_GROUP_OPERATORS = ('nowait_operators', '*')
NOWAIT_ROOT_SLUG = 'nowait'


register_setting(
    name='NOWAIT_ROOT_SLUG',
    description='The slug of root page of nowait app into mezzanine site',
    editable=True,
    default=NOWAIT_ROOT_SLUG
)

register_setting(
    name='NOWAIT_GROUP_ADMINS',
    description='Group of nowait admin users',
    editable=False,
    default=NOWAIT_GROUP_ADMINS
)

register_setting(
    name='NOWAIT_GROUP_OPERATORS',
    description='Group of nowait admin users',
    editable=False,
    default=NOWAIT_GROUP_OPERATORS
)
