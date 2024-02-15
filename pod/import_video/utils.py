"""Esup-Pod meeting and import_video utils."""

import json
import os
import requests
import shutil

from datetime import datetime as dt
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from html.parser import HTMLParser
from pod.video.models import Video
from pod.video.models import Type
from urllib.parse import parse_qs, urlparse
from requests import Session

MAX_UPLOAD_SIZE_ON_IMPORT = getattr(settings, "MAX_UPLOAD_SIZE_ON_IMPORT", 4)

DEFAULT_TYPE_ID = getattr(settings, "DEFAULT_TYPE_ID", 1)

VIDEO_ALLOWED_EXTENSIONS = getattr(
    settings,
    "VIDEO_ALLOWED_EXTENSIONS",
    (
        "3gp",
        "avi",
        "divx",
        "flv",
        "m2p",
        "m4v",
        "mkv",
        "mov",
        "mp4",
        "mpeg",
        "mpg",
        "mts",
        "wmv",
        "mp3",
        "ogg",
        "wav",
        "wma",
        "webm",
        "ts",
    ),
)

VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")


def secure_request_for_upload(request):
    """Check that the request is correct for uploading a recording.

    Args:
        request (Request): HTTP request

    Raises:
        ValueError: if bad data
    """
    # Source_url and recording_name are necessary
    if request.POST.get("source_url") == "" or request.POST.get("recording_name") == "":
        msg = {}
        msg["error"] = _("Unable to upload the video to Pod")
        msg["message"] = _("No URL found / No recording name")
        msg["proposition"] = _(
            "Try changing the record type or address for this recording"
        )
        raise ValueError(msg)


def parse_remote_file(session: Session, source_html_url: str):
    """Parse the remote HTML file on the BBB server.

    Args:
        session (Session) : session useful to achieve requests (and keep cookies between)
        source_html_url (String): URL to parse

    Raises:
        ValueError: exception raised if no video found in this URL

    Returns:
        String: name of the video found in the page
    """
    try:
        response = session.get(source_html_url)
        if response.status_code != 200:
            msg = {}
            msg["error"] = _(
                "The HTML file for this recording was not found on the server."
            )
            # If we want to display the 404/500... page to the user
            # msg["message"] = response.content.decode("utf-8")
            msg["message"] = _("Error number: %s") % response.status_code
            raise ValueError(msg)

        # Parse the BBB video HTML file
        parser = create_parser(response)

        # Video file found
        if parser.video_check:
            # Security check about extensions
            extension = parser.video_file.split(".")[-1].lower()
            if extension not in VIDEO_ALLOWED_EXTENSIONS:
                msg = {}
                msg["error"] = _(
                    "The video file for this recording was not found in the HTML file."
                )
                msg["message"] = _("The found file is not a valid video.")
                raise ValueError(msg)

            # Returns the name of the video (if necessary, title is parser.title)
            return parser.video_file
        else:
            msg = ""
            # Useful tips for Pod links
            if (
                source_html_url.find("/video/") != -1
                or source_html_url.find("/media/videos/") != -1
            ):
                msg = _(
                    "In the case of a video from a Pod platform, please enter "
                    "the source file address, available in the video edition."
                )
            raise ValueError("<div role='alert' class='alert alert-info'>%s</div>" % msg)
    except Exception as exc:
        msg = {}
        msg["error"] = _(
            "The video file for this recording was not found in the HTML file."
        )
        msg["message"] = mark_safe(str(exc))
        raise ValueError(msg)


def create_parser(response):
    """Parse the BBB video HTML file and manage its encoding."""
    parser = video_parser()
    if response.encoding == "ISO-8859-1":
        parser.feed(response.text.encode("ISO-8859-1").decode("utf-8"))
    else:
        parser.feed(response.text)
    return parser


def manage_recording_url(source_url: str, video_file_add: str) -> str:
    """Generate the BBB video URL.

    See more explanations in manage_download() function.

    Args:
        source_url (String): Source file URL
        video_file_add (String): Name of the video file to add to the URL

    Returns:
        String: good URL of a BBB recording video or of the video file
    """
    try:
        bbb_playback_video = "/video/"
        url = urlparse(source_url)
        if url.query:
            query = parse_qs(url.query, keep_blank_values=True)
            if query["token"][0]:
                # 1st case (ex: ESR URL), URL likes (ex for ESR URL:)
                # https://_site_/recording/_recording_id/video?token=_token_
                # Get recording unique identifier
                recording_id = url.path.split("/")[2]
                # Define 2nd video URL
                # Ex: https://_site_/video/_recording_id/video-0.m4v
                source_video_url = "%s://%s%s%s/%s" % (
                    url.scheme,
                    url.netloc,
                    bbb_playback_video,
                    recording_id,
                    video_file_add,
                )
            else:
                # 2nd case (BBB URL standard without token)
                source_video_url = source_url + video_file_add
            return source_video_url
        else:
            return source_url + video_file_add
    except Exception:
        return source_url + video_file_add


