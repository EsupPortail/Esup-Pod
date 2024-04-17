"""Esup-Pod - Create packages of archived videos."""
import csv
import os
import shutil

from datetime import datetime, timedelta
from xml.dom import minidom
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from pod.video.models import Video


"""TODO
* Verifier si ca supp egalement les encodages
* Exporter tous les compléments avant suppression (chapitrage, ss-titres...)
* Vérifier qu'il n'y a eu aucune vue dans l'année avant d'archiver
"""

"""CUSTOM PARAMETERS."""
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

    mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % vid.slug)
    # create directory to store all the data.
    os.makedirs(mediaPackage_dir, exist_ok=True)
    with open(mediaPackage_file, "w") as f:
        f.write(
            minidom.parseString(
                mediaPackage_content.toxml().replace("\n", "")
            ).toprettyxml()
        )


def read_archived_csv() -> dict:
    """Get data from ARCHIVE_CSV."""
    csv_data = {}
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

    def add_arguments(self, parser) -> None:
        """Add possible args to the command."""
        parser.add_argument(
            "--dry",
            help="Simulate what would be done.",
            action="store_true",
            default=False,
        )

    def handle(self, *args, **options) -> None:
        """Handle a command call."""
        if options["dry"]:
            print("Simulation mode ('dry'). Nothing will be deleted.")

        # get data from ARCHIVE_CSV
        csv_data = read_archived_csv()

        # get videos
        vids = Video.objects.filter(
            owner__username=ARCHIVE_OWNER_USERNAME,
            date_delete__lte=datetime.now() - timedelta(days=HOW_MANY_DAYS),
            recentViewcount=0
        )

        for vid in vids:

            # vid = Video.objects.get(id=video_id)
            print("- Video slug: %s -" % vid.slug)

            if vid.recentViewcount > 0:
                # If video has been shared with a token, it can still be viewed.
                print("Video has recent views (%s) - ignored" % vid.recentViewcount)
                continue

            csv_entry = csv_data.get(str(vid.id))
            if csv_entry:
                # Create video folder
                mediaPackage_dir = os.path.join(
                    ARCHIVE_ROOT, vid.owner.username, vid.slug
                )
                # move video file
                store_as_dublincore(vid, mediaPackage_dir, csv_entry["User name"])

                # TODO:
                # - Il faut aussi déplacer tous les fichiers liés (
                # chapitres, notes, commentaires, enrichissements, compléments...)
                # - Que faire du fichier CSV ? il faudrait y retirer toutes les
                # lignes supprimées, quitte à faire un nouveau CSV

                # nb: User Name is stored as "firstname lastname (username)" in csv.
                # move video source file to mediaPackage_dir
                if os.access(vid.video.path, os.F_OK):
                    print("move from %s" % vid.video.path)
                    if not options["dry"]:
                        shutil.move(
                            vid.video.path,
                            os.path.join(
                                mediaPackage_dir,
                                os.path.basename(vid.video.name)
                            )
                        )
                        # os.rename(vid.video.path, os.path.join(mediaPackage_dir,
                        # os.path.basename(vid.video.name)))
                        # delete video
                        vid.delete()
                    # Supprime l'objet vidéo et le dossier associé (encodage, logs, etc..)
                    # Supprime les thumbnails (x3)
                    # Les completion semblent stockée uniquement en bdd
                    # (voir "Completion Track") par exemple pour les ss/titres
                    # Documents complémentaires ?
                    # Notes / Commentaires ?
                else:
                    print("ERROR: Cannot acces to file '%s'." % vid.video.path)
            else:
                print("Video %s not present in archived file" % vid.id)
            print("---")
