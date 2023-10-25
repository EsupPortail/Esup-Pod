"""Esup-Pod main views."""

# This file is part of Esup-Pod.
#
# Esup-Pod is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Esup-Pod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Esup-Pod. If not, see <https://www.gnu.org/licenses/>.
import bleach

from .forms import ContactUsForm, SUBJECT_CHOICES
from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET
from django.template import loader
from django.core.mail import EmailMultiAlternatives
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import JsonResponse
from wsgiref.util import FileWrapper
from django.db.models import Q, Count
from pod.video.models import Video, remove_accents
from pod.authentication.forms import FrontOwnerForm, SetNotificationForm
from django.db.models import Sum
import os
import mimetypes
import json
from django.contrib.auth.decorators import login_required
from .models import Configuration
from honeypot.decorators import check_honeypot


##
# Settings exposed in templates
#
TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "DESC_SITE": "The purpose of Esup-Pod is to facilitate the provision of video and\
        thereby encourage its use in teaching and research.",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/esup-pod.svg",
        "LOGO_PLAYER": "img/pod_favicon.svg",
        "LINK_PLAYER": "",
        "LINK_PLAYER_NAME": _("Home"),
        "FOOTER_TEXT": ("",),
        "FAVICON": "img/pod_favicon.svg",
        "CSS_OVERRIDE": "",
        "PRE_HEADER_TEMPLATE": "",
        "POST_FOOTER_TEMPLATE": "",
        "TRACKING_TEMPLATE": "",
    },
)

__TITLE_SITE__ = getattr(TEMPLATE_VISIBLE_SETTINGS, "TITLE_SITE", "Pod")
CONTACT_US_EMAIL = getattr(
    settings,
    "CONTACT_US_EMAIL",
    [mail for name, mail in getattr(settings, "MANAGERS")],
)
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")
USER_CONTACT_EMAIL_CASE = getattr(settings, "USER_CONTACT_EMAIL_CASE", [])
CUSTOM_CONTACT_US = getattr(settings, "CUSTOM_CONTACT_US", False)
MANAGERS = getattr(settings, "MANAGERS", [])
USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)
USER_CONTACT_EMAIL_CASE = getattr(settings, "USER_CONTACT_EMAIL_CASE", [])

SUPPORT_EMAIL = getattr(settings, "SUPPORT_EMAIL", None)
HIDE_USERNAME = getattr(settings, "HIDE_USERNAME", False)
MENUBAR_HIDE_INACTIVE_OWNERS = getattr(settings, "MENUBAR_HIDE_INACTIVE_OWNERS", True)
MENUBAR_SHOW_STAFF_OWNERS_ONLY = getattr(
    settings, "MENUBAR_SHOW_STAFF_OWNERS_ONLY", False
)
HIDE_USER_TAB = getattr(settings, "HIDE_USER_TAB", False)
LOGIN_URL = getattr(settings, "LOGIN_URL", "/authentication_login/")


def in_maintenance():
    """Return true if maintenance_mode is ON."""
    return (
        True if Configuration.objects.get(key="maintenance_mode").value == "1" else False
    )


@csrf_protect
def download_file(request):
    if request.POST and request.POST.get("filename"):
        filename = os.path.join(settings.MEDIA_ROOT, request.POST["filename"])
        wrapper = FileWrapper(open(filename, "rb"))
        response = HttpResponse(wrapper, content_type=mimetypes.guess_type(filename)[0])
        response["Content-Length"] = os.path.getsize(filename)
        response["Content-Disposition"] = 'attachment; filename="%s"' % os.path.basename(
            filename
        )
        return response
    else:
        raise PermissionDenied


def get_manager_email(owner):
    """
    Get manager email.

    @param owner instanceOf User Model.
    return email of user's manager if exist
    else return all managers emails
    """
    # Si la fonctionnalité des etablissements est activée
    if USE_ESTABLISHMENT_FIELD and owner:
        v_estab = owner.owner.establishment.lower()
        # vérifier si le mail du manager (de l'etablissement
        # du propriétaire de la vidéo) est renseigné
        if v_estab in dict(MANAGERS):
            # print('send to ------> ', [dict(MANAGERS)[v_estab]])
            return [dict(MANAGERS)[v_estab]]
    return CONTACT_US_EMAIL


