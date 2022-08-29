# -*- coding: utf-8 -*-
"""Esup-pod recorder views."""
from __future__ import unicode_literals
import os
import datetime
import uuid
import urllib
from urllib.parse import unquote

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.views.decorators import user_passes_test
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site
from pod.recorder.models import Recorder, Recording, RecordingFileTreatment
from .forms import RecordingForm, RecordingFileTreatmentDeleteForm
from django.contrib import messages
import hashlib
from django.http import HttpResponseRedirect, JsonResponse
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

# from pod.main.context_processors import TEMPLATE_VISIBLE_SETTINGS
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import urllib.parse
from django.shortcuts import get_object_or_404
from pod.main.views import in_maintenance
from django.views.decorators.csrf import csrf_exempt
from xml.dom import minidom

##
# Settings exposed in templates
#
TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/logo_etb.svg",
        "LOGO_PLAYER": "img/logoPod.svg",
        "LINK_PLAYER": "",
        "FOOTER_TEXT": ("",),
        "FAVICON": "img/logoPod.svg",
        "CSS_OVERRIDE": "",
        "PRE_HEADER_TEMPLATE": "",
        "POST_FOOTER_TEMPLATE": "",
        "TRACKING_TEMPLATE": "",
    },
)

DEFAULT_RECORDER_PATH = getattr(settings, "DEFAULT_RECORDER_PATH", "/data/ftp-pod/ftp/")

USE_CAS = getattr(settings, "USE_CAS", False)
USE_SHIB = getattr(settings, "USE_SHIB", False)
LOGIN_URL = getattr(settings, "LOGIN_URL", "/authentication_login/")
TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, "TITLE_SITE", "Pod")
RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY = getattr(
    settings, "RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY", False
)
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


def check_recorder(recorder, request):
    if recorder is None:
        messages.add_message(request, messages.ERROR, _("Recorder should be indicated."))
        raise PermissionDenied
    try:
        recorder = Recorder.objects.get(id=recorder)
    except ObjectDoesNotExist:
        messages.add_message(request, messages.ERROR, _("Recorder not found."))
        raise PermissionDenied
    return recorder


def case_delete(form, request):
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
    if request.POST.get("user") and request.POST.get("user") != "":
        return form.cleaned_data["user"]
    else:
        return request.user


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def add_recording(request):
    if in_maintenance():
        return redirect(reverse("maintenance"))
    mediapath = request.GET.get("mediapath") if (request.GET.get("mediapath")) else ""
    course_title = (
        request.GET.get("course_title") if request.GET.get("course_title") else ""
    )
    recorder = request.GET.get("recorder") or None

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
        messages.add_message(request, messages.ERROR, _("Mediapath should be indicated."))
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
            return redirect(reverse("video:my_videos"))
        else:
            message = _("One or more errors have been found in the form.")
            messages.add_message(request, messages.ERROR, message)

    return render(request, "recorder/add_recording.html", {"form": form})


def reformat_url_if_use_cas_or_shib(request, link_url):
    # Pointing to the URL of the CAS allows to reach the already
    # authenticated form URL like
    # https://pod.univ.fr/sso-cas/login/?next=https%3A%2F%2Fpod.univ
    # .fr%2Fadd_recording%2F%3Fmediapath%3Df18a5104-5a80-47a8-954e
    # -7a142a67a935.zip%26course_title%3DEnregistrement%252021
    # %2520juin%25202019%26recorder%3D1
    host = (
        "https://%s" % request.get_host()
        if (request.is_secure())
        else "http://%s" % request.get_host()
    )
    if not link_url.startswith(("/", host)):
        raise SuspiciousOperation("link url is not internal")
    if USE_CAS:
        return "".join(
            [
                request.build_absolute_uri("/"),
                "sso-cas/login/?next=",
                urllib.parse.quote_plus(link_url),
            ]
        )
    elif USE_SHIB:
        return "".join(
            [
                request.build_absolute_uri(LOGIN_URL),
                "?referrer=",
                urllib.parse.quote_plus(link_url),
            ]
        )
    else:
        return link_url


