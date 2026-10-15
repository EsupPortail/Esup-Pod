"""Esup-Pod - Launch custom calculation model for each video of the platform

*  run with `python manage.py arch_launcher [--dry]`
"""

import importlib
import os
import sys

import paramiko
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from django.core.management import BaseCommand, CommandError

from pod.video.management.commands.respite_launcher import Vdata

from pod.video.models import Video
from pod.video.utils import BASE_DIR, archive_and_get_link

from django.conf import settings


ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
STFP_HOST_ARCHIVE = getattr(settings, "STFP_HOST_ARCHIVE", "")
STFP_USER_ARCHIVE = getattr(settings, "STFP_USER_ARCHIVE", "")
STFP_PASSWORD_ARCHIVE = getattr(settings, "STFP_PASSWORD", "")
STFP_REMOTE_DIR = getattr(settings, "STFP_REMOTE_DIR", "")


class Command(BaseCommand):
    dry_mode = False

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry",
            help="Simulate what would be done.",
            action="store_true",
            default=False,
        )

    def handle(self, *args, **options):
        """Run ARCH processing for all applicable videos"""
        if options["dry"]:
            self.dry_mode = True

        videos = Video.objects.exclude(owner__username=ARCHIVE_OWNER_USERNAME)

        for vid in videos:

            vdata = Vdata()
            data = vdata.get_video_data(vid)

            if (self._load_arch_model("base_arch").calcul(data, self.dry_mode)):
                safe_slug = slugify(str(vid.slug))
                _, link = archive_and_get_link(safe_slug, "video_archived_storage")

                try:
                    self.send_zip(
                        file_path=os.path.join(BASE_DIR, "") + link,
                        sftp_host=STFP_HOST_ARCHIVE,
                        sftp_user=STFP_USER_ARCHIVE,
                        sftp_password=STFP_PASSWORD_ARCHIVE,
                        remote_dir=STFP_REMOTE_DIR,
                    )
                except Exception as e :
                    self.stdout.write(
                        self.style.ERROR(
                            "Cannot send the video " + str(vid.title) + " to the FTP server.\n" + str(e)
                        )
                    )
                    sys.exit()

                self.stdout.write(
                    self.style.SUCCESS("An archive package was successfully created for the video " + str(vid.title) + " and sent to the FTP server.")
                )
            else :
                self.stdout.write(
                    self.style.WARNING(
                        "No archive package was created for the video " + str(vid.title)
                    )
                )

    def _load_arch_model(self, model):
        """Import and return the ARCH model module."""
        try:
            return importlib.import_module(
                "pod.video.management.commands.arch_model." + model
            )

        except ModuleNotFoundError as e:
            self.stderr.write(self.style.ERROR(_("An Error occurred while processing.")))
            raise CommandError(
                _("Archiving model not found: %(error)s") % {"error": e}
            ) from e
        except ImportError as e:
            self.stderr.write(self.style.ERROR(_("An Error occurred while processing.")))
            raise CommandError(
                _("Archiving model import error: %(error)s") % {"error": e}
            ) from e

    def send_zip(self, file_path, sftp_host, sftp_user, sftp_password, remote_dir="/"):
        """Send the zip file to the specified FTP server using SFTP."""
        transport = paramiko.Transport((sftp_host, 22))
        transport.connect(
            username=sftp_user,
            password=sftp_password,
        )

        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            remote_path = remote_dir.rstrip("/") + "/" + file_path.split("/")[-1]
            sftp.put(file_path, remote_path)
        finally:
            sftp.close()
            transport.close()
