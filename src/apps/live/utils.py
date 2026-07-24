"""
Esup-Pod - Live utilities.

Utility functions for the live module:
- Model defaults for Event dates
- File system checks (port from V4)
- Email notification on event scheduling (port from V4)
"""

import logging
import os
import re
from datetime import datetime
from time import sleep

from django.conf import settings
from django.core.mail import mail_managers, EmailMultiAlternatives
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

# --- Settings ---
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")
SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)
MANAGERS = getattr(settings, "MANAGERS", {})
DEBUG = getattr(settings, "DEBUG", True)
TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings, "TEMPLATE_VISIBLE_SETTINGS", {"TITLE_SITE": "Pod"}
)
EVENT_CHECK_MAX_ATTEMPT = getattr(settings, "EVENT_CHECK_MAX_ATTEMPT", 10)


# ---------------------------------------------------------------------------
# Model defaults
# ---------------------------------------------------------------------------


def current_time():
    """Return the current datetime rounded to the minute."""
    return timezone.now().replace(second=0, microsecond=0)


def one_hour_hence():
    """Return the current datetime + 1 hour, rounded to the minute."""
    return current_time() + timezone.timedelta(hours=1)


# ---------------------------------------------------------------------------
# File system checks (ported from V4)
# ---------------------------------------------------------------------------


def check_size_not_changing(
    resource_path: str, max_attempt: int = EVENT_CHECK_MAX_ATTEMPT
) -> None:
    """
    Check if the size of a resource remains unchanged over a number of attempts.

    Raises:
        Exception: if the file size keeps changing after max_attempt retries.
        OSError: if the resource does not exist or is inaccessible.
    """
    file_size = os.path.getsize(resource_path)
    size_match = False
    attempt_number = 0

    while not size_match and attempt_number <= max_attempt:
        sleep(1)
        new_size = os.path.getsize(resource_path)
        if file_size != new_size:
            logger.warning(
                "File size of %s changing from %s to %s, attempt number %s",
                resource_path,
                file_size,
                new_size,
                attempt_number,
            )
            file_size = new_size
            attempt_number += 1
            if attempt_number == max_attempt:
                logger.error("File: %s is still changing", resource_path)
                raise Exception("checkFileSize aborted")
        else:
            logger.info("Size checked for %s: %s", resource_path, new_size)
            size_match = True


def check_exists(
    resource_path: str, is_dir: bool, max_attempt: int = EVENT_CHECK_MAX_ATTEMPT
) -> None:
    """
    Check whether a file or directory exists, retrying up to max_attempt times.

    Args:
        resource_path: resource path and name.
        is_dir: True for a dir, False for a file.
        max_attempt: number of attempts before raising.
    Raises:
        Exception: if the resource doesn't exist after max_attempt retries.
    """
    fct = os.path.isdir if is_dir else os.path.exists
    r_type = "Dir" if is_dir else "File"
    attempt_number = 1

    while not fct(resource_path) and attempt_number <= max_attempt:
        logger.warning("%s does not exist, attempt number %s", r_type, attempt_number)
        if attempt_number == max_attempt:
            logger.error("Impossible to get %s: %s", r_type, resource_path)
            raise Exception(f"{r_type}: {resource_path} does not exist")
        attempt_number += 1
        sleep(1)


def check_dir_exists(
    dest_dir_name: str, max_attempt: int = EVENT_CHECK_MAX_ATTEMPT
) -> None:
    """Check a directory exists, retrying if needed."""
    return check_exists(dest_dir_name, True, max_attempt)


def check_file_exists(
    full_file_name: str, max_attempt: int = EVENT_CHECK_MAX_ATTEMPT
) -> None:
    """Check a file exists, retrying if needed."""
    return check_exists(full_file_name, False, max_attempt)


# ---------------------------------------------------------------------------
# Date utilities (ported from V4)
# ---------------------------------------------------------------------------


def date_string_to_second(date_string: str) -> int:
    """
    Convert a time string ("hh:mm:ss") to seconds.

    Returns 0 if the format is invalid.
    """
    seconds = 0
    pattern = re.compile(r"^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$")
    if pattern.match(date_string):
        elapsed_time = datetime.strptime(date_string, "%H:%M:%S").time()
        seconds = (
            (elapsed_time.hour * 3600) + (elapsed_time.minute * 60) + elapsed_time.second
        )
    elif DEBUG:
        logger.warning(
            'date_string_to_second: expected format "hh:mm:ss", got: %s', date_string
        )
    return seconds


# ---------------------------------------------------------------------------
# Email notification (ported from V4)
# ---------------------------------------------------------------------------


def get_event_url(event) -> str:
    """Return the full URL of the event, with private hashkey if draft."""
    url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
    url_event = "%s:%s" % (url_scheme, event.get_full_url())
    if event.is_draft:
        url_event += event.get_hashkey() + "/"
    return url_event


def get_bcc(manager) -> list:
    """Return a BCC list from the manager setting."""
    if isinstance(manager, (list, tuple)):
        return list(manager)
    elif isinstance(manager, str):
        return [manager]
    return []


def get_cc(event) -> list:
    """Return the CC list (additional owners' emails)."""
    return [ao.email for ao in event.additional_owners.all()]


def send_email(subject, message, from_email, to_email, cc_email, html_message) -> None:
    """Send an email with HTML alternative."""
    msg = EmailMultiAlternatives(subject, message, from_email, to_email, cc=cc_email)
    msg.attach_alternative(html_message, "text/html")
    if not DEBUG:
        msg.send()


def send_managers(owner, subject, full_message, fail, html_message) -> None:
    """Send an email to managers."""
    full_html_message = html_message + "<br>%s%s" % (_("Post by:"), owner)
    mail_managers(
        subject, full_message, fail_silently=fail, html_message=full_html_message
    )


def send_establishment(
    event, subject, message, from_email, to_email, html_message
) -> None:
    """Send an email to the establishment manager."""
    event_estab = event.owner.owner.establishment.lower()
    manager = dict(MANAGERS)[event_estab]
    bcc_email = get_bcc(manager)
    msg = EmailMultiAlternatives(subject, message, from_email, to_email, bcc=bcc_email)
    msg.attach_alternative(html_message, "text/html")
    msg.send()


def send_email_confirmation(event) -> None:
    """Send a confirmation email when an event is scheduled."""
    if DEBUG:
        logger.debug("SEND EMAIL ON EVENT SCHEDULING")

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
            'You have just scheduled a new event called "%(content_title)s" '
            "from %(start_date)s to %(end_date)s "
            "on video server: %(url_event)s). "
            "You can find the other sharing options in the dedicated tab."
        )
        % {
            "content_title": event.title,
            "start_date": event.start_date,
            "end_date": event.end_date,
            "url_event": url_event,
        },
        _("Regards."),
    )

    import bleach

    message = bleach.clean(html_message, tags=[], strip=True)
    full_message = message + "\n%s%s" % (_("Post by:"), event.owner)

    if (
        USE_ESTABLISHMENT_FIELD
        and MANAGERS
        and hasattr(event.owner, "owner")
        and hasattr(event.owner.owner, "establishment")
        and event.owner.owner.establishment.lower() in dict(MANAGERS)
    ):
        send_establishment(event, subject, message, from_email, to_email, html_message)
        return

    send_managers(event.owner, subject, full_message, False, html_message)
    cc_email = get_cc(event)
    send_email(subject, message, from_email, to_email, cc_email, html_message)
