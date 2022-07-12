import os
from django.conf import settings
from .models import EncodingVideo
from .models import EncodingAudio
from .models import PlaylistVideo
from .models import VideoRendition
from .models import Video
from .utils import create_outputdir, change_encoding_step, fix_video_duration, send_email_encoding, send_email, check_file, add_encoding_log, get_duration_from_mp4
from .Encoding_video import Encoding_video, FFMPEG_MP4_ENCODE
import json
import time
from django.core.files import File
import subprocess
import re
from django.core.files.images import ImageFile
from webvtt import WebVTT, Caption


if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel

FFMPEG_MP4_ENCODE = getattr(settings, "FFMPEG_MP4_ENCODE", FFMPEG_MP4_ENCODE)
EMAIL_ON_ENCODING_COMPLETION = getattr(settings, "EMAIL_ON_ENCODING_COMPLETION", True)
TRANSCRIPT = getattr(settings, "USE_TRANSCRIPTION", False)
import tempfile

if TRANSCRIPT:
    from . import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

FILE_UPLOAD_TEMP_DIR = getattr(settings, "FILE_UPLOAD_TEMP_DIR", "/tmp")


ENCODING_CHOICES = getattr(
    settings,
    "ENCODING_CHOICES",
    (
        ("audio", "audio"),
        ("360p", "360p"),
        ("480p", "480p"),
        ("720p", "720p"),
        ("1080p", "1080p"),
        ("playlist", "playlist"),
    ),
)


