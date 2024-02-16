"""
Useful script for migrating BBB records when changing BBB
infrastructure. Typically, when moving from a local architecture to the
French Ministry of Higher Education and Research (ESR) BBB architecture.

More information on this module at: https://www.esup-portail.org/wiki/x/C4CFUQ

Reminder of constraints :
 - no use of Pod's old BBB module (this module will be phased out in the near future)
 - problem with the BBB API: moderators are only available when the BBB session
 session is in progress. After that, the information is no longer available in BBB.
 This information is present in the BBB client, i.e. Pod or Moodle
 (or Greenlight...).
 - by default, it is possible to reconstruct a BBB record in the BBB infrastructure
 (typically to obtain the recording in video format) only if the raw files
 are still present.
 By default, these raw files are deleted after 14 days.

Principle :
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
It is also planned (if access to the Moodle database is write-only, of course) to add
information directly to the BBB session in Moodle (intro field).
This is made possible by using the --use-import-video parameter,
the --use-database-moodle parameter and setup directly in this file.
This script has already been tested with Moodle 4.


This script also allows you to :
 - simulate what will be done via the --dry parameter
 - process only certain lines via the --min-value-record-process
 and --max-value-record-process parameters.

Examples and use cases :
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
from xml.dom import minidom

# For PostgreSQL database #
# Don't forget to run the following command the 1st time
# pip install psycopg2-binary
import psycopg2
import psycopg2.extras
from psycopg2 import sql

# For MariaDB/MySQL database #
# Don't forget to run the following command the 1st time
# pip install mysql-connector-python
# import mysql.connector


# # Script config (TO EDIT) # #
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
# Moodle database connection parameters
DB_PARAMS = {
    "host": "bddmoodle.univ.fr",
    "database": "moodle",
    "user": "moodle",
    "password": "",
    "port": "",
    "connect_timeout": "10",
}
# Information message set in Moodle database, table mdl_bigbluebuttonbn, field intro
SCRIPT_INFORM = (
    "<p class='alert alert-dark'>"
    "Suite au changement d'infrastructure BigBlueButton, les enregistrements BBB "
    "réalisées avant le 01/06/2024 ne sont plus accessibles par défaut dans Moodle.<br>"
    "Ces enregistrements seront disponibles du 01/06/2024 au 01/12/2024 sur Pod"
    "(<a class='alert-link' href='https://pod.univ.fr' target='_blank'>"
    "pod.univ.fr</a>), "
    "via le module <b>Importer une vidéo externe</b>.<br>"
    "Vous retrouverez dans ce module vos anciens enregistrements BBB, qu'il vous sera "
    "possible de convertir en vidéo pour les rendre accessibles à vos usagers.<br>"
    "Pour plus d'informations sur cette migration, n'hésitez pas à consulter "
    "la page dédiée sur le site <a class='alert-link' "
    "href='https://numerique.univ.fr' target='_blank'>numerique.univ.fr"
    "</a>.<br><a href='https://pod.univ.fr/import_video/'"
    " class='btn btn-primary' target='_blank'>"
    "Accéder au module d'import des vidéos dans Pod</a>."
    "</p>"
)
# #
# # # #


# # Config from settings-local.py (CUSTOM SETTINGS) # #
# Path used in the event of a claim
DEFAULT_RECORDER_PATH = getattr(settings, "DEFAULT_RECORDER_PATH", "/data/ftp-pod/ftp/")
# # # #

# Global variable
number_records_to_encode = 0


def connect_moodle_database():
    """Connect to the Moodle database and returns cursor."""
    try:
        # For Postgre database
        connection = psycopg2.connect(**DB_PARAMS)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # For MariaDB/MySQL database
        # connection = mysql.connector.connect(**DB_PARAMS)
        # cursor = connection.cursor()
        return connection, cursor

    # For MariaDB/MySQL database
    # except mysql.connector.Error as e:
    # For Postgre database
    except psycopg2.Error as e:
        print("Error: Unable to connect to the Moodle database.")
        print(e)
        return None, None


def disconnect_moodle_database(connection, cursor):
    """Disconnect to Moodle database."""
    try:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    except Exception as e:
        print("Error: Unable to disconnect to the Moodle database.")
        print(e)


def process(options):
    """Achieve the BBB recordings migration"""

    # Get the BBB recordings from BBB/Scalelite server API
    recordings = get_bbb_recordings_by_xml()

    print("***Total number of records: %s***" % len(recordings))

    number_record_processed = (
        options["max_value_record_process"] - options["min_value_record_process"] + 1
    )
    print("***Number of records to be processed: %s***" % number_record_processed)

    # Manage the recordings
    i = 0
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
    # Number of recordings to encode
    print("***Number of records to encode in video: %s***" % number_records_to_encode)


def get_bbb_recordings_by_xml():
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
        urlToRequest = SCRIPT_BBB_SERVER_URL
        urlToRequest += "bigbluebutton/api/getRecordings?checksum=" + checksum
        addr = requests.get(urlToRequest)
        print("Request on URL: " + urlToRequest + ", status: " + str(addr.status_code))
        # XML result to parse
        xmldoc = minidom.parseString(addr.text)
        returncode = xmldoc.getElementsByTagName("returncode")[0].firstChild.data
        # Management of FAILED error (basically error in checksum)
        if returncode == "FAILED":
            err = "Return code = FAILED for: " + urlToRequest
            err += " => : " + xmldoc.toxml() + ""
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


def get_recording(recording):  # noqa: C901
    """Returns a BBB recording, using the Generic_recording class."""
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
        presentation_url = ""
        video_url = ""
        # Check playback data
        for playback in recording.getElementsByTagName("playback"):
            # Depends on BBB parameters, we can have multiple format
            for format in playback.getElementsByTagName("format"):
                type = format.getElementsByTagName("type")[0].firstChild.data
                # For bbb-recorder, we need URL of presentation format
                if type == "presentation":
                    # Recording URL is the BBB presentation URL
                    presentation_url = format.getElementsByTagName("url")[
                        0
                    ].firstChild.data
                    # Convert format 2.0 to 2.3 if necessary
                    presentation_url = convert_format(
                        presentation_url, internal_meeting_id
                    )
                if type == "video":
                    # Recording URL is the BBB video URL
                    video_url = format.getElementsByTagName("url")[0].firstChild.data

        # Define the result with the Generic_recording class
        generic_recording = Generic_recording(
            internal_meeting_id,
            meeting_id,
            meeting_name,
            start_time,
            origin,
            presentation_url,
            video_url,
        )
    except Exception as e:
        err = "Problem to get BBB recording: " + str(e) + ". " + traceback.format_exc()
        print(err)
    return generic_recording


def get_video_file_name(file_name, date, extension):
    """Normalize a video file name"""
    slug = slugify("%s %s" % (file_name[0:40], str(date)[0:10]))
    return "%s.%s" % (slug, extension)


def download_bbb_video_file(source_url, dest_file):
    """Download a BBB video playback"""
    session = requests.Session()
    # Download and parse the remote HTML file (BBB specific)
    video_file_add = parse_remote_file(session, source_url)
    # Verify that video exists
    source_video_url = manage_recording_url(source_url, video_file_add)
    if check_url_exists(source_video_url):
        # Download the video file
        source_video_url = manage_download(session, source_url, video_file_add, dest_file)
    else:
        print("Unable to download %s : video file doesn't exist." % source_url)


def process_recording_to_claim(options, generic_recording):
    """Download video playback or encode presentation playback to recorder directory.

    Please note: the claim requires the encoding of records in presentation playback.
    For a presentation playback, a process (asynchronous if CELERY_TO_ENCODE) is started.
    Be careful : if not asynchronous, each encoding is made in a subprocess.
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