def recorder_notify(request):

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
                return HttpResponse("nok : key is not valid")

            link_url = "".join(
                [
                    request.build_absolute_uri(reverse("record:add_recording")),
                    "?mediapath=",
                    mediapath,
                    "&course_title=%s" % course_title,
                    "&recorder=%s" % recorder.id,
                ]
            )
            link_url = reformat_url_if_use_cas_or_shib(request, link_url)

            text_msg = _(
                "Hello, \n\na new recording has just be added on the video "
                'website "%(title_site)s" from the recorder "%('
                'recorder)s". '
                "\nTo add it, just click on link below.\n\n%(link_url)s\nif "
                "you cannot click on link, just copy-paste it in your "
                "browser. "
                "\n\nRegards"
            ) % {
                "title_site": TITLE_SITE,
                "recorder": recorder.name,
                "link_url": link_url,
            }

            html_msg = _(
                "Hello, <p>a new recording has just be added on %("
                'title_site)s from the recorder "%(recorder)s". '
                '<br/>To add it, just click on link below.</p><a href="%('
                'link_url)s">%(link_url)s</a><br/><i>if you cannot click on '
                "link, just copy-paste it in your browser.</i> "
                "<p><p>Regards</p>"
            ) % {
                "title_site": TITLE_SITE,
                "recorder": recorder.name,
                "link_url": link_url,
            }
            # Sending the mail to the managers defined in the administration
            # for the concerned recorder
            if recorder.user:
                admin_emails = [recorder.user.email]
            else:
                admin_emails = User.objects.filter(is_superuser=True).values_list(
                    "email", flat=True
                )
            subject = "[" + TITLE_SITE + "] %s" % _("New recording added.")
            # Send the mail to the managers or admins (if not found)
            email_msg = EmailMultiAlternatives(
                subject, text_msg, settings.DEFAULT_FROM_EMAIL, admin_emails
            )

            email_msg.attach_alternative(html_msg, "text/html")
            email_msg.send(fail_silently=False)
            return HttpResponse("ok")
        else:
            return HttpResponse(
                "nok : address_ip not valid or recorder not found in this site"
            )
    else:
        return HttpResponse("nok : recordingPlace or mediapath or key are missing")


@csrf_protect
@login_required(redirect_field_name="referrer")
@staff_member_required(redirect_field_name="referrer")
def claim_record(request):
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

    if request.is_ajax():
        return render(
            request,
            "recorder/record_list.html",
            {"records": records, "full_path": full_path},
        )

    return render(
        request,
        "recorder/claim_record.html",
        {"records": records, "full_path": full_path},
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
@user_passes_test(
    lambda u: u.is_superuser or u.has_perm("recorder.delete_recording"),
    redirect_field_name="referrer",
)
def delete_record(request, id=None):

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
        request, "recorder/record_delete.html", {"record": record, "form": form}
    )


# OPENCAST VIEWS
@login_required(redirect_field_name="referrer")
def studio_pod(request):
    if in_maintenance():
        return redirect(reverse("maintenance"))
    if RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(
            request, "recorder/opencast-studio.html", {"access_not_allowed": True}
        )
    # Render the Opencast studio index file
    opencast_studio_rendered = render_to_string("studio/index.html")
    # head = opencast_studio_rendered[opencast_studio_rendered.index("<head>")
    # + len("<head>"):opencast_studio_rendered.index("</head>")]
    body = opencast_studio_rendered[
        opencast_studio_rendered.index("<body>")
        + len("<body>") : opencast_studio_rendered.index("</body>")
    ]
    return render(
        # Render the Opencast studio index file
        request,
        "recorder/opencast-studio.html",
        {"body": body, "default_presenter": OPENCAST_DEFAULT_PRESENTER},
    )


