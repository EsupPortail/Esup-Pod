import json
import logging
import os
import os.path
import re
from datetime import datetime
from time import sleep

import bleach
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives, mail_managers
from django.utils.translation import ugettext_lazy as _

from pod.main.views import TEMPLATE_VISIBLE_SETTINGS

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)

DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")

USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)

MANAGERS = getattr(settings, "MANAGERS", {})

DEBUG = getattr(settings, "DEBUG", True)

EVENT_CHECK_MAX_ATTEMPT = getattr(settings, "EVENT_CHECK_MAX_ATTEMPT", 10)

logger = logging.getLogger(__name__)


def send_email_confirmation(event):
    """Send an email on creation/modification event."""
    if DEBUG:
        print("SEND EMAIL ON EVENT SCHEDULING")

    url_event = get_event_url(event)

    subject = "[%s] %s" % (
        TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"),
        _("Registration of event #%(content_id)s") % {"content_id": event.id},
    )

    from_email = DEFAULT_FROM_EMAIL

    to_email = [event.owner.email]

    html_message = "<p>%s</p><p>%s</p><p>%s</p>" % (
        _("Hello,"),
        _(
            "You have just scheduled a new event called “%(content_title)s” "
            + "from %(start_date)s to %(end_date)s "
            + "on video server: %(url_event)s)."
            + " You can find the other sharing options in the dedicated tab."
        )
        % {
            "content_title": event.title,
            "start_date": event.start_date,
            "end_date": event.end_date,
            "url_event": url_event,
        },
        _("Regards."),
    )

    message = bleach.clean(html_message, tags=[], strip=True)
    full_message = message + "\n%s%s" % (
        _("Post by:"),
        event.owner,
    )

    # email establishment
    if (
        USE_ESTABLISHMENT_FIELD
        and MANAGERS
        and event.owner.owner.establishment.lower() in dict(MANAGERS)
    ):
        send_establishment(event, subject, message, from_email, to_email, html_message)
        return

    # email to managers
    send_managers(event.owner, subject, full_message, False, html_message)

    # send email
    cc_email = get_cc(event)
    send_email(subject, message, from_email, to_email, cc_email, html_message)


def get_event_url(event):
    url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
    url_event = "%s:%s" % (url_scheme, event.get_full_url())

    if event.is_draft:
        url_event += event.get_hashkey() + "/"
    return url_event


def get_bcc(manager):
    if isinstance(manager, (list, tuple)):
        return manager
    elif isinstance(manager, str):
        return [manager]
    return []


def get_cc(event):
    to_cc = []
    for additional_owners in event.additional_owners.all():
        to_cc.append(additional_owners.email)
    return to_cc


def send_establishment(event, subject, message, from_email, to_email, html_message):
    event_estab = event.owner.owner.establishment.lower()
    manager = dict(MANAGERS)[event_estab]
    bcc_email = get_bcc(manager)
    msg = EmailMultiAlternatives(subject, message, from_email, to_email, bcc=bcc_email)
    msg.attach_alternative(html_message, "text/html")
    msg.send()


def send_managers(owner, subject, full_message, fail, html_message):
    full_html_message = html_message + "<br>%s%s" % (
        _("Post by:"),
        owner,
    )
    mail_managers(
        subject,
        full_message,
        fail_silently=fail,
        html_message=full_html_message,
    )


def send_email(subject, message, from_email, to_email, cc_email, html_message):
    msg = EmailMultiAlternatives(
        subject,
        message,
        from_email,
        to_email,
        cc=cc_email,
    )

    msg.attach_alternative(html_message, "text/html")

    if not DEBUG:
        msg.send()


def date_string_to_second(date_string):
    """
    Calcul the number of seconds from a date string.
    Args:
        date_string: the format must be like "hh:mm:ss".
    Returns:
        number of seconds of 0 if format error.
    """
    seconds = 0
    pattern = re.compile(r"^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$")
    if pattern.match(date_string):
        elapsed_time = datetime.strptime(date_string, "%H:%M:%S").time()
        seconds = (
            (elapsed_time.hour * 3600) + (elapsed_time.minute * 60) + elapsed_time.second
        )
    elif DEBUG:
        print('Error date_string_to_second: Excepted format: "hh:mm:ss"')
    return seconds


def get_event_id_and_broadcaster_id(request):
    """
    Extracts the event ID and broadcaster ID from the given HTTP request.
    Args:
        request: An HTTP request object.
    Returns:
        A tuple containing the event ID
        and broadcaster ID extracted from the request body.
    """
    event_id = broadcaster_id = None
    body_unicode = request.body.decode("utf-8")
    if request.method == "GET":
        event_id = request.GET.get("idevent", None)
        broadcaster_id = request.GET.get("idbroadcaster", None)

    if request.method == "POST":
        body_data = json.loads(body_unicode)
        event_id = body_data.get("idevent", None)
        broadcaster_id = body_data.get("idbroadcaster", None)

    return event_id, broadcaster_id


def check_size_not_changing(resource_path, max_attempt=EVENT_CHECK_MAX_ATTEMPT):
    """
    Checks  if the size of a resource remains unchanged over a specified number of attempts.
    Args:
        resource_path: resource path and name.
        max_attempt: number of attempt before aborting if the resource size still changes.
    Raises:
        Exception: if the number of attempt if reached.
        OSError: if resource does not exist or is inaccessible.
    """
    file_size = os.path.getsize(resource_path)
    size_match = False

    attempt_number = 0
    while not size_match and attempt_number <= max_attempt:
        sleep(1)
        new_size = os.path.getsize(resource_path)
        if file_size != new_size:
            logger.warning(
                f"File size of {resource_path} changing from "
                f"{file_size} to {new_size}, attempt number {attempt_number} "
            )
            file_size = new_size
            attempt_number += 1
            if attempt_number == max_attempt:
                logger.error(f"File: {resource_path} is still changing")
                raise Exception("checkFileSize aborted")
        else:
            logger.info(f"Size checked for {resource_path}: {new_size}")
            size_match = True


def check_exists(resource_path, is_dir, max_attempt=EVENT_CHECK_MAX_ATTEMPT):
    """
    Checks whether a file or directory exists.
    Args:
        resource_path: resource path and name.
        is_dir(bool): True for a dir, False for a file .
        max_attempt: number of attempt.
    Raises:
        Exception: if the number of attempt if reached.
    """
    fct = os.path.isdir if is_dir else os.path.exists
    r_type = "Dir" if is_dir else "File"
    attempt_number = 1
    while not fct(resource_path) and attempt_number <= max_attempt:
        logger.warning(f"{r_type} does not exists, attempt number {attempt_number} ")

        if attempt_number == max_attempt:
            logger.error(f"Impossible to get {r_type}: {resource_path}")
            raise Exception(f"{r_type}: {resource_path} does not exists")

        attempt_number = attempt_number + 1
        sleep(1)


def check_permission(request):
    """
    Checks whether the current user has permission to view a page.
    Args:
        request: An HTTP request object.
    Raises:
        PermissionDenied: If the user is not a superuser
        and does not have the 'live.acces_live_pages' permission.
    """
    if not (request.user.is_superuser or request.user.has_perm("live.acces_live_pages")):
        messages.add_message(request, messages.ERROR, _("You cannot view this page."))
        raise PermissionDenied