class Encoding_video_model(Encoding_video):

    def remove_old_data(self):
        """Remove old data."""
        video_to_encode = Video.objects.get(id=self.id)
        video_to_encode.thumbnail = None
        if video_to_encode.overview:
            image_overview = os.path.join(
                os.path.dirname(video_to_encode.overview.path), "overview.png"
            )
            if os.path.isfile(image_overview):
                os.remove(image_overview)
            video_to_encode.overview.delete()
        video_to_encode.overview = None
        video_to_encode.save()

        encoding_log_msg = ""
        encoding_log_msg += self.remove_previous_encoding_video(video_to_encode)
        encoding_log_msg += self.remove_previous_encoding_audio(video_to_encode)
        encoding_log_msg += self.remove_previous_encoding_playlist(video_to_encode)
        self.encoding_log += encoding_log_msg

    def remove_previous_encoding_video(self, video_to_encode):
        """Remove previously encoded video."""
        msg = "\n"
        previous_encoding_video = EncodingVideo.objects.filter(video=video_to_encode)
        if len(previous_encoding_video) > 0:
            msg += "\nDELETE PREVIOUS ENCODING VIDEO"
            # previous_encoding.delete()
            for encoding in previous_encoding_video:
                encoding.delete()
        else:
            msg += "Video: Nothing to delete"
        return msg

    def remove_previous_encoding_audio(self, video_to_encode):
        """Remove previously encoded audio."""
        msg = "\n"
        previous_encoding_audio = EncodingAudio.objects.filter(video=video_to_encode)
        if len(previous_encoding_audio) > 0:
            msg += "\nDELETE PREVIOUS ENCODING AUDIO"
            # previous_encoding.delete()
            for encoding in previous_encoding_audio:
                encoding.delete()
        else:
            msg += "Audio: Nothing to delete"
        return msg

    def remove_previous_encoding_playlist(self, video_to_encode):
        """Remove previously encoded playlist."""
        msg = "\n"
        previous_playlist = PlaylistVideo.objects.filter(video=video_to_encode)
        if len(previous_playlist) > 0:
            msg += "DELETE PREVIOUS PLAYLIST M3U8"
            # previous_encoding.delete()
            for encoding in previous_playlist:
                encoding.delete()
        else:
            msg += "Playlist: Nothing to delete"
        return msg
    
    def create_overview_vtt(video_id, nb_img, image, duration, overviewfilename):
        """Create overview webvtt file."""
        msg = "\ncreate overview vtt file"
        image_width = image["image_width"]
        image_height = image["image_height"]
        image_url = image["image_url"]
        # creating webvtt file
        webvtt = WebVTT()
        for i in range(0, nb_img):
            if nb_img == 99:
                start = format(float(duration * i / 100), ".3f")
                end = format(float(duration * (i + 1) / 100), ".3f")
            else:
                start = format(float(i), ".3f")
                end = format(float(i + 1), ".3f")

            start_time = time.strftime("%H:%M:%S", time.gmtime(int(str(start).split(".")[0])))
            start_time += ".%s" % (str(start).split(".")[1])
            end_time = time.strftime(
                "%H:%M:%S", time.gmtime(int(str(end).split(".")[0]))
            ) + ".%s" % (str(end).split(".")[1])
            caption = Caption(
                "%s" % start_time,
                "%s" % end_time,
                "%s#xywh=%d,%d,%d,%d"
                % (image_url, image_width * i, 0, image_width, image_height),
            )
            webvtt.captions.append(caption)
        webvtt.save(overviewfilename)
        if check_file(overviewfilename):
            msg += "\n- overviewfilename:\n%s" % overviewfilename
        else:
            msg = "overviewfilename Wrong file or path:" + "\n%s" % overviewfilename
            add_encoding_log(video_id, msg)
            change_encoding_step(video_id, -1, msg)
            send_email(msg, video_id)
        return msg

    def create_overview_image(
        self,
        video_id,
        source,
        duration,
        nb_img,
        image_width,
        overviewimagefilename,
        overviewfilename,
    ):
        """Create image overview for video navigation."""
        msg = "\ncreate overview image file"
        cmd_ffmpegthumbnailer = ""
        cmd_montage = ""
        for i in range(0, nb_img):
            stamp = "%s" % i
            if nb_img == 99:
                stamp += "%"
            else:
                stamp = time.strftime("%H:%M:%S", time.gmtime(i))
            cmd_ffmpegthumbnailer = (
                'ffmpegthumbnailer -t "%(stamp)s" \
            -s "%(image_width)s" -i %(source)s -c png \
            -o %(overviewimagefilename)s_strip%(num)s.png'
                % {
                    "stamp": stamp,
                    "source": source,
                    "num": i,
                    "overviewimagefilename": overviewimagefilename,
                    "image_width": image_width,
                }
            )
            # subprocess.getoutput(cmd_ffmpegthumbnailer)
            subprocess.run(cmd_ffmpegthumbnailer, shell=True)

            cmd_montage = (
                "montage -geometry +0+0 %(overviewimagefilename)s \
            %(overviewimagefilename)s_strip%(num)s.png \
            %(overviewimagefilename)s"
                % {"overviewimagefilename": overviewimagefilename, "num": i}
            )
            # subprocess.getoutput(cmd_montage)
            subprocess.run(cmd_montage, shell=True)

            if os.path.isfile(
                "%(overviewimagefilename)s_strip%(num)s.png"
                % {"overviewimagefilename": overviewimagefilename, "num": i}
            ):
                os.remove(
                    "%(overviewimagefilename)s_strip%(num)s.png"
                    % {"overviewimagefilename": overviewimagefilename, "num": i}
                )
        if check_file(overviewimagefilename):
            msg += "\n- overviewimagefilename:\n%s" % overviewimagefilename
            # Overview VTT
            overview = ImageFile(open(overviewimagefilename, "rb"))
            image_height = int(overview.height)
            overview.close()
            image_url = os.path.basename(overviewimagefilename)
            image = {
                "image_width": image_width,
                "image_height": image_height,
                "image_url": image_url,
            }
            msg += self.create_overview_vtt(video_id, nb_img, image, duration, overviewfilename)
            msg += self.save_overview_vtt(video_id, overviewfilename)
            #
        else:
            msg = "overviewimagefilename Wrong file or path:" + "\n%s" % overviewimagefilename
            msg += "\nthumbnailer command: \n- %s\n" % cmd_ffmpegthumbnailer
            msg += "\nmontage command: \n- %s\n" % cmd_montage
            msg += "\nduration %s - nb_img %s - image_width %s \n" % (
                duration,
                nb_img,
                image_width,
            )

            add_encoding_log(video_id, msg)
            change_encoding_step(video_id, -1, msg)
            send_email(msg, video_id)
        return msg


    def import_mp4(self, encod_video, output_dir, video_to_encode):
        filename = os.path.splitext(encod_video["filename"])[0]
        videofilenameMp4 = os.path.join(output_dir, "%s.mp4" % filename)
        msg = "\n- videofilenameMp4 :\n%s" % videofilenameMp4
        if check_file(videofilenameMp4):
            rendition = VideoRendition.objects.get(resolution=encod_video["rendition"])
            encoding, created = EncodingVideo.objects.get_or_create(
                name=self.get_encoding_choice_from_filename(filename),
                video=video_to_encode,
                rendition=rendition,
                encoding_format="video/mp4",
            )
            encoding.source_file = videofilenameMp4.replace(
                os.path.join(settings.MEDIA_ROOT, ""), ""
            )
            encoding.save()
        else:
            msg = "save_mp4_file Wrong file or path : " + "\n%s " % (videofilenameMp4)
            add_encoding_log(video_to_encode.id, msg)
            change_encoding_step(video_to_encode.id, -1, msg)
            send_email(msg, video_to_encode.id)
        return msg


    def import_thumbnail(info_encode_thumbnail, output_dir, video_to_encode):
        msg = ""
        if type(info_encode_thumbnail) is list:
            info_encode_thumbnail = info_encode_thumbnail[0]

        thumbnailfilename = os.path.join(output_dir, info_encode_thumbnail["filename"])
        if check_file(thumbnailfilename):
            if FILEPICKER:
                homedir, created = UserFolder.objects.get_or_create(
                    name="home", owner=video_to_encode.owner
                )
                videodir, created = UserFolder.objects.get_or_create(
                    name="%s" % video_to_encode.slug, owner=video_to_encode.owner
                )
                thumbnail = CustomImageModel(
                    folder=videodir, created_by=video_to_encode.owner
                )
                thumbnail.file.save(
                    info_encode_thumbnail["filename"],
                    File(open(thumbnailfilename, "rb")),
                    save=True,
                )
                thumbnail.save()
                video_to_encode.thumbnail = thumbnail
                video_to_encode.save()
            else:
                thumbnail = CustomImageModel()
                thumbnail.file.save(
                    info_encode_thumbnail["filename"],
                    File(open(thumbnailfilename, "rb")),
                    save=True,
                )
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


    def import_video(self, info_encode_video, output_dir, video_to_encode):
        msg = ""
        master_playlist = ""
        video_has_playlist = False
        for encod_video in info_encode_video:
            # PLAYLIST HLS FILE
            if encod_video["encoding_format"] == "video/mp2t":
                video_has_playlist = True
                import_msg, import_master_playlist = self.import_m3u8(
                    encod_video, output_dir, video_to_encode
                )
                msg += import_msg
                master_playlist += import_master_playlist

            if encod_video["encoding_format"] == "video/mp4":
                import_msg = self.import_mp4(encod_video, output_dir, video_to_encode)
                msg += import_msg

        if video_has_playlist:
            playlist_master_file = output_dir + "/playlist.m3u8"
            with open(playlist_master_file, "w") as f:
                f.write("#EXTM3U\n#EXT-X-VERSION:3\n" + master_playlist)

            if check_file(playlist_master_file):
                playlist, created = PlaylistVideo.objects.get_or_create(
                    name="playlist",
                    video=video_to_encode,
                    encoding_format="application/x-mpegURL",
                )
                playlist.source_file = (
                    output_dir.replace(os.path.join(settings.MEDIA_ROOT, ""), "")
                    + "/playlist.m3u8"
                )
                playlist.save()

                msg += "\n- Playlist :\n%s" % playlist_master_file
            else:
                msg = (
                    "save_playlist_master Wrong file or path : "
                    + "\n%s" % playlist_master_file
                )
                add_encoding_log(video_to_encode.id, msg)
                change_encoding_step(video_to_encode.id, -1, msg)
                send_email(msg, video_to_encode.id)
        return msg


    def create_and_save_thumbnails(source, image_width, video_id):
        """Create and save thumbnails."""
        msg = "\nCREATE AND SAVE THUMBNAILS: %s" % time.ctime()
        tempimgfile = tempfile.NamedTemporaryFile(dir=FILE_UPLOAD_TEMP_DIR, suffix="")
        for i in range(0, 3):
            percent = str((i + 1) * 25) + "%"
            cmd_ffmpegthumbnailer = (
                'ffmpegthumbnailer -t "%(percent)s" \
            -s "%(image_width)s" -i %(source)s -c png \
            -o %(tempfile)s_%(num)s.png'
                % {
                    "percent": percent,
                    "source": source,
                    "num": i,
                    "image_width": image_width,
                    "tempfile": tempimgfile.name,
                }
            )
            # subprocess.getoutput(cmd_ffmpegthumbnailer)
            subprocess.run(cmd_ffmpegthumbnailer, shell=True)
            thumbnailfilename = "%(tempfile)s_%(num)s.png" % {
                "num": i,
                "tempfile": tempimgfile.name,
            }
            if check_file(thumbnailfilename):
                if FILEPICKER:
                    video_to_encode = Video.objects.get(id=video_id)
                    homedir, created = UserFolder.objects.get_or_create(
                        name="home", owner=video_to_encode.owner
                    )
                    videodir, created = UserFolder.objects.get_or_create(
                        name="%s" % video_to_encode.slug,
                        owner=video_to_encode.owner,
                    )
                    thumbnail = CustomImageModel(
                        folder=videodir, created_by=video_to_encode.owner
                    )
                    thumbnail.file.save(
                        "%s_%s.png" % (video_to_encode.slug, i),
                        File(open(thumbnailfilename, "rb")),
                        save=True,
                    )
                    thumbnail.save()
                    if i == 0:
                        video_to_encode = Video.objects.get(id=video_id)
                        video_to_encode.thumbnail = thumbnail
                        video_to_encode.save()
                else:
                    thumbnail = CustomImageModel()
                    thumbnail.file.save(
                        "%d_%s.png" % (video_id, i),
                        File(open(thumbnailfilename, "rb")),
                        save=True,
                    )
                    thumbnail.save()
                    if i == 0:
                        video_to_encode = Video.objects.get(id=video_id)
                        video_to_encode.thumbnail = thumbnail
                        video_to_encode.save()
                # remove tempfile
                msg += "\n- thumbnailfilename %s:\n%s" % (i, thumbnail.file.path)
                os.remove(thumbnailfilename)
            else:
                msg += "\nERROR THUMBNAILS %s " % thumbnailfilename
                msg += "Wrong file or path"
                add_encoding_log(video_id, msg)
                change_encoding_step(video_id, -1, msg)
                send_email(msg, video_id)
        return msg

    def get_encoding_choice_from_filename(filename):
        choices = {}
        for choice in ENCODING_CHOICES:
            choices[choice[0][:3]] = choice[0]
        return choices.get(filename[:3], "360p")


    def import_m3u8(self, encod_video, output_dir, video_to_encode):
        msg = ""
        master_playlist = ""
        filename = os.path.splitext(encod_video["filename"])[0]
        videofilenameM3u8 = os.path.join(output_dir, "%s.m3u8" % filename)
        videofilenameTS = os.path.join(output_dir, "%s.ts" % filename)
        msg += "\n- videofilenameM3u8 :\n%s" % videofilenameM3u8
        msg += "\n- videofilenameTS :\n%s" % videofilenameTS

        rendition = VideoRendition.objects.get(resolution=encod_video["rendition"])

        int_bitrate = int(re.search(r"(\d+)k", rendition.video_bitrate, re.I).groups()[0])
        bandwidth = int_bitrate * 1000

        if check_file(videofilenameM3u8) and check_file(videofilenameTS):

            encoding, created = EncodingVideo.objects.get_or_create(
                name=self.get_encoding_choice_from_filename(filename),
                video=video_to_encode,
                rendition=rendition,
                encoding_format="video/mp2t",
            )
            encoding.source_file = videofilenameTS.replace(
                os.path.join(settings.MEDIA_ROOT, ""), ""
            )
            encoding.save()

            playlist, created = PlaylistVideo.objects.get_or_create(
                name=self.get_encoding_choice_from_filename(filename),
                video=video_to_encode,
                encoding_format="application/x-mpegURL",
            )
            playlist.source_file = videofilenameM3u8.replace(
                os.path.join(settings.MEDIA_ROOT, ""), ""
            )
            playlist.save()

            master_playlist += "#EXT-X-STREAM-INF:BANDWIDTH=%s," % bandwidth
            master_playlist += "RESOLUTION=%s\n%s\n" % (
                rendition.resolution,
                encod_video["filename"],
            )
        else:
            msg = "save_playlist_file Wrong file or path : " + "\n%s and %s" % (
                videofilenameM3u8,
                videofilenameTS,
            )
            add_encoding_log(video_to_encode.id, msg)
            change_encoding_step(video_to_encode.id, -1, msg)
            send_email(msg, video_to_encode.id)

        return msg, master_playlist

    def import_video(self, info_encode_video, output_dir, video_to_encode):
        msg = ""
        master_playlist = ""
        video_has_playlist = False
        for encod_video in info_encode_video:
            # PLAYLIST HLS FILE
            if encod_video["encoding_format"] == "video/mp2t":
                video_has_playlist = True
                import_msg, import_master_playlist = self.import_m3u8(
                    encod_video, output_dir, video_to_encode
                )
                msg += import_msg
                master_playlist += import_master_playlist

            if encod_video["encoding_format"] == "video/mp4":
                import_msg = self.import_mp4(encod_video, output_dir, video_to_encode)
                msg += import_msg

        if video_has_playlist:
            playlist_master_file = output_dir + "/playlist.m3u8"
            with open(playlist_master_file, "w") as f:
                f.write("#EXTM3U\n#EXT-X-VERSION:3\n" + master_playlist)

            if check_file(playlist_master_file):
                playlist, created = PlaylistVideo.objects.get_or_create(
                    name="playlist",
                    video=video_to_encode,
                    encoding_format="application/x-mpegURL",
                )
                playlist.source_file = (
                    output_dir.replace(os.path.join(settings.MEDIA_ROOT, ""), "")
                    + "/playlist.m3u8"
                )
                playlist.save()

                msg += "\n- Playlist :\n%s" % playlist_master_file
            else:
                msg = (
                    "save_playlist_master Wrong file or path : "
                    + "\n%s" % playlist_master_file
                )
                change_encoding_step(video_to_encode.id, -1, msg)
                send_email(msg, video_to_encode.id)
        return msg


    def video_part(self, video_to_encode, info_video, output_dir):
        msg = ""
        if info_video["has_stream_video"] and info_video.get("encode_video"):
            msg += self.import_video(
                info_video["encode_video"], output_dir, video_to_encode
            )
            video_id = video_to_encode.id
            # get the lower size of encoding mp4
            ev = EncodingVideo.objects.filter(
                video=video_to_encode, encoding_format="video/mp4"
            )
            if ev.count() == 0:
                msg = "NO MP4 FILES FOUND !"
                add_encoding_log(video_id, msg)
                change_encoding_step(video_id, -1, msg)
                send_email(msg, video_id)
                # return
            video_mp4 = sorted(ev, key=lambda m: m.height)[0]

            # create overview
            overviewfilename = "%(output_dir)s/overview.vtt" % {"output_dir": output_dir}
            image_url = "overview.png"
            overviewimagefilename = "%(output_dir)s/%(image_url)s" % {
                "output_dir": output_dir,
                "image_url": image_url,
            }
            image_width = video_mp4.width / 4  # width of generate image file
            change_encoding_step(
                video_id, 4, "encoding video file: 7/11 remove_previous_overview"
            )
            self.remove_previous_overview(overviewfilename, overviewimagefilename)
            video_duration = (
                info_video["duration"]
                if (info_video["duration"] > 0)
                else get_duration_from_mp4(video_mp4.source_file.path, output_dir)
            )
            nb_img = 99 if (video_duration > 99) else video_duration
            change_encoding_step(
                video_id, 4, "encoding video file: 8/11 create_overview_image"
            )
            msg_overview = self.create_overview_image(
                video_id,
                video_mp4.source_file.path,
                video_duration,
                nb_img,
                image_width,
                overviewimagefilename,
                overviewfilename,
            )
            add_encoding_log(video_id, "create_overview_image: %s" % msg_overview)
            # create thumbnail
            if info_video["has_stream_thumbnail"] and info_video.get("encode_thumbnail"):
                msg += self.import_thumbnail(
                    info_video["encode_thumbnail"], output_dir, video_to_encode
                )
            else:
                change_encoding_step(
                    video_id,
                    4,
                    "encoding video file : 11/11 create_and_save_thumbnails",
                )
                msg_thumbnail = self.create_and_save_thumbnails(
                    video_mp4.video.video.path, video_mp4.width, video_id
                )
                add_encoding_log(video_id, "create_and_save_thumbnails : %s" % msg_thumbnail)
        elif info_video["has_stream_video"] or info_video.get("encode_video"):
            msg += "\n- has stream video but not info video "
            add_encoding_log(video_to_encode.id, msg)
            change_encoding_step(video_to_encode.id, -1, msg)
            send_email(msg, video_to_encode.id)

        return msg

    def encoding_video(self, video_id, encoding_type):
        msg = ""
        video_to_encode = Video.objects.get(id=video_id)
        output_dir = create_outputdir(video_id, video_to_encode.video.path)
        info_video = {}

        with open(output_dir + "/info_video.json") as json_file:
            info_video = json.load(json_file)

        video_to_encode.duration = info_video["duration"]
        video_to_encode.encoding_in_progress = True
        video_to_encode.save()

        msg += self.video_part(video_to_encode, info_video, output_dir)

        msg += self.audio_part(video_to_encode, info_video, output_dir)

        video_encoding = Video.objects.get(id=video_id)

        if not info_video["has_stream_video"]:
            video_encoding.is_video = False
            video_encoding.save()

        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, 0, "done")

        video_encoding.encoding_in_progress = False
        video_encoding.save()

        fix_video_duration(video_encoding.id, output_dir)

        # End
        add_encoding_log(video_id, "End : %s" % time.ctime())
        with open(output_dir + "/encoding.log", "a") as f:
            f.write("\n\nEnd : %s" % time.ctime())

        # envois mail fin encodage
        if EMAIL_ON_ENCODING_COMPLETION:
            send_email_encoding(video_encoding)

        # Transcript
        if TRANSCRIPT and video_encoding.transcript:
            transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
            transcript_video(video_id, False)

        print("ALL is DONE")
