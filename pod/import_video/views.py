"""Views of the Import_video module."""
import os
import requests

# For PeerTube download
import json

from .models import ExternalRecording
from .forms import ExternalRecordingForm
from .utils import StatelessRecording, check_file_exists, download_video_file
from .utils import manage_recording_url, parse_remote_file
from .utils import save_video, secure_request_for_upload
from .utils import check_video_size, verify_video_exists_and_size
from datetime import datetime
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie
from pod.main.views import in_maintenance
from pod.main.utils import secure_post_request, display_message_with_icon

# For Youtube download
from pytube import YouTube
from pytube.exceptions import PytubeError, VideoUnavailable


RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY = getattr(
    settings, "RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY", True
)

DEFAULT_TYPE_ID = getattr(settings, "DEFAULT_TYPE_ID", 1)

VIDEO_ALLOWED_EXTENSIONS = getattr(
    settings,
    "VIDEO_ALLOWED_EXTENSIONS",
    (
        "3gp",
        "avi",
        "divx",
        "flv",
        "m2p",
        "m4v",
        "mkv",
        "mov",
        "mp4",
        "mpeg",
        "mpg",
        "mts",
        "wmv",
        "mp3",
        "ogg",
        "wav",
        "wma",
        "webm",
        "ts",
    ),
)


def secure_external_recording(request, recording):
    """Secure an external recording.

    Args:
        request (Request): HTTP request
        recording (ExternalRecording): ExternalRecording instance

    Raises:
        PermissionDenied: if user not allowed
    """
    if (
        recording
        and request.user != recording.owner
        and not (
            request.user.is_superuser
            or request.user.has_perm("import_video:view_recording")
        )
    ):
        display_message_with_icon(
            request, messages.ERROR, _("You cannot view this recording.")
        )
        raise PermissionDenied


def get_can_delete_external_recording(request, owner):
    """Return True if current user can delete this recording."""
    can_delete = False

    # Only owner can delete this external recording
    if (
        request.user == owner
        or (request.user.is_superuser)
        or (request.user.has_perm("import_video:delete_external_recording"))
    ):
        can_delete = True
    return can_delete


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def upload_external_recording_to_pod(request, record_id):
    """Upload external recording to Pod.

    Args:
        request (Request): HTTP request
        recording_id (Integer): record id (in database)

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTP Response: Redirect to the external recordings list
    """
    recording = get_object_or_404(
        ExternalRecording, id=record_id, site=get_current_site(request)
    )

    # Secure this external recording
    secure_external_recording(request, recording)

    # Only POST request
    secure_post_request(request)

    msg = ""
    upload = False
    try:
        upload = upload_recording_to_pod(request, record_id)
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        if args.get("error"):
            msg += "<strong>%s</strong><br>" % (args["error"])
        if args.get("message"):
            msg += args["message"]
        if args.get("proposition"):
            msg += "<br><span class='proposition'>%s</span>" % (args["proposition"])
    if upload and msg == "":
        msg += _(
            "The recording has been uploaded to Pod. "
            "You can see the generated video in My videos."
        )
        display_message_with_icon(request, messages.INFO, msg)
    else:
        display_message_with_icon(request, messages.ERROR, msg)
    return redirect(reverse("import_video:external_recordings", args=()))


