# -*- coding: utf-8 -*-
"""Esup-pod recorder views."""
import hashlib
import logging
import os
import re
import uuid
from datetime import datetime, timedelta

# import urllib
from urllib.parse import unquote
from defusedxml import minidom

import bleach
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.views.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import HttpResponseRedirect, JsonResponse

# import urllib.parse
from django.shortcuts import get_object_or_404

# from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.defaultfilters import truncatechars
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from pod.main.views import in_maintenance, TEMPLATE_VISIBLE_SETTINGS
from pod.main.utils import is_ajax
from pod.recorder.models import Recorder, Recording, RecordingFileTreatment
from .forms import RecordingForm, RecordingFileTreatmentDeleteForm
from .models import __REVATSO__
from .utils import (
    get_id_media,
    handle_upload_file,
    create_xml_element,
    get_media_package_content,
    digest_is_valid,
    create_digest_auth_response,
)

DEFAULT_RECORDER_PATH = getattr(settings, "DEFAULT_RECORDER_PATH", "/data/ftp-pod/ftp/")
DEFAULT_RECORDER_USER_ID = getattr(settings, "DEFAULT_RECORDER_USER_ID", 1)

# USE_CAS = getattr(settings, "USE_CAS", False)
# USE_SHIB = getattr(settings, "USE_SHIB", False)
LOGIN_URL = getattr(settings, "LOGIN_URL", "/authentication_login/")
__TITLE_SITE__ = getattr(TEMPLATE_VISIBLE_SETTINGS, "TITLE_SITE", "Pod")

OPENCAST_FILES_DIR = getattr(settings, "OPENCAST_FILES_DIR", "opencast-files")
OPENCAST_MEDIAPACKAGE = getattr(
    settings,
    "OPENCAST_MEDIAPACKAGE",
    """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <mediapackage xmlns="http://mediapackage.opencastproject.org" id="" start="">
    <media/>
    <metadata/>
    <attachments/>
    <publications/>
    </mediapackage>
    """,
)
# Possible value are "mid" or "piph" or "pipb"
OPENCAST_DEFAULT_PRESENTER = getattr(settings, "OPENCAST_DEFAULT_PRESENTER", "mid")

MEDIA_URL = getattr(settings, "MEDIA_URL", "/media/")

logger = logging.getLogger("pod.recorder.view")


def check_recorder(recorder_id, request):
    """Check if a Recorder with this id exist.

    Args:
        recorder_id (int): The recorder id.
        request (WSGIRequest): The request.

    Returns:
        The Recorder if exists or PermissionDenied otherwise.

    """
    if recorder_id is None:
        messages.add_message(request, messages.ERROR, _("Recorder should be indicated."))
        raise PermissionDenied
    try:
        recorder = Recorder.objects.get(id=recorder_id)
    except ObjectDoesNotExist:
        messages.add_message(request, messages.ERROR, _("Recorder not found."))
        raise PermissionDenied
    return recorder


def case_delete(form, request):
    """Delete a file."""
    file = form.cleaned_data["source_file"]
    try:
        if os.path.exists(file):
            os.remove(file)
        rec = RecordingFileTreatment.objects.get(file=file)
        rec.delete()
    except ObjectDoesNotExist:
        pass
    message = _("The selected record has been deleted.")
    messages.add_message(request, messages.INFO, message)


