"""Esup-Pod recorder plugin 'type_studio'."""

import datetime
import logging
import os
import threading
from xml.dom.minidom import Text as Dom_text
from defusedxml.minidom import parse as dom_parse

from django.conf import settings
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from pod.video.models import Video, get_storage_path_video
from pod.video_encode_transcript import encode
from ..utils import add_comment, studio_clean_old_entries
from ...live.models import Event
from ...settings import BASE_DIR

DEFAULT_RECORDER_TYPE_ID = getattr(settings, "DEFAULT_RECORDER_TYPE_ID", 1)
ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")
ENCODE_STUDIO = getattr(settings, "ENCODE_STUDIO", "start_encode_studio")
MEDIA_URL = getattr(settings, "MEDIA_URL", "/media/")
MEDIA_ROOT = getattr(settings, "MEDIA_ROOT", os.path.join(BASE_DIR, "media"))
OPENCAST_FILES_DIR = getattr(settings, "OPENCAST_FILES_DIR", "opencast-files")
# Possible value are "mid", "piph" or "pipb"
OPENCAST_DEFAULT_PRESENTER = getattr(settings, "OPENCAST_DEFAULT_PRESENTER", "mid")

log = logging.getLogger(__name__)


def process(recording) -> None:
    log.info("START PROCESS OF RECORDING %s" % recording)
    threading.Thread(target=encode_recording, args=[recording], daemon=True).start()


def save_basic_video(recording, video_src) -> Video:
    # Save & encode one video corresponding to the recording without cut
    # We don't generate an intermediate video
    recorder = recording.recorder
    video = Video()
    # Video title corresponds to recording title
    video.title = recording.title
    video.owner = recording.user
    # Video type
    video.type = recorder.type
    # Video management
    storage_path = get_storage_path_video(video, os.path.basename(video_src))
    dt = str(datetime.datetime.now()).replace(":", "-")
    name, ext = os.path.splitext(os.path.basename(video_src))
    ext = ext.lower()
    video.video = os.path.join(
        os.path.dirname(storage_path), slugify(name) + "_" + dt.replace(" ", "_") + ext
    )
    # Move source file to destination
    os.makedirs(os.path.dirname(video.video.path), exist_ok=True)
    os.rename(video_src, video.video.path)
    video.save()

    # Add any additional owners
    video.additional_owners.add(*recorder.additional_users.all())
    # Private access (draft mode)
    video.is_draft = recorder.is_draft
    # Restricted access (possibly to groups or by password)
    video.is_restricted = recorder.is_restricted
    video.restrict_access_to_groups.add(*recorder.restrict_access_to_groups.all())
    video.password = recorder.password
    # Add the possible channels
    video.channel.add(*recorder.channel.all())
    # Add the possible themes
    video.theme.add(*recorder.theme.all())
    # Add any disciplines
    video.discipline.add(*recorder.discipline.all())
    # Language choice
    video.main_lang = recorder.main_lang
    # Cursus
    video.cursus = recorder.cursus
    # Tags
    video.tags = recorder.tags.get_tag_list()
    # Transcription
    if getattr(settings, "USE_TRANSCRIPTION", False):
        video.transcript = recorder.transcript
    # Licence
    video.licence = recorder.licence
    # Allow downloading
    video.allow_downloading = recorder.allow_downloading
    # Is 360
    video.is_360 = recorder.is_360
    # Disable comments
    video.disable_comment = recorder.disable_comment
    # Add sites
    video.sites.add(*recorder.sites.all())
    # Finally save
    video.save()

    # Rename the XML file
    # os.rename(recording.source_file, recording.source_file + "_treated")

    studio_clean_old_entries()

    return video


def generate_intermediate_video(recording, videos, clip_begin, clip_end, presenter):
    # Video file output: in the same directory as the XML file
    # And with the same name .mp4
    video_output = recording.source_file.replace(".xml", ".mp4")
    subtime = get_subtime(clip_begin, clip_end)
    encode_studio = getattr(encode, ENCODE_STUDIO)
    encode_studio(recording.id, video_output, videos, subtime, presenter)


def get_subtime(clip_begin, clip_end) -> str:
    subtime = ""
    if clip_begin:
        subtime += "-ss %s " % str(clip_begin)
    if clip_end:
        subtime += "-to %s " % str(clip_end)
    return subtime


"""
def encode_recording_id(recording_id):
    recording = Recording.objects.get(id=recording_id)
    encode_recording(recording)
"""


def encode_recording(recording):
    recording.comment = ""
    recording.save()
    add_comment(recording.id, "Start at %s\n--\n" % datetime.datetime.now())

    try:
        xml_doc = dom_parse(recording.source_file)
    except KeyError as e:
        add_comment(recording.id, "Error: %s" % e)
        return -1
    videos = getElementsByName(xml_doc, "track")
    catalogs = getElementsByName(xml_doc, "catalog")
    att_presenter = getAttributeByName(xml_doc, "mediapackage", "presenter")
    presenter = (
        att_presenter
        if (att_presenter in ["mid", "piph", "pipb"])
        else OPENCAST_DEFAULT_PRESENTER
    )

    clip_begin, clip_end, event_id = extract_infos_from_catalog(catalogs, recording)

    if clip_begin or clip_end or len(videos) > 1:
        msg = "*** generate_intermediate_video (%s) %s ***" % (
            videos[0].get("type"),
            videos[0].get("src"),
        )
        add_comment(recording.id, msg)
        generate_intermediate_video(recording, videos, clip_begin, clip_end, presenter)
    else:
        msg = "*** Management of basic video file (%s) %s ***" % (
            videos[0].get("type"),
            videos[0].get("src"),
        )
        add_comment(recording.id, msg)

        # create Video using Recording properties
        video = save_basic_video(
            recording,
            os.path.join(MEDIA_ROOT, OPENCAST_FILES_DIR, videos[0].get("src")),
        )

        # link Video to Event
        link_video_to_event(recording, video, event_id)

        # encode the video
        encode_video = getattr(encode, ENCODE_VIDEO)
        encode_video(video.id)


