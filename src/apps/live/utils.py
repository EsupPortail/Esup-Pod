"""
Esup-Pod - Live utilities.

Utility functions for the live module:
- Model defaults for Event dates
- Email notification on event scheduling (port from V4)

File system check utilities (check_size_not_changing, check_exists,
check_dir_exists, check_file_exists) have been moved to src.apps.utils.files
and are re-exported here for backward compatibility.
"""

import logging
import re
from datetime import datetime

from django.conf import settings
from django.core.mail import mail_managers, EmailMultiAlternatives
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.apps.utils.files import (
    check_size_not_changing,
    check_exists,
    check_dir_exists,
    check_file_exists,
)

__all__ = [
    "check_size_not_changing",
    "check_exists",
    "check_dir_exists",
    "check_file_exists",
]

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

# Note: EVENT_CHECK_MAX_ATTEMPT is kept for settings consistency; the actual
# file-check functions now live in src.apps.utils.files.


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