def fetch_user(request, form):
    """Return the user from the request."""
    if request.POST.get("user") and request.POST.get("user") != "":
        return form.cleaned_data["user"]
    else:
        return request.user


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def add_recording(request):
    """Add a recording to the system."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    mediapath = request.GET.get("mediapath", "")
    course_title = request.GET.get("course_title", "")
    recorder = request.GET.get("recorder", None)

    recorder = check_recorder(recorder, request)

    initial = {
        "title": course_title,
        "type": recorder.recording_type,
        "recorder": recorder,
        "user": request.user,
    }

    if not mediapath and not (
        request.user.is_superuser or request.user.has_perm("recorder.add_recording")
    ):
        messages.add_message(
            request, messages.ERROR, _("Media path should be indicated.")
        )
        raise PermissionDenied

    if mediapath != "":
        initial["source_file"] = "%s" % os.path.join(DEFAULT_RECORDER_PATH, mediapath)

    form = RecordingForm(request, initial=initial)

    if request.method == "POST":  # If the form has been submitted...
        # A form bound to the POST data
        form = RecordingForm(request, request.POST)
        if form.is_valid():  # All validation rules pass
            if form.cleaned_data["delete"] is True:
                case_delete(form, request)
                return redirect("/")
            med = form.save(commit=False)
            med.user = fetch_user(request, form)
            med.save()
            file = form.cleaned_data["source_file"]
            rec = RecordingFileTreatment.objects.get(file=file)
            rec.delete()
            message = _(
                "Your publication is saved."
                " Adding it to your videos will be in a few minutes."
            )

            messages.add_message(request, messages.INFO, message)
            return redirect(reverse("video:dashboard"))
        else:
            message = _("One or more errors have been found in the form.")
            messages.add_message(request, messages.ERROR, message)

    return render(request, "recorder/add_recording.html", {"form": form})


def video_publish(recorder, mediapath, request, course_title):
    """Assign a video by email or automatically depending on the configuration of the recorder."""
    if recorder.publication_auto is True:
        # Here we have already checked that the upload is complete
        rft = RecordingFileTreatment.objects.get(file=mediapath, recorder=recorder)
        title = rft.file.split("/")
        title = title[len(title) - 1]
        recording = Recording(
            title=title,
            type=rft.type,
            source_file=rft.file,
            user=recorder.user,
            recorder=rft.recorder,
        )
        recording.save()
        rft.delete()
        return HttpResponse("auto")
    else:
        link_url = "".join(
            [
                request.build_absolute_uri(reverse("record:add_recording")),
                "?mediapath=",
                mediapath,
                "&course_title=%s" % course_title,
                "&recorder=%s" % recorder.id,
            ]
        )
        # link_url = reformat_url_if_use_cas_or_shib(request, link_url)

        html_msg = _(
            "<p>Hello,<br>a new recording has just been added on %("
            "title_site)s from the recorder “%(recorder)s”.<br>"
            'To assign it, just click on link below.</p><p><a href="%('
            'link_url)s">%(link_url)s</a><br><em>If you cannot click on '
            "the link, just copy-paste it in your browser.</em>"
            "</p><p>Regards.</p>"
        ) % {
            "title_site": __TITLE_SITE__,
            "recorder": recorder.name,
            "link_url": link_url,
        }

        text_msg = bleach.clean(html_msg, tags=[], strip=True)
        # Sending the mail to the managers defined in the administration
        # for the concerned recorder
        if recorder.user:
            admin_emails = [recorder.user.email]
        else:
            admin_emails = User.objects.filter(is_superuser=True).values_list(
                "email", flat=True
            )
        subject = "[" + __TITLE_SITE__ + "] %s" % _("New recording added.")
        # Send the mail to the managers or admins (if not found)
        email_msg = EmailMultiAlternatives(
            subject, text_msg, settings.DEFAULT_FROM_EMAIL, admin_emails
        )

        email_msg.attach_alternative(html_msg, "text/html")
        email_msg.send(fail_silently=False)
        return HttpResponse("ok")


def recorder_notify(request):
    """Notify the recorder."""
    # Used by URL like https://pod.univ.fr/recorder_notify/?recordingPlace
    # =192_168_1_10&mediapath=file.zip&key=77fac92a3f06d50228116898187e50e5
    mediapath = request.GET.get("mediapath") or ""
    recording_place = request.GET.get("recordingPlace") or ""
    course_title = request.GET.get("course_title") or ""
    key = request.GET.get("key") or ""
    # Check arguments
    if recording_place and mediapath and key:
        recording_ip_place = recording_place.replace("_", ".")
        try:
            # Check recorder existence corresponding to IP address
            recorder = Recorder.objects.get(
                address_ip=recording_ip_place, sites=get_current_site(request)
            )
        except ObjectDoesNotExist:
            recorder = None
        if recorder:
            # Generate hashkey
            m = hashlib.md5()
            m.update(recording_place.encode("utf-8") + recorder.salt.encode("utf-8"))
            if key != m.hexdigest():
                return HttpResponse("nok: key is not valid")
            return video_publish(recorder, mediapath, request, course_title)
        else:
            return HttpResponse(
                "nok: address_ip not valid or recorder not found in this site"
            )
    else:
        return HttpResponse("nok: recordingPlace or mediapath or key are missing")


@csrf_protect
@login_required(redirect_field_name="referrer")
@staff_member_required(redirect_field_name="referrer")
def claim_record(request):
    """Claim a record."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    site = get_current_site(request)
    # get records list ordered by date
    records_list = RecordingFileTreatment.objects.filter(require_manual_claim=True)

    records_list = records_list.exclude(
        pk__in=[rec.id for rec in records_list if site not in rec.recorder.sites.all()]
    )

    records_list = records_list.order_by("-date_added")
    page = request.GET.get("page", 1)

    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    paginator = Paginator(records_list, 12)
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)

    if is_ajax(request):
        return render(
            request,
            "recorder/record_list.html",
            {"records": records, "full_path": full_path},
        )

    return render(
        request,
        "recorder/claim_record.html",
        {"records": records, "full_path": full_path, "page_title": _("Claim a record")},
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
@user_passes_test(
    lambda u: u.is_superuser or u.has_perm("recorder.delete_recording"),
    redirect_field_name="referrer",
)
def delete_record(request, id=None):
    """Delete a record."""
    record = get_object_or_404(RecordingFileTreatment, id=id)

    form = RecordingFileTreatmentDeleteForm()

    if request.method == "POST":
        form = RecordingFileTreatmentDeleteForm(request.POST)
        if form.is_valid():
            if os.path.exists(record.file):
                os.remove(record.file)
            record.delete()
            messages.add_message(
                request, messages.INFO, _("The record has been deleted.")
            )
            return redirect(reverse("record:claim_record"))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request,
        "recorder/record_delete.html",
        {
            "record": record,
            "form": form,
            "page_title": _("Deleting the record “%s”")
            % (truncatechars(record.filename(), 43)),
        },
    )


