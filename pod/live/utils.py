import bleach
import json
import logging
import os.path

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMultiAlternatives, mail_managers
from time import sleep
from django.contrib import messages
from django.core.exceptions import PermissionDenied

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)

TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/esup-pod.svg",
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

DEBUG = getattr(settings, "DEBUG", True)

logger = logging.getLogger("pod.live")


def send_email_confirmation(event):
    """Send an email on creation/modification event."""
    if DEBUG:
        print("SEND EMAIL ON EVENT SCHEDULING")

    url_event = get_event_url(event)

    subject = "[%s] %s" % (
        __TITLE_SITE__,
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
    if type(manager) in (list, tuple):
        return manager
    elif type(manager) == str:
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
    full_html_message = html_message + "<br/>%s%s" % (
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


def get_event_id_and_broadcaster_id(request):
    """
    Extracts the event ID and broadcaster ID from the given HTTP request.
    Args:
        request: An HTTP request object.
    Returns:
        A tuple containing the event ID
        and broadcaster ID extracted from the request body.
    """
    body_unicode = request.body.decode("utf-8")
    body_data = json.loads(body_unicode)
    event_id = body_data.get("idevent", None)
    broadcaster_id = body_data.get("idbroadcaster", None)
    return event_id, broadcaster_id


def check_exists(resource_name, is_dir, max_attempt=6):
    """ Checks whether a file or directory exists."""
    fct = os.path.isdir if is_dir else os.path.exists
    type = "Dir" if is_dir else "File"
    attempt_number = 1
    while not fct(resource_name) and attempt_number <= max_attempt:
        logger.warning(f"{type} does not exists, attempt number {attempt_number} ")

        if attempt_number == max_attempt:
            logger.error(f"Impossible to get {type}: {resource_name}")
            raise Exception(
                f"{type}: {resource_name} does not exists")

        attempt_number = attempt_number + 1
        sleep(1)


def check_permission(request):
    """Checks whether the current user has permission to view a page.
    Args:
        request: An HTTP request object.
    Raises:
        PermissionDenied: If the user is not a superuser
        and does not have the 'live.acces_live_pages' permission.
    """
    if not (request.user.is_superuser or request.user.has_perm("live.acces_live_pages")):
        messages.add_message(request, messages.ERROR, _("You cannot view this page."))
        raise PermissionDenied
