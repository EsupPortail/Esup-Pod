"""Esup-Pod video utilities."""

from django.db.models.functions import Lower
import os
import json
import re
import shutil
import logging
from math import ceil
import csv
from datetime import date
from defusedxml import minidom
from django.core.serializers import serialize

from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from pod.video_encode_transcript.models import EncodingVideo, EncodingAudio
from pod.video_encode_transcript.models import PlaylistVideo
from django.contrib.auth import get_user_model
from pod.video.models import Video, Category, Type, Discipline, VideoToDelete

logger = logging.getLogger(__name__)
User = get_user_model()


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

USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)

MANAGERS = getattr(settings, "MANAGERS", {})

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)

VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")
BASE_DIR = getattr(settings, "BASE_DIR", "/")

NUMBER_TAGS_CLOUD = getattr(settings, "NUMBER_TAGS_CLOUD", 20)

ARCHIVE_CSV = "%s/archived.csv" % settings.LOG_DIRECTORY

ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")

ARCHIVE_ROOT = getattr(settings, "ARCHIVE_ROOT", "/video_archiving")

###############################################################
# EMAIL
###############################################################


def pagination_data(request_path, offset, limit, total_count):
    """Get next, previous url and info about max number of page and current page.

    :param request_path: str: current request path
    :param offset:       int: data offset
    :param limit:        int: data max number
    :param total_count:  int: total data count

    :return: Tuple[str]: next, previous url and current page info
    """
    next_url = previous_url = None
    pages_info = "0/0"
    # manage next previous url (Pagination)
    if offset + limit < total_count and limit <= total_count:
        next_url = "{}?limit={}&offset={}".format(request_path, limit, limit + offset)
    if offset - limit >= 0 and limit <= total_count:
        previous_url = "{}?limit={}&offset={}".format(request_path, limit, offset - limit)

    current_page = 1 if offset <= 0 else int((offset / limit)) + 1
    total = ceil(total_count / limit)
    pages_info = "{}/{}".format(current_page if total > 0 else 0, total)

    return next_url, previous_url, pages_info


def get_headband(channel, theme=None):
    """Get headband with priority to theme headband.

    :param channel: (Channel): channel
    :param theme: (Theme, optional): theme, Defaults to None.

    :return: dict: type(theme, channel) and headband path
    """
    result = {
        "type": "channel" if theme is None else "theme",
        "headband": None,
    }
    if theme is not None and theme.headband is not None:
        result["headband"] = theme.headband.file.url  # pragma: no cover
    elif theme is None and channel.headband is not None:
        result["headband"] = channel.headband.file.url  # pragma: no cover

    return result


def change_owner(video_id, new_owner) -> bool:
    """Replace current video_id owner by new_owner."""
    if video_id is None:
        return False

    video = Video.objects.filter(pk=video_id).first()
    if video is None:
        return False
    video.owner = new_owner
    video.save()
    move_video_file(video, new_owner)
    return True


def move_video_file(video, new_owner) -> None:
    """Move video files in new_owner folder."""
    # overview and encoding video folder name
    encod_folder_pattern = "%04d" % video.id
    old_dest = os.path.join(os.path.dirname(video.video.path), encod_folder_pattern)
    new_dest = re.sub(r"\w{64}", new_owner.owner.hashkey, old_dest)

    # move video files folder contains(overview, format etc...)
    if not os.path.exists(new_dest) and os.path.exists(old_dest):
        new_dest = re.sub(encod_folder_pattern + "/?", "", new_dest)
        if not os.path.exists(new_dest):
            os.makedirs(new_dest)
        shutil.move(old_dest, new_dest)

    # update video overview path
    if bool(video.overview):
        video.overview = re.sub(
            r"\w{64}", new_owner.owner.hashkey, video.overview.__str__()
        )

    # Update video playlist source file
    video_playlist_master = video.get_playlist_master()
    if video_playlist_master is not None:
        video_playlist_master.source_file.name = re.sub(
            r"\w{64}", new_owner.owner.hashkey, video_playlist_master.source_file.name
        )
        video_playlist_master.save()

    # Change the path of encodings related to a video
    models_to_update = [EncodingVideo, EncodingAudio, PlaylistVideo]
    for model in models_to_update:
        encodings = model.objects.filter(video=video)
        for encoding in encodings:
            encoding.source_file = re.sub(
                r"\w{64}", new_owner.owner.hashkey, encoding.source_file.name.__str__()
            )
            encoding.save()

    # Update video path
    video_file_pattern = r"[\w-]+\.\w+"
    old_video_path = video.video.path
    new_video_path = re.sub(r"\w{64}", new_owner.owner.hashkey, old_video_path)
    video.video.name = new_video_path.split("media/")[1]
    if not os.path.exists(new_video_path) and os.path.exists(old_video_path):
        new_video_path = re.sub(video_file_pattern, "", new_video_path)
        shutil.move(old_video_path, new_video_path)
    video.save()


