"""Util functions and classes for ai_enhancement module."""

import json
import bleach
import requests
import logging
from django.conf import settings
from requests import Response
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from pod.ai_enhancement.models import AIEnhancement
from pod.main.utils import extract_json_from_str
from pod.video.models import Discipline, Video
from webpush.models import PushInformation
from django.core.mail import send_mail
from django.core.mail import mail_managers
from django.core.mail import EmailMultiAlternatives

DEBUG = getattr(settings, "DEBUG", True)
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")

USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)

MANAGERS = getattr(settings, "MANAGERS", {})

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)

AI_ENHANCEMENT_API_URL = getattr(settings, "AI_ENHANCEMENT_API_URL", "")
AI_ENHANCEMENT_API_VERSION = getattr(settings, "AI_ENHANCEMENT_API_VERSION", "")
USE_NOTIFICATIONS = getattr(settings, "USE_NOTIFICATIONS", False)
EMAIL_ON_ENHANCEMENT_COMPLETION = getattr(
    settings, "EMAIL_ON_ENHANCEMENT_COMPLETION", True
)
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
        "LINK_PLAYER_NAME": _("Home"),
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

logger = logging.getLogger(__name__)


class AristoteAI:
    """Aristote AI Enhancement utilities."""

    def __init__(self, client_id, client_secret) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def get_token(self):
        """Get the token."""
        if self.token is None:
            self.connect_to_api()
        return self.token

    def connect_to_api(self) -> Response or None:
        """Connect to the API."""
        path = "/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            response = requests.post(
                AI_ENHANCEMENT_API_URL + path,
                data=json.dumps(data),
                headers=headers,
            )
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                return response.json()
            else:
                logger.error(f"Error: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {e}")
            return None

    def get_response(self, path: str) -> dict or None:
        """
        Get the AI response.

        Args:
            path (str): The path to the API endpoint.
        """
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.get_token()}",
        }
        try:
            response = requests.get(
                AI_ENHANCEMENT_API_URL + path,
                headers=headers,
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {e}")
            return None

    def get_ai_enhancements(self) -> dict or None:
        """Get the AI enhancements."""
        path = f"/{AI_ENHANCEMENT_API_VERSION}/enrichments"
        return self.get_response(path)

    def get_specific_ai_enhancement(self, enhancement_id: str) -> dict or None:
        """
        Get a specific AI enhancement.

        Args:
            enhancement_id (str): The enhancement id.
        """
        path = f"/{AI_ENHANCEMENT_API_VERSION}/enrichments/{enhancement_id}"
        return self.get_response(path)

    def create_enhancement_from_url(
        self,
        url: str,
        media_types: list,
        end_user_identifier: str,
        notification_webhook_url: str,
    ) -> dict or None:
        """Create an enhancement from a file."""
        if Discipline.objects.count() > 0:
            path = f"/{AI_ENHANCEMENT_API_VERSION}/enrichments/url"
            data = {
                "url": url,
                "notificationWebhookUrl": notification_webhook_url,
                "enrichmentParameters": {
                    "mediaTypes": media_types,
                    "disciplines": list(
                        Discipline.objects.all().values_list("title", flat=True)
                    ),
                    # "aiEvaluation": "true"                    # TODO: change this
                },
                "enduserIdentifier": end_user_identifier,
            }
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.get_token()}",
            }
            try:
                response = requests.post(
                    AI_ENHANCEMENT_API_URL + path,
                    data=json.dumps(data),
                    headers=headers,
                )
                if response.status_code == 200:
                    return (
                        extract_json_from_str(response.content.decode("utf-8"))
                        if response.content
                        else None
                    )
                else:
                    logger.error(f"Error: {response.status_code}")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Request Exception: {e}")
                return None
        else:
            raise ValueError("No discipline in the database.")

    def get_latest_enhancement_version(self, enhancement_id: str) -> dict or None:
        """Get the latest enhancement version."""
        path = (
            f"/{AI_ENHANCEMENT_API_VERSION}/enrichments/{enhancement_id}/versions/latest"
        )
        return self.get_response(path)

    def get_enhancement_versions(
        self, enhancement_id: str, with_transcript: bool = True
    ) -> dict or None:
        """Get the enhancement versions."""
        path = f"/{AI_ENHANCEMENT_API_VERSION}/enrichments/{enhancement_id}/versions?withTranscript={with_transcript}"
        return self.get_response(path)

    def get_specific_enhancement_version(
        self, enhancement_id: str, version_id: str
    ) -> dict or None:
        """Get a specific version."""
        path = f"/{AI_ENHANCEMENT_API_VERSION}/enrichments/{enhancement_id}/versions/{version_id}"
        return self.get_response(path)

    def delete_request(self, path: str) -> dict or None:
        """
        Send delete request.

        Args:
            path (str): The path to the API endpoint.
        """
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.get_token()}",
        }
        try:
            response = requests.delete(
                AI_ENHANCEMENT_API_URL + path,
                headers=headers,
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {e}")
            return None

    def delete_enhancement(self, enhancement_id: str) -> dict or None:
        """Delete the specific enhancement."""
        path = f"/{AI_ENHANCEMENT_API_VERSION}/enrichments/{enhancement_id}"
        return self.delete_request(path)


def enhancement_is_already_asked(video: Video) -> bool:
    """Check if the enhancement is already asked."""
    return AIEnhancement.objects.filter(video=video).exists()


def enhancement_is_ready(video: Video) -> bool:
    """Check if the enhancement is ready."""
    return AIEnhancement.objects.filter(video=video, is_ready=True).exists()


def notify_user(video: Video):
    """Notify user at the end of enhancement."""
    if (
        USE_NOTIFICATIONS
        and video.owner.owner.accepts_notifications
        and PushInformation.objects.filter(user=video.owner).exists()
    ):
        send_notification_enhancement(video)
    if EMAIL_ON_ENHANCEMENT_COMPLETION:
        send_email_enhancement(video)


def send_notification_enhancement(video):
    """Send push notification on video encoding or transcripting completion."""
    subject = "[%s] %s" % (
        __TITLE_SITE__,
        _("%(subject)s #%(content_id)s completed")
        % {"subject": _("Enhancement"), "content_id": video.id},
    )
    message = _(
        "“%(content_title)s” was processed by the AI."
        + " Suggestions for improvement are available on %(site_title)s."
    ) % {
        "content_title": video.title,
        "site_title": __TITLE_SITE__,
    }

    notify_user(
        video.owner,
        subject,
        message,
        url=reverse("video:video", args=(video.slug,)),
    )


def send_email_enhancement(video) -> None:
    """Send email notification on video improvement completion."""
    if DEBUG:
        logger.info("SEND EMAIL ON IA IMPROVEMENT COMPLETION")
    url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
    content_url = "%s:%s" % (url_scheme, video.get_full_url())
    subject = "[%s] %s" % (
        __TITLE_SITE__,
        _("IA improvement #%(content_id)s completed") % {"content_id": video.id},
    )

    html_message = (
        '<p>%s</p><p>%s</p><p>%s<br><a href="%s"><i>%s</i></a>\
                </p><p>%s</p>'
        % (
            _("Hello,"),
            _(
                "IA improvement “%(content_title)s” has been completed"
                + ", and is now available on %(site_title)s."
            )
            % {
                "content_title": "<strong>%s</strong>" % video.title,
                "site_title": __TITLE_SITE__,
            },
            _("You will find it here:"),
            content_url,
            content_url,
            _("Regards."),
        )
    )

    full_html_message = html_message + "<br>%s%s<br>%s%s" % (
        _("Post by:"),
        video.owner,
        _("the:"),
        video.date_added,
    )

    message = bleach.clean(html_message, tags=[], strip=True)
    full_message = bleach.clean(full_html_message, tags=[], strip=True)

    from_email = DEFAULT_FROM_EMAIL
    to_email = []
    to_email.append(video.owner.email)

    if (
        USE_ESTABLISHMENT_FIELD
        and MANAGERS
        and video.owner.owner.establishment.lower() in dict(MANAGERS)
    ):
        bcc_email = []
        video_estab = video.owner.owner.establishment.lower()
        manager = dict(MANAGERS)[video_estab]
        if isinstance(manager, (list, tuple)):
            bcc_email = manager
        elif isinstance(manager, str):
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
