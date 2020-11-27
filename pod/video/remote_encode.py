from django.conf import settings

import time
import logging
import threading
import subprocess
import shlex
import os
import json
import re

from .models import VideoRendition
from .models import EncodingVideo
from .models import EncodingLog
from .models import PlaylistVideo
from .models import Video

from .encode import remove_old_data

from .utils import change_encoding_step, add_encoding_log, check_file
from .utils import create_outputdir, send_email, send_email_encoding

log = logging.getLogger(__name__)

DEBUG = getattr(settings, 'DEBUG', True)

EMAIL_ON_ENCODING_COMPLETION = getattr(
    settings, 'EMAIL_ON_ENCODING_COMPLETION', True)

SSH_REMOTE_USER = getattr(
    settings, 'SSH_REMOTE_USER', "")
SSH_REMOTE_HOST = getattr(
    settings, 'SSH_REMOTE_HOST', "")


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
    msg = ""
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
        cmd = "./pod-encoding/submit.sh \
            -n encoding-{video_id} -i {video_input} \
            -v {video_id} -u {user_hashkey}".format(
            video_id=video_id,
            video_input=video_to_encode.video,
            user_hashkey=video_to_encode.owner.owner.hashkey
        )

        remote_cmd = "ssh {user}@{host} \"{cmd}\"".format(
            user=SSH_REMOTE_USER, host=SSH_REMOTE_HOST, cmd=cmd)

        if DEBUG:
            print(remote_cmd)

        try:
            output = subprocess.run(
                shlex.split(remote_cmd), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            if output.returncode != 0:
                msg += 20*"////" + "\n"
                msg += "ERROR RETURN CODE: {0}\n".format(output.returncode)
                msg += output
                add_encoding_log(video_id, msg)
                change_encoding_step(video_id, -1, msg)
                send_email(msg, video_id)
        except subprocess.CalledProcessError as e:
            # raise RuntimeError('ffprobe returned non-zero status: {}'.format(
            # e.stderr))
            msg += 20*"////" + "\n"
            msg += "Runtime Error: {0}\n".format(e)
            add_encoding_log(video_id, msg)
            change_encoding_step(video_id, -1, msg)
            send_email(msg, video_id)
        except OSError as err:
            # raise OSError(e.errno, 'ffprobe not found: {}'.format(e.strerror)
            msg += 20*"////" + "\n"
            msg += "OS error: {0}\n".format(err)
            add_encoding_log(video_id, msg)
            change_encoding_step(video_id, -1, msg)
            send_email(msg, video_id)

    else:
        msg += "Wrong file or path : "\
            + "\n%s" % video_to_encode.video.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)


def store_remote_encoding_video(video_id):
    msg = ""
    video_to_encode = Video.objects.get(id=video_id)
    output_dir = create_outputdir(video_id, video_to_encode.video.path)

    # /usr/local/django_projects/podv2/pod/media/videos/fa131629fb906539f440ce16d7de8d62280fe087e90e546e4a6b49259b9a2424/12690
    print(output_dir)

    info_video = {}

    with open(output_dir + "/info_video.json") as json_file:
        info_video = json.load(json_file)

    print(json.dumps(info_video, indent=2))

    print(info_video["duration"])

    if info_video["has_stream_video"] == "true":
        msg += import_remote_video(info_video, output_dir, video_to_encode)

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


def import_remote_video(info_video, output_dir, video_to_encode):
    msg = ""
    master_playlist = ""
    video_has_playlist = False
    for encod_video in info_video["encode_video"]:
        # PLAYLIST HLS FILE
        if encod_video["encoding_format"] == "video/mp2t":
            video_has_playlist = True
            import_msg, import_master_playlist = import_m3u8(
                encod_video,
                output_dir,
                video_to_encode
            )
            msg += import_msg
            master_playlist += import_master_playlist

        if encod_video["encoding_format"] == "video/mp4":
            import_msg = import_mp4(encod_video)
            msg += import_msg

    if video_has_playlist:
        playlist_master_file = output_dir + "/playlist.m3u8"
        with open(playlist_master_file, "w") as f:
            f.write("#EXTM3U\n#EXT-X-VERSION:3\n"+master_playlist)

        if check_file(playlist_master_file):
            playlist, created = PlaylistVideo.objects.get_or_create(
                name="playlist",
                video=video_to_encode,
                encoding_format="application/x-mpegURL")
            playlist.source_file = output_dir.replace(
                os.path.join(settings.MEDIA_ROOT, ""), '')
            playlist.source_file += "/playlist.m3u8"
            playlist.save()

            msg += "\n- Playlist :\n%s" % playlist_master_file
        else:
            msg = "save_playlist_master Wrong file or path : "\
                + "\n%s" % playlist_master_file
            add_encoding_log(video_to_encode.id, msg)
            change_encoding_step(video_to_encode.id, -1, msg)
            send_email(msg, video_to_encode.id)
    return msg


def import_mp4(encod_video):
    return "coucou"


def import_m3u8(encod_video, output_dir, video_to_encode):
    msg = ""
    master_playlist = ""
    filename = os.path.splitext(encod_video["filename"])[0]
    videofilenameM3u8 = os.path.join(
        output_dir, "%s.m3u8" % filename)
    videofilenameTS = os.path.join(output_dir, "%s.ts" % filename)
    msg += "\n- videofilenameM3u8 :\n%s" % videofilenameM3u8
    msg += "\n- videofilenameTS :\n%s" % videofilenameTS

    rendition = VideoRendition.objects.get(
        resolution=encod_video["rendition"])

    int_bitrate = int(
        re.search(r"(\d+)k", rendition.video_bitrate, re.I
                  ).groups()[0])
    bandwidth = int_bitrate * 1000

    if (
        check_file(videofilenameM3u8) and
        check_file(videofilenameTS)
    ):

        encoding, created = EncodingVideo.objects.get_or_create(
            name=filename,
            video=video_to_encode,
            rendition=rendition,
            encoding_format="video/mp2t")
        encoding.source_file = videofilenameTS.replace(
            os.path.join(settings.MEDIA_ROOT, ""), '')
        encoding.save()

        playlist, created = PlaylistVideo.objects.get_or_create(
            name=filename,
            video=video_to_encode,
            encoding_format="application/x-mpegURL")
        playlist.source_file = videofilenameM3u8.replace(
            os.path.join(settings.MEDIA_ROOT, ""), '')
        playlist.save()

        master_playlist += "#EXT-X-STREAM-INF:BANDWIDTH=%s,\
                RESOLUTION=%s\n%s.m3u8\n" % (
            bandwidth,
            rendition.resolution,
            encod_video["filename"]
        )
    else:
        msg = "save_playlist_file Wrong file or path : "\
            + "\n%s and %s" % (videofilenameM3u8, videofilenameTS)
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)

    return msg, master_playlist