def get_videos(
    title, user_id, search=None, limit: int = 12, offset: int = 0
) -> JsonResponse:
    """Return videos filtered by GET parameters 'title' with limit and offset.

    Args:
        request (Request): Http Request

    Returns:
        list[dict]: videos found
    """
    videos = Video.objects.filter(owner__id=user_id).order_by("id")
    if search is not None:
        title = search

    if title is not None:
        videos = videos.filter(
            Q(title__icontains=title)
            | Q(title_fr__icontains=title)
            | Q(title_en__icontains=title)
        )

    count = videos.count()
    results = list(
        map(
            lambda v: {
                "id": v.id,
                "title": v.title,
                "thumbnail": v.get_thumbnail_url(),
            },
            videos[offset : limit + offset],
        )
    )

    next_url, previous_url, page_infos = pagination_data(
        reverse("video:filter_videos", kwargs={"user_id": user_id}),
        offset,
        limit,
        count,
    )

    response = {
        "count": count,
        "next": next_url,
        "previous": previous_url,
        "page_infos": page_infos,
        "results": results,
    }
    return JsonResponse(response, safe=False)


def get_tag_cloud() -> list:
    """Get a list of the most popular tags (weight concept)."""
    # Convert tag cloud to list of dict, so it can be stored in CACHE
    tags = []
    for tag in Video.tags.tag_model.objects.weight():
        tags.append({"name": tag.name, "weight": tag.weight, "slug": tag.slug})

    # Sort tags by weight in descending order
    tags_sorted = sorted(tags, key=lambda x: x["weight"], reverse=True)

    # Return only the top tags
    return tags_sorted[:NUMBER_TAGS_CLOUD]


def sort_videos_list(videos_list: list, sort_field: str, sort_direction: str = ""):
    """Return videos list sorted by sort_field.

    Sorted by specific column name and ascending or descending direction
    """
    if sort_field and sort_field in {
        "category",
        "channel",
        "cursus",
        "date_added",
        "date_evt",
        "discipline",
        "duration",
        "id",
        "is_360",
        "is_restricted",
        "is_video",
        "licence",
        "main_lang",
        "owner",
        "sites",
        "theme",
        "title",
        "title_en",
        "title_fr",
        "type",
        "viewcount",
        "rank",
        "order",
    }:
        if sort_field in {"title", "title_fr", "title_en"}:
            sort_field = Lower(sort_field)
            if not sort_direction:
                sort_field = sort_field.desc()

        elif not sort_direction:
            sort_field = "-" + sort_field
        videos_list = videos_list.order_by(sort_field)

    return videos_list.distinct()


def get_id_from_request(request, key):
    """Get the value of a specified key from the request object."""
    if request.method == "POST" and request.POST.get(key):
        return request.POST.get(key)
    elif request.method == "GET" and request.GET.get(key):
        return request.GET.get(key)
    return None


def get_video_data(video):
    """Get a dictionary containing data from a video object."""
    return {
        "slug": video.slug,
        "title": video.title,
        "duration": video.duration_in_time,
        "thumbnail": video.get_thumbnail_card(),
        "is_video": video.is_video,
        "has_password": bool(video.password),
        "is_restricted": video.is_restricted,
        "has_chapter": video.chapter_set.all().count() > 0,
        "is_draft": video.is_draft,
    }