def get_dest_email(owner, video, form_subject, request):
    """Determine to which recipient an email should be addressed."""
    dest_email = []
    # Soit le owner a été spécifié
    # Soit on le récupere via la video
    # v_owner = instance de User
    v_owner = owner if (owner) else getattr(video, "owner", None)
    # Si ni le owner ni la video a été renseigné
    if not v_owner:
        # Vérifier si l'utilisateur est authentifié
        # le manager de son etablissement sera le dest du mail
        if request.user.is_authenticated:
            return get_manager_email(request.user)
        # Autrement le destinataire du mail sera le(s) manager(s)
        # ou le support dans le cas de Grenoble
        return SUPPORT_EMAIL if SUPPORT_EMAIL else CONTACT_US_EMAIL

    # Si activation de la fonctionnalité de mail custom
    if CUSTOM_CONTACT_US:
        # vérifier si le sujet du mail est attribué
        # au propriétaire de la vidéo
        if form_subject in USER_CONTACT_EMAIL_CASE:
            dest_email = [v_owner.email]
        else:
            dest_email = get_manager_email(v_owner)
    else:
        # Sinon aucune envie d'utiliser cette fonctionnalité
        # On utilise le fonctionnement de base
        dest_email = [v_owner.email] if v_owner else CONTACT_US_EMAIL
    return dest_email