@csrf_exempt
@login_required(redirect_field_name="referrer")
def presenter_post(request):
    if (
        request.POST
        and request.POST.get("presenter")
        and request.POST.get("presenter") in ["mid", "piph", "pipb"]
    ):
        request.session["presenter"] = request.POST.get("presenter")
        return JsonResponse({"valid": True}, status=200)

    return HttpResponseBadRequest()


@login_required(redirect_field_name="referrer")
def studio_static(request, file):
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


@login_required(redirect_field_name="referrer")
def settings_toml(request):
    # OpenCast Studio configuration
    # See https://github.com/elan-ev/opencast-studio/blob/master/CONFIGURATION.md
    # Add parameter : the pod studio URL
    studio_url = request.build_absolute_uri(
        reverse(
            "recorder:studio_pod",
        )
    )
    myvideo_url = request.build_absolute_uri(
        reverse(
            "video:my_videos",
        )
    )
    # force https for developpement server
    studio_url = studio_url.replace("http://", "https://")
    myvideo_url = myvideo_url.replace("http://", "https://")
    content_text = """
    [opencast]
    serverUrl = "%(serverUrl)s"
    [upload]
    presenterField = 'hidden'
    [return]
    target = "%(target)s"
    label = "%(label)s"
    [theme]
    """
    content_text = content_text % {
        "serverUrl": studio_url,
        "target": myvideo_url,
        "label": "mes videos",
    }
    return HttpResponse(content_text, content_type="text/plain")


@login_required(redirect_field_name="referrer")
def info_me_json(request):
    # Authentication for OpenCast Studio
    return render(request, "studio/me.json", {}, content_type="application/json")


@login_required(redirect_field_name="referrer")
def ingest_createMediaPackage(request):
    # URI createMediaPackage useful for OpenCast Studio
    # Necessary id. Example format : a3d9e9f3-66d0-403b-a775-acb3f79196d4
    idMedia = uuid.uuid4()
    # Necessary start date. Example format : 2021-12-08T08:52:28Z
    start = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%S%zZ")
    mediaPackage_dir = os.path.join(
        settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
    )
    mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
    # create directory to store all the data.
    os.makedirs(mediaPackage_dir, exist_ok=True)

    mediaPackage_content = minidom.parseString(OPENCAST_MEDIAPACKAGE)
    mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
    mediapackage.setAttribute("id", "%s" % idMedia)
    mediapackage.setAttribute("start", start)

    presenter = OPENCAST_DEFAULT_PRESENTER
    if request.session.get("presenter"):
        presenter = request.session["presenter"]
        del request.session["presenter"]
    mediapackage.setAttribute("presenter", presenter)

    with open(mediaPackage_file, "w") as f:
        f.write(mediaPackage_content.toxml())
    return HttpResponse(mediaPackage_content.toxml(), content_type="application/xml")