def get_storage_path_video(instance, filename) -> str:
    """Get the video storage path.

    Instance needs to implement owner
    """
    Video.get_storage_path_video(instance, filename)


def verify_field_length(field, field_name: str = "title", max_length: int = 100) -> list:
    """Check field length, and return message."""
    msg = list()
    if not field or field == "":
        msg.append(_("Please enter a title."))
    elif len(field) < 2 or len(field) > max_length:
        msg.append(
            _(
                "Please enter a %(field_name)s from 2 to %(max_length)s characters."
                % {"field_name": field_name, "max_length": max_length}
            )
        )
    return msg


def has_audio(video) -> bool:
    """
    Checks if a video contains an audio track.

    Args:
        video (:class:`pod.video.models`): The video object.

    Returns:
        bool: True if the video has an audio track, False otherwise.
    """
    try:
        # Get the path of the video file
        video_path = video.video.path

        # Build the path to the output directory
        output_dir = os.path.join(os.path.dirname(video_path), f"{video.id:04d}")

        # Path to the info_video.json file
        info_file = os.path.join(output_dir, "info_video.json")

        # Read the JSON file
        with open(info_file, "r", encoding="utf-8") as json_file:
            info_video = json.load(json_file)

        # Check if the "list_audio_track" key exists and the list is not empty
        if len(info_video["list_audio_track"]) > 0:
            return True
        else:
            return False

    except FileNotFoundError:
        print("Error: info_video.json file not found.")
    except json.JSONDecodeError:
        print("Error: Malformed JSON file.")
    except KeyError:
        print("Error: 'list_audio_track' key missing in JSON file.")
    except Exception as e:
        print(f"Unexpected error: {e}")

    # Default to True if an error occurs
    return True


def get_base_queryset_for_taxonomies(model, user_videos):
    """
    Crée le QuerySet de base pour les filtres de taxonomies (Type, Discipline)
    liés aux vidéos d'un utilisateur.
    """
    return (
        model.objects.filter(video__in=user_videos)
        .distinct()
        .annotate(video_count=Count("video", filter=Q(video__in=user_videos)))
    )


def apply_search_order_limit_for_taxonomies(
    qs, search_term, field_name="title", order_by_field="title", limit=20
):
    """
    Apply the search filter (on field_name), order, and limit
    for taxonomies returning id, slug, field_name, and video_count.
    """
    if search_term:
        search_filter = {f"{field_name}__icontains": search_term}
        qs = qs.filter(**search_filter)
    return list(
        qs.order_by(order_by_field).values("id", "slug", field_name, "video_count")[
            :limit
        ]
    )


def get_filtered_categories_for_user(user, search_term=None, limit=20):
    """Retrieves and filters categories for a user."""
    if not getattr(settings, "USE_CATEGORY", True):
        return []
    qs = Category.objects.filter(owner=user).prefetch_related("video")
    if search_term:
        qs = qs.filter(title__icontains=search_term)
    return list(qs.order_by("title").values("id", "slug", "title")[:limit])


def get_filtered_types_for_videos(user_videos, search_term=None, limit=20):
    """Retrieves and filters types associated with a list of videos."""
    if not getattr(settings, "USE_TYPES", True):
        return []
    qs = get_base_queryset_for_taxonomies(Type, user_videos)
    return apply_search_order_limit_for_taxonomies(
        qs, search_term, "title", "title", limit
    )


def get_filtered_disciplines_for_videos(user_videos, search_term=None, limit=20):
    """Retrieves and filters the disciplines associated with a list of videos."""
    if not getattr(settings, "USE_DISCIPLINES", True):
        return []
    qs = get_base_queryset_for_taxonomies(Discipline, user_videos)
    return apply_search_order_limit_for_taxonomies(
        qs, search_term, "title", "title", limit
    )


