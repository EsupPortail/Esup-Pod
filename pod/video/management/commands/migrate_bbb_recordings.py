"""
Useful script for migrating BBB records when changing BBB infrastructure.

Typically, when moving from a local architecture to the
French Ministry of Higher Education and Research (ESR) BBB architecture.

More information on this module at: https://www.esup-portail.org/wiki/x/C4CFUQ

Reminder of constraints:
 - no use of Pod's old BBB module (this module will be phased out in the near future)
 - problem with the BBB API: moderators are only available when the BBB session
 session is in progress. After that, the information is no longer available in BBB.
 This information is present in the BBB client, i.e. Pod or Moodle
 (or Greenlight...).
 - by default, it is possible to reconstruct a BBB record in the BBB infrastructure
 (typically to obtain the recording in video format) only if the raw files
 are still present.
 By default, these raw files are deleted after 14 days.

Principle:
 - add recording management to the external video import module,
 BBB, presentation type. This means using the Github project bbb-recorder;
 in any case, there's no choice for this migration.
 You need to install bbb-recorder on the encoding servers and set up
 IMPORT_VIDEO_BBB_RECORDER_PLUGIN and IMPORT_VIDEO_BBB_RECORDER_PATH correctly.
 This feature has been added in Esup-Pod 3.5.1.

 - create this migration script, which offers several possibilities:

    * 1° option, for those who have few recordings to recover

This script will convert presentations from the old BBB architecture into video files
(as before, via the bbb-recorder plugin) and put these files in the directory
of a recorder used to claim recordings.
Of course, if there are already video presentations, the video file will be copied
directly.
Once all the videos have been encoded, the local BBB architecture can be stopped.
This is made possible by using the --use-manual-claim parameter and the
setup directly in this file.
Please note that, depending on your Pod architecture, encoding will be performed
either via Celery tasks or directly, one after the other. Don't hesitate to test
on a few recordings first and run this script in the background (use &).

    * 2nd option, for those who have a lot of recordings to retrieve

The idea is to give users time to choose which records they wish to keep
(it's not possible or useful to convert everything).
To do this, you'll need to leave the old BBB/Scalelite server open at least
for a few months (just to access the records).
On the scripting side, you'll need access to the Moodle database to know
who did what.
So, for each BBB recording, the script would create a line in Pod's
"My external videos" module, of type BBB, for the moderators.
If these moderators have never logged into Pod, they will be created in Pod.
They can then import these recordings into Pod themselves.
Just in case, if records are not identifiable, they will be associated
to an administrator. In this way, for records from sources other than Pod or Moodle,
they will automatically be associated with an administrator (unless
this script is modified).
It is also planned (if access to the Moodle database is writable, of course) to add
information directly to the BBB session in Moodle (intro field).
This is made possible by using the --use-import-video parameter,
the --use-database-moodle parameter and setup directly in this file.
This script has already been tested with Moodle 4.


This script also allows you to:
 - simulate what will be done via the --dry parameter
 - process only certain lines via the --min-value-record-process
 and --max-value-record-process parameters.

Examples and use cases:
 * Use of record claim for all records, in simulation only:
 python -W ignore manage.py migrate_bbb_recordings --use-manual-claim --dry

 * Use of record claim for only 2 records, in simulation only:
 python -W ignore manage.py migrate_bbb_recordings --min-value-record-process=1
 --max-value-record-process=2 --use-manual-claim --dry &

 - Use of external video import module, with access to Moodle database for
 all recordings, in simulation only:
 * python -W ignore manage.py migrate_bbb_recordings --use-import-video
 --use-database-moodle --dry

Documentation for this system is available on the Esup-Pod Wiki:
https://www.esup-portail.org/wiki/x/C4CFUQ

"""

import hashlib
import json
import os
import requests
import traceback
from datetime import datetime as dt
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
from pod.import_video.utils import manage_download, parse_remote_file
from pod.import_video.utils import manage_recording_url, check_url_exists
from pod.import_video.models import ExternalRecording
from pod.import_video.views import start_bbb_encode_presentation_and_move_to_destination
from pod.meeting.models import Meeting
from pod.recorder.models import Recorder
from defusedxml import minidom

# # Script config (TO EDIT) # #
# Moodle database engine (postgresql, mysql or None)
MOODLE_DB_TYPE = None

MOODLE_DB_TYPE = "postgresql"

