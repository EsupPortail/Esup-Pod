"""This command is useful to check the directory DEFAULT_RECORDER_PATH,
and its subdirectories, if they contain videos that were published by
recorders. The idea is to have one directory for each recorder. Example : at
the Montpellier university, there is one Multicam recorder for Polytech. In
settings, we have : - DEFAULT_RECORDER_PATH (in settings_local.py) =
/data/www/%userpod%/media/uploads/ - in Pod database(cf. Pod
administration), recorder_recorder table : a line for the Polytech Multicam
recorder, with value 'polytech' for 'directory' property - FTP Directory (
directly on the recorder settings) :
/data/www/%userpod%/media/uploads/polytech or empty (depends on vsftpd
config) So, the recorder makes a publication, via FTP, on the directory
/data/www/%userpod%/media/uploads/polytech and this script checks regularly
this directory. When video files are published, an email is  sent to
recorder's manager (cf. Pod administration), with a publication link. To
have more details, see online documentation.

This script must be executed regurlaly (for an example, with a CRON task).
Example : crontab -e */15 * * * * /usr/bin/bash -c 'export
WORKON_HOME=/data/www/%userpod%/.virtualenvs; export
VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3.6; cd
/data/www/%userpod%/django_projects/podv2; source
/usr/bin/virtualenvwrapper.sh; workon django_pod; python manage.py recorder
checkDirectory' """
import os
from django.utils import translation
from django.core.management.base import BaseCommand
from django.conf import settings
from pod.recorder.models import Recorder, Recording, RecordingFileTreatment
import hashlib
import requests
from django.core.mail import mail_admins
from django.utils import timezone

LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", 'fr')

# Mediacourse directory
DEFAULT_RECORDER_PATH = getattr(
    settings, 'DEFAULT_RECORDER_PATH',
    "/data/ftp-pod/ftp/"
)

# Site address
BASE_URL = getattr(
    settings, 'BASE_URL',
    "https://pod.univ.fr"
)

VIDEO_ALLOWED_EXTENSIONS = getattr(
    settings, 'VIDEO_ALLOWED_EXTENSIONS', (
        '3gp',
        'avi',
        'divx',
        'flv',
        'm2p',
        'm4v',
        'mkv',
        'mov',
        'mp4',
        'mpeg',
        'mpg',
        'mts',
        'wmv',
        'mp3',
        'ogg',
        'wav',
        'wma',
        'webm',
        'ts'
    )
)

# Site address
ALLOW_MANUAL_RECORDING_CLAIMING = getattr(
    settings, 'ALLOW_MANUAL_RECORDING_CLAIMING',
    False
)
# Mode debug (0: False, 1: True)
DEBUG = getattr(
    settings, 'DEBUG',
    False
)

SELF_REQUESTS_PROXIES = getattr(
    settings, 'SELF_REQUESTS_PROXIES',
    {
        "http": None,
        "https": None,
    }
)
ALLOW_INSECURE_REQUESTS = getattr(
    settings, 'ALLOW_INSECURE_REQUESTS',
    False
)


def print_if_debug(str):
    if DEBUG:
        print(str)


def case_full_upload(html_message_error, message_error, recorder, source_file,
                     filename, file_size):
    print_if_debug("- This video wasn't already processed. Starting the "
                   "process.")
    # Generation of the hashkey, depending on the IP address of the
    # recorder
    m = hashlib.md5()
    m.update(recorder.ipunder().encode(
        'utf-8') + recorder.salt.encode('utf-8'))

    if recorder.user is None:
        html_message_error, message_error = case_no_manager(
            html_message_error, message_error, recorder,
            source_file)
    else:
        html_message_error, message_error = case_manager_exist(
            html_message_error, message_error, recorder,
            source_file, filename, file_size, m)
    return html_message_error, message_error