def get_filtered_tags_for_videos(user_videos, search_term=None, limit=20):
    """Retrieves and filters tags associated with a list of videos."""
    if not getattr(settings, "USE_TAGS", True):
        return []
    TagModel = Video.tags.tag_model
    qs = TagModel.objects.filter(video__in=user_videos).distinct()
    if search_term:
        qs = qs.filter(name__icontains=search_term)
    return list(qs.order_by("name").values("name", "slug")[:limit])


def get_filtered_owners_for_videos(user_videos, search_term=None, limit=20):
    """Retrieves and filters owners (owner + additional) associated with a list of videos."""
    primary_owner_ids = set(user_videos.values_list("owner_id", flat=True))
    additional_owner_ids = set(
        user_videos.values_list("additional_owners__id", flat=True)
    )
    user_ids = {
        uid for uid in primary_owner_ids.union(additional_owner_ids) if uid is not None
    }

    if not user_ids:
        return []

    users_qs = User.objects.filter(id__in=list(user_ids))

    if getattr(settings, "MENUBAR_HIDE_INACTIVE_OWNERS", False):
        users_qs = users_qs.filter(is_active=True)
    if getattr(settings, "MENUBAR_SHOW_STAFF_OWNERS_ONLY", False):
        users_qs = users_qs.filter(is_staff=True)

    if search_term:
        users_qs = users_qs.filter(
            Q(username__icontains=search_term)
            | Q(first_name__icontains=search_term)
            | Q(last_name__icontains=search_term)
        )

    return list(
        users_qs.order_by("username").values("id", "username", "first_name", "last_name")[
            :limit
        ]
    )


def archive_video(vid):
    """
    It Allows the archive process without launching 'get_video archived deleted treatment' in the purpose to be used in other functions
    """
    write_in_csv(vid, "archived")
    archive_user, created = User.objects.get_or_create(
        username=ARCHIVE_OWNER_USERNAME,
    )
    # Rename video and change owner.
    vid.owner = archive_user
    vid.is_draft = True
    vid.title = "%s %s %s" % (
        _("Archived"),
        date.today(),
        vid.title,
    )
    # Trunc title to 250 chars max.
    vid.title = vid.title[:250]
    vid.save()

    # add video to delete
    vid_delete, created = VideoToDelete.objects.get_or_create(
        date_deletion=vid.date_delete
    )
    vid_delete.video.add(vid)
    vid_delete.save()


def check_csv_header(csv_file: str, fieldnames: list) -> None:
    """Check for (and add) missing columns in an existing CSV file."""
    with open(csv_file, "r") as f:
        lines = f.readlines()
    if len(lines[0].split(";")) < len(fieldnames):
        print("Adding missing header columns in %s." % csv_file)
        lines[0] = ";".join(fieldnames) + "\n"
        with open(csv_file, "w") as f:
            f.writelines(lines)