def extract_infos_from_catalog(catalogs, recording):
    """Extract event_id, clip_begin and clip_end from xml.
    Update Recording if title or creator are defined.
    """
    event_id = ""
    clip_begin = None
    clip_end = None

    for catalog in catalogs:
        # check if file exists before parsing
        try:
            xml_doc = dom_parse(catalog.get("src"))
        except FileNotFoundError as e:
            add_comment(recording.id, "Error: %s" % e)
            continue

        # if title or creator defined, update Recording
        if catalog.get("type") == "dublincore/episode":
            change_title(recording, getElementValueByName(xml_doc, "dcterms:title"))
            change_user(recording, getElementValueByName(xml_doc, "dcterms:creator"))
            event_id = getElementValueByName(xml_doc, "dcterms:course")

        # get begin and end if defined
        elif catalog.get("type") == "smil/cutting":
            default_begin = getAttributeByName(xml_doc, "video", "clipBegin")
            default_end = getAttributeByName(xml_doc, "video", "clipEnd")
            clip_begin = (
                str(round(float(default_begin.replace("s", "")), 2))
                if default_begin
                else None
            )
            clip_end = (
                str(round(float(default_end.replace("s", "")), 2))
                if default_end
                else None
            )
    return clip_begin, clip_end, event_id


def change_title(recording, title) -> None:
    """
    Change recording title.

    Args:
        recording (Recording): The recording.
        title (str): The title to set.
    """
    if title != "":
        recording.title = title
        recording.save()


def change_user(recording, username) -> None:
    """
    Change recording user.

    Args:
        recording (Recording): The recording.
        username (str): The username to set.
    """
    user = User.objects.filter(username=username).first() if username != "" else None
    if user:
        recording.user = user
        recording.save()


def link_video_to_event(recording, video, event_id) -> None:
    """Associate the Video to the Event.
    Add Event's creator as additional owner of the video.
    Set same description, type and restrictions.
    """
    if isinstance(event_id, int) or event_id.isdigit():
        msg = "*** Associating Event '%s' to Video ***" % (event_id,)
        add_comment(recording.id, msg)
        evt = Event.objects.filter(id=int(event_id)).first()

        if evt is not None:
            evt.videos.add(video)
            evt.save()

            video.description = evt.description
            video.type = evt.type
            video.is_draft = evt.is_draft
            if video.owner != evt.owner:
                video.additional_owners.add(evt.owner)
            if evt.is_draft:
                video.password = None
                video.is_restricted = False
                video.restrict_access_to_groups.clear()
            else:
                video.password = evt.password
                video.is_restricted = evt.is_restricted
                video.restrict_access_to_groups.set(evt.restrict_access_to_groups.all())

            video.save()


def getAttributeByName(xml_doc, tag_name, attribute):
    """
    Retrieves the value of a specified attribute from the first element with the given tag name in the xml.

    Args:
        xml_doc (minidom.Document): The xml doc to search.
        tag_name (str): The tag name of the element.
        attribute (str): The name of the attribute to get.

    Returns:
        str or None: The value of the specified attribute, or None if the attribute or element is not found.
    """
    elements = xml_doc.getElementsByTagName(tag_name)
    if elements and len(elements) > 0:
        attr = elements[0].getAttribute(attribute)
        # don't know why values with 'e' are discarded
        if attr and "e" not in attr:
            return attr
    return None


def getElementsByName(xml_doc, name) -> list:
    """
    Extracts from xml document the elements with tag name.
    And returns type and path of a file for all elements having attributes 'url' and 'type'.

    Args:
        xml_doc (minidom.Document): The XML document to search for elements.
        name (str): The tag name of the elements to retrieve.

    Returns:
        list: A list of dictionaries representing the extracted elements.
        Each dictionary contains 'type' and 'src' as keys
    """
    elements = []

    # Check if the specified tag name is present in the XML document
    tag_elements = xml_doc.getElementsByTagName(name)
    if not tag_elements:
        print(f"Tag name '{name}' not found in the xml")
        return elements

    for element in tag_elements:
        elements_url = element.getElementsByTagName("url")

        # Check if at least one <url> element is present
        if elements_url:
            element_url = elements_url[0]

            if element_url.firstChild and element_url.firstChild.data:
                url_data = element_url.firstChild.data
                if MEDIA_URL in url_data:
                    element_path = url_data[url_data.index(MEDIA_URL) + len(MEDIA_URL) :]
                    src = os.path.join(MEDIA_ROOT, element_path)

                    # Check if the file exists
                    if os.path.isfile(src):
                        elements.append(
                            {"type": element.getAttribute("type"), "src": src}
                        )

    return elements


def getElementValueByName(xml_doc, name) -> str:
    """
    Get the value of a xml element.

    Args:
        xml_doc(minidom.Element): parsed minidom file
        name(str): element name
    Returns:
        str: the value of xml element or empty string
    """
    list_elements = xml_doc.getElementsByTagName(name)
    if not list_elements:
        print(f"element {name} not found in xml")
        return ""
    element = list_elements[0]
    if not isinstance(element.firstChild, Dom_text):
        print(f"element {name} not a minidom.Text")
        return ""
    return element.firstChild.data
