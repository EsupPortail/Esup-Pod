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
    """Adds a comment to a recording."""
    recording = Recording.objects.get(id=recording_id)
    recording.comment = "%s\n%s" % (recording.comment, comment)
    recording.save()


def studio_clean_old_files():
    """
    Cleans up old files in the "opencast-files" folder.
    The function removes files that are older than 7 days
    from the "opencast-files" folder in the media root.
    """
    folder_to_clean = os.path.join(settings.MEDIA_ROOT, "opencast-files")
    now = time.time()

    for f in os.listdir(folder_to_clean):
        f = os.path.join(folder_to_clean, f)
        if os.stat(f).st_mtime < now - 7 * 86400:
            if os.path.isfile(f):
                os.remove(f)


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
    idMedia = ""
    type_name = ""
    opencast_filename = None
    # tags = "" # not use actually
    idMedia = get_id_media(request)
    if request.POST.get("flavor") and request.POST.get("flavor") != "":
        type_name = request.POST.get("flavor")
    mediaPackage_dir = os.path.join(
        settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
    )

    mediaPackage_content, mediaPackage_file = get_media_package_content(
        mediaPackage_dir, idMedia
    )

    if element_name != "attachment":
        if element_name == "track":
            opencast_filename, ext = os.path.splitext(request.FILES["BODY"].name)
            filename = "%s%s" % (type_name.replace("/", "_").replace(" ", ""), ext)
        elif element_name == "catalog":
            filename = request.FILES["BODY"].name

        opencastMediaFile = os.path.join(mediaPackage_dir, filename)
        with open(opencastMediaFile, "wb+") as destination:
            for chunk in request.FILES["BODY"].chunks():
                destination.write(chunk)

        url_text = "%(http)s://%(host)s%(media)sopencast-files/%(idMedia)s/%(fn)s" % {
            "http": "https" if request.is_secure() else "http",
            "host": request.get_host(),
            "media": MEDIA_URL,
            "idMedia": "%s" % idMedia,
            "fn": filename,
        }
    else:
        url_text = ""
    element = create_xml_element(
        mediaPackage_content,
        element_name,
        type_name,
        mimetype,
        url_text,
        opencast_filename,
    )
    media = mediaPackage_content.getElementsByTagName(tag_name)[0]
    media.appendChild(element)

    with open(mediaPackage_file, "w+") as f:
        f.write(mediaPackage_content.toxml())

    return HttpResponse(mediaPackage_content.toxml(), content_type="application/xml")


def get_id_media(request):
    """
    Extracts and returns idMedia from the mediaPackage in the request.
    """
    if (
        request.POST.get("mediaPackage") != ""
        and request.POST.get("mediaPackage") != "{}"
    ):
        mediaPackage = request.POST.get("mediaPackage")
        # XML result to parse
        xmldoc = minidom.parseString(mediaPackage)
        # Get the idMedia
        idMedia = xmldoc.getElementsByTagName("mediapackage")[0].getAttribute("id")
        return idMedia
    return None


def get_media_package_content(mediaPackage_dir, idMedia):
    """
    Retrieve the media package content and the media package file by parsing an XML file.
    """
    mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
    mediaPackage_content = minidom.parse(mediaPackage_file)  # parse an open file
    mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
    if mediapackage.getAttribute("id") != idMedia:
        raise PermissionDenied("Access denied: ID mismatch.")

    return mediaPackage_content, mediaPackage_file


def create_xml_element(
    mediaPackage_content,
    element_name,
    type_name,
    mimetype,
    url_text,
    opencast_filename=None,
):
    """
    Create an XML element with the specified attributes.

    Args:
        mediaPackage_content: The media package content.
        element_name (str): The name of the XML element.
        type_name (str): The type of the XML element.
        mimetype (str): The mimetype of the XML element.
        url_text (str): The URL text of the XML element.
        opencast_filename : defaults to None.

    Returns:
        element : The created XML element.
    """
    element = mediaPackage_content.createElement(element_name)
    element.setAttributeNode(mediaPackage_content.createAttribute("id"))
    element.setAttributeNode(mediaPackage_content.createAttribute("type"))
    element.setAttribute("id", "%s" % uuid.uuid4())
    element.setAttribute("type", type_name)
    if element_name == "track":
        element.setAttributeNode(mediaPackage_content.createAttribute("filename"))
        element.setAttribute("filename", opencast_filename)
    mimetype_element = mediaPackage_content.createElement("mimetype")
    mimetype_element.appendChild(mediaPackage_content.createTextNode(mimetype))
    element.appendChild(mimetype_element)
    url = mediaPackage_content.createElement("url")
    url.appendChild(mediaPackage_content.createTextNode(url_text))
    element.appendChild(url)
    if element_name == "track":
        live = mediaPackage_content.createElement("live")
        live.appendChild(mediaPackage_content.createTextNode("false"))
        element.appendChild(live)

    return element