@login_required(redirect_field_name="referrer")
def external_recordings(request):
    """List external recordings.

    Args:
        request (Request): HTTP Request

    Returns:
        HTTPResponse: external recordings list
    """
    if RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(request, "import_video/list.html", {"access_not_allowed": True})

    site = get_current_site(request)

    # List of the external recordings from the database
    external_recordings = ExternalRecording.objects.filter(
        owner__id=request.user.id, site=site
    )
    # | request.user.owners_external_recordings.all().filter(site=site)
    external_recordings = external_recordings.order_by("-id").distinct()

    recordings = []
    for data in external_recordings:
        recording = get_stateless_recording(request, data)

        recordings.append(recording)

    return render(
        request,
        "import_video/list.html",
        {
            "recordings": recordings,
            "page_title": _("My external videos"),
        },
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def add_or_edit_external_recording(request, id=None):
    """Add or edit an external recording.

    Args:
        request (Request): HTTP request
        id (Integer, optional): external recording id. Defaults to None (for creation).

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTPResponse: edition page
    """
    if in_maintenance():
        return redirect(reverse("maintenance"))

    recording = (
        get_object_or_404(ExternalRecording, id=id, site=get_current_site(request))
        if id
        else None
    )

    # Secure external recording
    secure_external_recording(request, recording)

    if RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(
            request,
            "import_video/add_or_edit.html",
            {"access_not_allowed": True},
        )

    default_owner = recording.owner.pk if recording else request.user.pk
    form = ExternalRecordingForm(
        instance=recording,
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser,
        current_user=request.user,
        initial={"owner": default_owner, "id": id},
    )

    if request.method == "POST":
        form = ExternalRecordingForm(
            request.POST,
            instance=recording,
            is_staff=request.user.is_staff,
            is_superuser=request.user.is_superuser,
            current_user=request.user,
            current_lang=request.LANGUAGE_CODE,
        )
        if form.is_valid():
            recording = save_recording_form(request, form)
            display_message_with_icon(
                request, messages.INFO, _("The changes have been saved.")
            )
            return redirect(reverse("import_video:external_recordings"))
        else:
            display_message_with_icon(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    page_title = (
        "%s <b>%s</b>" % (_("Edit the external video"), recording.name)
        if recording
        else _("Create an external video")
    )
    return render(
        request,
        "import_video/add_or_edit.html",
        {"form": form, "page_title": mark_safe(page_title)},
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def delete_external_recording(request, id):
    """Delete an external recording.

    Args:
        request (Request): HTTP request
        id (Integer): record id (in database)

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTP Response: Redirect to the recordings list
    """
    recording = get_object_or_404(
        ExternalRecording, id=id, site=get_current_site(request)
    )

    # Secure external recording
    secure_external_recording(request, recording)

    # Only POST request
    secure_post_request(request)

    msg = ""
    delete = False
    try:
        delete = recording.delete()
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        if args["error"]:
            msg += "<strong>%s</strong><br>" % (args["error"])
        if args["message"]:
            msg += args["message"]
    if delete and msg == "":
        msg += _("The external recording has been deleted.")
        display_message_with_icon(request, messages.INFO, msg)
    else:
        display_message_with_icon(request, messages.ERROR, msg)
    return redirect(reverse("import_video:external_recordings", args=()))


def save_recording_form(request, form):
    """Save an external recording.

    Args:
        request (Request): HTTP request
        form (Form): recording form

    Returns:
        ExternalRecording: recording saved in database
    """
    recording = form.save(commit=False)
    recording.site = get_current_site(request)
    if (
        (request.user.is_superuser or request.user.has_perm("import_video:add_recording"))
        and request.POST.get("owner")
        and request.POST.get("owner") != ""
    ):
        recording.owner = form.cleaned_data["owner"]
    elif getattr(recording, "owner", None) is None:
        recording.owner = request.user

    recording.save()
    form.save_m2m()
    return recording


# ##############################    Upload recordings to Pod
def save_external_recording(request, record_id):
    """Save an external recording in database.

    Args:
        request (Request): HTTP request
        record_id (Integer): id of the recording in database

    Raises:
        ValueError: if impossible creation
    """
    try:
        # Update the external recording
        recording, created = ExternalRecording.objects.update_or_create(
            id=record_id,
            defaults={"uploaded_to_pod_by": request.user},
        )
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to create the external recording")
        msg["message"] = str(exc)
        raise ValueError(msg)


def upload_recording_to_pod(request, record_id):
    """Upload recording to Pod (main function).

    Args:
        request (Request): HTTP request
        record_id (Integer): id record in the database

    Raises:
        ValueError: exception raised if no URL found or other problem

    Returns:
        Boolean: True if upload achieved
    """
    try:
        # Management by type of recording
        recording = ExternalRecording.objects.get(id=record_id)

        # Check that request is correct for upload
        secure_request_for_upload(request)

        # Manage differents source types
        if recording.type == "youtube":
            return upload_youtube_recording_to_pod(request, record_id)
        elif recording.type == "peertube":
            return upload_peertube_recording_to_pod(request, record_id)
        else:
            return upload_bbb_recording_to_pod(request, record_id)
    except Exception as exc:
        msg = {}
        proposition = ""
        msg["error"] = _("Impossible to upload to Pod the video")
        try:
            # Management of error messages from sub-functions
            message = "%s (%s)" % (exc.args[0]["error"], exc.args[0]["message"])
            proposition = exc.args[0].get("proposition")
        except Exception:
            # Management of error messages in all cases
            message = str(exc)

        msg["message"] = mark_safe(message)
        msg["proposition"] = proposition
        raise ValueError(msg)


def upload_bbb_recording_to_pod(request, record_id):
    """Upload a BBB or video file recording to Pod.

    Args:
        request (Request): HTTP request
        record_id (Integer): id record in the database

    Raises:
        ValueError: exception raised if no video found at this URL

    Returns:
        Boolean: True if upload achieved
    """
    try:
        recording = ExternalRecording.objects.get(id=record_id)
        source_url = request.POST.get("source_url")

        # Step 1: Download and parse the remote HTML file if necessary
        # Check if extension is a video extension
        extension = source_url.split(".")[-1].lower()
        if extension in VIDEO_ALLOWED_EXTENSIONS:
            # URL corresponds to a video file
            source_video_url = source_url
        else:
            # Download and parse the remote HTML file
            video_file = parse_remote_file(source_url)
            source_video_url = source_url + video_file

        # Verify that video exists and not oversised
        verify_video_exists_and_size(source_video_url)

        # Step 2: Define destination source file
        extension = source_video_url.split(".")[-1].lower()
        discrim = datetime.now().strftime("%Y%m%d%H%M%S")
        dest_file = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            request.user.owner.hashkey,
            os.path.basename("%s-%s.%s" % (discrim, recording.id, extension)),
        )

        os.makedirs(os.path.dirname(dest_file), exist_ok=True)

        # Step 3: Download the video file
        download_video_file(source_video_url, dest_file)

        # Step 4: Save informations about the recording
        recording_title = request.POST.get("recording_name")
        save_external_recording(request, record_id)

        # Step 5: Save and encode Pod video
        description = _(
            "This video was uploaded to Pod; its origin is %(type)s: "
            '<a href="%(url)s" target="_blank">%(url)s</a>'
        ) % {"type": recording.get_type_display(), "url": source_video_url}

        save_video(request, dest_file, recording_title, description)

        return True
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to upload to Pod the video")
        try:
            # Management of error messages from sub-functions
            message = "%s %s" % (exc.args[0]["error"], exc.args[0]["message"])
        except Exception:
            # Management of error messages in all cases
            message = str(exc)

        msg["message"] = mark_safe(message)
        msg["proposition"] = _(
            "Try changing the record type or address for this recording."
        )
        raise ValueError(msg)


def upload_youtube_recording_to_pod(request, record_id):
    """Upload Youtube recording to Pod.

    Use PyTube with its API
    More information: https://pytube.io/en/latest/api.html
    Args:
        request (Request): HTTP request
        record_id (Integer): id record in the database

    Raises:
        ValueError: exception raised if no YouTube video found or content inaccessible

    Returns:
        Boolean: True if upload achieved
    """
    try:
        # Manage source URL from video playback
        source_url = request.POST.get("source_url")

        # Use pytube to download Youtube file
        yt_video = YouTube(
            source_url,
            # on_complete_callback=complete_func,
            # use_oauth=True,
            # allow_oauth_cache=True
        )
        # Publish date (format: 2023-05-13 00:00:00)
        # Event date (format: 2023-05-13)
        date_evt = str(yt_video.publish_date)[0:10]

        # Setting video resolution
        yt_stream = yt_video.streams.get_highest_resolution()

        # Verify that video not oversized
        check_video_size(yt_stream.filesize)

        # User directory
        dest_dir = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            request.user.owner.hashkey,
        )
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)

        discrim = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = "%s-%s" % (discrim, get_valid_filename(yt_stream.default_filename))
        # Video file path
        dest_file = os.path.join(
            dest_dir,
            filename,
        )

        # Download video
        yt_stream.download(dest_dir, filename=filename)

        # Step 4: Save informations about the recording
        save_external_recording(request, record_id)

        # Step 5: Save and encode Pod video
        description = _(
            "This video '%(name)s' was uploaded to Pod; "
            'its origin is Youtube: <a href="%(url)s" target="_blank">%(url)s</a>'
        ) % {"name": yt_video.title, "url": source_url}
        recording_title = request.POST.get("recording_name")
        save_video(request, dest_file, recording_title, description, date_evt)
        return True

    except VideoUnavailable:
        msg = {}
        msg["error"] = _("YouTube error")
        msg["message"] = _(
            "YouTube content is unavailable. "
            "This content does not appear to be publicly available."
        )
        msg["proposition"] = _(
            "Try changing the access rights to the video directly in Youtube."
        )
        raise ValueError(msg)
    except PytubeError as pterror:
        msg = {}
        msg["error"] = _("YouTube error '%s'" % (mark_safe(pterror)))
        msg["message"] = _(
            "YouTube content is inaccessible. "
            "This content does not appear to be publicly available."
        )
        msg["proposition"] = _("Try changing the address of this recording.")
        raise ValueError(msg)
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to upload to Pod the video")
        try:
            # Management of error messages from sub-functions
            message = "%s %s" % (exc.args[0]["error"], exc.args[0]["message"])
        except Exception:
            # Management of error messages in all cases
            message = str(exc)

        msg["message"] = mark_safe(message)
        msg["proposition"] = _(
            "Try changing the record type or address for this recording."
        )
        raise ValueError(msg)