def process_recording_to_import_video(options, generic_recording):
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
            msg = "BBB session made with Moodle."
    if generic_owners:
        msg += " Create user in Pod if necessary."
        # Owners found in Moodle
        for generic_owner in generic_owners:
            # Create if necessary the user in Pod
            pod_owner = get_or_create_user_pod(options, generic_owner)
            # Create the external recording for an owner, if necessary
            manage_external_recording(options, generic_recording, site, pod_owner, msg)
        # Update information in Moodle (field intro)
        set_information_in_moodle(options, generic_recording)
    else:
        # Only 1 owner (administrator at least if not found)
        manage_external_recording(options, generic_recording, site, owner, msg)


def get_created_in_pod(generic_recording):
    """Allow to know if this recording was made with Pod.

    In such a case, we know the meeting (owner information)."""
    # Check if the recording was made by Pod client
    meeting = Meeting.objects.filter(meeting_id=generic_recording.meeting_id).first()
    return meeting


def get_or_create_user_pod(options, generic_owner):
    """Returns the Pod user corresponding to the generic owner.

    If necessary, create this user in Pod."""
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


def manage_external_recording(options, generic_recording, site, owner, msg):
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


def create_external_recording(generic_recording, site, owner):
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


def get_created_in_moodle(generic_recording):  # noqa: C901
    """Allow to know if this recording was made with Moodle.

    In such a case, we know the list of owners."""
    # Default value
    owners_found = []
    try:
        participants = ""

        connection, cursor = connect_moodle_database()
        with cursor as c:
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
                participants = res["participants"]
                if participants != "":
                    # Parse participants as a JSON string
                    parsed_data = json.loads(participants)
                    for item in parsed_data:
                        # Search for moderators
                        if (
                            item["selectiontype"] == "user"
                            and item["role"] == "moderator"
                        ):
                            user_id_moodle = item["selectionid"]
                            user_moodle = get_moodle_user(user_id_moodle)
                            if user_moodle:
                                print(
                                    " - Moderator found in Moodle: %s %s"
                                    % (user_moodle.username, user_moodle.email)
                                )
                                owners_found.append(user_moodle)

    except Exception as e:
        err = (
            "Problem to find moderators for BBB recording in Moodle"
            ": " + str(e) + ". " + traceback.format_exc()
        )
        print(err)
    return owners_found