def manage_download(
    session: Session,
    source_url: str,
    video_file_add: str,
    dest_file: str
) -> str:
    """Manage the download of a BBB video file.

    2 possibilities :
     - Download BBB video file directly.
     - Download BBB video file where source URL is protected by a single-use token.
    In such a case, 2 requests are made, using the same session.
    A cookie is set at the first request (the parsing one, called before)
    and used for the second one.

    This function is a simple shortcut to the calls of manage_recording_url
    and download_video_file.

    Args:
        session (Session) : Session useful to achieve requests (and keep cookies between)
        source_url (String): Source file URL
        video_file_add (String): Name of the video file to add to the URL
        dest_file (String): Destination file of the Pod video

    Returns:
        source_video_url (String) : video source file URL

    Raises:
        ValueError: if impossible download
    """
    try:
        source_video_url = manage_recording_url(source_url, video_file_add)
        download_video_file(session, source_video_url, dest_file)
        return source_video_url
    except Exception as exc:
        raise ValueError(mark_safe(str(exc)))


def download_video_file(session: Session, source_video_url: str, dest_file: str):
    """Download video file.

    Args:
        session (Session) : Session useful to achieve requests (and keep cookies between)
        source_video_url (String): Video file URL
        dest_file (String): Destination file of the Pod video

    Raises:
        ValueError: if impossible download
    """
    # Check if video file exists
    try:
        with session.get(source_video_url, timeout=(10, 180), stream=True) as response:
            # Can be useful to debug
            # print(session.cookies.get_dict())
            if response.status_code != 200:
                raise ValueError(
                    _("The video file for this recording " "was not found on the server.")
                )

            with open(dest_file, "wb+") as file:
                # Total size, in bytes, from response header
                # total_size = int(response.headers.get('content-length', 0))
                # Other possible methods
                # Method 1 : iterate over every chunk and calculate % of total
                # for chunk in response.iter_content(chunk_size=1024*1024):
                #    file.write(chunk)
                # Method 2 : Binary download
                # file.write(response.content)
                # Method 3 : The fastest
                shutil.copyfileobj(response.raw, file)
    except Exception as exc:
        raise ValueError(mark_safe(str(exc)))


def save_video(
    user: User,
    dest_path: str,
    recording_name: str,
    description: str,
    date_evt=None
):
    """Save and encode the Pod video file.

    Args:
        user (User): User who saved the video
        dest_path (String): Destination path of the Pod video
        recording_name (String): Recording name
        description (String): Description added to the Pod video
        date_evt (Datetime, optional): Event date. Default to None

    Raises:
        ValueError: if impossible creation
    """
    try:
        video = Video.objects.create(
            video=dest_path,
            title=recording_name,
            owner=user,
            description=description,
            is_draft=True,
            type=Type.objects.get(id=DEFAULT_TYPE_ID),
            date_evt=date_evt,
        )

        video.launch_encode = True
        video.save()
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to create the Pod video")
        msg["message"] = mark_safe(str(exc))
        raise ValueError(msg)


def check_url_exists(source_url: str) -> bool:
    """Check that the source URL exists.

    Args:
        source_url (String): Source URL

    Returns:
        Boolean: URL exists (True) or not (False)
    """
    try:
        response = requests.head(source_url, timeout=2)
        if response.status_code < 400:
            return True
        else:
            return False
    except Exception:
        return False


def verify_video_exists_and_size(video_url: str):
    """Check that the video file exists and its size does not exceed the limit.

    Args:
        video_url (String): Video source URL

    Raises:
        ValueError: exception raised if no video found in this URL or video oversized
    """
    try:
        response = requests.head(video_url, timeout=2)
        if response.status_code < 400:
            # Video file size
            size = int(response.headers.get("Content-Length", "0"))
            check_video_size(size)
        else:
            msg = {}
            msg["error"] = _("No video file found.")
            msg["message"] = _("No video file found for this address.")
            raise ValueError(msg)
    except Exception:
        msg = {}
        msg["error"] = _("No video file found.")
        msg["message"] = _("No video file found for this address.")
        raise ValueError(msg)


