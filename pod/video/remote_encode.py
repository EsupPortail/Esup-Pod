from django.conf import settings

import time
import logging
import threading

from .models import Video, EncodingLog
from .encode import remove_old_data

from .utils import change_encoding_step, add_encoding_log, check_file
from .utils import create_outputdir, send_email, send_email_encoding

log = logging.getLogger(__name__)

EMAIL_ON_ENCODING_COMPLETION = getattr(
    settings, 'EMAIL_ON_ENCODING_COMPLETION', True)


# ##########################################################################
# REMOTE ENCODE VIDEO : THREAD TO LAUNCH ENCODE
# ##########################################################################


def start_store_remote_encoding_video(video_id):
    log.info("START STORE ENCODED FILES FOR VIDEO ID %s" % video_id)
    t = threading.Thread(target=store_remote_encoding_video,
                         args=[video_id])
    t.setDaemon(True)
    t.start()

# ##########################################################################
# REMOTE ENCODE VIDEO : MAIN FUNCTION
# ##########################################################################


def remote_encode_video(video_id):
    start = "Start at : %s" % time.ctime()

    video_to_encode = Video.objects.get(id=video_id)
    video_to_encode.encoding_in_progress = True
    video_to_encode.save()
    change_encoding_step(video_id, 0, "start")

    encoding_log, created = EncodingLog.objects.get_or_create(
        video=Video.objects.get(id=video_id))
    encoding_log.log = "%s" % start
    encoding_log.save()

    if check_file(video_to_encode.video.path):
        change_encoding_step(video_id, 1, "remove old data")
        remove_msg = remove_old_data(video_id)
        add_encoding_log(video_id, "remove old data : %s" % remove_msg)

        # create video dir
        change_encoding_step(video_id, 2, "create output dir")
        output_dir = create_outputdir(video_id, video_to_encode.video.path)
        add_encoding_log(video_id, "output_dir : %s" % output_dir)

        # clear log file
        open(output_dir + "/encoding.log", 'w').close()
        with open(output_dir + "/encoding.log", "a") as f:
            f.write("%s\n" % start)

        # launch remote encoding

    else:
        msg = "Wrong file or path : "\
            + "\n%s" % video_to_encode.video.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)


def store_remote_encoding_video(video_id):
    video_to_encode = Video.objects.get(id=video_id)
    output_dir = create_outputdir(video_id, video_to_encode.video.path)
    # get info_video_json
    # check output_dir files
    # if video -> create thumbnails if not exist and create overview

    change_encoding_step(video_id, 0, "done")

    video_to_encode = Video.objects.get(id=video_id)
    video_to_encode.encoding_in_progress = False
    video_to_encode.save()

    # End
    add_encoding_log(video_id, "End : %s" % time.ctime())
    with open(output_dir + "/encoding.log", "a") as f:
        f.write("\n\nEnd : %s" % time.ctime())

    # envois mail fin encodage
    if EMAIL_ON_ENCODING_COMPLETION:
        send_email_encoding(video_to_encode)

    # Transcript
    """
    main_threaded_transcript(video_id) if (
            TRANSCRIPT and video_to_encode.transcript
        ) else False
    """
    print('ALL is DONE')