def write_in_csv(vid: Video, arch_type: str) -> None:
    """Add in `type`.csv file informations about the video."""
    file = "%s/%s.csv" % (settings.LOG_DIRECTORY, arch_type)
    exists = os.path.isfile(file)

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
        "Source file",
        "Description",
        "Views",
    ]
    if exists:
        check_csv_header(file, fieldnames)

    with open(file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, delimiter=";", fieldnames=fieldnames)

        if not exists:
            writer.writeheader()

        # Force the username attribute even if HIDE_USERNAME is true whereas the __str__ method
        # of Owner Class used by vid.owner.owner doesn't do so
        user_name = "%s %s (%s)" % (
            vid.owner.first_name,
            vid.owner.last_name,
            vid.owner.username,
        )

        writer.writerow(
            {
                "Date": date.today(),
                "User name": user_name,
                "User email": vid.owner.email,
                "User Affiliation": vid.owner.owner.affiliation,
                "User Establishment": vid.owner.owner.establishment,
                "Video Id": vid.id,
                "Video title": vid.title,
                "Video URL": "https:%s" % vid.get_full_url(),
                "Video type": vid.type.title,
                "Date added": "%s" % vid.date_added.strftime("%Y/%m/%d"),
                "Source file": vid.video,
                "Description": vid.description.replace(";", "$semic$")
                .replace("\r", "")
                .replace("\n\n", "\n")
                .replace("\n", "$newl$"),
                "Views": vid.viewcount,
            }
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


def export_complement(
    folder: str, export_type: str, export_objects: list, dry_mode: bool = True
) -> None:
    """Store a video complement as json."""
    if len(export_objects) > 0:
        export_file = os.path.join(folder, "%s.json" % export_type)
        print("  * Export %s %s." % (len(export_objects), export_type))
        if not dry_mode:
            with open(export_file, "w") as out:
                content = serialize("json", export_objects)
                out.write(content)


def move_video_to_archive(
    mediaPackage_dir: str, vid: Video, dry_mode: bool = True
) -> None:
    """Move video source file to mediaPackage_dir."""
    if os.access(vid.video.path, os.F_OK):
        print(
            "  * Moving %s to " % vid.video.path,
            os.path.join(mediaPackage_dir, os.path.basename(vid.video.name)),
        )
        if not dry_mode:
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


def copy_archive_to(media_package_dir: str, vid: Video) -> None:
    """Move video source file to mediaPackage_dir."""
    if os.access(vid.video.path, os.F_OK):
        shutil.copy(
            vid.video.path,
            os.path.join(media_package_dir),
        )
    else:
        print("ERROR: Cannot access to file '%s'." % vid.video.path)


def archive_pack(
    media_package_dir: str,
    user_name: str,
    vid: Video,
    only_copy: bool = True,
    dry_mode: bool = True,
) -> None:
    """Create a archive package for Video vid."""
    from pod.video.models import Notes, AdvancedNotes, Comment, ViewCount
    from pod.chapter.models import Chapter
    from pod.completion.models import Contributor, Document, Overlay, Track
    from pod.enrichment.models import Enrichment

    # Create directory to store all the data
    os.makedirs(media_package_dir, exist_ok=True)

    # Move video file
    store_as_dublincore(vid, media_package_dir, user_name)

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
        export_complement(
            media_package_dir, model.__name__, model.objects.filter(video=vid), dry_mode
        )
    # Export also the video itself as json
    export_complement(media_package_dir, "Video", [vid], dry_mode)

    # Store also files linked to Enrichments
    for enrich in Enrichment.objects.filter(video=vid):
        if enrich.document:
            print("  * Copying %s..." % enrich.document.file.path)
            shutil.copy(enrich.document.file.path, media_package_dir)
        if enrich.image:
            print("  * Copying %s..." % enrich.image.file.path)
            shutil.copy(enrich.image.file.path, media_package_dir)

    # Store file complements.
    for file in Document.objects.filter(video=vid):
        print("  * Copying %s..." % file.document.file.path)
        shutil.copy(file.document.file.path, media_package_dir)

    # Store additional tracks (caption / subtitles)
    for track in Track.objects.filter(video=vid):
        print("  * Copying %s..." % track.src.file.path)
        shutil.copy(track.src.file.path, media_package_dir)

    # TODO:
    # - Que faire du fichier CSV ? il faudrait y retirer toutes les
    # lignes supprimées, quitte à faire un nouveau CSV

    # You can decide if you simply copy the video or if you move it to the archive.
    if only_copy:
        copy_archive_to(media_package_dir, vid)
    else:
        move_video_to_archive(media_package_dir, vid, dry_mode)


def archive_and_get_link(slug, sub_fold="tmp"):
    """Generate a zip archive of the video and metadata from the concerned media folder"""
    media_url = getattr(settings, "MEDIA_URL", "/media/")
    media_root = getattr(settings, "MEDIA_ROOT", os.path.join(BASE_DIR, "media"))

    media_package_dir = os.path.join(media_root, sub_fold, slug)
    vid = Video.objects.filter(slug=slug).first()
    archive_pack(str(media_package_dir), "", vid, only_copy=True, dry_mode=False)

    shutil.make_archive(str(media_package_dir), "zip", str(media_package_dir))

    # remove old temp folder
    shutil.rmtree(media_package_dir)

    return media_url + sub_fold + "/" + slug + ".zip"
