"""
WSGI config for pod_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pod.settings")
proxy_host = getattr(settings, "PROXY_HOST", None)
proxy_port = getattr(settings, "PROXY_PORT", None)
if proxy_host and proxy_port:
    os.environ["http_proxy"] = os.environ["https_proxy"] = f"{proxy_host}:{proxy_port}"

application = get_wsgi_application()