def case_manager_exist(html_message_error, message_error, recorder,
                       source_file, filename, file_size, m):
    # Generation of the URL to notify the mediacourse recorder's
    # manager, of the form:
    # https://pod.univ.fr/mediacourses_notify/?recordingPlace
    # =192_168_1_10&mediapath=file.zip&key
    # =77fac92a3f06d50228116898187e50e5
    urlNotify = ''.join([BASE_URL,
                         "/recorder_notify/?recordingPlace=" +
                         recorder.ipunder() +
                         "&mediapath=" +
                         source_file +
                         "&key=" + m.hexdigest() +
                         "&course_title=" + filename])
    print_if_debug(
            "- Generate the URL , with haskey, to notify the "
            "mediacourse recorder's manager : " + urlNotify)
    # Make a request on this URL
    try:
        request = requests.get(urlNotify, proxies=SELF_REQUESTS_PROXIES)
    except Exception:
        if(ALLOW_INSECURE_REQUESTS):
            request = requests.get(urlNotify, proxies=SELF_REQUESTS_PROXIES,
                                   verify=False)
        else:
            certif_err = "The request on recorder_notfy cannot be complete."\
                        "It may be a certificate issue. If you want to ignore"\
                        "the verification of the SSl certificate set"\
                        "ALLOW_INSECURE_REQUESTS to True"
            message_error += certif_err
            print_if_debug(certif_err)
            return html_message_error, message_error
    # If all (arguments,...) are good, an email is sent to
    # mediacourse recorder's manager that a video was published
    if str(request.content)[1:] == "'ok'":
        # Email was sent. Job is done
        print_if_debug(
            "- Request was made to URL with success. An "
            "email was sent to mediacourse recorder's "
            "manager.")
        # Save this information in the database, to avoid to
        # send multiple emails
        RecordingFileTreatment.objects.filter(
            file=source_file, ).update(file_size=file_size,
                                       email_sent=True,
                                       date_email_sent=timezone
                                       .now())
        print_if_debug(
            "- Information saved in the "
            "recorder_recordingfiletreatment table.")
    else:
        # Email wasn't sent, due to an error
        print_if_debug(
            " - Request was made to URL with failure(" + str(
                request.content)[1:] + "). An email wasn't sent to "
            "mediacourse recorder's "
            "manager.")
        # Catch the the error encountered
        html_message_error += "<li><b>Error</b> : Security error"
        " for the file " + source_file + ": <b>" + str(request.content)[1:] + \
            "</b>.<br/><i>>>>Check the publish link : " + urlNotify + \
            "</i></li> "
        message_error += "\n Error : Security error for the file " \
                         + source_file + " : " + \
                         str(request.content)[1:] + \
                         ".\n   >>> Check the publish link : " + \
                         urlNotify
    return html_message_error, message_error


def case_no_manager(html_message_error, message_error, recorder, source_file):
    # Raise error and send mail to admin if a recorder has no
    # manager and manual claiming is disabled
    if not ALLOW_MANUAL_RECORDING_CLAIMING:
        html_message_error += "<li><b>Error</b> : No manager " \
                              "for the recorder" + recorder.name \
                              + "<br/><i>>>> You must assign a " \
                                "user for this recorder" \
                                " or set the" \
                                " ALLOW_MANUAL_RECORDING" \
                                "_CLAIMING " \
                                "setting to True</i></li> "
        message_error += "\n Error : No manager for the " \
                         "recorder " + recorder.name + \
                         "\n   " \
                         ">>> You need to assign a user for this" \
                         " recorder or set the ALLOW_MANUAL" \
                         "_RECORDING_CLAIMING setting to True."
        print_if_debug(
            "\n\n*** An email recorder job [Error(s) "
            "encountered] was sent to Pod admins, "
            "with message : ***" + message_error)
        mail_admins(
            "Mediacourse job [Error(s) encountered]",
            message_error, fail_silently=False,
            html_message=html_message_error)
    else:
        RecordingFileTreatment.objects.filter(
            file=source_file).update(
            require_manual_claim=True)
        print_if_debug(
            "- There is no manager for this recording, "
            "waiting for claiming")
    return html_message_error, message_error


def file_exist(file, file_size, source_file, recorder, message_error,
               html_message_error, filename):
    if file.email_sent:
        print_if_debug(
            "- An email, with the publication link, was already sent to "
            "mediacourse recorder's manager. Nothing to do. Stopping the "
            "process for this file.")
    elif file.require_manual_claim:
        print_if_debug(
            " - Recording already treated, waiting for claiming ...")
    else:
        # File size saved in database
        file_size_in_db = file.file_size
        # Check if file is complete
        if file_size > 0 and file_size > file_size_in_db:
            print_if_debug(
                    "- This video was partially uploaded. Waiting for "
                    "complete file.")
            file = RecordingFileTreatment.objects.filter(
                file=source_file, ).update(file_size=file_size,
                                           email_sent=False)
            # This video wasn't already processed and no mail was sent to
            # recorder's manager => Process the video
        else:
            case_full_upload(html_message_error, message_error, recorder,
                             source_file, filename, file_size)
    return html_message_error, message_error