if MOODLE_DB_TYPE == "postgresql":
    # For PostgreSQL database #
    # Don't forget to run the following command the 1st time
    # pip install psycopg2-binary
    from psycopg2 import connect
    import psycopg2.extras
    from psycopg2 import sql
    from psycopg2 import Error as DBError
elif MOODLE_DB_TYPE == "mysql":
    # For MariaDB/MySQL database #
    # Don't forget to run the following command the 1st time
    # pip install mysql-connector-python
    from mysql.connector import connect
    from mysql.connector import Error as DBError


# Old BigBlueButton config #
# Old BigBlueButton/Scalelite server URL
SCRIPT_BBB_SERVER_URL = "https://bbb.univ.fr/"
# BigBlueButton key or Scalelite LOADBALANCER_SECRET
SCRIPT_BBB_SECRET_KEY = ""
# BBB or Scalelite version is greater than 2.3
# Useful for presentation playback in 2.0 (for BBB <= 2.2) or 2.3 (for BBB >= 2.3) format
# Set to True by default
SCRIPT_PLAYBACK_URL_23 = True
# #

# use-manual-claim #
# Recorder used to get BBB recordings
SCRIPT_RECORDER_ID = 1
# #

# use-import-video #
# Administrator to whom recordings will be added,
# whose moderators have not been identified
SCRIPT_ADMIN_ID = 1
# #

# use-database-moodle #
# Moodle databases connection parameters
DB_PARAMS = {
    # The default Moodle DB (if a recording has no bbb-origin-server-name)
    "default": {
        "host": "bddmoodle.univ.fr",
        "database": "moodle",
        "user": "moodle",
        "password": "",
        "port": None,
        "connect_timeout": 10,
    },
    # Add as many Moodle DB as bbb-origin-server-name you have
    "server2": {
        "host": "bddmoodle.univ.fr",
        "database": "moodle2",
        "user": "moodle2",
        "password": "",
        "port": None,
        "connect_timeout": 10,
    },
}

# List of origin_server_name to be ignored by this script
IGNORED_SERVERS = ["not-a-moodle.univ.fr"]

# Site domain (like pod.univ.fr)
SITE_DOMAIN = get_current_site(None).domain

# Information message set in Moodle database, table mdl_bigbluebuttonbn, field intro
SCRIPT_INFORM = (
    "<p class='alert alert-dark'>"
    "Suite au changement d’infrastructure BigBlueButton, les enregistrements BBB "
    "réalisées avant le XX/XX/2024 ne sont plus accessibles par défaut dans Moodle.<br>"
    "Ces enregistrements seront disponibles du XX/XX/2024 au YY/YY/2024 sur Pod"
    "(<a class='alert-link' href='https://%s' target='_blank'>%s</a>), "
    "via le module <strong>Importer une vidéo externe</strong>.<br>"
    "Vous retrouverez dans ce module vos anciens enregistrements BBB, qu’il vous sera "
    "possible de convertir en vidéo pour les rendre accessibles à vos usagers.<br>"
    "Pour plus d’informations sur cette migration, n’hésitez pas à consulter "
    "la page dédiée sur le site <a class='alert-link' "
    "href='https://numerique.univ.fr' target='_blank'>numerique.univ.fr"
    "</a>.<br><a href='https://%s/import_video/'"
    " class='btn btn-primary' target='_blank'>"
    "Accéder au module d’import des vidéos dans Pod</a>."
    "</p>" % (SITE_DOMAIN, SITE_DOMAIN, SITE_DOMAIN)
)
# #
# # # #


# # Config from settings-local.py (CUSTOM SETTINGS) # #
# Path used in the event of a claim
DEFAULT_RECORDER_PATH = getattr(settings, "DEFAULT_RECORDER_PATH", "/data/ftp-pod/ftp/")
# # # #

# Global variable
number_records_to_encode = 0

# Ask BBB or load previous xml
USE_CACHE = False


class Generic_user:
    """Class for a generic user."""

    def __init__(
        self, user_id: str, username: str, firstname: str, lastname: str, email: str
    ) -> None:
        """Initialize."""
        self.id = user_id
        self.username = username
        self.firstname = firstname
        self.lastname = lastname
        self.email = email

    def __str__(self) -> str:
        """Display a generic user object as string."""
        if self.id:
            return "%s %s (%s)" % (self.firstname, self.lastname, self.username)
        else:
            return "None"