def upload_peertube_recording_to_pod(request, record_id):  # noqa: C901
    """Upload Peertube recording to Pod.

    More information: https://docs.joinpeertube.org/api/rest-getting-started
    Args:
        request (Request): HTTP request
        record_id (Integer): id record in the database

    Raises:
        ValueError: exception raised if no PeerTube video found in this URL

    Returns:
        Boolean: True if upload achieved
    """
    try:
        # Manage source URL from video playback
        source_url = request.POST.get("source_url")

        # Check if extension is a video extension
        extension = source_url.split(".")[-1].lower()
        if extension in VIDEO_ALLOWED_EXTENSIONS:
            # URL corresponds to a video file. Format example:
            #  - https://xxxx.fr/download/videos/id-quality.mp4
            # with: id = id/uuid/shortUUID, quality=480/720/1080
            source_video_url = source_url
            # PeerTube API for this video:
            # https://xxxx.fr/api/v1/videos/id
            pos_pt = source_url.rfind("-")
            if pos_pt != -1:
                url_api_video = source_url[0:pos_pt].replace(
                    "/download/videos/", "/api/v1/videos/"
                )
            else:
                msg = {}
                msg["error"] = _("PeerTube error")
                msg["message"] = _(
                    "The address entered does not appear to be a valid PeerTube address."
                )
                msg["proposition"] = _("Try changing the address of the recording.")
                raise ValueError(msg)
        else:
            # URL corresponds to a PeerTube URL. Format example:
            #  - https://xxx.fr/w/id
            #  - https://xxx.fr/videos/watch/id
            # with: id = id/uuid/shortUUID
            # PeerTube API for this video:
            # https://xxxx.fr/api/v1/videos/id
            url_api_video = source_url.replace("/w/", "/api/v1/videos/")
            url_api_video = url_api_video.replace("/videos/watch/", "/api/v1/videos/")

        with requests.get(url_api_video, timeout=(10, 180), stream=True) as response:
            if response.status_code != 200:
                msg = {}
                msg["error"] = _("PeerTube error")
                msg["message"] = _(
                    "The address entered does not appear to be a valid PeerTube address "
                    "or the PeerTube server is not responding as expected."
                )
                msg["proposition"] = _(
                    "Try changing the address of the recording or retry later."
                )
                raise ValueError(msg)
            else:
                pt_video_json = json.loads(response.content.decode("utf-8"))
                # URL
                pt_video_url = pt_video_json["url"]
                # UUID, useful for the filename
                pt_video_uuid = pt_video_json["uuid"]
                pt_video_name = pt_video_json["name"]
                pt_video_description = pt_video_json["description"]
                if pt_video_description is None:
                    pt_video_description = ""
                else:
                    pt_video_description = pt_video_description.replace("\r\n", "<br>")
                # Creation date (format: 2023-05-23T08:16:34.690Z)
                pt_video_created_at = pt_video_json["createdAt"]
                # Evant date (format: 2023-05-23)
                date_evt = pt_video_created_at[0:10]
                # Source video file
                source_video_url = pt_video_json["files"][0]["fileDownloadUrl"]

        # Verify that video exists and not oversized
        verify_video_exists_and_size(source_video_url)

        # Step 2: Define destination source file
        discrim = datetime.now().strftime("%Y%m%d%H%M%S")
        extension = source_video_url.split(".")[-1].lower()
        dest_file = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            request.user.owner.hashkey,
            os.path.basename("%s-%s.%s" % (discrim, pt_video_uuid, extension)),
        )
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)

        # Step 3: Download the video file
        download_video_file(source_video_url, dest_file)

        # Step 4: Save informations about the recording
        recording_title = request.POST.get("recording_name")
        save_external_recording(request, record_id)

        # Step 5: Save and encode Pod video
        description = _(
            "This video '%(name)s' was uploaded to Pod; its origin is PeerTube: "
            "<a href='%(url)s' target='blank'>%(url)s</a>."
        ) % {"name": pt_video_name, "url": pt_video_url}
        description = ("%s<br>%s") % (description, pt_video_description)
        save_video(request, dest_file, recording_title, description, date_evt)

        return True
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to upload to Pod the PeerTube video")
        try:
            # Management of error messages from sub-functions
            message = "%s %s" % (exc.args[0]["error"], exc.args[0]["message"])
        except Exception:
            # Management of error messages in all cases
            message = str(exc)

        msg["message"] = mark_safe(message)
        msg["proposition"] = _(
            "Try changing the record type or address for this recording."
        )
        raise ValueError(msg)