def set_information_in_moodle(options, generic_recording):
    """Set information about this migration in Moodle (if possible).

    Update the field : public.mdl_bigbluebuttonbn.intro in Moodle
    to store information, if possible (database user in read/write, permissions...).
    Use SCRIPT_INFORM.
    """
    try:
        connection, cursor = connect_moodle_database()
        with cursor as c:
            # Request for Moodle v4
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
                id = res["id"]
                intro = res["intro"]
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


def get_moodle_user(user_id):
    """Returns a generic user by user id in Moodle database."""
    dict_user = []
    generic_user = None
    connection, cursor = connect_moodle_database()
    with cursor as c:
        # Most important field: username
        select_query = sql.SQL(
            "SELECT id, username, firstname, lastname, email FROM public.mdl_user "
            "WHERE id = '%s' " % (user_id)
        ).format(sql.Identifier("type"))
        c.execute(select_query)
        dict_user = c.fetchone()
        generic_user = Generic_user(
            dict_user["id"],
            dict_user["username"],
            dict_user["firstname"],
            dict_user["lastname"],
            dict_user["email"],
        )

    return generic_user


def convert_format(source_url, internal_meeting_id):
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

    return source_url


def check_system(options):  # noqa: C901
    """Check the system (configuration, recorder, access rights). Blocking function."""
    error = False
    if options["use_manual_claim"]:
        # A recorder is mandatory in the event of a claim
        recorder = Recorder.objects.filter(id=SCRIPT_RECORDER_ID).first()
        if not recorder:
            error = True
            print(
                "ERROR : No recorder found with id %s. "
                "Please create one." % SCRIPT_RECORDER_ID
            )
        else:
            claim_path = os.path.join(DEFAULT_RECORDER_PATH, recorder.directory)
            # Check directory exist
            if not os.path.exists(claim_path):
                error = True
                print(
                    "ERROR : Directory %s doesn't exist. "
                    "Please configure one." % claim_path
                )
    if options["use_import_video"]:
        # Administrator to whom recordings will be added,
        # whose moderators have not been identified
        administrator = User.objects.filter(id=SCRIPT_ADMIN_ID).first()
        if not administrator:
            error = True
            print(
                "ERROR : No administrator found with id %s. "
                "Please create one." % SCRIPT_ADMIN_ID
            )
    if options["use_database_moodle"]:
        # Check connection to Moodle database
        connection, cursor = connect_moodle_database()
        if not cursor:
            error = True
            print(
                "ERROR : Unable to connect to Moodle database. Please configure "
                "DB_PARAMS in this file, check firewall rules and permissions."
            )
        else:
            disconnect_moodle_database(connection, cursor)

    if error:
        exit()


class Generic_user:
    """Class for a generic user."""

    def __init__(self, user_id, username, firstname, lastname, email):
        """Initialize."""
        self.id = user_id
        self.username = username
        self.firstname = firstname
        self.lastname = lastname
        self.email = email

    def __str__(self):
        """Display a generic user object as string."""
        if self.id:
            return "%s %s (%s)" % (self.firstname, self.lastname, self.username)
        else:
            return "None"


class Generic_recording:
    """Class for a generic recording."""

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
        # Generated source URL : video playback if possible
        self.source_url = self.video_url
        if self.source_url == "":
            # Else presentation playback
            self.source_url = self.presentation_url


class Command(BaseCommand):
    """Migrate BBB recordings into the Pod database."""

    help = "Migrate BigBlueButton recordings"

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        """Handle the BBB migration command call."""

        if options["dry"]:
            print("Simulation mode ('dry'). Nothing will be achieved.")

        # Check configuration, recoder, rights...
        check_system(options)

        # Main function
        process(options)