def check_video_size(video_size: int):
    """Check that the video file size does not exceed the limit.

    Args:
        video_size (Integer): Video file size

    Raises:
        ValueError: exception raised if video oversized
    """
    size_max = int(MAX_UPLOAD_SIZE_ON_IMPORT) * 1024 * 1024 * 1024
    if MAX_UPLOAD_SIZE_ON_IMPORT != 0 and video_size > size_max:
        msg = {}
        msg["error"] = _("File too large.")
        msg["message"] = (
            _("The size of the video file exceeds the maximum allowed value, %s Gb.")
            % MAX_UPLOAD_SIZE_ON_IMPORT
        )
        raise ValueError(msg)


def check_source_url(source_url: str):  # noqa: C901
    """Check the source URL to identify the used platform.

    Platforms managed :
     - Mediacad platform (Médiathèque académique) : rewrite source URL if required
     and manage JSON API.
     - Old BigBlueButton : source URL for old BBB presentation playback
    """
    base_url = ""
    media_id = ""
    format = ""
    url_api_video = ""
    source_video_url = ""
    platform = ""
    platform_type = None
    # Source URL array
    array_url = source_url.split("/")
    # Parse for parameters
    url = urlparse(source_url)
    if url.query:
        query = parse_qs(url.query, keep_blank_values=True)

    try:
        if source_url.find("/download.php?t=") != -1 and url.query:
            # Mediacad direct video link (with ##format## in: mp4, source, webm)
            # ##mediacadBaseUrl##/download.php?t=##token##&e=##format##&m=##mediaId##
            base_url = source_url[: source_url.find("/download.php?t=")]
            media_id = query["m"][0]
            format = query["e"][0].replace("source", "mp4")
            # Force to download mp4 file if source
            source_video_url = source_url.replace("&e=source", "&e=mp4")
            platform = "Mediacad"
        elif (
            source_url.find("/d/d") != -1
            and source_url.find("/default/media/display/m") != -1
        ):
            # Mediacad direct video link (with ##format## in: mp4, source, webm)
            # ##mediacadBaseUrl##/default/media/display/m/##mediaId##/e/##format##/d/d
            base_url = source_url[: source_url.find("/default/media/display/m/")]
            media_id = array_url[-5]
            format = array_url[-3].replace("source", "mp4")
            # Force to download mp4 file if source
            source_video_url = source_url.replace("/e/source", "/e/mp4")
            platform = "Mediacad"
        elif source_url.find("/d/m/e") != -1:
            # Mediacad direct video link (with ##format## in: mp4, source, webm)
            # ##mediacadBaseUrl##/m/##mediaId##/d/m/e/##format##
            base_url = source_url[: source_url.find("/m/")]
            media_id = array_url[-5]
            format = array_url[-1].replace("source", "mp4")
            source_video_url = source_url.replace("/e/source", "/e/mp4")
            platform = "Mediacad"
        elif source_url.find("/default/media/display/") != -1:
            # Mediacad page link
            # ##mediacadBaseUrl##/default/media/display/m/##mediaId##
            # ##mediacadBaseUrl##/default/media/display/page/1/sort/date/m/##mediaId##
            base_url = source_url[: source_url.find("/default/media/display/")]
            media_id = array_url[-1]
            format = "mp4"
            source_video_url = source_url + "/e/mp4/d/d"
            platform = "Mediacad"
        elif source_url.find("/m/") != -1:
            # Mediacad page link
            # ##mediacadBaseUrl##/m/##mediaId##
            base_url = source_url[: source_url.find("/m/")]
            media_id = array_url[-1]
            format = "mp4"
            # Download possible on all Mediacad platform with such an URL
            source_video_url = "%s/default/media/display/m/%s/e/mp4/d/d" % (
                base_url,
                media_id,
            )
            platform = "Mediacad"
        elif source_url.find("/playback/presentation/2.0/playback.html?") != -1:
            # Old BBB 2.x (<2.3) presentation link
            # Conversion from
            # https://xxx/playback/presentation/2.0/playback.html?meetingId=ID
            # to https://xxx/playback/presentation/2.3/ID?meetingId=ID
            media_id = array_url[-1]
            source_video_url = source_url.replace(
                "/2.0/playback.html", "/2.3/" + media_id
            ).replace("playback.html?meetingId=", "")
            format = "webm"
            platform = "BBB_Presentation"
        elif source_url.find("/playback/presentation/2.3/") != -1:
            # Old BBB 2.3 presentation link : no conversion needed
            source_video_url = source_url
            format = "webm"
            platform = "BBB_Presentation"

        # Platform's URL identified
        if platform == "Mediacad":
            # Mediacad API (JSON format) is available at :
            # ##mediacadBaseUrl##/default/media/display/m/##mediaId##/d/j
            url_api_video = "%s/default/media/display/m/%s/d/j" % (base_url, media_id)
            # Platform type
            platform_type = TypeSourceURL(
                platform, source_video_url, format, url_api_video
            )
        if platform == "BBB_Presentation":
            # Platform type: older BBB, format presentation
            platform_type = TypeSourceURL(
                platform, source_video_url, format, ""
            )

        return platform_type
    except Exception as exc:
        msg = {}
        msg["error"] = _("The video file for this recording was not found.")
        msg["message"] = mark_safe(str(exc))
        raise ValueError(msg)


