"""
This command is useful to check the directory DEFAULT_MEDIACOURSE_RECORDER_PATH, and its subdirectories, if they contain videos that were published by the mediacourse recorders.
The idea is to have one directory for each recorder.
Example : at the Montpellier university, there is one Multicam recorder for Polytech.
In settings, we have :
 - DEFAULT_MEDIACOURSE_RECORDER_PATH (in settings_local.py) = /data/www/%userpod%/media/uploads/
 - in Pod database(cf. Pod administration), mediacourse_recorder table : a line for the Polytech Multicam recorder, with value 'polytech' for 'directory' property
 - FTP Directory (directly on the recorder settings) : /data/www/%userpod%/media/uploads/polytech or empty (depends on vsftpd config)
So, the recorder makes a publication, via FTP, on the directory /data/www/%userpod%/media/uploads/polytech and this script checks regularly this directory.
When video files are published, an email is  sent to mediacourse recorder's manager (cf. Pod administration), with a publication link.
To have more details, see online documentation.

This script must be executed regurlaly (for an example, with a CRON task).
Example : crontab -e
*/15 * * * * /usr/bin/bash -c 'export WORKON_HOME=/data/www/%userpod%/.virtualenvs; export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3.6; cd /data/www/%userpod%/django_projects/podv2; source /usr/bin/virtualenvwrapper.sh; workon django_pod; python manage.py mediacourse checkDirectory'
"""
import os
from django.utils import translation
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

from pod.recorder.models import Recorder, Recording, RecordingFile
from pod.video.models import Video

from django.core.exceptions import ObjectDoesNotExist
import hashlib
import requests
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.core.files import File
from django.core.files.storage import default_storage
from django.utils import timezone

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
ALLOW_MANUAL_RECORDING_CLAIMING  = getattr(
    settings, 'ALLOW_MANUAL_RECORDING_CLAIMING',
    False
)
# Mode debug (0: False, 1: True)
DEBUG = 1

