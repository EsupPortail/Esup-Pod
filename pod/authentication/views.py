"""Authentication views."""

from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.utils.translation import gettext_lazy as _
from django.contrib import auth

# Needed to trigger signals
# flake8: noqa
from . import signals

USE_CAS = getattr(settings, "USE_CAS", False)
USE_SHIB = getattr(settings, "USE_SHIB", False)
USE_OIDC = getattr(settings, "USE_OIDC", False)
SHIB_URL = getattr(settings, "SHIB_URL", "/idp/shibboleth.sso/Login")
SHIB_LOGOUT_URL = getattr(settings, "SHIB_LOGOUT_URL", "")
OIDC_NAME = getattr(settings, "OIDC_NAME", "OpenID Connect")


def authentication_login(request):
    """Handle authentication login attempt."""
    referrer = request.GET["referrer"] if request.GET.get("referrer") else "/"
    host = (
        "https://%s" % request.get_host()
        if (request.is_secure())
        else "http://%s" % request.get_host()
    )
    if not referrer.startswith(("/", host)):
        raise SuspiciousOperation("referrer is not internal")
    iframe_param = "is_iframe=true&" if (request.GET.get("is_iframe")) else ""
    if request.user.is_authenticated:
        return redirect(referrer)
    if USE_CAS or USE_SHIB or USE_OIDC:
        return render(
            request,
            "authentication/login.html",
            {
                "USE_CAS": USE_CAS,
                "USE_SHIB": USE_SHIB,
                "SHIB_URL": SHIB_URL,
                "USE_OIDC": USE_OIDC,
                "OIDC_NAME": OIDC_NAME,
                "referrer": referrer,
                "page_title": _("Authentication"),
            },
        )
    else:
        url = reverse("local-login")
        url += "?%snext=%s" % (iframe_param, referrer.replace("&", "%26"))
        return redirect(url)


def local_logout(request):
    """Logout a user connected locally."""
    url = reverse("local-logout")
    url += "?next=/"
    return redirect(url)


def authentication_logout(request):
    """Logout a user."""
    if request.user.is_anonymous:
        return local_logout(request)
    if request.user.owner.auth_type == "CAS":
        return redirect(reverse("cas_ng_logout"))
    elif request.user.owner.auth_type == "Shibboleth":
        auth.logout(request)
        logout = SHIB_LOGOUT_URL + "?return=" + request.build_absolute_uri("/")
        return redirect(logout)
    else:
        return local_logout(request)
