"""Esup-Pod recorder utilities."""

import shutil
import time
import os
import uuid
from .models import Recording
from django.conf import settings
from xml.dom import minidom
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

OPENCAST_FILES_DIR = getattr(settings, "OPENCAST_FILES_DIR", "opencast-files")
MEDIA_URL = getattr(settings, "MEDIA_URL", "/media/")


def add_comment(recording_id, comment):
    """Add a comment to a recording."""
    recording = Recording.objects.get(id=recording_id)
    recording.comment = "%s\n%s" % (recording.comment, comment)
    recording.save()


def studio_clean_old_entries():
    """
    Clean up old entries in the opencast folder.

    The function removes entries that are older than 7 days
    from the opencast folder in the media root.
    """
    folder_to_clean = os.path.join(settings.MEDIA_ROOT, OPENCAST_FILES_DIR)
    now = time.time()

    for entry in os.listdir(folder_to_clean):
        entry_path = os.path.join(folder_to_clean, entry)
        if os.stat(entry_path).st_mtime < now - 7 * 86400:
            if os.path.isdir(entry_path):
                shutil.rmtree(entry_path)
            else:
                os.remove(entry_path)


def handle_upload_file(request, element_name, mimetype, tag_name):
    """
    Handle file upload and create XML element in the media package.

    Args:
        request : The HTTP request object.
        element_name (str): The name of the XML element.
        mimetype (str): The mimetype of the uploaded file.
        tag_name (str): The tag name of the media package element.

    Returns:
        HttpResponse: The HTTP response containing the generated XML content.
    """
    id_media = ""
    type_name = ""
    opencast_filename = None
    # tags = "" # not use actually
    id_media = get_id_media(request)
    if request.POST.get("flavor") and request.POST.get("flavor") != "":
        type_name = request.POST.get("flavor")
    media_package_dir = os.path.join(
        settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % id_media
    )

    media_package_content, media_package_file = get_media_package_content(
        media_package_dir, id_media
    )

    if element_name != "attachment":
        if element_name == "track":
            opencast_filename, ext = os.path.splitext(request.FILES["BODY"].name)
            filename = "%s%s" % (type_name.replace("/", "_").replace(" ", ""), ext)
        elif element_name == "catalog":
            filename = request.FILES["BODY"].name

        opencastMediaFile = os.path.join(media_package_dir, filename)
        with open(opencastMediaFile, "wb+") as destination:
            for chunk in request.FILES["BODY"].chunks():
                destination.write(chunk)

        url_text = "%(http)s://%(host)s%(media)sopencast-files/%(id_media)s/%(fn)s" % {
            "http": "https" if request.is_secure() else "http",
            "host": request.get_host(),
            "media": MEDIA_URL,
            "id_media": "%s" % id_media,
            "fn": filename,
        }
    else:
        url_text = ""
    element = create_xml_element(
        media_package_content,
        element_name,
        type_name,
        mimetype,
        url_text,
        opencast_filename,
    )
    media = media_package_content.getElementsByTagName(tag_name)[0]
    media.appendChild(element)

    with open(media_package_file, "w+") as f:
        f.write(media_package_content.toxml())

    return HttpResponse(media_package_content.toxml(), content_type="application/xml")


def get_id_media(request):
    """Extract and returns id_media from the mediaPackage in the request."""
    if (
        request.POST.get("mediaPackage") != ""
        and request.POST.get("mediaPackage") != "{}"
    ):
        mediaPackage = request.POST.get("mediaPackage")
        # XML result to parse
        xmldoc = minidom.parseString(mediaPackage)
        # Get the id_media
        id_media = xmldoc.getElementsByTagName("mediapackage")[0].getAttribute("id")
        return id_media
    return None


def get_media_package_content(media_package_dir, id_media):
    """Retrieve media package content & media package file by parsing an XML file."""
    media_package_file = os.path.join(media_package_dir, "%s.xml" % id_media)
    media_package_content = minidom.parse(media_package_file)  # parse an open file
    mediapackage = media_package_content.getElementsByTagName("mediapackage")[0]
    if mediapackage.getAttribute("id") != id_media:
        raise PermissionDenied("Access denied: ID mismatch.")

    return media_package_content, media_package_file


def create_xml_element(
    media_package_content,
    element_name,
    type_name,
    mimetype,
    url_text,
    opencast_filename=None,
):
    """
    Create an XML element with the specified attributes.

    Args:
        media_package_content: The media package content.
        element_name (str): The name of the XML element.
        type_name (str): The type of the XML element.
        mimetype (str): The mimetype of the XML element.
        url_text (str): The URL text of the XML element.
        opencast_filename : defaults to None.

    Returns:
        element : The created XML element.
    """
    element = media_package_content.createElement(element_name)
    element.setAttributeNode(media_package_content.createAttribute("id"))
    element.setAttributeNode(media_package_content.createAttribute("type"))
    element.setAttribute("id", "%s" % uuid.uuid4())
    element.setAttribute("type", type_name)
    if element_name == "track":
        element.setAttributeNode(media_package_content.createAttribute("filename"))
        element.setAttribute("filename", opencast_filename)
    mimetype_element = media_package_content.createElement("mimetype")
    mimetype_element.appendChild(media_package_content.createTextNode(mimetype))
    element.appendChild(mimetype_element)
    url = media_package_content.createElement("url")
    url.appendChild(media_package_content.createTextNode(url_text))
    element.appendChild(url)
    if element_name == "track":
        live = media_package_content.createElement("live")
        live.appendChild(media_package_content.createTextNode("false"))
        element.appendChild(live)

    return element
