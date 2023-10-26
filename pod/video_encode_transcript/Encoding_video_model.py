"""Model for video encoding."""
import os
import re
from django.conf import settings
from .models import EncodingVideo
from .models import EncodingAudio
from .models import VideoRendition
from .models import PlaylistVideo
from .models import EncodingLog
from pod.video.models import Video
from pod.completion.models import Track
from django.core.files import File
from .Encoding_video import (
    Encoding_video,
    FFMPEG_NB_THUMBNAIL,
    FFMPEG_CREATE_THUMBNAIL,
    FFMPEG_CMD,
    FFMPEG_INPUT,
    FFMPEG_NB_THREADS,
)
from pod.video.models import LANG_CHOICES
import json

from .encoding_utils import (
    launch_cmd,
    check_file,
)

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

__LANG_CHOICES_DICT__ = {
    key: value for key, value in LANG_CHOICES[0][1] + LANG_CHOICES[1][1]
}
DEFAULT_LANG_TRACK = getattr(settings, "DEFAULT_LANG_TRACK", "fr")

if getattr(settings, "USE_PODFILE", False):
    __FILEPICKER__ = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
    from pod.podfile.models import CustomFileModel
else:
    __FILEPICKER__ = False
    from pod.main.models import CustomImageModel
    from pod.main.models import CustomFileModel


