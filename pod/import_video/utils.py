"""Utils for Meeting and Import_video module."""
import json
import requests
import shutil

from datetime import datetime as dt
from django.conf import settings
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from html.parser import HTMLParser
from pod.video.models import Video
from pod.video.models import Type
from urllib.parse import parse_qs, urlparse

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


def parse_remote_file(session, source_html_url):
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
                "The HTML file for this recording was not found on the BBB server."
            )
            # If we want to display the 404/500... page to the user
            # msg["message"] = response.content.decode("utf-8")
            msg["message"] = _("Error number: %s") % response.status_code
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
                    "The video file for this recording was not found in the HTML file."
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
            msg["message"] = _("No video file found.")
            raise ValueError(msg)
    except Exception as exc:
        msg = {}
        msg["error"] = _(
            "The video file for this recording was not found in the HTML file."
        )
        msg["message"] = mark_safe(str(exc))
        raise ValueError(msg)


def manage_recording_url(source_url, video_file_add):
    """Generate the BBB video URL.

    See more explanations in manage_download() function.

    Args:
        source_url (String): Source file URL
        video_file_add (String): Name of the video file to add to the URL

    Returns:
        String: good URL of a BBB recording video
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
                    video_file_add
                )
            else:
                # 2nd case (BBB URL standard without token)
                source_video_url = source_url + video_file_add
            return source_video_url
        else:
            return source_url + video_file_add
    except Exception:
        return source_url + video_file_add


def manage_download(session, source_url, video_file_add, dest_file):
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
        session (Session) : session useful to achieve requests (and keep cookies between)
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


def download_video_file(session, source_video_url, dest_file):
    """Download BBB video file.

    Args:
        session (Session) : session useful to achieve requests (and keep cookies between)
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
                raise ValueError(_(
                    "The video file for this recording "
                    "was not found on the BBB server."
                ))

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


def save_video(request, dest_path, recording_name, description, date_evt=None):
    """Save and encode the Pod video file.

    Args:
        request (Request): HTTP request
        dest_path (String): Destination path of the Pod video
        recording_name (String): recording name
        description (String): description added to the Pod video
        date_evt (Datetime, optional): Event date. Defaults to None.

    Raises:
        ValueError: if impossible creation
    """
    try:
        video = Video.objects.create(
            video=dest_path,
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
        msg["message"] = mark_safe(str(exc))
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


def verify_video_exists_and_size(video_url):
    """Check that the video file exists and its size does not exceed the limit.

    Args:
        video_url (String): Video source URL

    Raises:
        ValueError: exception raised if no video found in this URL or video oversized
    """
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


def check_video_size(video_size):
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
        exclusion_list = ['uploadedToPodBy']
        return json.dumps(
            {key: value for key, value in self.__dict__.items()
             if key not in exclusion_list}
        )