@login_required(redirect_field_name="referrer")
@csrf_exempt
def ingest_addDCCatalog(request):
    # URI addDCCatalog useful for OpenCast Studio
    # Form management with 3 parameters : mediaPackage, dublinCore, flavor
    # For Pod, management of dublinCore is useless
    if (
        request.POST.get("mediaPackage")
        and request.POST.get("flavor")
        and request.POST.get("dublinCore")
    ):
        typeCatalog = "dublincore/episode"
        # Id catalog. Example format: 798017b1-2c45-42b1-85b0-41ce804fa527
        idCatalog = uuid.uuid4()
        # Id media package
        idMedia = ""
        # dublinCore
        dublinCore = ""
        if (
            request.POST.get("mediaPackage") != ""
            and request.POST.get("mediaPackage") != "{}"
        ):
            mediaPackage = request.POST.get("mediaPackage")
            # XML result to parse
            xmldoc = minidom.parseString(mediaPackage)
            # Get the good id and start date
            idMedia = xmldoc.getElementsByTagName("mediapackage")[0].getAttribute("id")

        if request.POST.get("flavor") and request.POST.get("flavor") != "":
            typeCatalog = request.POST.get("flavor")
        if request.POST.get("dublinCore") and request.POST.get("dublinCore") != "":
            dublinCore = request.POST.get("dublinCore")

        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        # create directory to store the dublincore file.
        os.makedirs(mediaPackage_dir, exist_ok=True)
        # store the dublin core file
        dublinCore_file = os.path.join(mediaPackage_dir, "dublincore.xml")
        with open(dublinCore_file, "w+") as f:
            f.write(unquote(dublinCore))

        mediaPackage_content = minidom.parse(mediaPackage_file)  # parse an open file
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        if mediapackage.getAttribute("id") != idMedia:
            raise PermissionDenied

        dc_url = str(
            "%(http)s://%(host)s%(media)sopencast-files/%(idMedia)s/dublincore.xml"
            % {
                "http": "https" if request.is_secure() else "http",
                "host": request.get_host(),
                "media": MEDIA_URL,
                "idMedia": "%s" % idMedia,
            }
        )
        catalog = mediaPackage_content.createElement("catalog")
        catalog.setAttributeNode(mediaPackage_content.createAttribute("type"))
        catalog.setAttributeNode(mediaPackage_content.createAttribute("id"))
        catalog.setAttribute("id", "%s" % idCatalog)
        catalog.setAttribute("type", typeCatalog)
        mimetype = mediaPackage_content.createElement("mimetype")
        mimetype.appendChild(mediaPackage_content.createTextNode("text/xml"))
        catalog.appendChild(mimetype)
        url = mediaPackage_content.createElement("url")
        url.appendChild(mediaPackage_content.createTextNode(dc_url))
        catalog.appendChild(url)

        metadata = mediaPackage_content.getElementsByTagName("metadata")[0]
        metadata.appendChild(catalog)

        with open(mediaPackage_file, "w+") as f:
            f.write(mediaPackage_content.toxml())

        return HttpResponse(mediaPackage_content.toxml(), content_type="application/xml")

    return HttpResponseBadRequest()


@csrf_exempt
@login_required(redirect_field_name="referrer")
def ingest_addAttachment(request):
    # URI addAttachment useful for OpenCast Studio
    # Form management with 3 parameters : mediaPackage, flavor, BODY (acl.xml file)
    if (
        request.POST.get("mediaPackage")
        and request.POST.get("flavor")
        and request.FILES.get("BODY")
    ):
        idMedia = ""
        typeAttachment = ""
        if (
            request.POST.get("mediaPackage") != ""
            and request.POST.get("mediaPackage") != "{}"
        ):
            mediaPackage = request.POST.get("mediaPackage")
            # XML result to parse
            xmldoc = minidom.parseString(mediaPackage)
            # Get the good id and start date
            idMedia = xmldoc.getElementsByTagName("mediapackage")[0].getAttribute("id")
        if request.POST.get("flavor") and request.POST.get("flavor") != "":
            typeAttachment = request.POST.get("flavor")
        # save the ACLFile ???

        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        mediaPackage_content = minidom.parse(mediaPackage_file)  # parse an open file
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        if mediapackage.getAttribute("id") != idMedia:
            raise PermissionDenied

        attachment = mediaPackage_content.createElement("attachment")
        attachment.setAttributeNode(mediaPackage_content.createAttribute("type"))
        attachment.setAttributeNode(mediaPackage_content.createAttribute("id"))
        attachment.setAttribute("id", "%s" % uuid.uuid4())
        attachment.setAttribute("type", typeAttachment)
        mimetype = mediaPackage_content.createElement("mimetype")
        mimetype.appendChild(mediaPackage_content.createTextNode("text/xml"))
        attachment.appendChild(mimetype)
        url = mediaPackage_content.createElement("url")
        url.appendChild(mediaPackage_content.createTextNode(""))
        attachment.appendChild(url)

        attachments = mediaPackage_content.getElementsByTagName("attachments")[0]
        attachments.appendChild(attachment)

        with open(mediaPackage_file, "w+") as f:
            f.write(mediaPackage_content.toxml())

        return HttpResponse(mediaPackage_content.toxml(), content_type="application/xml")

    return HttpResponseBadRequest()