class Encoding_video_model(Encoding_video):
    """Encoding video model."""

    def remove_old_data(self):
        """Remove data from previous encoding."""
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
        encoding_log_msg += self.remove_previous_encoding_log(video_to_encode)
        self.add_encoding_log("remove_old_data", "", True, encoding_log_msg)

    def remove_previous_encoding_log(self, video_to_encode):
        """Remove previous logs."""
        msg = "\n"
        log_json = self.get_output_dir() + "/info_video.json"
        if os.path.exists(log_json):
            os.remove(log_json)
            msg += "\nDELETE PREVIOUS ENCODING LOG"
        else:
            msg += "Audio: Nothing to delete"
        return msg

    def remove_previous_encoding_objects(self, model_class, video_to_encode):
        """Remove previously encoded objects of the given model."""
        msg = "\n"
        object_type = model_class.__name__
        object_type = re.sub(r"([A-Z])", r" \1", object_type).upper()
        previous_encoding_video = model_class.objects.filter(video=video_to_encode)
        if len(previous_encoding_video) > 0:
            msg += "DELETE PREVIOUS{}".format(object_type)
            # previous_encoding.delete()
            for encoding in previous_encoding_video:
                encoding.delete()
        else:
            msg += "Video: Nothing to delete"
        return msg

    def remove_previous_encoding_video(self, video_to_encode):
        """Remove previously encoded video."""
        return self.remove_previous_encoding_objects(EncodingVideo, video_to_encode)

    def remove_previous_encoding_audio(self, video_to_encode):
        """Remove previously encoded audio."""
        return self.remove_previous_encoding_objects(EncodingAudio, video_to_encode)

    def remove_previous_encoding_playlist(self, video_to_encode):
        """Remove previously encoded playlist."""
        return self.remove_previous_encoding_objects(PlaylistVideo, video_to_encode)

    def get_true_path(self, original):
        """Get the true path by replacing the MEDIA_ROOT from the original path."""
        return original.replace(os.path.join(settings.MEDIA_ROOT, ""), "")

    def store_json_list_mp3_m4a_files(self, info_video, video_to_encode):
        """Store JSON list of MP3 and M4A files for encoding."""
        encoding_list = ["list_m4a_files", "list_mp3_files"]
        for encode_item in encoding_list:
            mp3_files = info_video[encode_item]
            for audio_file in mp3_files:
                if not check_file(mp3_files[audio_file]):
                    continue
                encoding, created = EncodingAudio.objects.get_or_create(
                    name="audio",
                    video=video_to_encode,
                    encoding_format=(
                        "audio/mp3" if (encode_item == "list_mp3_files") else "video/mp4"
                    ),
                    # need to double check path
                    source_file=self.get_true_path(mp3_files[audio_file]),
                )

    def store_json_list_mp4_hls_files(self, info_video, video_to_encode):
        mp4_files = info_video["list_mp4_files"]
        for video_file in mp4_files:
            if not check_file(mp4_files[video_file]):
                continue
            rendition = VideoRendition.objects.get(resolution__contains="x" + video_file)
            encod_name = video_file + "p"
            encoding, created = EncodingVideo.objects.get_or_create(
                name=encod_name,
                video=video_to_encode,
                rendition=rendition,
                encoding_format="video/mp4",
                source_file=self.get_true_path(mp4_files[video_file]),
            )

        hls_files = info_video["list_hls_files"]
        for video_file in hls_files:
            if not check_file(hls_files[video_file]):
                continue
            rendition = VideoRendition.objects.get(resolution__contains="x" + video_file)
            encod_name = video_file + "p"
            encoding, created = PlaylistVideo.objects.get_or_create(
                name=encod_name,
                video=video_to_encode,
                encoding_format="application/x-mpegURL",
                source_file=self.get_true_path(hls_files[video_file]),
            )
            ts_file = hls_files[video_file].replace(".m3u8", ".ts")
            if check_file(ts_file):
                encoding, created = EncodingVideo.objects.get_or_create(
                    name=encod_name,
                    video=video_to_encode,
                    rendition=rendition,
                    encoding_format="video/mp2t",
                    source_file=self.get_true_path(ts_file),
                )

        if check_file(os.path.join(self.get_output_dir(), "livestream.m3u8")):
            playlist_file = self.get_true_path(
                os.path.join(self.get_output_dir(), "livestream.m3u8")
            )
            encoding, created = PlaylistVideo.objects.get_or_create(
                name="playlist",
                video=video_to_encode,
                encoding_format="application/x-mpegURL",
                source_file=playlist_file,
            )

    def store_json_encoding_log(self, info_video, video_to_encode):
        # Need to modify start and stop
        log_to_text = ""
        # logs = info_video["encoding_log"]
        log_to_text = log_to_text + "Start : " + self.start
        """
        for log in logs:
            log_to_text = log_to_text + "[" + log + "]\n\n"
            logdetails = logs[log]
            for logcate in logdetails:
                log_to_text = (
                    log_to_text
                    + "- "
                    + logcate
                    + " : \n"
                    + str(logdetails[logcate])
                    + "\n"
                )
        """
        # add path to log file to easily open it
        log_to_text = log_to_text + "\nLog File : \n"
        log_to_text = log_to_text + self.get_output_dir() + "/info_video.json"
        log_to_text = log_to_text + "\nEnd : " + self.stop

        encoding_log, created = EncodingLog.objects.get_or_create(video=video_to_encode)
        encoding_log.log = log_to_text
        encoding_log.logfile = self.get_true_path(
            self.get_output_dir() + "/info_video.json"
        )
        encoding_log.save()

    def store_json_list_subtitle_files(self, info_video, video_to_encode):
        list_subtitle_files = info_video["list_subtitle_files"]
        if __FILEPICKER__:
            videodir, created = UserFolder.objects.get_or_create(
                name="%s" % video_to_encode.slug,
                owner=video_to_encode.owner,
            )

        for sub in list_subtitle_files:
            if not check_file(list_subtitle_files[sub][1]):
                continue
            if __FILEPICKER__:
                podfile, created = CustomFileModel.objects.get_or_create(
                    file=self.get_true_path(list_subtitle_files[sub][1]),
                    name=list_subtitle_files[sub][1],
                    description="A subtitle file",
                    created_by=video_to_encode.owner,
                    folder=videodir,
                )
            else:
                podfile = CustomFileModel()
                podfile.file = self.get_true_path(list_subtitle_files[sub][1])

            print("subtitle lang: %s " % list_subtitle_files[sub][0])

            sub_lang = list_subtitle_files[sub][0]
            track_lang = (
                sub_lang[:2]
                if (__LANG_CHOICES_DICT__.get(sub_lang[:2]))
                else DEFAULT_LANG_TRACK
            )

            Track.objects.get_or_create(
                video=video_to_encode,
                kind="subtitles",
                lang=track_lang,
                src=podfile,
                enrich_ready=True,
            )

    def store_json_list_thumbnail_files(self, info_video):
        """store_json_list_thumbnail_files."""
        video = Video.objects.get(id=self.id)
        list_thumbnail_files = info_video["list_thumbnail_files"]
        thumbnail = CustomImageModel()
        if __FILEPICKER__:
            videodir, created = UserFolder.objects.get_or_create(
                name="%s" % video.slug,
                owner=video.owner,
            )
            thumbnail = CustomImageModel(folder=videodir, created_by=video.owner)
        for index, thumbnail_path in enumerate(list_thumbnail_files):
            if check_file(list_thumbnail_files[thumbnail_path]):
                thumbnail.file.save(
                    "%s_%s.png" % (video.slug, thumbnail_path),
                    File(open(list_thumbnail_files[thumbnail_path], "rb")),
                    save=True,
                )
                thumbnail.save()
                if index == 1 and thumbnail.id:
                    video.thumbnail = thumbnail
                    video.save()
                # rm temp location
                os.remove(list_thumbnail_files[thumbnail_path])
        return video

    def store_json_list_overview_files(self, info_video):
        list_overview_files = info_video["list_overview_files"]
        video = Video.objects.get(id=self.id)
        if len(list_overview_files) > 0:
            vtt_file = (
                list_overview_files["0"]
                if ".vtt" in list_overview_files["0"]
                else list_overview_files["1"]
            )
            video.overview = self.get_true_path(vtt_file)
            video.save()
        return video

    def store_json_info(self):
        """Open json file and store its data in current instance."""
        with open(self.get_output_dir() + "/info_video.json") as json_file:
            info_video = json.load(json_file)
            video_to_encode = Video.objects.get(id=self.id)
            video_to_encode.duration = info_video["duration"]
            video_to_encode.save()

            self.store_json_list_mp3_m4a_files(info_video, video_to_encode)
            self.store_json_list_mp4_hls_files(info_video, video_to_encode)
            self.store_json_encoding_log(info_video, video_to_encode)
            self.store_json_list_subtitle_files(info_video, video_to_encode)
            # update and create new video to be sur that thumbnail and overview be present
            self.store_json_list_thumbnail_files(info_video)
            video = self.store_json_list_overview_files(info_video)

            return video

    def get_create_thumbnail_command_from_video(self, video_to_encode):
        """Create command line to generate thumbnails from video."""
        thumbnail_command = "%s " % FFMPEG_CMD
        ev = EncodingVideo.objects.filter(
            video=video_to_encode, encoding_format="video/mp4"
        )
        encoding_log, created = EncodingLog.objects.get_or_create(video=video_to_encode)
        if not created:
            encoding_log.log = ""
        encoding_log.log += "\n----------------------------------------"
        if ev.count() == 0:
            encoding_log.log += "\nget_create_thumbnail_command_from_video"
            encoding_log.log += "\nNO MP4 FILES FOUND!"
            return ""
        video_mp4 = sorted(ev, key=lambda m: m.height)[0]
        input_file = video_mp4.source_file.path
        thumbnail_command += FFMPEG_INPUT % {
            "input": input_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }
        output_file = os.path.join(self.output_dir, "thumbnail")
        thumbnail_command += FFMPEG_CREATE_THUMBNAIL % {
            "duration": self.duration,
            "nb_thumbnail": FFMPEG_NB_THUMBNAIL,
            "output": output_file,
        }
        for nb in range(0, FFMPEG_NB_THUMBNAIL):
            num_thumb = str(nb + 1)
            self.list_thumbnail_files[num_thumb] = "%s_000%s.png" % (
                output_file,
                num_thumb,
            )
        encoding_log.log += "\n %s" % thumbnail_command
        encoding_log.save()
        return thumbnail_command

    def recreate_thumbnail(self):
        self.create_output_dir()
        self.get_video_data()
        info_video = {}
        for attribute, value in self.__dict__.items():
            info_video[attribute] = value
        video_to_encode = Video.objects.get(id=self.id)
        encoding_log, created = EncodingLog.objects.get_or_create(video=video_to_encode)
        if len(self.list_image_track) > 0:
            thumbnail_command = self.get_extract_thumbnail_command()
            return_value, return_msg = launch_cmd(thumbnail_command)
            if not created:
                encoding_log.log = ""
            encoding_log.log += "\n----------------------------------------"
            encoding_log.log += "\n extract_thumbnail_command"
            encoding_log.log += "\n %s" % thumbnail_command
            encoding_log.log += "\n %s" % return_value
            encoding_log.log += "\n %s" % return_msg
        elif self.is_video():
            thumbnail_command = self.get_create_thumbnail_command_from_video(
                video_to_encode
            )
            if thumbnail_command:
                return_value, return_msg = launch_cmd(thumbnail_command)
                encoding_log.log += "\n----------------------------------------"
                encoding_log.log += "\n create_thumbnail_command"
                encoding_log.log += "\n %s" % thumbnail_command
                encoding_log.log += "\n %s" % return_value
                encoding_log.log += "\n %s" % return_msg
        encoding_log.save()
        if len(self.list_thumbnail_files) > 0:
            info_video["list_thumbnail_files"] = self.list_thumbnail_files
            self.store_json_list_thumbnail_files(info_video)

    def encode_video(self):
        """Start video encoding."""
        self.start_encode()
