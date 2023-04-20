"""Esup-Pod video utilities."""
import os
import re
import shutil
from math import ceil
import time

from django.urls import reverse
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.core.mail import mail_managers
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.sites.shortcuts import get_current_site

from .models import EncodingStep
from .models import EncodingLog
from .models import Video


DEBUG = getattr(settings, "DEBUG", True)

TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/logo_etb.svg",
        "LOGO_PLAYER": "img/pod_favicon.svg",
        "LINK_PLAYER": "",
        "FOOTER_TEXT": ("",),
        "FAVICON": "img/pod_favicon.svg",
        "CSS_OVERRIDE": "",
        "PRE_HEADER_TEMPLATE": "",
        "POST_FOOTER_TEMPLATE": "",
        "TRACKING_TEMPLATE": "",
    },
)

__TITLE_SITE__ = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)

DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")

USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)

MANAGERS = getattr(settings, "MANAGERS", {})

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)


def get_available_videos():
    """Get all videos available."""
    videos = Video.objects.filter(encoding_in_progress=False, is_draft=False).defer(
        "video", "slug", "owner", "additional_owners", "description"
    )
    # for clean install, produces errors
    try:
        videos = videos.exclude(
            pk__in=[vid.id for vid in videos if not vid.encoded]
        ).filter(sites=get_current_site(None))
    except Exception:
        pass
    return videos


# ##########################################################################
# ENCODE VIDEO : GENERIC FUNCTIONS
# ##########################################################################


def change_encoding_step(video_id, num_step, desc):
    """Change encoding step."""
    encoding_step, created = EncodingStep.objects.get_or_create(
        video=Video.objects.get(id=video_id)
    )
    encoding_step.num_step = num_step
    encoding_step.desc_step = desc[:255]
    encoding_step.save()
    if DEBUG:
        print("step: %d - desc: %s" % (num_step, desc))


def add_encoding_log(video_id, log):
    """Add message in video_id encoding log."""
    encoding_log, created = EncodingLog.objects.get_or_create(
        video=Video.objects.get(id=video_id)
    )
    if created:
        encoding_log.log = log
    else:
        encoding_log.log += "\n\n%s" % log
    encoding_log.save()
    if DEBUG:
        print(log)


def check_file(path_file):
    """Check if path_file is accessible and is not null."""
    if os.access(path_file, os.F_OK) and os.stat(path_file).st_size > 0:
        return True
    return False


def create_outputdir(video_id, video_path):
    """ENCODE VIDEO: CREATE OUTPUT DIR."""
    dirname = os.path.dirname(video_path)
    output_dir = os.path.join(dirname, "%04d" % video_id)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


###############################################################
# EMAIL
###############################################################


def send_email(msg, video_id):
    """Send email notification when video encoding failed."""
    subject = "[" + __TITLE_SITE__ + "] Error Encoding Video id:%s" % video_id
    message = "Error Encoding  video id : %s\n%s" % (video_id, msg)
    html_message = "<p>Error Encoding video id : %s</p><p>%s</p>" % (
        video_id,
        msg.replace("\n", "<br/>"),
    )
    mail_admins(subject, message, fail_silently=False, html_message=html_message)


def send_email_recording(msg, recording_id):
    """Send email notification when recording encoding failed."""
    subject = "[" + __TITLE_SITE__ + "] Error Encoding Recording id:%s" % recording_id
    message = "Error Encoding  recording id : %s\n%s" % (recording_id, msg)
    html_message = "<p>Error Encoding recording id : %s</p><p>%s</p>" % (
        recording_id,
        msg.replace("\n", "<br/>"),
    )
    mail_admins(subject, message, fail_silently=False, html_message=html_message)


