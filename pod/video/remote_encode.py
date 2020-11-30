from django.conf import settings
from django.core.files import File

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
from .models import EncodingAudio
from .models import EncodingLog
from .models import PlaylistVideo
from .models import Video

from .encode import remove_old_data, remove_previous_overview
from .encode import create_overview_image, create_and_save_thumbnails

from .utils import change_encoding_step, add_encoding_log, check_file
from .utils import create_outputdir, send_email, send_email_encoding

if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel

log = logging.getLogger(__name__)

DEBUG = getattr(settings, 'DEBUG', True)

EMAIL_ON_ENCODING_COMPLETION = getattr(
    settings, 'EMAIL_ON_ENCODING_COMPLETION', True)

SSH_REMOTE_USER = getattr(
    settings, 'SSH_REMOTE_USER', "")
SSH_REMOTE_HOST = getattr(
    settings, 'SSH_REMOTE_HOST', "")
SSH_REMOTE_KEY = getattr(
    settings, 'SSH_REMOTE_KEY', "")


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
        video=video_to_encode)
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
            -v {video_id} -u {user_hashkey} -d {debug}".format(
            video_id=video_id,
            video_input=video_to_encode.video,
            user_hashkey=video_to_encode.owner.owner.hashkey,
            debug=DEBUG
        )

        key = " -i %s " % SSH_REMOTE_KEY if SSH_REMOTE_KEY != "" else ""

        remote_cmd = "ssh {key} {user}@{host} \"{cmd}\"".format(
            key=key, user=SSH_REMOTE_USER, host=SSH_REMOTE_HOST, cmd=cmd)

        if DEBUG:
            print(remote_cmd)

        process_cmd(remote_cmd, video_id)

    else:
        msg += "Wrong file or path : "\
            + "\n%s" % video_to_encode.video.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)


def process_cmd(remote_cmd, video_id):
    msg = ""
    try:
        output = subprocess.run(
            shlex.split(remote_cmd), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        add_encoding_log(video_id, "slurm output : %s" % output.stdout)
        if DEBUG:
            print(output.stdout)
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


def store_remote_encoding_video(video_id):
    msg = ""
    video_to_encode = Video.objects.get(id=video_id)
    output_dir = create_outputdir(video_id, video_to_encode.video.path)
    info_video = {}

    with open(output_dir + "/info_video.json") as json_file:
        info_video = json.load(json_file)

    if DEBUG:
        print(output_dir)
        print(json.dumps(info_video, indent=2))

    video_to_encode.duration = info_video["duration"]
    video_to_encode.encoding_in_progress = True
    video_to_encode.save()

    msg += remote_video_part(video_to_encode, info_video, output_dir)

    msg += remote_audio_part(video_to_encode, info_video, output_dir)

    if not info_video["has_stream_video"]:
        video_to_encode = Video.objects.get(id=video_id)
        video_to_encode.is_video = False
        video_to_encode.save()

    add_encoding_log(video_id, msg)
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


def remote_audio_part(video_to_encode, info_video, output_dir):
    msg = ""
    if (
            info_video["has_stream_audio"]
            and info_video.get("encode_audio")):
        msg += import_remote_audio(
            info_video["encode_audio"],
            output_dir,
            video_to_encode
        )
        if (
                info_video["has_stream_thumbnail"]
                and info_video.get("encode_thumbnail")):
            msg += import_remote_thumbnail(
                info_video["encode_thumbnail"],
                output_dir,
                video_to_encode
            )
    elif (
            info_video["has_stream_audio"]
            or info_video.get("encode_audio")):
        msg += "\n- has stream audio but not info audio in json "
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
    return msg


def remote_video_part(video_to_encode, info_video, output_dir):
    msg = ""
    if (
            info_video["has_stream_video"]
            and info_video.get("encode_video")):
        msg += import_remote_video(
            info_video["encode_video"],
            output_dir,
            video_to_encode
        )
        video_id = video_to_encode.id
        # get the lower size of encoding mp4
        ev = EncodingVideo.objects.filter(
            video=video_to_encode, encoding_format="video/mp4")
        if ev.count() == 0:
            msg = "NO MP4 FILES FOUND !"
            add_encoding_log(video_id, msg)
            change_encoding_step(video_id, -1, msg)
            send_email(msg, video_id)
            # return
        video_mp4 = sorted(ev, key=lambda m: m.height)[0]

        # create overview
        overviewfilename = '%(output_dir)s/overview.vtt' % {
            'output_dir': output_dir}
        image_url = 'overview.png'
        overviewimagefilename = '%(output_dir)s/%(image_url)s' % {
            'output_dir': output_dir, 'image_url': image_url}
        image_width = video_mp4.width / 4  # width of generate image file
        change_encoding_step(
            video_id, 4,
            "encoding video file : 7/11 remove_previous_overview")
        remove_previous_overview(overviewfilename, overviewimagefilename)
        nb_img = 99 if (
            info_video["duration"] > 99) else info_video["duration"]
        change_encoding_step(
            video_id, 4,
            "encoding video file : 8/11 create_overview_image")
        msg_overview = create_overview_image(
            video_id,
            video_mp4.video.video.path, info_video["duration"],
            nb_img, image_width, overviewimagefilename, overviewfilename)
        add_encoding_log(
            video_id,
            "create_overview_image : %s" % msg_overview)
        # create thumbnail
        if (
                info_video["has_stream_thumbnail"]
                and info_video.get("encode_thumbnail")):
            msg += import_remote_thumbnail(
                info_video["encode_thumbnail"],
                output_dir,
                video_to_encode
            )
        else:
            change_encoding_step(
                video_id, 4,
                "encoding video file : 11/11 create_and_save_thumbnails")
            msg_thumbnail = create_and_save_thumbnails(
                video_mp4.video.video.path, video_mp4.width, video_id)
            add_encoding_log(
                video_id,
                "create_and_save_thumbnails : %s" % msg_thumbnail)
    elif (
            info_video["has_stream_video"]
            or info_video.get("encode_video")):
        msg += "\n- has stream video but not info video "
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)

    return msg


