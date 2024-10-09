"""Esup-Pod - Export packages of archived videos and delete originals.

*  run with 'python manage.py create_archive_package [--dry]'
"""

import csv
import os
import shutil

from datetime import datetime, timedelta
from defusedxml import minidom
from django.conf import settings
from django.core.mail import mail_managers
from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from django.template.defaultfilters import slugify, striptags
from django.template.loader import render_to_string
from django.utils.translation import activate
from django.utils.translation import gettext as _

from pod.video.models import Video, Notes, AdvancedNotes, Comment, ViewCount
from pod.chapter.models import Chapter
from pod.completion.models import Contributor, Document, Overlay, Track
from pod.enrichment.models import Enrichment
from pod.main.utils import sizeof_fmt


"""CUSTOM PARAMETERS."""
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")
ARCHIVE_ROOT = getattr(settings, "ARCHIVE_ROOT", "/video_archiving")
ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
ARCHIVE_CSV = "%s/archived.csv" % settings.LOG_DIRECTORY
# Delay before an archived video is moved to archive_ROOT
ARCHIVE_HOW_MANY_DAYS = getattr(settings, "ARCHIVE_HOW_MANY_DAYS", 365)

__TITLE_SITE__ = (
    settings.TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (settings.TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)


def store_as_dublincore(vid: Video, mediaPackage_dir: str, user_name: str) -> None:
    """Store video metadata as Dublin Core Format in mediaPackage_dir."""
    xmlcontent = '<?xml version="1.0" encoding="utf-8"?>\n'
    xmlcontent += (
        "<!DOCTYPE rdf:RDF PUBLIC " '"-//DUBLIN CORE//DCMES DTD 2002/07/31//EN" \n'
    )
    xmlcontent += (
        '"http://dublincore.org/documents/2002/07' '/31/dcmes-xml/dcmes-xml-dtd.dtd">\n'
    )
    xmlcontent += (
        "<rdf:RDF xmlns:rdf="
        '"http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
        ' xmlns:dc ="http://purl.org/dc/elements/1.1/">\n'
    )
    rendered = render_to_string(
        "videos/dublincore.html", {"video": vid, "xml": True}, None
    )
    xmlcontent += rendered
    xmlcontent += "</rdf:RDF>"
    # complete creator
    mediaPackage_content = minidom.parseString(xmlcontent)

    dc_creator = mediaPackage_content.getElementsByTagName("dc.creator")[0]

    if dc_creator.firstChild is None:
        new_node = mediaPackage_content.createTextNode(user_name)
        dc_creator.appendChild(new_node)
    else:
        dc_creator.firstChild.replaceWholeText(user_name)

    mediaPackage_file = os.path.join(mediaPackage_dir, "dublincore.xml")
    with open(mediaPackage_file, "w") as f:
        f.write(
            minidom.parseString(
                mediaPackage_content.toxml().replace("\n", "")
            ).toprettyxml()
        )


def read_archived_csv() -> dict:
    """Get data from ARCHIVE_CSV."""
    csv_data = {}
    if os.access(ARCHIVE_CSV, os.F_OK):
        with open(ARCHIVE_CSV, "r", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "Date",
                "User name",
                "User email",
                "User Affiliation",
                "User Establishment",
                "Video Id",
                "Video title",
                "Video URL",
                "Video type",
                "Date added",
            ]
            reader = csv.DictReader(
                csvfile, skipinitialspace=True, delimiter=";", fieldnames=fieldnames
            )
            for row in reader:
                dico = {k: v for k, v in row.items()}
                csv_data[dico["Video Id"]] = dico

    return csv_data


class Command(BaseCommand):
    """Move old archived videos from disk to ARCHIVE_ROOT."""

    help = "Move old archived videos to ARCHIVE_ROOT."
    dry_mode = False

    def add_arguments(self, parser) -> None:
        """Add possible args to the command."""
        parser.add_argument(
            "--dry",
            help="Simulate what would be done.",
            action="store_true",
            default=False,
        )

    def export_complement(
        self, folder: str, export_type: str, export_objects: list
    ) -> None:
        """Store a video complement as json."""
        if len(export_objects) > 0:
            export_file = os.path.join(folder, "%s.json" % export_type)
            print("  * Export %s %s." % (len(export_objects), export_type))
            if not self.dry_mode:
                with open(export_file, "w") as out:
                    content = serialize("json", export_objects)
                    out.write(content)

    def move_video_to_archive(self, mediaPackage_dir: str, vid: Video) -> None:
        """Move video source file to mediaPackage_dir."""
        if os.access(vid.video.path, os.F_OK):
            print("  * Moving %s" % vid.video.path)
            if not self.dry_mode:
                shutil.move(
                    vid.video.path,
                    os.path.join(mediaPackage_dir, os.path.basename(vid.video.name)),
                )
                # Delete Video object
                vid.delete()
            # Deletes the video object and the associated folder (encoding, logs, etc.)
            # Remove thumbnails (x3)
        else:
            print("ERROR: Cannot access to file '%s'." % vid.video.path)

    def archive_pack(self, video_dir: str, user_name: str, vid: Video) -> None:
        """Create a archive package for Video vid."""
        # Get username from CSV
        user_name = user_name.split("(")
        # extract username from "Fullname (username)" string
        user_name = user_name[-1][:-1]

        # Create video folder
        mediaPackage_dir = os.path.join(ARCHIVE_ROOT, user_name, video_dir)

        # Create directory to store all the data
        os.makedirs(mediaPackage_dir, exist_ok=True)

        # Move video file
        store_as_dublincore(vid, mediaPackage_dir, user_name)

        # Store Video complements as json
        for model in [
            Chapter,
            Contributor,
            Overlay,
            Enrichment,
            Notes,
            AdvancedNotes,
            Comment,
            ViewCount,
        ]:
            # nb: contributors are already exported in dublincore.xml
            self.export_complement(
                mediaPackage_dir, model.__name__, model.objects.filter(video=vid)
            )
        # Export also the video itself as json
        self.export_complement(mediaPackage_dir, "Video", [vid])

        # Store also files linked to Enrichments
        for enrich in Enrichment.objects.filter(video=vid):
            if enrich.document:
                print("  * Copying %s..." % enrich.document.file.path)
                shutil.copy(enrich.document.file.path, mediaPackage_dir)
            if enrich.image:
                print("  * Copying %s..." % enrich.image.file.path)
                shutil.copy(enrich.image.file.path, mediaPackage_dir)

        # Store file complements.
        for file in Document.objects.filter(video=vid):
            print("  * Copying %s..." % file.document.file.path)
            shutil.copy(file.document.file.path, mediaPackage_dir)

        # Store additional tracks (caption / subtitles)
        for track in Track.objects.filter(video=vid):
            print("  * Copying %s..." % track.src.file.path)
            shutil.copy(track.src.file.path, mediaPackage_dir)

        # TODO:
        # - Que faire du fichier CSV ? il faudrait y retirer toutes les
        # lignes supprimées, quitte à faire un nouveau CSV

        self.move_video_to_archive(mediaPackage_dir, vid)

    def get_list_video_html(self, list_video: list) -> str:
        """Generate an html version of list_video."""
        msg_html = ["<ol>"]
        for vid in list_video:
            msg_html.append("<li>%s</li>" % vid)
        msg_html.append("</ol>")
        return "\n".join(msg_html)

    def handle(self, *args, **options) -> None:
        """Handle a command call."""
        activate(LANGUAGE_CODE)
        total_duration = 0
        total_processed = 0
        total_weight = 0
        list_video = []
        ignored_video = []

        if options["dry"]:
            self.dry_mode = True
            print("Simulation mode ('dry'). Nothing will be deleted.")

        # Get data from ARCHIVE_CSV
        csv_data = read_archived_csv()

        # Get videos
        vids = Video.objects.filter(
            owner__username=ARCHIVE_OWNER_USERNAME,
            date_delete__lte=datetime.now() - timedelta(days=ARCHIVE_HOW_MANY_DAYS),
        )

        print(
            "%s videos archived since more than %s days found."
            % (len(vids), ARCHIVE_HOW_MANY_DAYS)
        )
        for vid in vids:
            # vid = Video.objects.get(id=video_id)
            print("- Video slug: %s -" % vid.slug)

            if vid.recentViewcount > 0:
                # Do not archive a video with recent views.
                # (if video has been shared with a token, it can still be viewed)
                print("  * IGNORED (%s recent views)" % vid.recentViewcount)
                ignored_video.append(str(vid))
                continue

            # Recover original video slug
            to_remove = len(_("Archived") + " 0000-00-00 ")
            video_dir = "%04d-%s" % (vid.id, slugify(vid.title[to_remove:]))

            csv_entry = csv_data.get(str(vid.id))
            if csv_entry:
                total_duration += vid.duration
                total_processed += 1
                if os.access(vid.video.path, os.F_OK):
                    total_weight += os.path.getsize(vid.video.path)
                list_video.append(str(vid))
                self.archive_pack(video_dir, csv_entry["User name"], vid)
            else:
                print("  * Video %s not present in archived file" % vid.id)
            print("---")
        # Convert seconds in human readable time
        total_duration = str(timedelta(seconds=total_duration))
        total_msg = _(
            "Package archiving done. %(amount)s video(s) packaged (%(weight)s - [%(duration)s])"
            " - %(nb_ignored)s video(s) ignored."
        ) % {
            "amount": total_processed,
            "weight": sizeof_fmt(total_weight),
            "duration": total_duration,
            "nb_ignored": len(ignored_video),
        }

        print(total_msg)
        if total_processed > 0:
            self.inform_managers(list_video, ignored_video, total_msg, total_processed)

    def inform_managers(
        self, list_video: list, ignored_video: list, total_msg: str, total_processed: int
    ) -> None:
        """Inform site managers of packaged archives."""
        msg_html = [_("Hello manager(s) of  %s,") % __TITLE_SITE__]
        msg_html.append("<br>")
        if self.dry_mode:
            msg = (
                _(
                    "For your information, "
                    "below is the list of archived videos that would’ve been packaged in "
                    "your ARCHIVE_ROOT folder. Run the <code>create_archive_package</code> "
                    "command without the <code>--dry</code> option to delete them from %s."
                )
                % __TITLE_SITE__
            )
        else:
            msg = (
                _(
                    (
                        "For your information, "
                        "below is the list of archived videos that have been packaged in "
                        "your ARCHIVE_ROOT folder, and definitely deleted from %s."
                    )
                )
                % __TITLE_SITE__
            )

        msg_html.append("<p>%s</p>" % msg)
        msg_html.append(self.get_list_video_html(list_video))

        msg = _(
            "And below is the list of ignored videos that were not packaged "
            "because they have been recently viewed."
        )

        msg_html.append("<p>%s</p>" % msg)
        msg_html.append(self.get_list_video_html(ignored_video))

        msg_html.append("<p>%s</p>" % total_msg)
        msg_html.append("<p>%s</p>" % _("Regards."))
        msg_html = "\n".join(msg_html)
        subject = _("Packaging %s archived videos on Pod") % total_processed
        mail_managers(
            subject,
            striptags(msg_html),
            fail_silently=False,
            html_message=msg_html,
        )
        print("Summary sent by email to managers.")