def send_email_transcript(video_to_encode):
    """Send email on transcripting completion."""
    if DEBUG:
        print("SEND EMAIL ON TRANSCRIPTING COMPLETION")
    url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
    content_url = "%s:%s" % (url_scheme, video_to_encode.get_full_url())
    subject = "[%s] %s" % (
        __TITLE_SITE__,
        _("Transcripting #%(content_id)s completed") % {"content_id": video_to_encode.id},
    )
    message = "%s\n%s\n\n%s\n%s\n%s\n" % (
        _("Hello,"),
        _(
            "The content “%(content_title)s” has been automatically"
            + " transcript, and is now available on %(site_title)s."
        )
        % {"content_title": video_to_encode.title, "site_title": __TITLE_SITE__},
        _("You will find it here:"),
        content_url,
        _("Regards."),
    )
    full_message = message + "\n%s%s\n%s%s" % (
        _("Post by:"),
        video_to_encode.owner,
        _("the:"),
        video_to_encode.date_added,
    )
    from_email = DEFAULT_FROM_EMAIL
    to_email = []
    to_email.append(video_to_encode.owner.email)
    html_message = ""

    html_message = (
        '<p>%s</p><p>%s</p><p>%s<br><a href="%s"><i>%s</i></a>\
                </p><p>%s</p>'
        % (
            _("Hello,"),
            _(
                "The content “%(content_title)s” has been automatically"
                + " transcript, and is now available on %(site_title)s."
            )
            % {
                "content_title": "<b>%s</b>" % video_to_encode.title,
                "site_title": __TITLE_SITE__,
            },
            _("You will find it here:"),
            content_url,
            content_url,
            _("Regards."),
        )
    )
    full_html_message = html_message + "<br/>%s%s<br/>%s%s" % (
        _("Post by:"),
        video_to_encode.owner,
        _("the:"),
        video_to_encode.date_added,
    )

    if (
        USE_ESTABLISHMENT_FIELD
        and MANAGERS
        and video_to_encode.owner.owner.establishment.lower() in dict(MANAGERS)
    ):
        bcc_email = []
        video_estab = video_to_encode.owner.owner.establishment.lower()
        manager = dict(MANAGERS)[video_estab]
        if type(manager) in (list, tuple):
            bcc_email = manager
        elif type(manager) == str:
            bcc_email.append(manager)
        msg = EmailMultiAlternatives(
            subject, message, from_email, to_email, bcc=bcc_email
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
    else:
        mail_managers(
            subject,
            full_message,
            fail_silently=False,
            html_message=full_html_message,
        )
        if not DEBUG:
            send_mail(
                subject,
                message,
                from_email,
                to_email,
                fail_silently=False,
                html_message=html_message,
            )


def send_email_encoding(video_to_encode):
    """Send an email on encoding completion."""
    if DEBUG:
        print("SEND EMAIL ON ENCODING COMPLETION")
    url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
    content_url = "%s:%s" % (url_scheme, video_to_encode.get_full_url())
    subject = "[%s] %s" % (
        __TITLE_SITE__,
        _("Encoding #%(content_id)s completed") % {"content_id": video_to_encode.id},
    )
    message = "%s\n%s\n\n%s\n%s\n%s\n" % (
        _("Hello,"),
        _(
            "The video “%(content_title)s” has been encoded to Web "
            + "formats, and is now available on %(site_title)s."
        )
        % {"content_title": video_to_encode.title, "site_title": __TITLE_SITE__},
        _("You will find it here:"),
        content_url,
        _("Regards."),
    )
    full_message = message + "\n%s%s\n%s%s" % (
        _("Post by:"),
        video_to_encode.owner,
        _("the:"),
        video_to_encode.date_added,
    )
    from_email = DEFAULT_FROM_EMAIL
    to_email = []
    to_email.append(video_to_encode.owner.email)
    html_message = ""

    html_message = (
        '<p>%s</p><p>%s</p><p>%s<br><a href="%s"><i>%s</i></a>\
                </p><p>%s</p>'
        % (
            _("Hello,"),
            _(
                "The video “%(content_title)s” has been encoded to Web "
                + "formats, and is now available on %(site_title)s."
            )
            % {
                "content_title": "<b>%s</b>" % video_to_encode.title,
                "site_title": __TITLE_SITE__,
            },
            _("You will find it here:"),
            content_url,
            content_url,
            _("Regards."),
        )
    )
    full_html_message = html_message + "<br/>%s%s<br/>%s%s" % (
        _("Post by:"),
        video_to_encode.owner,
        _("the:"),
        video_to_encode.date_added,
    )

    if (
        USE_ESTABLISHMENT_FIELD
        and MANAGERS
        and video_to_encode.owner.owner.establishment.lower() in dict(MANAGERS)
    ):
        bcc_email = []
        video_estab = video_to_encode.owner.owner.establishment.lower()
        manager = dict(MANAGERS)[video_estab]
        if type(manager) in (list, tuple):
            bcc_email = manager
        elif type(manager) == str:
            bcc_email.append(manager)
        msg = EmailMultiAlternatives(
            subject, message, from_email, to_email, bcc=bcc_email
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
    else:
        mail_managers(
            subject,
            full_message,
            fail_silently=False,
            html_message=full_html_message,
        )
        if not DEBUG:
            send_mail(
                subject,
                message,
                from_email,
                to_email,
                fail_silently=False,
                html_message=html_message,
            )


def pagination_data(request_path, offset, limit, total_count):
    """Get next, previous url and info about max number of page and current page.

    :param request_path: str: current request path
    :param offset:       int: data offset
    :param limit:        int: data max number
    :param total_count:  int: total data count

    :return: Tuple[str]: next, previous url and current page info
    """
    next_url = previous_url = None
    pages_info = "0/0"
    # manage next previous url (Pagination)
    if offset + limit < total_count and limit <= total_count:
        next_url = "{}?limit={}&offset={}".format(request_path, limit, limit + offset)
    if offset - limit >= 0 and limit <= total_count:
        previous_url = "{}?limit={}&offset={}".format(request_path, limit, offset - limit)

    current_page = 1 if offset <= 0 else int((offset / limit)) + 1
    total = ceil(total_count / limit)
    pages_info = "{}/{}".format(current_page if total > 0 else 0, total)

    return next_url, previous_url, pages_info


def get_headband(channel, theme=None):
    """Get headband with priority to theme headband.

    :param channel: (Channel): channel
    :param theme: (Theme, optional): theme, Defaults to None.

    :return: dict: type(theme, channel) and headband path
    """
    result = {
        "type": "channel" if theme is None else "theme",
        "headband": None,
    }
    if theme is not None and theme.headband is not None:
        result["headband"] = theme.headband.file.url  # pragma: no cover
    elif theme is None and channel.headband is not None:
        result["headband"] = channel.headband.file.url  # pragma: no cover

    return result


def change_owner(video_id, new_owner):
    """Replace current video_id owner by new_owner."""
    if video_id is None:
        return False

    video = Video.objects.filter(pk=video_id).first()
    if video is None:
        return False
    video.owner = new_owner
    video.save()
    move_video_file(video, new_owner)
    return True


def move_video_file(video, new_owner):
    """Move video files in new_owner folder."""
    # overview and encoding video folder name
    encod_folder_pattern = "%04d" % video.id
    old_dest = os.path.join(os.path.dirname(video.video.path), encod_folder_pattern)
    new_dest = re.sub(r"\w{64}", new_owner.owner.hashkey, old_dest)

    # move video files folder contains(overview, format etc...)
    if not os.path.exists(new_dest) and os.path.exists(old_dest):
        new_dest = re.sub(encod_folder_pattern + "/?", "", new_dest)
        if not os.path.exists(new_dest):
            os.makedirs(new_dest)
        shutil.move(old_dest, new_dest)

    # update video overview path
    if bool(video.overview):
        video.overview = re.sub(
            r"\w{64}", new_owner.owner.hashkey, video.overview.__str__()
        )

    # Update video playlist source file
    video_playlist_master = video.get_playlist_master()
    if video_playlist_master is not None:
        video_playlist_master.source_file.name = re.sub(
            r"\w{64}", new_owner.owner.hashkey, video_playlist_master.source_file.name
        )
        video_playlist_master.save()

    # update video path
    video_file_pattern = r"[\w-]+\.\w+"
    old_video_path = video.video.path
    new_video_path = re.sub(r"\w{64}", new_owner.owner.hashkey, old_video_path)
    video.video.name = new_video_path.split("media/")[1]
    if not os.path.exists(new_video_path) and os.path.exists(old_video_path):
        new_video_path = re.sub(video_file_pattern, "", new_video_path)
        shutil.move(old_video_path, new_video_path)
    video.save()


def get_videos(title, user_id, search=None, limit=12, offset=0):
    """Return videos filtered by GET parameters 'title' with limit and offset.

    Args:
        request (Request): Http Request

    Returns:
        list[dict]: videos found
    """
    videos = Video.objects.filter(owner__id=user_id).order_by("id")
    if search is not None:
        title = search

    if title is not None:
        videos = videos.filter(
            Q(title__icontains=title)
            | Q(title_fr__icontains=title)
            | Q(title_en__icontains=title)
        )

    count = videos.count()
    results = list(
        map(
            lambda v: {"id": v.id, "title": v.title, "thumbnail": v.get_thumbnail_url()},
            videos[offset : limit + offset],
        )
    )

    next_url, previous_url, page_infos = pagination_data(
        reverse("video:filter_videos", kwargs={"user_id": user_id}), offset, limit, count
    )

    response = {
        "count": count,
        "next": next_url,
        "previous": previous_url,
        "page_infos": page_infos,
        "results": results,
    }
    return JsonResponse(response, safe=False)


def time_to_seconds(a_time):
    """Convert a time to seconds."""
    seconds = time.strptime(str(a_time), '%H:%M:%S')
    seconds = seconds.tm_sec + seconds.tm_min * 60 + seconds.tm_hour * 3600
    return seconds