def studio_toml(request, studio_url):
    """Render a settings.toml configuration file for Opencast Studio."""
    # OpenCast Studio configuration
    # See https://github.com/elan-ev/opencast-studio/blob/master/CONFIGURATION.md
    # Add parameter: the pod studio URL
    studio_url = request.build_absolute_uri(
        reverse(
            "recorder:studio_pod",
        )
    )
    dashboard_url = request.build_absolute_uri(
        reverse(
            "video:dashboard",
        )
    )
    # force https for developpement server
    studio_url = studio_url.replace("http://", "https://")
    dashboard_url = dashboard_url.replace("http://", "https://")
    content_text = """
    [opencast]
    serverUrl = "%(serverUrl)s"
    loginProvided = true
    [upload]
    presenterField = 'hidden'
    seriesField = 'hidden'
    [return]
    target = "%(target)s"
    label = "%(label)s"
    [theme]
    """
    content_text = content_text % {
        "serverUrl": studio_url,
        "target": dashboard_url,
        "label": "mes videos",
    }
    return HttpResponse(content_text, content_type="text/plain")


# INNER METHODS
def open_studio_pod(request):
    """Render the Opencast studio view in Esup-Pod."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    if __REVATSO__ and request.user.is_staff is False:
        return render(
            request, "recorder/opencast-studio.html", {"access_not_allowed": True}
        )
    # Render the Opencast studio index file
    opencast_studio_rendered = (
        render_to_string("studio/index.html").replace("\r", "").replace("\n", "")
    )
    head = opencast_studio_rendered[
        opencast_studio_rendered.index("<head>")
        + len("<head>") : opencast_studio_rendered.index("</head>")
    ]
    scripts = re.findall('<script .[a-z="]+ src=".[a-z/.0-9]+"></script>', head)
    styles = re.findall("<style>.*</style>", head)
    body = opencast_studio_rendered[
        opencast_studio_rendered.index("<body>")
        + len("<body>") : opencast_studio_rendered.index("</body>")
    ]
    body = "".join(scripts) + "".join(styles) + body
    return render(
        # Render the Opencast studio index file
        request,
        "recorder/opencast-studio.html",
        {"body": body, "default_presenter": OPENCAST_DEFAULT_PRESENTER},
    )


def open_presenter_post(request):
    """Check if the value for `presenter` is valid."""
    if (
        request.POST
        and request.POST.get("presenter")
        and request.POST.get("presenter") in ["mid", "piph", "pipb"]
    ):
        request.session["presenter"] = request.POST.get("presenter")
        return JsonResponse({"valid": True}, status=200)

    return HttpResponseBadRequest()


def open_studio_static(request, file):
    """Redirect to all static files inside Opencast studio static subfolder."""
    extension = file.split(".")[-1]
    if extension == "js":
        path_file = os.path.join(
            settings.BASE_DIR, "custom", "static", "opencast", "studio/static/%s" % file
        )
        f = open(path_file, "r")
        content_file = f.read()
        content_file = content_file.replace("Opencast", "Pod")
        return HttpResponse(content_file, content_type="application/javascript")
    return HttpResponseRedirect("/static/opencast/studio/static/%s" % file)


def open_info_me_json(request):
    """Render an info/me.json file for current user roles in Opencast Studio."""
    # Providing a user with ROLE_STUDIO should grant all necessary rights.
    # See https://github.com/elan-ev/opencast-studio/blob/master/README.md
    return render(request, "studio/me.json", {}, content_type="application/json")


def open_ingest_createMediaPackage(request):
    """Create and return a mediaPacakge xml file."""
    # URI createMediaPackage useful for OpenCast Studio
    # Necessary id. Example format: a3d9e9f3-66d0-403b-a775-acb3f79196d4
    id_media = uuid.uuid4()
    # Necessary start date. Example format: 2021-12-08T08:52:28Z
    start = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%zZ")
    media_package_dir = os.path.join(
        settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % id_media
    )
    media_package_file = os.path.join(media_package_dir, "%s.xml" % id_media)
    # create directory to store all the data.
    os.makedirs(media_package_dir, exist_ok=True)

    media_package_content = minidom.parseString(OPENCAST_MEDIAPACKAGE)
    mediapackage = media_package_content.getElementsByTagName("mediapackage")[0]
    mediapackage.setAttribute("id", "%s" % id_media)
    mediapackage.setAttribute("start", start)

    presenter = OPENCAST_DEFAULT_PRESENTER
    if request.session.get("presenter"):
        presenter = request.session["presenter"]
        del request.session["presenter"]
    mediapackage.setAttribute("presenter", presenter)

    with open(media_package_file, "w") as f:
        f.write(media_package_content.toxml())
    return HttpResponse(media_package_content.toxml(), content_type="application/xml")


def open_ingest_addDCCatalog(request):
    """URI addDCCatalog useful for OpenCast Studio."""
    # Form management with 3 parameters: mediaPackage, dublin_core, flavor
    # For Pod, management of dublin_core is useless
    if (
        request.POST.get("mediaPackage")
        and request.POST.get("flavor")
        and (request.POST.get("dublinCore") or request.FILES.getlist("dublinCore"))
    ):
        typeCatalog = "dublincore/episode"
        id_media = get_id_media(request)

        # Create directory to store the data
        media_package_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % id_media
        )
        os.makedirs(media_package_dir, exist_ok=True)

        media_package_content, media_package_file = get_media_package_content(
            media_package_dir, id_media
        )

        # Create the dublincore file.
        dublincore_file = os.path.join(media_package_dir, "dublincore.xml")

        # Get and store the content of dublincore file.
        if request.POST.get("dublinCore") and request.POST.get("dublinCore") != "":
            dublin_core_file = request.POST.get("dublinCore")
            with open(dublincore_file, "w+") as f:
                f.write(unquote(dublin_core_file))

        elif request.FILES.getlist("dublinCore"):
            file = request.FILES.getlist("dublinCore")[0]
            with open(dublincore_file, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

        # Create the xml file with the same name as the folder with typeCatalog access url
        if request.POST.get("flavor") and request.POST.get("flavor") != "":
            typeCatalog = request.POST.get("flavor")

        dc_url = str(
            "%(http)s://%(host)s%(media)sopencast-files/%(id_media)s/dublincore.xml"
            % {
                "http": "https" if request.is_secure() else "http",
                "host": request.get_host(),
                "media": MEDIA_URL,
                "id_media": "%s" % id_media,
            }
        )
        catalog = create_xml_element(
            media_package_content, "catalog", typeCatalog, "text/xml", dc_url
        )

        metadata = media_package_content.getElementsByTagName("metadata")[0]
        metadata.appendChild(catalog)

        with open(media_package_file, "w+") as f:
            f.write(media_package_content.toxml())

        return HttpResponse(media_package_content.toxml(), content_type="application/xml")

    return HttpResponseBadRequest()


def open_ingest_addAttachment(request):
    """URI addAttachment useful for OpenCast Studio."""
    # Form management with 3 parameters: mediaPackage, flavor, BODY (acl.xml file)
    if (
        request.POST.get("mediaPackage")
        and request.POST.get("flavor")
        and (request.FILES.get("BODY") or request.FILES.getlist("file"))
    ):
        return handle_upload_file(request, "attachment", "text/xml", "attachments")
    return HttpResponseBadRequest()


def open_ingest_addTrack(request):
    """URI addTrack useful for OpenCast Studio."""
    # Form management with 4 parameters: mediaPackage, flavor, tags, BODY (video file)
    if (
        request.POST.get("mediaPackage")
        and request.POST.get("flavor")
        and (request.FILES.get("BODY") or request.FILES.getlist("file"))
        # and request.POST.get("tags") # unused tags
    ):
        return handle_upload_file(request, "track", "video/webm", "media")
    return HttpResponseBadRequest()


def open_ingest_addCatalog(request):
    """URI ingest useful for OpenCast Studio (when cutting video)."""
    # Form management with 3 parameter: flavor, mediaPackage, BODY(smil file)
    if (
        request.POST.get("mediaPackage")
        and request.POST.get("flavor")
        and (request.FILES.get("BODY") or request.FILES.getlist("file"))
    ):
        return handle_upload_file(request, "catalog", "text/xml", "metadata")
    return HttpResponseBadRequest()


def open_ingest_ingest(request):
    """URI ingest useful for OpenCast Studio."""
    # Form management with 1 parameter: mediaPackage
    # Management of the mediaPackage (XML)

    if request.POST.get("mediaPackage"):
        id_media = get_id_media(request)
        media_package_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % id_media
        )
        media_package_content, media_package_file = get_media_package_content(
            media_package_dir, id_media
        )

        # Create the recording
        # Search for the recorder corresponding to the Studio
        recorder = Recorder.objects.filter(
            recording_type="studio", sites=get_current_site(None)
        ).first()

        if recorder:
            if not request.user.is_anonymous:
                req_user = request.user
            else:
                req_user = User.objects.get(id=DEFAULT_RECORDER_USER_ID)

            recording = Recording.objects.create(
                user=req_user,
                title=id_media,
                type="studio",
                # Source file corresponds to Pod XML file
                source_file=media_package_file,
                recorder=recorder,
            )
            recording.save()
        else:
            messages.add_message(
                request, messages.ERROR, _("Recorder for Studio not found.")
            )
            raise PermissionDenied

        return HttpResponse(media_package_content.toxml(), content_type="application/xml")

    return HttpResponseBadRequest()


# OPENCAST VIEWS WITH LOGIN MANDATORY
@login_required(redirect_field_name="referrer")
def studio_pod(request):
    """Call open_studio_pod if user is logged in."""
    return open_studio_pod(request)


@csrf_exempt
@login_required(redirect_field_name="referrer")
def presenter_post(request):
    """Call open_presenter_post if user is logged in."""
    return open_presenter_post(request)


@login_required(redirect_field_name="referrer")
def studio_static(request, file):
    """Call open_studio_static if user is logged in."""
    return open_studio_static(request, file)


@login_required(redirect_field_name="referrer")
def studio_root_file(request, file):
    """Redirect to root static files of Opencast studio folder."""
    extension = file.split(".")[-1]
    if extension == "js":
        path_file = os.path.join(
            settings.BASE_DIR, "custom", "static", "opencast", "studio/%s" % file
        )
        f = open(path_file, "r")
        content_file = f.read()
        content_file = content_file.replace("Opencast", "Pod")
        return HttpResponse(content_file, content_type="application/javascript")
    return HttpResponseRedirect("/static/opencast/studio/%s" % file)


@login_required(redirect_field_name="referrer")
def settings_toml(request):
    """Render a settings.toml configuration file for Opencast Studio."""
    studio_url = request.build_absolute_uri(
        reverse(
            "recorder:studio_pod",
        )
    )
    return studio_toml(request, studio_url)


@login_required(redirect_field_name="referrer")
def info_me_json(request):
    """Call open_info_me_json if user is logged in."""
    return open_info_me_json(request)


@login_required(redirect_field_name="referrer")
def ingest_createMediaPackage(request):
    """Call open_ingest_createMediaPackage if user is logged in."""
    return open_ingest_createMediaPackage(request)


@login_required(redirect_field_name="referrer")
@csrf_exempt
def ingest_addDCCatalog(request):
    """Call open_ingest_addDCCatalog if user is logged in."""
    return open_ingest_addDCCatalog(request)


@csrf_exempt
@login_required(redirect_field_name="referrer")
def ingest_addAttachment(request):
    """Call open_ingest_addAttachment if user is logged in."""
    return open_ingest_addAttachment(request)


@csrf_exempt
@login_required(redirect_field_name="referrer")
def ingest_addTrack(request):
    """Call open_ingest_addTrack if user is logged in."""
    return open_ingest_addTrack(request)


@csrf_exempt
@login_required(redirect_field_name="referrer")
def ingest_addCatalog(request):
    """Call open_ingest_addCatalog if user is logged in."""
    return open_ingest_addCatalog(request)


@csrf_exempt
@login_required(redirect_field_name="referrer")
def ingest_ingest(request):
    """Call open_ingest_ingest if user is logged in."""
    return open_ingest_ingest(request)


# OPENCAST VIEWS WITH Almost DIGEST AUTH (FOR EXTERNAL API CALL)
@csrf_exempt
@require_http_methods(["POST"])
def digest_presenter_post(request):
    """Call open_presenter_post if user credentials are valid."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    return open_presenter_post(request)


