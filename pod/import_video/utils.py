"""Utils for Meeting and Import_video module."""
import requests
import shutil

from datetime import datetime as dt
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from html.parser import HTMLParser
from pod.video.models import Video
from pod.video.models import Type
from urllib.parse import parse_qs, urlparse

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
        msg["error"] = _("Impossible to upload to Pod the video")
        msg["message"] = _("No URL found / No recording name")
        msg["proposition"] = _(
            "Try changing the record type or address for this recording"
        )
        raise ValueError(msg)


def manage_recording_url(video_url):
    """Verify the video URL and change it, if necessary (for ESR URL).

    Args:
        video_url (String): URL to verify

    Returns:
        String: good URL of a BBB recording video
    """
    try:
        bbb_playback_video = "/playback/video/"
        url = urlparse(video_url)
        if url.query:
            query = parse_qs(url.query, keep_blank_values=True)
            if query["token"][0]:
                # For ESR URL
                # Ex: https://_site_/recording/_uid_/video?token=_token_
                # Get recording unique identifier
                uid = url.path.split("/")[2]
                # New video URL
                # Ex: https://_site_/playback/video/_uid_/
                return url.scheme + "://" + url.netloc + bbb_playback_video + uid + "/"
            else:
                return video_url
        else:
            return video_url
    except Exception:
        return video_url


def parse_remote_file(source_html_url):
    """Parse the remote HTML file on the BBB server.

    Args:
        source_html_url (String): URL to parse

    Raises:
        ValueError: exception raised if no video found in this URL

    Returns:
        String: name of the video found in the page
    """
    try:
        response = requests.get(source_html_url)
        if response.status_code != 200:
            msg = {}
            msg["error"] = _(
                "The HTML file for this recording was not found on the BBB server."
            )
            # If we want to display the 404/500... page to the user
            # msg["message"] = response.content.decode("utf-8")
            msg["message"] = "Error number : %s" % response.status_code
            raise ValueError(msg)

        # Parse the BBB video HTML file
        parser = video_parser()
        # Manage the encoding
        if response.encoding == "ISO-8859-1":
            parser.feed(response.text.encode("ISO-8859-1").decode("utf-8"))
        else:
            parser.feed(response.text)

        # Video file found
        if parser.video_check:
            # Security check about extensions
            extension = parser.video_file.split(".")[-1].lower()
            if extension not in VIDEO_ALLOWED_EXTENSIONS:
                msg = {}
                msg["error"] = _(
                    "The video file for this recording was not " "found in the HTML file."
                )
                msg["message"] = _("The found file is not a valid video.")
                raise ValueError(msg)

            # Returns the name of the video (if necessary, title is parser.title)
            return parser.video_file
        else:
            msg = {}
            msg["error"] = _(
                "The video file for this recording was not found in the HTML file."
            )
            msg["message"] = _("No video file found")
            raise ValueError(msg)
    except Exception as exc:
        msg = {}
        msg["error"] = _(
            "The video file for this recording was not found in the HTML file."
        )
        msg["message"] = str(exc)
        raise ValueError(msg)


def download_video_file(source_video_url, dest_file):
    """Download BBB video file.

    Args:
        source_video_url (String): Video file URL
        dest_file (String): Destination file of the Pod video

    Raises:
        ValueError: if impossible download
    """
    # Check if video file exists
    try:
        with requests.get(source_video_url, timeout=(10, 180), stream=True) as response:
            if response.status_code != 200:
                msg = {}
                msg["error"] = _(
                    "The video file for this recording "
                    "was not found on the BBB server."
                )
                # If we want to display the 404/500... page to the user
                # msg["message"] = response.content.decode("utf-8")
                msg["message"] = "Error number : %s" % response.status_code
                raise ValueError(msg)

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
        msg = {}
        msg["error"] = _("Impossible to download the video file from the server.")
        msg["message"] = str(exc)
        raise ValueError(msg)


def save_video(request, dest_file, recording_name, description, date_evt=None):
    """Save and encode the Pod video file.

    Args:
        request (Request): HTTP request
        dest_file (String): Destination file of the Pod video
        recording_name (String): recording name
        description (String): description added to the Pod video
        date_evt (Datetime, optional): Event date. Defaults to None.

    Raises:
        ValueError: if impossible creation
    """
    try:
        video = Video.objects.create(
            video=dest_file,
            title=recording_name,
            owner=request.user,
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
        msg["message"] = str(exc)
        raise ValueError(msg)


def check_file_exists(source_url):
    """Check that the URL exists.

    Args:
        source_url (String): Source URL

    Returns:
        Boolean: file exists (True) or not (False)
    """
    response = requests.head(source_url, timeout=2)
    if response.status_code < 400:
        return True
    else:
        return False


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