class Generic_recording:
    """Class for a generic recording."""

    # Optional BBB recording fields
    origin_server_name = ""
    origin_version = ""
    origin_context = ""
    recording_name = ""
    origin_id = ""
    origin_label = ""
    description = ""
    published = ""
    state = ""

    def __init__(
        self,
        internal_meeting_id,
        meeting_id,
        meeting_name,
        start_time,
        origin,
        presentation_url,
        video_url,
    ):
        """Initialize."""
        self.internal_meeting_id = internal_meeting_id
        self.meeting_id = meeting_id
        self.meeting_name = meeting_name
        self.start_time = start_time
        self.origin = origin
        self.presentation_url = presentation_url
        self.video_url = video_url
        # Generated formatted date
        self.start_date = dt.fromtimestamp(float(start_time) / 1000)
        # Generated source URL: video playback if possible
        self.source_url = self.video_url
        if self.source_url == "":
            # Else presentation playback
            self.source_url = self.presentation_url

    def as_list(self) -> list:
        """Get a Generic_recording as list."""
        return [
            self.meeting_name,
            self.recording_name,
            self.start_date.strftime("%Y-%m-%d"),
            self.origin,
            self.origin_server_name,
            self.origin_version,
            self.origin_context,
            self.origin_id,
            self.origin_label,
            self.description,
            self.published,
            self.state,
            self.source_url,
        ]

    def __str__(self):
        """Get a Generic_recording as string."""
        return "%s,%s,%s,%s" % (
            self.meeting_name,
            self.start_date,
            self.origin,
            self.source_url,
        )


def connect_moodle_database(generic_recording=None):
    """Connect to the Moodle database and returns cursor."""
    if generic_recording and generic_recording.origin_server_name:
        server = generic_recording.origin_server_name
    else:
        server = "default"

    try:
        connection = connect(**DB_PARAMS[server])
        if MOODLE_DB_TYPE == "postgresql":
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            cursor = connection.cursor()
        return connection, cursor

    except DBError as e:
        print("Error: Unable to connect to the Moodle database for server `%s`." % server)
        print(e)
        return None, None


def disconnect_moodle_database(connection, cursor) -> None:
    """Disconnect the Moodle database."""
    try:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    except Exception as e:
        print("Error: Unable to close connection to Moodle database.")
        print(e)