def recorder_exist(recorder, filename, message_error, html_message_error):
    # There is a connection between the directory and a recorder
    print_if_debug(
            " - This video was published by '" + recorder.name + "' recorder.")
    # Absolute path of the video

    source_file = os.path.join(DEFAULT_RECORDER_PATH, recorder.directory,
                               filename)
    # Check if this video was already processed
    recording = Recording.objects.filter(source_file=source_file).first()
    # Check if an email was already sent to recorder's manager
    # for this video
    file = RecordingFileTreatment.objects.filter(file=source_file).first()

    if recording:
        # This video was already processed
        print_if_debug(
            "- This video was already processed. Nothing to do. Stopping "
            "the process for this file.")
    else:
        # Size of the existant file
        file_size = os.path.getsize(source_file)
        if file:
            html_message_error, message_error = file_exist(file, file_size,
                                                           source_file,
                                                           recorder,
                                                           message_error,
                                                           html_message_error,
                                                           filename)
        else:
            print_if_debug(" - The job is created.")
            # The job is created but no email is sent
            RecordingFileTreatment.objects.create(file=source_file,
                                                  recorder=recorder,
                                                  file_size=file_size,
                                                  email_sent=False,
                                                  type=recorder.recording_type)
    return html_message_error, message_error


def process_directory(html_message_error, message_error, files, root):
    for filename in files:
        # Name of the directory
        dirname = root.split(os.path.sep)[-1]
        print_if_debug("\n*** Process the file " + os.path
                       .join(DEFAULT_RECORDER_PATH, dirname, filename)
                       + " ***")
        # Check if extension is a good extension (videos
        # extensions + zip)
        extension = filename.split(".")[-1]

        valid_ext = VIDEO_ALLOWED_EXTENSIONS + ("zip",)
        if not (extension in valid_ext and filename != extension):
            print_if_debug(
                    " - WARNING : " + extension + "is not a valid video "
                                                  "extension. If it should "
                                                  "be, add it to the setting "
                                                  "VIDEO_ALLOWED_EXTENSIONS")
            continue
        # Search for the recorder corresponding to this directory
        recorder = Recorder.objects.filter(
            directory=dirname).first()
        if recorder:
            html_message_error, message_error = recorder_exist(
                recorder, filename, message_error, html_message_error)
        else:
            # There isn't a connection between the directory and a recorder
            print_if_debug(" - No recorder found for this file.")
            # Catch the the error encountered
            html_message_error += "<li><b>Error</b> : No recorder found for "
            "the file " + os.path.join(
                DEFAULT_RECORDER_PATH, dirname, filename) + "<br/><i>>>>You "
            "must create a recorder"
            "for '" + dirname + "' directory.</i></li>"
            message_error += "\n   Error" \
                             ": No recorder found for the file : " + \
                             os.path.join(DEFAULT_RECORDER_PATH, dirname,
                                          filename)
            "\n   >>> You must "
            "create a recorder for '" + dirname + "' directory."
    return html_message_error, message_error


class Command(BaseCommand):
    # First possible argument : checkDirectory
    args = 'checkDirectory'
    help = 'Check the directory and subdirectories if they contain videos '
    'published by the recorders. '
    valid_args = ['checkDirectory']

    def add_arguments(self, parser):
        parser.add_argument('task')

    def handle(self, *args, **options):

        # Activate a fixed locale fr
        translation.activate(LANGUAGE_CODE)
        if options['task'] and options['task'] in self.valid_args:

            html_message_error = ""
            message_error = ""
            # Path the tree
            for root, dirs, files in os.walk(DEFAULT_RECORDER_PATH):
                html_message_error, message_error = process_directory(
                    html_message_error, message_error, files, root)
            # If there was at least one error, send an email to Pod admins
            if message_error != "":
                print_if_debug(
                        "\n\n*** An email Mediacourse recorder job [Error(s) "
                        "encountered] was sent to Pod admins, with message : "
                        "***" + message_error)
                mail_admins("Mediacourse job [Error(s) encountered]",
                            message_error, fail_silently=False,
                            html_message=html_message_error)
        else:
            print(
                "*** Warning: you must give some arguments: %s ***" %
                self.valid_args)