@require_http_methods(["GET"])
def digest_studio_static(request, file):
    """Call open_studio_static if user credentials are valid."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    return open_studio_static(request, file)


@require_http_methods(["GET"])
def digest_settings_toml(request):
    """Render a settings.toml configuration file for Opencast Studio."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    studio_url = request.build_absolute_uri(
        reverse(
            "recorder_digest:digest_studio_pod",
        )
    )

    return studio_toml(request, studio_url)


@require_http_methods(["GET"])
def digest_info_me_json(request):
    """Call open_info_me_json if user credentials are valid."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    return open_info_me_json(request)


@require_http_methods(["GET"])
def digest_ingest_createMediaPackage(request):
    """Call open_ingest_createMediaPackage if user credentials are valid."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    return open_ingest_createMediaPackage(request)


@csrf_exempt
@require_http_methods(["POST"])
def digest_ingest_addDCCatalog(request):
    """Call open_ingest_addDCCatalog if user credentials are valid."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    return open_ingest_addDCCatalog(request)


@csrf_exempt
@require_http_methods(["POST"])
def digest_ingest_addAttachment(request):
    """Call open_ingest_addAttachment if user credentials are valid."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    return open_ingest_addAttachment(request)


@csrf_exempt
@require_http_methods(["POST"])
def digest_ingest_addTrack(request):
    """Call open_ingest_addTrack if user credentials are valid."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    return open_ingest_addTrack(request)


@csrf_exempt
@require_http_methods(["POST"])
def digest_ingest_addCatalog(request):
    """Call open_ingest_addCatalog if user credentials are valid."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    return open_ingest_addCatalog(request)