def define_dest_file_and_path(user: User, id: str, extension: str):
    """Define standard destination filename and path for an external recording."""
    # Set a discriminant
    discrim = dt.now().strftime("%Y%m%d%H%M%S")
    dest_file = os.path.join(
        settings.MEDIA_ROOT,
        VIDEOS_DIR,
        user.owner.hashkey,
        os.path.basename("%s-%s.%s" % (discrim, id, extension)),
    )
    dest_path = os.path.join(
        VIDEOS_DIR,
        user.owner.hashkey,
        os.path.basename("%s-%s.%s" % (discrim, id, extension)),
    )
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    return dest_file, dest_path


def check_file_exists(source: str) -> bool:
    """Check that a local file exists."""
    if os.path.exists(source):
        return True
    else:
        return False


def move_file(source: str, destination: str):
    """Move a file from a source to another destination."""
    try:
        # Ensure that the source file exists
        if not check_file_exists(source):
            print(f"The source file '{source}' does not exist.")
            return

        # Move the file to the destination directory
        shutil.move(source, destination)
    except Exception as e:
        print(f"Error moving the file: {e}")


class TypeSourceURL:
    """Manage external recording source URL.

    Define context, and platform used, about a source URL.
    """

    # Source URL type, like Mediacad, Pod...
    type = ""
    # Source video file URL
    url = ""
    # Video extension (mp4, webm...)
    extension = ""
    # API URL if supplied
    api_url = ""

    def __init__(self, type, url, extension, api_url):
        """Initialize."""
        self.type = type
        self.url = url
        self.extension = extension
        self.api_url = api_url


class video_parser(HTMLParser):
    """Useful to parse the BBB Web page and search for video file.

    Used to parse BBB 2.6+ URL for video recordings.
    Args:
        HTMLParser (_type_): _description_
    """

    def __init__(self):
        """Initialize video parser."""
        super().__init__()
        self.reset()
        # Variables for title
        self.title_check = False
        self.title = ""
        # Variables for video file
        self.video_check = False
        self.video_file = ""
        self.video_type = ""

    def handle_starttag(self, tag, attrs):
        """Parse BBB Web page and search video file."""
        attrs = dict(attrs)
        # Search for source tag
        if tag == "source":
            # Found the line. Managed format :
            # attrs = {'src': 'video-0.m4v', 'type': 'video/mp4'}
            # print("video line : %s" % attrs)
            self.video_check = True
            self.video_file = attrs.get("src", "")
            self.video_type = attrs.get("type", "")
        # Search for title tag
        if tag == "title":
            # Found the title line
            self.title_check = True

    def handle_data(self, data):
        """Search for title tag."""
        if self.title_check:
            # Get the title that corresponds to recording's name
            self.title = data
            self.title_check = False


class StatelessRecording:
    """Recording model, not saved in database.

    Useful to manage :
     - internal (meeting module) recordings
     - external (import_video module) recordings
    for the views.
    """

    id = ""
    name = ""
    state = ""
    startTime = ""
    endTime = ""
    # Type
    type = ""
    # Rights
    canUpload = False
    canDelete = False
    # User that has uploaded this recording to Pod
    uploadedToPodBy = ""
    # Presentation playback URL
    presentationUrl = ""
    # Video playback URL, used as the source URL for the video file
    videoUrl = ""

    def __init__(self, id, name, state):
        """Initiliaze."""
        self.id = id
        self.name = name
        self.state = state

    def get_start_time(self):
        """Return BBB epoch in milliseconds."""
        return dt.fromtimestamp(float(self.startTime) / 1000)

    def get_end_time(self):
        """Return BBB epoch in milliseconds."""
        return dt.fromtimestamp(float(self.endTime) / 1000)

    def get_duration(self):
        """Return duration."""
        return str(self.get_end_time() - self.get_start_time()).split(".")[0]

    def to_json(self):
        """Return recording data (without uploadedToPodBy) in JSON format."""
        exclusion_list = ["uploadedToPodBy"]
        return json.dumps(
            {
                key: value
                for key, value in self.__dict__.items()
                if key not in exclusion_list
            }
        )