def get_stateless_recording(request, data):
    """Return a stateless recording from an external recording.

    Args:
        request (Request): HTTP request
        data (ExternalRecording): external recording

    Returns:
        StatelessRecording: stateless recording
    """
    recording = StatelessRecording(data.id, data.name, "published")
    # By default, upload to Pod is possible
    recording.canUpload = True
    # Only owner can delete this external recording
    recording.canDelete = get_can_delete_external_recording(request, data.owner)

    recording.startTime = data.start_at

    recording.uploadedToPodBy = data.uploaded_to_pod_by

    # State management
    if recording.uploadedToPodBy is None:
        recording.state = _("Video file not uploaded to Pod")
    else:
        recording.state = _("Video file already uploaded to Pod")

    # Management of the external recording type
    if data.type == "bigbluebutton":
        # Manage BBB recording URL, if necessary
        video_url = manage_recording_url(data.source_url)
        # For BBB, external URL can be the video or presentation playback
        if video_url.find("playback/video") != -1:
            # Management for standards video URLs with BBB or Scalelite server
            recording.videoUrl = video_url
        elif video_url.find("playback/presentation/2.3") != -1:
            # Management for standards presentation URLs with BBB or Scalelite server
            # Add computed video playback
            recording.videoUrl = video_url.replace(
                "playback/presentation/2.3", "playback/video"
            )
            recording.presentationUrl = video_url
        else:
            # Management of other situations, non standards URLs
            recording.videoUrl = video_url

        # For old BBB or BBB 2.6+ without video playback
        if check_file_exists(recording.videoUrl) is False:
            recording.state = _(
                "No video file found. Upload to Pod as a video is not possible."
            )
            recording.canUpload = False
            recording.videoUrl = ""
    else:
        # For PeerTube, Video file, Youtube
        recording.videoUrl = data.source_url

    # Display type label
    recording.type = data.get_type_display

    return recording