@csrf_exempt
@login_required(redirect_field_name="referrer")
def ingest_addTrack(request):
    # URI addTrack useful for OpenCast Studio
    # Form management with 4 parameters : mediaPackage, flavor, tags, BODY (video file)
    if (
        request.POST.get("mediaPackage")
        and request.POST.get("flavor")
        # and request.POST.get("tags") # unused tags
        and request.FILES.get("BODY")
    ):
        idMedia = ""
        typeTrack = ""
        # tags = "" # not use actually
        if (
            request.POST.get("mediaPackage") != ""
            and request.POST.get("mediaPackage") != "{}"
        ):
            mediaPackage = request.POST.get("mediaPackage")
            # XML result to parse
            xmldoc = minidom.parseString(mediaPackage)
            # Get the good id and start date
            idMedia = xmldoc.getElementsByTagName("mediapackage")[0].getAttribute("id")
        if request.POST.get("flavor") and request.POST.get("flavor") != "":
            typeTrack = request.POST.get("flavor")
        # if request.POST.get("tags") and request.POST.get("tags") != "":
        #    tags = request.POST.get("tags")

        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        mediaPackage_content = minidom.parse(mediaPackage_file)  # parse an open file
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]

        if mediapackage.getAttribute("id") != idMedia:
            raise PermissionDenied

        opencast_filename, ext = os.path.splitext(request.FILES["BODY"].name)

        dest_filename = "%s%s" % (typeTrack.replace("/", "_").replace(" ", ""), ext)
        # Upload the video file
        opencastMediaFile = os.path.join(mediaPackage_dir, dest_filename)
        with open(opencastMediaFile, "wb+") as destination:
            for chunk in request.FILES["BODY"].chunks():
                destination.write(chunk)

        track = mediaPackage_content.createElement("track")
        track.setAttributeNode(mediaPackage_content.createAttribute("id"))
        track.setAttributeNode(mediaPackage_content.createAttribute("type"))
        track.setAttributeNode(mediaPackage_content.createAttribute("filename"))
        track.setAttribute("id", "%s" % uuid.uuid4())
        track.setAttribute("type", typeTrack)
        track.setAttribute("filename", opencast_filename)
        mimetype = mediaPackage_content.createElement("mimetype")
        mimetype.appendChild(mediaPackage_content.createTextNode("video/webm"))
        track.appendChild(mimetype)
        track_url = "%(http)s://%(host)s%(media)sopencast-files/%(idMedia)s/%(fn)s" % {
            "http": "https" if request.is_secure() else "http",
            "host": request.get_host(),
            "media": MEDIA_URL,
            "idMedia": "%s" % idMedia,
            "fn": dest_filename,
        }
        url = mediaPackage_content.createElement("url")
        url.appendChild(mediaPackage_content.createTextNode(track_url))
        track.appendChild(url)
        live = mediaPackage_content.createElement("live")
        live.appendChild(mediaPackage_content.createTextNode("false"))
        track.appendChild(live)

        media = mediaPackage_content.getElementsByTagName("media")[0]
        media.appendChild(track)

        with open(mediaPackage_file, "w+") as f:
            f.write(mediaPackage_content.toxml())

        return HttpResponse(mediaPackage_content.toxml(), content_type="application/xml")
    return HttpResponseBadRequest()


