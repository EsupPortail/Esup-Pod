"""Esup-Pod - Export packages of archived videos and delete originals.

*  run with 'python manage.py create_archive_package [--dry]'
"""
import csv
import os
import shutil

from datetime import datetime, timedelta
from xml.dom import minidom
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.translation import activate
from django.utils.translation import gettext as _

from pod.video.models import Video
from pod.chapter.models import Chapter
from pod.completion.models import Contributor, Document, Overlay, Track


"""TODO
* Verifier si ca supp egalement les encodages
* Exporter tous les compléments avant suppression :
* [x] Chapitrage
* [x] Completion
* [] enrichissements
* [] SS-titres
"""

"""CUSTOM PARAMETERS."""
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")
ARCHIVE_ROOT = getattr(settings, "ARCHIVE_ROOT", "/video_archiving")
ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
ARCHIVE_CSV = "%s/archived.csv" % settings.LOG_DIRECTORY
HOW_MANY_DAYS = 365  # Delay before an archived video is moved to archive_ROOT


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
    mediaPackage_content = minidom.parseString(xmlcontent.replace("&", ""))
    mediapackage = mediaPackage_content.getElementsByTagName("dc.creator")[0]
    mediapackage.firstChild.replaceWholeText(user_name)

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


def export_complement(folder: str, export_type: str, export_objects: list) -> None:
    """Store a video complement as json."""
    if len(export_objects) > 0:
        export_file = os.path.join(folder, "%s.json" % export_type)
        print("Export %s %s." % (len(export_objects), export_type))
        with open(export_file, "w") as out:
            content = serialize('json', export_objects)
            print("export_file=%s" % export_file)
            out.write(content)


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

    def move_video_to_archive(self, mediaPackage_dir: str, vid: Video) -> None:
        """Move video source file to mediaPackage_dir."""
        if os.access(vid.video.path, os.F_OK):
            print("Moving %s" % vid.video.path)
            if not self.dry_mode:
                shutil.move(
                    vid.video.path,
                    os.path.join(
                        mediaPackage_dir, os.path.basename(vid.video.name)
                    ),
                )
                # Delete Video object
                vid.delete()
            # Supprime l'objet vidéo et le dossier associé (encodage, logs, etc..)
            # Supprime les thumbnails (x3)
            # Les completion semblent stockée uniquement en bdd
            # (voir "Completion Track") par exemple pour les ss/titres
            # Documents complémentaires ?
            # https://pod-test.univ-cotedazur.fr/media/files/8e5785441e2778e256f91df587311eecb14bb13441a609922d248277ccfcbb67/pod-webinaire.pdf
            # Notes / Commentaires ?
        else:
            print("ERROR: Cannot acces to file '%s'." % vid.video.path)

    def handle(self, *args, **options) -> None:
        """Handle a command call."""
        activate(LANGUAGE_CODE)

        if options["dry"]:
            self.dry_mode = True
            print("Simulation mode ('dry'). Nothing will be deleted.")

        # get data from ARCHIVE_CSV
        csv_data = read_archived_csv()

        # get videos
        vids = Video.objects.filter(
            owner__username=ARCHIVE_OWNER_USERNAME,
            date_delete__lte=datetime.now() - timedelta(days=HOW_MANY_DAYS),
        )

        print("%s videos archived since more than %s days found." % (len(vids), HOW_MANY_DAYS))
        for vid in vids:

            # vid = Video.objects.get(id=video_id)
            print("- Video slug: %s -" % vid.slug)

            if vid.recentViewcount > 0:
                # Do not archive a video with recent views.
                # (if video has been shared with a token, it can still be viewed)
                print("- Video %s ignored (%s recent views)" % (vid.slug, vid.recentViewcount))
                continue

            # Recover original video slug
            to_remove = len(_("Archived") + " 0000-00-00 ")
            video_dir = "%04d-%s" % (vid.id, slugify(vid.title[to_remove:]))

            csv_entry = csv_data.get(str(vid.id))
            if csv_entry:

                # Get username from CSV
                user_name = csv_entry["User name"].split("(")
                # extract username from "Fullname (username)" string
                user_name = user_name[-1][:-1]

                # Create video folder
                # ICI il faudrait le faire à partir de l'owner d'origine, sinon tout est à ARCHIVE
                mediaPackage_dir = os.path.join(
                    ARCHIVE_ROOT, user_name, video_dir
                )

                # create directory to store all the data.
                os.makedirs(mediaPackage_dir, exist_ok=True)

                # move video file
                store_as_dublincore(vid, mediaPackage_dir, csv_entry["User name"])

                # Store Video complements
                for type in [Chapter, Contributor, Document, Overlay, Track]:
                    export_complement(mediaPackage_dir,
                                      type.__name__,
                                      type.objects.filter(video=vid))

                # TODO:
                # - Que faire du fichier CSV ? il faudrait y retirer toutes les
                # lignes supprimées, quitte à faire un nouveau CSV

                self.move_video_to_archive(mediaPackage_dir, vid)
            else:
                print("Video %s not present in archived file" % vid.id)
            print("---")