class Command(BaseCommand):
    # First possible argument : checkDirectory
    args = 'checkDirectory'
    help = 'Check the directory and subdirectories if they contain videos published by the recorders.'
    valid_args = ['checkDirectory']

    def add_arguments(self, parser):
        parser.add_argument('task')

    def handle(self, *args, **options):
        # Activate a fixed locale fr
        translation.activate('fr')
        if options['task'] and options['task'] in self.valid_args:
            html_message_error = ""
            message_error = ""
            # Path the tree
            for root, dirs, files in os.walk(DEFAULT_RECORDER_PATH):
                for filename in files:
                    # Name of the directory
                    dirname = root.split(os.path.sep)[-1]
                    if DEBUG:
                        print("\n*** Process the file " + os.path.join(DEFAULT_RECORDER_PATH, dirname, filename) + " ***")
                    extension = filename.split(".")[-1]
                    print(extension in VIDEO_ALLOWED_EXTENSIONS)
                    if not (extension in VIDEO_ALLOWED_EXTENSIONS and filename != extension):
                        if DEBUG:
                            print(" - " + extension + " is not a valid video extension. If it should be, add it to the setting VIDEO_ALLOWED_EXTENSIONS")
                        continue

                    # Search for the recorder corresponding to this directory
                    oRecorder = Recorder.objects.filter(directory=dirname).first()
                    if oRecorder:
                        # There is a connection between the directory and a recorder
                        if DEBUG:
                            print(" - This video was published by '" + oRecorder.name + "' recorder.")
                        # Absolute path of the video

                        source_file = os.path.join(DEFAULT_RECORDER_PATH, oRecorder.directory, filename)
                        # Check if this video was already processed
                        oRecording = Recording.objects.filter(source_file=source_file).first()
                        # Check if an email was already sent to mediacourse recorder's manager for this video
                        oFile = RecordingFile.objects.filter(file=source_file).first()

                        if oRecording:
                            # This video was already processed
                            if DEBUG:
                                print(" - This video was already processed. Nothing to do. Stopping the process for this file.")
                        else:
                            # Size of the existant file
                            file_size = default_storage.size(source_file)
                            if oFile:

                                if oFile.email_sent :
                                    if DEBUG:
                                        print(" - An email, with the publication link, was already sent to mediacourse recorder's manager. Nothing to do. Stopping the process for this file.")
                                elif oFile.require_manual_claim:
                                    if DEBUG:
                                        print(" - Recording already treated, waiting for claiming ...")
                                else:
                                    # File size saved in database
                                    file_size_in_db = oFile.file_size
                                    # Check if file is complete
                                    if file_size > 0 and file_size > file_size_in_db:
                                        if DEBUG:
                                            print(" - This video was partially uploaded. Waiting for complete file.")
                                        oFile = RecordingFile.objects.filter(file=source_file,).update(file_size=file_size, email_sent=False)
                                        # This video wasn't already processed and no mail was sent to mediacourse recorder's manager => Process the video
                                    else:
                                        if DEBUG:
                                            print(" - This video wasn't already processed and no mail was sent to mediacourse recorder's manager. Starting the process.")
                                        # Generation of the hashkey, depending on the IP address of the recorder
                                        m = hashlib.md5()
                                        m.update(oRecorder.ipunder().encode('utf-8') + oRecorder.salt.encode('utf-8'))

                                        if oRecorder.user is None:
                                            #Raise error and send mail to admin if a recorder has no manager and manual claiming is disabled
                                            if not ALLOW_MANUAL_RECORDING_CLAIMING:
                                                html_message_error += "<li><b>Error</b> : No manager for the recorder" + oRecorder.name + "<br/><i>>>> You must assign a user for this recorder or set the ALLOW_MANUAL_RECORDING_CLAIMING setting to True</i></li>"
                                                message_error += "\n   Error : No manager for the recorder " + oRecorder.name + "\n   >>> You must assign a user for this recorder or set the ALLOW_MANUAL_RECORDING_CLAIMING setting to True."
                                                if DEBUG:
                                                    print(
                                                        "\n\n*** An email Mediacourse recorder job [Error(s) encountered] was sent to Pod admins, with message : ***" + message_error)
                                                mail_admins("Mediacourse job [Error(s) encountered]", message_error,fail_silently=False, html_message=html_message_error)
                                            else:
                                                RecordingFile.objects.filter(file=source_file).update(require_manual_claim=True)
                                                if DEBUG:
                                                    print(" - There is no manager for this recording, waiting for claiming")
                                        else:
                                            # Generation of the URL to notify the mediacourse recorder's manager, of the form: https://pod.univ.fr/mediacourses_notify/?recordingPlace=192_168_1_10&mediapath=file.zip&key=77fac92a3f06d50228116898187e50e5
                                            urlNotify = '' . join([BASE_URL, "/recorder_notify/?recordingPlace=" + oRecorder.ipunder() + "&mediapath=" + filename + "&key=" + m.hexdigest()])
                                            if DEBUG:
                                                print(" - Generate the URL , with haskey, to notify the mediacourse recorder's manager : " + urlNotify)
                                            # Make a request on this URL
                                            r = requests.get(urlNotify)
                                            # If all (arguments,...) are good, an email is sent to mediacourse recorder's manager that a video was published
                                            if str(r.content)[1:] == "'ok'":
                                                # Email was sent. Job is done
                                                if DEBUG:
                                                    print(" - Request was made to URL with success. An email was sent to mediacourse recorder's manager.")
                                                # Save this information in the database, to avoid to send multiple emails
                                                oFile = RecordingFile.objects.filter(file=source_file,).update(file_size=file_size, email_sent=True, date_email_sent=timezone.now())
                                                if DEBUG:
                                                    print(" - Information saved in the multicam_job table.")
                                            else:
                                                # Email wasn't sent, due to an error
                                                if DEBUG:
                                                    print(" - Request was made to URL with failure(" + str(r.content)[1:] + "). An email wasn't sent to mediacourse recorder's manager.")
                                                # Catch the the error encountered
                                                html_message_error += "<li><b>Error</b> : Security error for the file " + source_file + " : <b>" + str(r.content)[1:] + "</b>.<br/><i>>>>Check the publish link : " + urlNotify + "</i></li>"
                                                message_error += "\n   Error : Security error for the file " + source_file + " : " + str(r.content)[1:] + ".\n   >>> Check the publish link : " + urlNotify
                            else:
                                if DEBUG:
                                    print(" - The job is created but no email is sent.")
                                # The job is created but no email is sent
                                oFile = RecordingFile.objects.create(file=source_file, file_size = file_size, email_sent=False)
                    else:
                        # There isn't a connection between the directory and a recorder
                        if DEBUG:
                            print(" - No recorder found for this file.")
                        # Catch the the error encountered
                        html_message_error += "<li><b>Error</b> : No recorder found for the file " + os.path.join(DEFAULT_RECORDER_PATH, dirname, filename) + "<br/><i>>>>You must create a recorder for '" + dirname + "' directory.</i></li>"
                        message_error += "\n   Error : No recorder found for the file : " + os.path.join(DEFAULT_RECORDER_PATH, dirname, filename) + "\n   >>> You must create a recorder for '" + dirname + "' directory."
            # If there was at least one erreor, send an email to Pod admins
            if message_error != "":
                if DEBUG:
                    print("\n\n*** An email Mediacourse recorder job [Error(s) encountered] was sent to Pod admins, with message : ***" + message_error)
                mail_admins("Mediacourse job [Error(s) encountered]", message_error, fail_silently=False, html_message=html_message_error)
        else:
            print("*** Warning: you must give some arguments: %s ***"% self.valid_args)