@csrf_exempt
@login_required(redirect_field_name="referrer")
def ingest_addCatalog(request):
    # URI ingest useful for OpenCast Studio (when cutting video)
    # Form management with 3 parameter : flavor, mediaPackage, BODY(smil file)
    if (
        request.POST.get("mediaPackage")
        and request.POST.get("flavor")
        and request.FILES.get("BODY")
    ):
        idMedia = ""
        typeCatalog = ""
        # tags = "" # not use actually
        if (
            request.POST.get("mediaPackage") != ""
            and request.POST.get("mediaPackage") != "{}"
        ):
            mediaPackage = request.POST.get("mediaPackage")
            # XML result to parse
            xmldoc = minidom.parseString(mediaPackage)
            # Get the good id and start date
            idMedia = xmldoc.getElementsByTagName("mediapackage")[0].getAttribute("id")
        if request.POST.get("flavor") and request.POST.get("flavor") != "":
            typeCatalog = request.POST.get("flavor")

        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        mediaPackage_content = minidom.parse(mediaPackage_file)  # parse an open file
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]

        if mediapackage.getAttribute("id") != idMedia:
            raise PermissionDenied

        opencast_filename = request.FILES["BODY"].name
        # Upload the cutting file
        opencastMediaFile = os.path.join(mediaPackage_dir, opencast_filename)
        with open(opencastMediaFile, "wb+") as destination:
            for chunk in request.FILES["BODY"].chunks():
                destination.write(chunk)

        catalog_url = "%(http)s://%(host)s%(media)sopencast-files/%(idMedia)s/%(fn)s" % {
            "http": "https" if request.is_secure() else "http",
            "host": request.get_host(),
            "media": MEDIA_URL,
            "idMedia": "%s" % idMedia,
            "fn": opencast_filename,
        }
        catalog = mediaPackage_content.createElement("catalog")
        catalog.setAttributeNode(mediaPackage_content.createAttribute("type"))
        catalog.setAttributeNode(mediaPackage_content.createAttribute("id"))
        catalog.setAttribute("id", "%s" % uuid.uuid4())
        catalog.setAttribute("type", typeCatalog)
        mimetype = mediaPackage_content.createElement("mimetype")
        mimetype.appendChild(mediaPackage_content.createTextNode("text/xml"))
        catalog.appendChild(mimetype)
        url = mediaPackage_content.createElement("url")
        url.appendChild(mediaPackage_content.createTextNode(catalog_url))
        catalog.appendChild(url)

        metadata = mediaPackage_content.getElementsByTagName("metadata")[0]
        metadata.appendChild(catalog)
        with open(mediaPackage_file, "w+") as f:
            f.write(mediaPackage_content.toxml())
        return HttpResponse(mediaPackage_content.toxml(), content_type="application/xml")
    return HttpResponseBadRequest()


@csrf_exempt
@login_required(redirect_field_name="referrer")
def ingest_ingest(request):
    # URI ingest useful for OpenCast Studio
    # Form management with 1 parameter : mediaPackage
    # Management of the mediaPackage (XML)
    if (
        request.POST.get("mediaPackage")
        and request.POST.get("mediaPackage") != ""
        and request.POST.get("mediaPackage") != "{}"
    ):
        mediaPackage = request.POST.get("mediaPackage")
        # XML result to parse
        xmldoc = minidom.parseString(mediaPackage)
        idMedia = xmldoc.getElementsByTagName("mediapackage")[0].getAttribute("id")
        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        mediaPackage_content = minidom.parse(mediaPackage_file)  # parse an open file
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]

        if mediapackage.getAttribute("id") != idMedia:
            raise PermissionDenied

        # Create the recording
        # Search for the recorder corresponding to the Studio
        recorder = Recorder.objects.filter(
            recording_type="studio", sites=get_current_site(None)
        ).first()
        if recorder:
            recording = Recording.objects.create(
                user=request.user,
                title=idMedia,
                type="studio",
                # Source file corresponds to Pod XML file
                source_file=mediaPackage_file,
                recorder=recorder,
            )
            recording.save()
        else:
            messages.add_message(
                request, messages.ERROR, _("Recorder for Studio not found.")
            )
            raise PermissionDenied

        return HttpResponse(mediaPackage_content.toxml(), content_type="application/xml")

    return HttpResponseBadRequest()
