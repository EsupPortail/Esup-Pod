"""Esup-Pod - Check if video owners still exist in LDAP and reaffect videos if not.

*  run with 'python manage.py check_video_owner_exists [--dry]'
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from pod.video.models import Video
from pod.authentication.populatedCASbackend import get_ldap_conn, get_entry
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.template.defaultfilters import striptags
from django.core.mail import send_mail
from django.core.mail import mail_managers

User = get_user_model()

DEFAULT_OWNER_USERNAME = getattr(settings, "DEFAULT_OWNER_USERNAME", "default_owner")
ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")

USE_ESTABLISHMENT = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)

MANAGERS = getattr(settings, "MANAGERS", [])

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
URL_SCHEME = "https" if SECURE_SSL_REDIRECT else "http"
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
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")


class Command(BaseCommand):
    """Check if video owners still exist in LDAP."""

    help = "Check if video owners still exist in LDAP"
    dry_mode = False
    ldap_existing_usernames = []

    all_reaffected_videos = {}

    def add_arguments(self, parser):
        """Add possible args to the command."""
        parser.add_argument(
            "--dry",
            help="Simulate what would be done.",
            action="store_true",
            default=False,
        )

    def user_exists_in_ldap(self, conn, username):
        """Check if the owner username is in LDAP"""
        if username in self.ldap_existing_usernames:
            return True

        entry = get_entry(conn, username, [])
        if entry is not None:
            self.ldap_existing_usernames.append(username)
            return True

        return False

    def format_owner(self, user):
        """Format the owner name."""
        full_name = f"{user.first_name} {user.last_name}".strip()
        if full_name:
            return f"{full_name} ({user.username})"
        return f"({user.username})"

    def handle(self, *args, **options):
        """Handle the check_video_owner_exists command call."""
        dry_mode = options["dry"]

        promoted_count = 0
        video_count = 0
        conn = get_ldap_conn()
        if conn is None:
            self.stderr.write("LDAP connection error")
            return

        if dry_mode:
            self.stdout.write(self.style.WARNING("Running in dry mode"))

        videos = (
            Video.objects.select_related("owner")
            .prefetch_related("additional_owners")
            .order_by("id")
        )

        self.stdout.write(f"Number of videos found: {videos.count()}")

        default_owner, created = User.objects.get_or_create(
            username=DEFAULT_OWNER_USERNAME,
        )

        for video in videos:
            video_count += 1
            owner = video.owner
            if (
                owner.username == ARCHIVE_OWNER_USERNAME
                or owner.username == DEFAULT_OWNER_USERNAME
            ):
                continue

            if self.user_exists_in_ldap(conn, owner.username):
                continue

            promoted_count = self.reaffect_video(
                conn, default_owner, dry_mode, promoted_count, video
            )

        conn.unbind()

        self.notify_manager()

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished {video_count} videos.\n{promoted_count} owner(s) would be promoted."
                if dry_mode
                else f"Finished {video_count} videos.\n{promoted_count} owner(s) promoted."
            )
        )

    def reaffect_video(self, conn, default_owner, dry_mode, promoted_count, video):
        """Reaffect video to an owner who is in LDAP or a default user and notify him/her."""
        valid_additional_owner = default_owner
        for additional_owner in video.additional_owners.all():
            if self.user_exists_in_ldap(conn, additional_owner.username):
                valid_additional_owner = additional_owner
                break
        old_owner = video.owner
        estab = (video.owner.owner.establishment or "other").lower()
        if valid_additional_owner:
            promoted_count += 1

            if dry_mode:
                self.stdout.write(
                    f"[DRY-MODE] Would promote {valid_additional_owner.username} "
                    f"as owner of video {video.id}"
                )
            else:
                self.stdout.write(
                    f"Promoting {valid_additional_owner.username} "
                    f"as owner of video {video.id}"
                )

                with transaction.atomic():
                    video.owner = valid_additional_owner
                    video.save()
                    video.additional_owners.remove(valid_additional_owner)
                if valid_additional_owner != default_owner:
                    self.notify_user(video)

            if (
                USE_ESTABLISHMENT
                and MANAGERS
                and video.owner.owner.establishment.lower() in dict(MANAGERS)
            ):
                self.all_reaffected_videos.setdefault(estab, {})[video] = _(
                    "%(old)s replaced by %(new)s"
                ) % {
                    "old": self.format_owner(old_owner),
                    "new": self.format_owner(valid_additional_owner),
                }
            else:
                self.all_reaffected_videos.setdefault("other", {})[video] = _(
                    "%(old)s replaced by %(new)s"
                ) % {
                    "old": self.format_owner(old_owner),
                    "new": self.format_owner(valid_additional_owner),
                }
        return promoted_count

    def notify_manager(self):
        """Notify all managers for reaffected videos."""
        for estab in self.all_reaffected_videos:
            if len(self.all_reaffected_videos[estab]) > 0:
                if estab != "other":
                    msg_html = _("Hello manager(s) of %(estab)s on %(site_title)s,") % {
                        "estab": estab,
                        "site_title": __TITLE_SITE__,
                    }
                else:
                    msg_html = _("Hello manager(s) of %(site_title)s,") % {
                        "site_title": __TITLE_SITE__
                    }
                msg_html += (
                    "<br>\n<p>"
                    + _(
                        "For information, you will find below the list of reaffected videos."
                    )
                    + "</p>"
                )

                msg_html += "\n<p><ul>"
                for video, info in self.all_reaffected_videos[estab].items():
                    msg_html += "<li>"
                    msg_html += (
                        "%(title)s ("
                        + "<a href='%(scheme)s:%(url)s' rel='noopener'"
                        + " target='_blank'>%(scheme)s:%(url)s</a>) : "
                    ) % {
                        "scheme": URL_SCHEME,
                        "url": video.get_full_url(),
                        "title": video,
                    }
                    msg_html += f"{info}</li>"

                msg_html += "\n</ul></p>"
                msg_html += "\n<p>" + _("Regards") + "</p>\n"

                subject = _("The reaffected videos on Pod")

                if estab == "other":
                    mail_managers(
                        subject,
                        striptags(msg_html),
                        fail_silently=False,
                        html_message=msg_html,
                    )
                else:
                    to_email = []
                    to_email.append(dict(MANAGERS)[estab])
                    send_mail(
                        "[%s] %s"
                        % (
                            __TITLE_SITE__,
                            subject,
                        ),
                        striptags(msg_html),
                        DEFAULT_FROM_EMAIL,
                        to_email,
                        fail_silently=False,
                        html_message=msg_html,
                    )
                if MANAGERS:
                    print(
                        _(
                            "Manager(s) of “%(et)s” notified for %(nb)s reaffected video(s)."
                        )
                        % {"et": estab, "nb": len(self.all_reaffected_videos[estab])}
                    )

    def notify_user(self, video: Video):
        """Notify user who becomes owner of a video"""
        name = video.owner.last_name + " " + video.owner.first_name
        msg_html = _("Hello %(name)s,") % {"name": name}
        msg_html += "<br>\n"
        msg_html += (
            "<p>"
            + _(
                'You are now the owner of the video <a href="%(scheme)s:%(url)s">“%(title)s”</a>.'
            )
            % {"scheme": URL_SCHEME, "url": video.get_full_url(), "title": video.title}
            + "</p>\n"
        )
        msg_html += (
            "\n<p>"
            + _(
                "You were automatically designated as the owner because the previous owner is "
                "no longer at the institution and you were previously an additional owner."
            )
            + "</p>\n"
        )
        msg_html += "\n<p>" + _("Regards") + "</p>\n"
        # self.stdout.write(f"{video.id} {video.title} {video.slug}")

        to_email = [video.owner.email]
        for additional in video.additional_owners.all():
            to_email.append(additional.email)
            print(
                _("Sending mail to %(to_email)s for video %(title)s.")
                % {"to_email": to_email, "title": video.title}
            )
        return send_mail(
            "[%s] %s"
            % (__TITLE_SITE__, _("You have been designated as the owner of a video")),
            striptags(msg_html),
            DEFAULT_FROM_EMAIL,
            to_email,
            fail_silently=False,
            html_message=msg_html,
        )
