import importlib
import os

from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _


from pod import settings

from django.core.management import BaseCommand, CommandError

from pod.video.management.commands.respite_launcher import Command, Vdata

from pod.video.models import Video
from pod.video.utils import archive_pack, _safe_join_under_root, BASE_DIR, archive_and_get_link

ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")


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
        if options["dry"]:
            self.dry_mode = True

        videos = Video.objects.exclude(owner__username=ARCHIVE_OWNER_USERNAME)

        for vid in videos:
            self.stdout.write(str(vid.title))

            vdata = Vdata()
            data = vdata.get_video_data(vid)

            if (self._load_arch_model("base_arch").calcul(data, self.dry_mode)):
                safe_slug = slugify(str(vid.slug))
                archive_and_get_link(safe_slug, "video_archived_storage")
                self.stdout.write(
                    self.style.SUCCESS("An archive package was successfully created for the video "+str(vid.title))
                )
            else :
                self.stdout.write(
                    self.style.WARNING(
                        "No archive package was created for the video "+str(vid.title)
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
                _("Arch model not found: %(error)s") % {"error": e}
            ) from e
        except ImportError as e:
            self.stderr.write(self.style.ERROR(_("An Error occurred while processing.")))
            raise CommandError(
                _("Arch model import error: %(error)s") % {"error": e}
            ) from e