@csrf_protect
@check_honeypot(field_name="firstname")
def contact_us(request):
    """Handle "Contact us" form."""
    owner = (
        User.objects.get(id=request.GET.get("owner"))
        if (
            request.GET.get("owner")
            and User.objects.filter(id=request.GET.get("owner")).first()
        )
        else None
    )

    video = (
        Video.objects.get(id=request.GET.get("video"), sites=get_current_site(request))
        if (
            request.GET.get("video")
            and request.GET.get("video").isdigit()
            and Video.objects.filter(
                id=request.GET.get("video"), sites=get_current_site(request)
            ).first()
        )
        else None
    )

    description = (
        "%s: %s\n%s: %s%s\n\n"
        % (
            _("Title"),
            video.title,
            _("Link"),
            "https:" if request.is_secure() else "http:",
            video.get_full_url(request),
        )
        if video
        else None
    )

    send_subject = (
        request.GET.get("subject")
        if (
            request.GET.get("subject")
            and request.GET.get("subject") in [key for key, value in SUBJECT_CHOICES]
        )
        else None
    )

    prefix = "https://" if request.is_secure() else "http://"
    home_page = "".join([prefix, get_current_site(request).domain])
    url_referrer = (
        request.META["HTTP_REFERER"] if request.META.get("HTTP_REFERER") else home_page
    )

    form = ContactUsForm(
        request,
        initial={
            "url_referrer": url_referrer,
            "subject": send_subject,
            "description": description,
        },
    )

    if request.method == "POST":
        form = ContactUsForm(request, request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            form_subject = (
                form.cleaned_data["subject"]
                if (form.cleaned_data.get("subject"))
                else send_subject
            )
            subject = "[ %s ] %s" % (
                __TITLE_SITE__,
                dict(SUBJECT_CHOICES)[form_subject],
            )
            email = form.cleaned_data["email"]
            message = form.cleaned_data["description"]

            valid_human = form.cleaned_data["valid_human"]
            if valid_human:
                return redirect(form.cleaned_data["url_referrer"])

            html_content = loader.get_template("mail/mail.html").render(
                {
                    "name": name,
                    "email": email,
                    "TITLE_SITE": __TITLE_SITE__,
                    "message": message.replace("\n", "<br>"),
                    "url_referrer": form.cleaned_data["url_referrer"],
                }
            )
            text_content = bleach.clean(html_content, tags=[], strip=True)
            dest_email = []
            dest_email = get_dest_email(owner, video, form_subject, request)

            msg = EmailMultiAlternatives(
                subject, text_content, DEFAULT_FROM_EMAIL, dest_email, reply_to=[email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            # EMAIL TO SENDER
            subject = "[ %s ] %s %s" % (
                __TITLE_SITE__,
                _("your message untitled"),
                dict(SUBJECT_CHOICES)[form_subject],
            )

            html_content = loader.get_template("mail/mail_sender.html").render(
                {
                    "TITLE_SITE": __TITLE_SITE__,
                    "message": message.replace("\n", "<br>"),
                }
            )
            text_content = bleach.clean(html_content, tags=[], strip=True)
            msg = EmailMultiAlternatives(
                subject, text_content, DEFAULT_FROM_EMAIL, [email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            messages.add_message(request, messages.INFO, _("Your message has been sent."))

            return redirect(form.cleaned_data["url_referrer"])

        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request,
        "contact_us.html",
        {"form": form, "owner": owner, "page_title": _("Contact us")},
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def user_autocomplete(request):
    """Search for users with partial names, for autocompletion."""
    if request.is_ajax():
        additional_filters = {
            "video__is_draft": False,
            "owner__sites": get_current_site(request),
        }
        if MENUBAR_HIDE_INACTIVE_OWNERS:
            additional_filters["is_active"] = True
        if MENUBAR_SHOW_STAFF_OWNERS_ONLY:
            additional_filters["is_staff"] = True
        VALUES_LIST = ["username", "first_name", "last_name", "video_count"]
        q = remove_accents(request.POST.get("term", "").lower())
        users = (
            User.objects.filter(**additional_filters)
            .filter(
                Q(username__istartswith=q)
                | Q(last_name__istartswith=q)
                | Q(first_name__istartswith=q)
            )
            .distinct()
            .order_by("last_name")
            .annotate(
                video_count=Count("video", sites=get_current_site(request), distinct=True)
            )
            .values(*list(VALUES_LIST))[:100]
        )

        data = json.dumps(list(users))
    else:
        return HttpResponseBadRequest()
    mimetype = "application/json"
    return HttpResponse(data, mimetype)


def maintenance(request):
    text = Configuration.objects.get(key="maintenance_text_disabled").value
    return render(request, "maintenance.html", {"text": text})


# Restrict to only GET requests
@require_GET
def robots_txt(request):
    """Render robots.txt file to tell robots crawlers some pages they must not parse."""
    lines = [
        "User-Agent: *",
        "Disallow: %s" % LOGIN_URL,
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# Restrict to only GET requests
@require_GET
def info_pod(request):
    """Render a json response to give information about Pod instance."""
    data = {
        "TITLE_SITE": __TITLE_SITE__,
        "VERSION": settings.VERSION,
        "COUNT_VIDEO": Video.objects.all().count(),
        "DURATION_VIDEO": Video.objects.aggregate(Sum("duration")).get(
            "duration__sum", 0
        ),
    }
    return JsonResponse(data)


@csrf_protect
@login_required(redirect_field_name="referrer")
def userpicture(request):
    frontOwnerForm = FrontOwnerForm(instance=request.user.owner)

    if request.method == "POST":
        frontOwnerForm = FrontOwnerForm(request.POST, instance=request.user.owner)
        if frontOwnerForm.is_valid():
            frontOwnerForm.save()
            # messages.add_message(
            #    request, messages.INFO, _('Your picture has been saved.'))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request,
        "userpicture/userpicture.html",
        {"frontOwnerForm": frontOwnerForm},
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def set_notifications(request):
    """Sets 'accepts_notifications' attribute on owner instance."""
    setNotificationForm = SetNotificationForm(instance=request.user.owner)

    if request.method == "POST":
        setNotificationForm = SetNotificationForm(
            request.POST, instance=request.user.owner
        )
        if setNotificationForm.is_valid():
            setNotificationForm.save()
            return JsonResponse(
                {
                    "success": True,
                    "user_accepts_notifications": request.user.owner.accepts_notifications,
                }
            )
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return JsonResponse({"success": False})
