"""Authentication views."""

from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.http import QueryDict
from django.utils.http import url_has_allowed_host_and_scheme
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

    if referrer.startswith("https:/") and not referrer.startswith("https://"):
        referrer = "https://" + referrer[len("https:/") :]
    elif referrer.startswith("http:/") and not referrer.startswith("http://"):
        referrer = "http://" + referrer[len("http:/") :]

    if not url_has_allowed_host_and_scheme(
        referrer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        raise SuspiciousOperation("referrer is not internal")
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
        query = QueryDict(mutable=True)
        if request.GET.get("is_iframe"):
            query["is_iframe"] = "true"
        query["next"] = referrer
        url += "?" + query.urlencode(safe="/")
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