@csrf_exempt
@require_http_methods(["POST"])
def digest_ingest_ingest(request):
    """Call open_ingest_ingest if user credentials are valid."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    return open_ingest_ingest(request)


@require_http_methods(["GET"])
def digest_hosts_json(request):
    """URI hosts_json useful for OpenCast Studio."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    host = (
        "https://%s" % request.get_host()
        if (request.is_secure())
        else "http://%s" % request.get_host()
    )
    server_ip = request.headers.get(
        "x-forwarded-for", request.META.get("REMOTE_ADDR", "")
    )
    server_ip = server_ip.split(",")[0] if server_ip else None

    # cf https://stable.opencast.org/docs.html?path=/services & https://stable.opencast.org/services/hosts.json
    return JsonResponse(
        {
            "hosts": {
                "host": {
                    "base_url": host,
                    "address": server_ip,
                    "node_name": "AllInOne",
                    "memory": 2082471936,
                    "cores": 2,
                    "max_load": 2,
                    "online": True,
                    "active": True,
                    "maintenance": False,
                }
            },
        },
        status=200,
    )


@csrf_exempt
@require_http_methods(["POST"])
def digest_capture_admin(request, name):
    """URI capture_admin useful for OpenCast Studio."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    known_states = [
        "idle",
        "shutting_down",
        "capturing",
        "uploading",
        "unknown",
        "offline",
        "error",
    ]
    if request.POST.get("state", "") not in known_states:
        return HttpResponseBadRequest()

    return HttpResponse(name + " set to " + request.POST.get("state"))


@csrf_exempt
@require_http_methods(["POST"])
def digest_capture_admin_configuration(request, name):
    """URI capture_admin_configuration useful for OpenCast Studio."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    xml_to_return = '<?xml version="1.0" encoding="utf-8"?>'

    # attention clés / valeurs identiques à ce qui est envoyé
    if request.content_type == "multipart/form-data":
        dom = minidom.parseString(request.POST.get("configuration"))
        entries = dom.getElementsByTagName("entry")

        xml_to_return += (
            '<!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">'
        )
        xml_to_return += "<properties>"
        for entry in entries:
            key = entry.getAttribute("key")
            value = entry.firstChild.nodeValue if entry.firstChild else None
            if key and value:
                xml_to_return += f'<entry key="{key}">{value}</entry>'
        xml_to_return += "</properties>"

    return HttpResponse(xml_to_return, content_type="application/xml")