def process(options) -> None:
    """Achieve the BBB recordings migration."""
    # Get the BBB recordings from BBB/Scalelite server API
    recordings = get_bbb_recordings_by_xml()

    print("***Total number of records: %s***" % len(recordings))

    number_record_processed = (
        options["max_value_record_process"] - options["min_value_record_process"] + 1
    )
    print("***Number of records to be processed: %s***" % number_record_processed)

    # Manage the recordings
    i = 0
    record_strings = []
    for recording in recordings:
        i += 1
        # Only recordings within the interval are taken into account.
        if (
            i >= options["min_value_record_process"]
            and i <= options["max_value_record_process"]
        ):
            # Get the recording
            generic_recording = get_recording(recording)
            if options["use_manual_claim"]:
                # #1 Use Manual claim
                print(
                    "------------------------------\n"
                    "Use manual claim for recording #%s %s"
                    % (str(i), generic_recording.internal_meeting_id)
                )
                # The claim requires the encoding of records in presentation.
                process_recording_to_claim(options, generic_recording)
                print("------------------------------")
            elif options["use_import_video"]:
                # #2 Use import video
                print(
                    "------------------------------\n"
                    "Use import video for recording #%s %s"
                    % (str(i), generic_recording.internal_meeting_id)
                )
                process_recording_to_import_video(options, generic_recording)
                print("------------------------------")
            elif options["use_export_csv"]:
                # #3 Use Export recordings as CSV
                print("\n#%s ; %s" % (str(i), generic_recording))

                line = generic_recording.as_list()
                if options["use_database_moodle"]:
                    generic_owners = get_created_in_moodle(generic_recording)
                    generic_owners = [str(o) for o in generic_owners]
                    line.append(generic_owners)

                record_strings.append(line)
    if options["use_export_csv"]:
        header = [
            "meeting_name",
            "recording_name",
            "start_date",
            "origin",
            "origin_server_name",
            "origin_version",
            "origin_context",
            "origin_id",
            "origin_label",
            "description",
            "published",
            "state",
            "source_url",
        ]

        if options["use_database_moodle"]:
            header.append("Moodle_owners")
        import csv

        with open("out.csv", "w", newline="") as f:
            writer = csv.writer(
                f, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            writer.writerow(header)
            writer.writerows(record_strings)
    # Number of recordings to encode
    print("***Number of records to encode in video: %s***" % number_records_to_encode)


def get_bbb_recordings_by_xml() -> list:
    """Get the BBB recordings from BBB/Scalelite server."""
    print("\n*** Get the BBB recordings from BBB/Scalelite server.  ***")
    recordings = []
    try:
        # See https://docs.bigbluebutton.org/dev/api.html#usage
        # for checksum and security
        checksum = hashlib.sha1(
            str("getRecordings" + SCRIPT_BBB_SECRET_KEY).encode("utf-8")
        ).hexdigest()
        # Request on BBB/Scalelite server (API)
        # URL example:
        # https://bbb.univ.fr/bigbluebutton/api/getRecordings?checksum=xxxx
        if USE_CACHE is False:
            urlToRequest = SCRIPT_BBB_SERVER_URL
            urlToRequest += "bigbluebutton/api/getRecordings?checksum=" + checksum
            addr = requests.get(urlToRequest)
            print(
                "Request on URL: " + urlToRequest + ", status: " + str(addr.status_code)
            )
            with open("getRecordings.xml", "w") as f:
                f.write(addr.text)
                print("BBB Response saved to `getRecordings.xml`.")
            # XML result to parse
            xmldoc = minidom.parseString(addr.text)
        else:
            xmldoc = minidom.parse("getRecordings.xml")
            print("Parsing `getRecordings.xml`...")
        returncode = xmldoc.getElementsByTagName("returncode")[0].firstChild.data
        # Management of FAILED error (basically error in checksum)
        if returncode == "FAILED":
            err = "Return code = FAILED for: " + urlToRequest
            err += " => " + xmldoc.toxml() + ""
            print(err)
        # Actual recordings
        recordings = xmldoc.getElementsByTagName("recording")
    except Exception as e:
        err = (
            "Problem to parse XML recordings on the BBB/Scalelite server "
            "or save in Pod database: " + str(e) + ". " + traceback.format_exc()
        )
        print(err)
    return recordings


def get_recording(recording) -> Generic_recording:
    """Return a BBB recording, using the Generic_recording class."""
    generic_recording = None
    try:
        # Get recording informations
        internal_meeting_id = recording.getElementsByTagName("internalMeetingID")[
            0
        ].firstChild.data

        meeting_id = recording.getElementsByTagName("meetingID")[0].firstChild.data
        meeting_name = recording.getElementsByTagName("name")[0].firstChild.data
        start_time = recording.getElementsByTagName("startTime")[0].firstChild.data
        # Origin can be empty (Pod or other clients), Greenlight, Moodle...
        origin = ""
        if recording.getElementsByTagName("bbb-origin"):
            origin = recording.getElementsByTagName("bbb-origin")[0].firstChild.data

        # Get recording URL that corresponds to the presentation URL
        # Take only the "presentation" or "video" format
        # Not other format like "screenshare" or "podcast"

        # Check playback data
        presentation_url, video_url = get_recording_urls()

        # Define the result with the Generic_recording class
        generic_recording = Generic_recording(
            internal_meeting_id,
            meeting_id,
            meeting_name.strip(),
            start_time,
            origin,
            presentation_url,
            video_url,
        )

        # Get other optional BBB tags
        for name, tag in [
            ("origin_server_name", "bbb-origin-server-name"),
            ("origin_version", "bbb-origin-version"),
            ("origin_context", "bbb-context"),
            ("origin_id", "bbb-context-id"),
            ("origin_label", "bbb-context-label"),
            ("description", "bbb-recording-description"),
            ("published", "published"),
            ("state", "state"),
            ("recording_name", "bbb-recording-name"),
        ]:
            # Check that tag exists
            if recording.getElementsByTagName(tag):
                # Check that tag is not empty
                if recording.getElementsByTagName(tag)[0].firstChild:
                    value = recording.getElementsByTagName(tag)[0].firstChild.data
                    setattr(generic_recording, name, value.strip())

    except Exception as e:
        err = "Problem to get BBB recording: " + str(e) + ". " + traceback.format_exc()
        print(err)
    return generic_recording


def get_recording_urls(recording, internal_meeting_id):
    """Get URLs for a BBB recording."""
    # Depends on BBB parameters, we can have multiple format
    presentation_url = ""
    video_url = ""
    for playback in recording.getElementsByTagName("playback"):
        for format in playback.getElementsByTagName("format"):
            type = format.getElementsByTagName("type")[0].firstChild.data
            # For bbb-recorder, we need URL of presentation format
            if type == "presentation":
                # Recording URL is the BBB presentation URL
                presentation_url = format.getElementsByTagName("url")[0].firstChild.data
                # Convert format 2.0 to 2.3 if necessary
                presentation_url = convert_format(presentation_url, internal_meeting_id)
            if type == "video":
                # Recording URL is the BBB video URL
                video_url = format.getElementsByTagName("url")[0].firstChild.data
    return presentation_url, video_url


def get_video_file_name(file_name: str, date: dt, extension: str) -> str:
    """Normalize a video file name."""
    slug = slugify("%s %s" % (file_name[0:40], str(date)[0:10]))
    return "%s.%s" % (slug, extension)


def download_bbb_video_file(source_url: str, dest_file: str) -> None:
    """Download a BBB video playback."""
    session = requests.Session()
    # Download and parse the remote HTML file (BBB specific)
    video_file_add = parse_remote_file(session, source_url)
    # Verify that video exists
    source_video_url = manage_recording_url(source_url, video_file_add)
    if check_url_exists(source_video_url):
        # Download the video file
        source_video_url = manage_download(session, source_url, video_file_add, dest_file)
    else:
        print("Unable to download %s: video file doesn't exist." % source_url)


def process_recording_to_claim(options, generic_recording) -> None:
    """Download video playback or encode presentation playback to recorder directory.

    Please note: the claim requires the encoding of records in presentation playback.
    For a presentation playback, a process (asynchronous if CELERY_TO_ENCODE) is started.
    Be careful: if not asynchronous, each encoding is made in a subprocess.
    Must used in an asynchronous way.
    """
    recorder = Recorder.objects.get(id=SCRIPT_RECORDER_ID)

    if generic_recording.video_url != "":
        # Video playback
        source_url = generic_recording.video_url
        file_name = get_video_file_name(
            generic_recording.meeting_name, generic_recording.start_date, "m4v"
        )
        # Video file in the recorder directory
        dest_file = os.path.join(
            DEFAULT_RECORDER_PATH,
            recorder.directory,
            os.path.basename(file_name),
        )
        print(
            " - Recording %s, video playback %s: "
            "download video file into %s."
            % (generic_recording.internal_meeting_id, source_url, dest_file)
        )
        if not options["dry"]:
            # Download the video file
            download_bbb_video_file(source_url, dest_file)
    else:
        # Increment the number of records to be encoded
        global number_records_to_encode
        number_records_to_encode += 1

        source_url = generic_recording.presentation_url
        file_name = get_video_file_name(
            generic_recording.meeting_name, generic_recording.start_date, "webm"
        )
        # Video file generated in the recorder directory
        dest_file = os.path.join(
            DEFAULT_RECORDER_PATH,
            recorder.directory,
            os.path.basename(file_name),
        )
        print(
            " - Recording %s - presentation playback %s: "
            "encode presentation into %s"
            % (generic_recording.internal_meeting_id, source_url, dest_file)
        )
        if not options["dry"]:
            # Send asynchronous/synchronous encode task (depends on CELERY_TO_ENCODE)
            # to convert presentation in video and move it into the recorder directory
            start_bbb_encode_presentation_and_move_to_destination(
                file_name, source_url, dest_file
            )


def process_recording_to_import_video(options, generic_recording) -> None:
    """Add the recording to the import video in Pod.

    Please note: the link must remain valid for several months,
    until the user can import it into Pod.
    """
    msg = ""
    # List of owners (generic_user)
    generic_owners = []
    # Default owner is the administrator (if no user found)
    owner = User.objects.get(id=SCRIPT_ADMIN_ID)
    # Default site
    site = get_current_site(None)
    # Search if this recording was made with Pod
    meeting = get_created_in_pod(generic_recording)
    if meeting:
        # Recording made with Pod, we found the owner and the site
        owner = meeting.owner
        site = meeting.site
        msg = "BBB session made with Pod."
    else:
        # Search if this recording was made with Moodle (if configured)
        if options["use_database_moodle"]:
            generic_owners = get_created_in_moodle(generic_recording)
            if generic_owners:
                msg = "BBB session made with Moodle."
    if generic_owners:
        msg += " Create user in Pod if necessary."
        # Owners found in Moodle
        for generic_owner in generic_owners:
            # Create if necessary the user in Pod
            pod_owner = get_or_create_user_pod(options, generic_owner)
            # Create the external recording for an owner, if necessary
            manage_external_recording(options, generic_recording, site, pod_owner, msg)
        if options["use_database_moodle"]:
            # Update information in Moodle (field intro)
            set_information_in_moodle(options, generic_recording)
    else:
        # Only 1 owner (administrator at least if not found)
        manage_external_recording(options, generic_recording, site, owner, msg)


def process_recording_to_export_csv(options, generic_recording) -> str:
    """Convert a recording to a comma separated values."""
    print(
        " - Recording %s, playback %s"
        "create an external recording if necessary."
        % (
            generic_recording.internal_meeting_id,
            generic_recording.source_url,
        )
    )
    return "%s,%s" % (
        generic_recording.internal_meeting_id,
        generic_recording.source_url,
    )


def get_created_in_pod(generic_recording: Generic_recording) -> Meeting:
    """Allow to know if this recording was made with Pod.

    In such a case, we know the meeting (owner information).
    """
    # Check if the recording was made by Pod client
    meeting = Meeting.objects.filter(meeting_id=generic_recording.meeting_id).first()
    return meeting


def get_or_create_user_pod(options, generic_owner: Generic_user):
    """Return the Pod user corresponding to the generic owner.

    If necessary, create this user in Pod.
    """
    # Search for user in Pod database
    user = User.objects.filter(username=generic_owner.username).first()
    if user:
        return user
    else:
        # Create user in Pod database
        # Owner are necessary staff;
        # if not, this will be changed at the user 1st connection.
        if not options["dry"]:
            # Create
            user = User.objects.create(
                username=generic_owner.username,
                first_name=generic_owner.firstname,
                last_name=generic_owner.lastname,
                email=generic_owner.email,
                is_staff=True,
                is_active=True,
            )
            return user
        else:
            return generic_owner


def manage_external_recording(options, generic_recording, site, owner, msg) -> None:
    """Print and create an external recording for a BBB recording, if necessary."""
    print(
        " - Recording %s, playback %s, owner %s: "
        "create an external recording if necessary. %s"
        % (
            generic_recording.internal_meeting_id,
            generic_recording.source_url,
            owner,
            msg,
        )
    )
    if not options["dry"]:
        # Create the external recording for the owner
        create_external_recording(generic_recording, site, owner)


def create_external_recording(generic_recording: Generic_recording, site, owner) -> None:
    """Create an external recording for a BBB recording, if necessary."""
    # Check if external recording already exists for this owner
    external_recording = ExternalRecording.objects.filter(
        source_url=generic_recording.source_url, owner=owner
    ).first()
    if not external_recording:
        # We need to create a new external recording
        ExternalRecording.objects.create(
            name=generic_recording.meeting_name,
            start_at=generic_recording.start_date,
            type="bigbluebutton",
            source_url=generic_recording.source_url,
            site=site,
            owner=owner,
        )


def get_created_in_moodle(generic_recording: Generic_recording) -> list:
    """Allow to know if this recording was made with Moodle.

    In such a case, we know the list of owners.
    """
    # Default value
    owners_found = []
    # Do not search in IGNORED_SERVERS
    if generic_recording.origin_server_name in IGNORED_SERVERS:
        print("origin_server_name ignored (%s)." % generic_recording.origin_server_name)
        return owners_found
    try:
        connection, cursor = connect_moodle_database(generic_recording)
        with cursor as c:
            select_query = (
                "SELECT b.id, b.intro, b.course, b.participants FROM "
                "mdl_bigbluebuttonbn_recordings r, mdl_bigbluebuttonbn b "
                "WHERE r.bigbluebuttonbnid = b.id "
                "AND r.recordingid = '%s' "
                "AND r.status = 2" % (generic_recording.internal_meeting_id)
            )
            if MOODLE_DB_TYPE == "postgresql":
                select_query = sql.SQL(
                    "SELECT b.id, b.intro, b.course, b.participants FROM "
                    "public.mdl_bigbluebuttonbn_recordings r, public.mdl_bigbluebuttonbn b "
                    "WHERE r.bigbluebuttonbnid = b.id "
                    "AND r.recordingid = '%s' "
                    "AND r.status = 2" % (generic_recording.internal_meeting_id)
                ).format(sql.Identifier("type"))
            c.execute(select_query)
            results = c.fetchall()
            for res in results:
                # course_id = res["course"]
                # Format for participants:
                # '[{"selectiontype":"all","selectionid":"all","role":"viewer"},
                # {"selectiontype":"user","selectionid":"83","role":"moderator"}]'
                extract_moodle_participants(res[3], connection, cursor, owners_found)
        disconnect_moodle_database(connection, cursor)
    except Exception as e:
        err = (
            "Problem to find moderators for BBB recording in Moodle"
            ": " + str(e) + ". " + traceback.format_exc()
        )
        print(err)
    return owners_found


def extract_moodle_participants(participants, connection, cursor, owners_found) -> None:
    """Extract participants from a BBB recording in Moodle."""
    if participants != "":
        # Parse participants as a JSON string
        parsed_data = json.loads(participants)
        for item in parsed_data:
            print("%s participants in this recording." % len(parsed_data))
            # Search for moderators
            if item["selectiontype"] == "user" and item["role"] == "moderator":
                user_id_moodle = item["selectionid"]
                user_moodle = get_moodle_user(user_id_moodle, connection, cursor)
                if user_moodle:
                    print(
                        " - Moderator found in Moodle: %s %s"
                        % (user_moodle.username, user_moodle.email)
                    )
                    owners_found.append(user_moodle)
    else:
        print("No participant in this recording.")


def set_information_in_moodle(options, generic_recording) -> None:
    """Set information about this migration in Moodle (if possible).

    Update the field: public.mdl_bigbluebuttonbn.intro in Moodle
    to store information, if possible (database user in read/write, permissions...).
    Use SCRIPT_INFORM.
    """
    try:
        connection, cursor = connect_moodle_database(generic_recording)
        with cursor as c:
            # Request for Moodle v4
            select_query = (
                "SELECT b.id, b.intro, b.course, b.participants FROM "
                "mdl_bigbluebuttonbn_recordings r, mdl_bigbluebuttonbn b "
                "WHERE r.bigbluebuttonbnid = b.id "
                "AND r.recordingid = '%s' "
                "AND r.status = 2" % (generic_recording.internal_meeting_id)
            )
            if MOODLE_DB_TYPE == "postgresql":
                select_query = sql.SQL(
                    "SELECT b.id, b.intro, b.course, b.participants FROM "
                    "public.mdl_bigbluebuttonbn_recordings r, public.mdl_bigbluebuttonbn b "
                    "WHERE r.bigbluebuttonbnid = b.id "
                    "AND r.recordingid = '%s' "
                    "AND r.status = 2" % (generic_recording.internal_meeting_id)
                ).format(sql.Identifier("type"))
            c.execute(select_query)
            results = c.fetchall()
            for res in results:
                id = res[0]
                intro = res[1]
                # course_id = res["course"]
                print(" - Set information in Moodle.")
                # If SCRIPT_INFORM wasn't already added
                if not options["dry"] and intro.find("Pod") == -1:
                    # Update
                    update_query = sql.SQL(
                        "UPDATE public.mdl_bigbluebuttonbn SET {} = %s WHERE id = %s"
                    ).format(sql.Identifier("intro"))
                    # New value for the intro column
                    new_intro = "%s<br>%s" % (intro, SCRIPT_INFORM)
                    # Execute the UPDATE query
                    cursor.execute(update_query, (new_intro, id))
                    # Commit the transaction
                    connection.commit()

    except Exception as e:
        # Non-blocking error
        # Typically if user not allowed to write in Moodle database or permission not set
        err = (
            "Not allow to set information in Moodle"
            ": " + str(e) + ". " + traceback.format_exc()
        )
        print(err)


def get_moodle_user(user_id: str, connection, cursor) -> Generic_user:
    """Return a generic user by user id in Moodle database."""
    dict_user = []
    generic_user = None
    with cursor as c:
        # Most important field: username
        select_query = (
            "SELECT id, username, firstname, lastname, email FROM mdl_user "
            "WHERE id = '%s' " % (user_id)
        )
        if MOODLE_DB_TYPE == "postgresql":
            select_query = sql.SQL(
                "SELECT id, username, firstname, lastname, email FROM public.mdl_user "
                "WHERE id = '%s' " % (user_id)
            ).format(sql.Identifier("type"))
        c.execute(select_query)
        dict_user = c.fetchone()
        generic_user = Generic_user(
            dict_user[0],
            dict_user[1],
            dict_user[2],
            dict_user[3],
            dict_user[4],
        )

    return generic_user


def convert_format(source_url: str, internal_meeting_id: str) -> str:
    """Convert presentation playback URL if necessary (see SCRIPT_PLAYBACK_URL_23)."""
    try:
        # Conversion - if necessary - from
        # https://xxx/playback/presentation/2.0/playback.html?meetingId=ID
        # to https://xxx/playback/presentation/2.3/ID?meetingId=ID
        if SCRIPT_PLAYBACK_URL_23 and source_url.find("/2.0/") >= 0:
            source_url = source_url.replace(
                "/2.0/playback.html", "/2.3/" + internal_meeting_id
            )
    except Exception as e:
        err = "Problem to convert format: " + str(e) + ". " + traceback.format_exc()
        print(err)

    return source_url.strip()


def check_system(options) -> None:  # noqa: C901
    """Check the system (configuration, recorder, access rights). Blocking function."""
    error = False
    if options["use_manual_claim"]:
        # A recorder is mandatory in the event of a claim
        recorder = Recorder.objects.filter(id=SCRIPT_RECORDER_ID).first()
        if not recorder:
            error = True
            print(
                "ERROR: No recorder found with id %s. "
                "Please create one." % SCRIPT_RECORDER_ID
            )
        else:
            claim_path = os.path.join(DEFAULT_RECORDER_PATH, recorder.directory)
            # Check directory exist
            if not os.path.exists(claim_path):
                error = True
                print(
                    "ERROR: Directory %s doesn't exist. "
                    "Please configure one." % claim_path
                )
    if options["use_import_video"]:
        # Administrator to whom recordings will be added,
        # whose moderators have not been identified
        administrator = User.objects.filter(id=SCRIPT_ADMIN_ID).first()
        if not administrator:
            error = True
            print(
                "ERROR: No administrator found with id %s. "
                "Please create one." % SCRIPT_ADMIN_ID
            )
    if options["use_database_moodle"]:
        # Check connection to Moodle database
        if MOODLE_DB_TYPE is None:
            error = True
            print(
                "ERROR: Undefined MOODLE_DB_TYPE."
                " Please set your Moodle DB type (postgresql or mysql)."
            )
        else:
            connection, cursor = connect_moodle_database()
            if not cursor:
                error = True
                print(
                    "ERROR: Unable to connect to Moodle database. Please configure "
                    "DB_PARAMS in this file, check firewall rules and permissions."
                )
            else:
                disconnect_moodle_database(connection, cursor)

    if error:
        exit()


class Command(BaseCommand):
    """Migrate BBB recordings into the Pod database."""

    help = "Migrate BigBlueButton recordings"

    def add_arguments(self, parser) -> None:
        """Allow arguments to be used with the command."""
        parser.add_argument(
            "--use-manual-claim",
            action="store_true",
            default=False,
            help="Use manual claim (default=False)?",
        )
        parser.add_argument(
            "--use-import-video",
            action="store_true",
            default=False,
            help="Use import video module to get recordings (default=False)?",
        )
        parser.add_argument(
            "--use_export_csv",
            action="store_true",
            default=False,
            help="Export BBB recordings in csv format (default=False)?",
        )
        parser.add_argument(
            "--use-database-moodle",
            action="store_true",
            default=False,
            help=(
                "Use Moodle database to search for moderators (default=False)? "
                "Only useful when --use-import-video was set to True."
            ),
        )
        parser.add_argument(
            "--min-value-record-process",
            type=int,
            default=1,
            help="Minimum value of records to process (default=1).",
        )
        parser.add_argument(
            "--max-value-record-process",
            type=int,
            default=10000,
            help="Maximum value of records to process (default=10000).",
        )
        parser.add_argument(
            "--dry",
            help="Simulates what will be achieved (default=False).",
            action="store_true",
            default=False,
        )

    def handle(self, *args, **options) -> None:
        """Handle the BBB migration command call."""
        if options["dry"]:
            print("Simulation mode ('dry'). Nothing will be achieved.")

        # Check configuration, recoder, rights...
        check_system(options)

        # Main function
        process(options)
