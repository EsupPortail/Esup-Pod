"""
Django local settings for main.

Django version : 1.11.10.
"""
from django.conf import settings

import os


##
# Assets for Ckeditor are localized in this directory
#
CKEDITOR_BASEPATH = os.path.join(
    getattr(settings, 'STATIC_URL', '/static/'), 'ckeditor', 'ckeditor')