def import_remote_thumbnail(
    info_encode_thumbnail,
    output_dir,
    video_to_encode
):
    msg = ""
    if type(info_encode_thumbnail) is list:
        info_encode_thumbnail = info_encode_thumbnail[0]

    thumbnailfilename = os.path.join(
        output_dir, info_encode_thumbnail["filename"])
    if check_file(thumbnailfilename):
        if FILEPICKER:
            homedir, created = UserFolder.objects.get_or_create(
                name='home',
                owner=video_to_encode.owner)
            videodir, created = UserFolder.objects.get_or_create(
                name='%s' % video_to_encode.slug,
                owner=video_to_encode.owner)
            thumbnail = CustomImageModel(
                folder=videodir,
                created_by=video_to_encode.owner
            )
            thumbnail.file.save(
                info_encode_thumbnail["filename"],
                File(open(thumbnailfilename, "rb")),
                save=True)
            thumbnail.save()
            video_to_encode.thumbnail = thumbnail
            video_to_encode.save()
        else:
            thumbnail = CustomImageModel()
            thumbnail.file.save(
                info_encode_thumbnail["filename"],
                File(open(thumbnailfilename, "rb")),
                save=True)
            thumbnail.save()
            video_to_encode.thumbnail = thumbnail
            video_to_encode.save()
        # remove tempfile
        msg += "\n- thumbnailfilename :\n%s" % (thumbnail.file.path)
        os.remove(thumbnailfilename)
    else:
        msg += "\nERROR THUMBNAILS %s " % thumbnailfilename
        msg += "Wrong file or path"
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
    return msg


def import_remote_audio(info_encode_audio, output_dir, video_to_encode):
    msg = ""
    if type(info_encode_audio) is dict:
        info_encode_audio = [info_encode_audio]
    for encode_audio in info_encode_audio:
        if encode_audio["encoding_format"] == "audio/mp3":
            filename = os.path.splitext(encode_audio["filename"])[0]
            audiofilename = os.path.join(output_dir, "%s.mp3" % filename)
            if check_file(audiofilename):
                encoding, created = EncodingAudio.objects.get_or_create(
                    name="audio",
                    video=video_to_encode,
                    encoding_format="audio/mp3")
                encoding.source_file = audiofilename.replace(
                    os.path.join(settings.MEDIA_ROOT, ""), '')
                encoding.save()
                msg += "\n- encode_video_mp3 :\n%s" % audiofilename
            else:
                msg += "\n- encode_video_mp3 Wrong file or path "
                msg += audiofilename + " "
                add_encoding_log(video_to_encode.id, msg)
                change_encoding_step(video_to_encode.id, -1, msg)
                send_email(msg, video_to_encode.id)
        if encode_audio["encoding_format"] == "video/mp4":
            filename = os.path.splitext(encode_audio["filename"])[0]
            audiofilename = os.path.join(output_dir, "%s.m4a" % filename)
            if check_file(audiofilename):
                encoding, created = EncodingAudio.objects.get_or_create(
                    name="audio",
                    video=video_to_encode,
                    encoding_format="video/mp4")
                encoding.source_file = audiofilename.replace(
                    os.path.join(settings.MEDIA_ROOT, ""), '')
                encoding.save()
                msg += "\n- encode_video_m4a :\n%s" % audiofilename
            else:
                msg += "\n- encode_video_m4a Wrong file or path "
                msg += audiofilename + " "
                add_encoding_log(video_to_encode.id, msg)
                change_encoding_step(video_to_encode.id, -1, msg)
                send_email(msg, video_to_encode.id)
    return msg


def import_remote_video(info_encode_video, output_dir, video_to_encode):
    msg = ""
    master_playlist = ""
    video_has_playlist = False
    for encod_video in info_encode_video:
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
            import_msg = import_mp4(encod_video,
                                    output_dir,
                                    video_to_encode)
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
                os.path.join(settings.MEDIA_ROOT, ""), '') + "/playlist.m3u8"
            playlist.save()

            msg += "\n- Playlist :\n%s" % playlist_master_file
        else:
            msg = "save_playlist_master Wrong file or path : "\
                + "\n%s" % playlist_master_file
            add_encoding_log(video_to_encode.id, msg)
            change_encoding_step(video_to_encode.id, -1, msg)
            send_email(msg, video_to_encode.id)
    return msg


def import_mp4(encod_video, output_dir, video_to_encode):
    filename = os.path.splitext(encod_video["filename"])[0]
    videofilenameMp4 = os.path.join(output_dir, "%s.mp4" % filename)
    msg = "\n- videofilenameMp4 :\n%s" % videofilenameMp4
    if check_file(videofilenameMp4):
        rendition = VideoRendition.objects.get(
            resolution=encod_video["rendition"])
        encoding, created = EncodingVideo.objects.get_or_create(
            name=filename,
            video=video_to_encode,
            rendition=rendition,
            encoding_format="video/mp4")
        encoding.source_file = videofilenameMp4.replace(
            os.path.join(settings.MEDIA_ROOT, ""), '')
        encoding.save()
    else:
        msg = "save_mp4_file Wrong file or path : "\
            + "\n%s " % (videofilenameMp4)
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
    return msg


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

        master_playlist += "#EXT-X-STREAM-INF:BANDWIDTH=%s," % bandwidth
        master_playlist += "RESOLUTION=%s\n%s\n" % (
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