@require_http_methods(["GET"])
def digest_admin_ng_series(request):
    """URI admin_ng_series useful for OpenCast Studio."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    # Example format: 2021-12-08T08:52:28Z
    one_minute_ago = datetime.now() + timedelta(minutes=-1)
    creation_date = one_minute_ago.strftime("%Y-%m-%dT%H:%M:%S%zZ")

    return JsonResponse(
        {
            "total": 1,
            "offset": 0,
            "count": 1,
            "limit": 100,
            "results": [
                {
                    "createdBy": "admin",
                    "organizers": [],
                    "id": "ID-blender-foundation",
                    "contributors": [],
                    "creation_date": creation_date,
                    "title": "admin",
                }
            ],
        },
        status=200,
    )


@require_http_methods(["GET"])
def digest_available(request):
    """URI available useful for OpenCast Studio."""
    if not digest_is_valid(request):
        return create_digest_auth_response(request)

    host = (
        "https://%s" % request.get_host()
        if (request.is_secure())
        else "http://%s" % request.get_host()
    )

    # Example format: 2021-12-08T08:52:28Z
    yesterday = datetime.now() + timedelta(days=-1)
    online = yesterday.strftime("%Y-%m-%dT%H:%M:%S%zZ")
    return JsonResponse(
        {
            "services": {
                "service": {
                    "type": "org.opencastproject.capture.admin",
                    "host": host,
                    "path": "open/studio/capture-admin",
                    "active": True,
                    "online": True,
                    "maintenance": False,
                    "jobproducer": False,
                    "onlinefrom": online,
                    "service_state": "NORMAL",
                    "state_changed": online,
                    "error_state_trigger": 0,
                    "warning_state_trigger": 0,
                }
            }
        },
        status=200,
    )
