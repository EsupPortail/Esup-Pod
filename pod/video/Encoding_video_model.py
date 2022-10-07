import os
from django.conf import settings
from .models import EncodingVideo
from .models import EncodingAudio
from .models import VideoRendition
from .models import PlaylistVideo
from .models import EncodingLog
from .models import Video
from pod.completion.models import Track
from django.core.files import File
from .utils import check_file
from .Encoding_video import Encoding_video, FFMPEG_MP4_ENCODE
import json
from pod.main.lang_settings import ALL_LANG_CHOICES, PREF_LANG_CHOICES

FFMPEG_MP4_ENCODE = getattr(settings, "FFMPEG_MP4_ENCODE", FFMPEG_MP4_ENCODE)
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
LANG_CHOICES = getattr(
    settings,
    "LANG_CHOICES",
    ((" ", PREF_LANG_CHOICES), ("----------", ALL_LANG_CHOICES)),
)
LANG_CHOICES_DICT = {key: value for key, value in LANG_CHOICES[0][1] + LANG_CHOICES[1][1]}
DEFAULT_LANG_TRACK = getattr(settings, "DEFAULT_LANG_TRACK", "fr")

if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
    from pod.podfile.models import CustomFileModel
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel
    from pod.main.models import CustomFileModel


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
        encoding_log_msg += self.remove_previous_encoding_log(video_to_encode)
        self.add_encoding_log("remove_old_data", "", True, encoding_log_msg)

    def remove_previous_encoding_log(self, video_to_encode):
        """Remove previously logs"""
        msg = "\n"
        log_json = self.get_output_dir() + "/info_video.json"
        if os.path.exists(log_json):
            os.remove(log_json)
            msg += "\nDELETE PREVIOUS ENCODING LOG"
        else:
            msg += "Audio: Nothing to delete"
        return msg

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

    def get_true_path(self, original):
        return original.replace(os.path.join(settings.MEDIA_ROOT, ""), "")

    def store_json_list_mp3_m4a_files(self, info_video, video_to_encode):
        encoding_list = ["list_m4a_files", "list_mp3_files"]
        for encode_item in encoding_list:
            mp3_files = info_video[encode_item]
            for audio_file in mp3_files:
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
        for list_video in ["list_hls_files", "list_mp4_files"]:
            mp4_files = info_video[list_video]
            for video_file in mp4_files:
                rendition = VideoRendition.objects.get(
                    resolution__contains="x" + video_file
                )
                encod_name = video_file + "p"
                if list_video == "list_mp4_files":
                    encoding, created = EncodingVideo.objects.get_or_create(
                        name=encod_name,
                        video=video_to_encode,
                        rendition=rendition,
                        encoding_format="video/mp4",
                        source_file=self.get_true_path(mp4_files[video_file]),
                    )
                elif list_video == "list_hls_files":
                    encoding, created = PlaylistVideo.objects.get_or_create(
                        name=encod_name,
                        video=video_to_encode,
                        encoding_format="application/x-mpegURL",
                        source_file=self.get_true_path(mp4_files[video_file]),
                    )
                    ts_file = mp4_files[video_file].replace(".m3u8", ".ts")
                    if os.path.exists(ts_file):
                        encoding, created = EncodingVideo.objects.get_or_create(
                            name=encod_name,
                            video=video_to_encode,
                            rendition=rendition,
                            encoding_format="video/mp2t",
                            source_file=self.get_true_path(ts_file),
                        )

        if os.path.exists(os.path.join(self.get_output_dir(), "livestream.m3u8")):
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

        for sub in list_subtitle_files:
            # home = UserFolder.objects.get(name="Home", owner=video_to_encode.owner)
            home, created = UserFolder.objects.get_or_create(
                name="home", owner=video_to_encode.owner
            )

            if FILEPICKER:
                podfile, created = CustomFileModel.objects.get_or_create(
                    file=self.get_true_path(list_subtitle_files[sub][1]),
                    name=list_subtitle_files[sub][1],
                    description="A subtitle file",
                    created_by=video_to_encode.owner,
                    folder=home,
                )
            else:
                podfile = CustomFileModel()
                podfile.file = self.get_true_path(list_subtitle_files[sub][1])

            print("subtitle lang: %s " % list_subtitle_files[sub][0])

            sub_lang = list_subtitle_files[sub][0]
            track_lang = (
                sub_lang[:2]
                if (LANG_CHOICES_DICT.get(sub_lang[:2]))
                else DEFAULT_LANG_TRACK
            )

            Track.objects.get_or_create(
                video=video_to_encode,
                kind="subtitles",
                lang=track_lang,
                src=podfile,
                enrich_ready=True,
            )

    def store_json_list_thumbnail_files(self, info_video, video_to_encode):
        list_thumbnail_files = info_video["list_thumbnail_files"]
        first = True

        videodir, created = UserFolder.objects.get_or_create(
            name="%s" % video_to_encode.slug,
            owner=video_to_encode.owner,
        )

        for thumbnail_path in list_thumbnail_files:
            if check_file(list_thumbnail_files[thumbnail_path]):
                if FILEPICKER:
                    thumbnail = CustomImageModel(
                        folder=videodir, created_by=video_to_encode.owner
                    )
                    thumbnail.file.save(
                        "%s_%s.png" % (video_to_encode.slug, thumbnail_path),
                        File(open(list_thumbnail_files[thumbnail_path], "rb")),
                        save=True,
                    )
                else:
                    thumbnail = CustomImageModel()
                    thumbnail.file.save(
                        "%d_%s.png" % (video_to_encode.slug, thumbnail_path),
                        File(open(list_thumbnail_files[thumbnail_path], "rb")),
                        save=True,
                    )
                    thumbnail.save()
                # rm temp location
                os.remove(list_thumbnail_files[thumbnail_path])
                if first:
                    video_to_encode.thumbnail = thumbnail
                    video_to_encode.save()
                    first = False

    def store_json_list_overview_files(self, info_video, video_to_encode):
        list_overview_files = info_video["list_overview_files"]

        if len(list_overview_files) > 0:
            vtt_file = (
                list_overview_files["0"]
                if ".vtt" in list_overview_files["0"]
                else list_overview_files["1"]
            )
            video_to_encode.overview = self.get_true_path(vtt_file)
            video_to_encode.save()

    def store_json_info(self):
        video_to_encode = Video.objects.get(id=self.id)

        with open(self.get_output_dir() + "/info_video.json") as json_file:
            info_video = json.load(json_file)
            video_to_encode.duration = info_video["duration"]
            video_to_encode.save()

            self.store_json_list_mp3_m4a_files(info_video, video_to_encode)
            self.store_json_list_mp4_hls_files(info_video, video_to_encode)
            self.store_json_encoding_log(info_video, video_to_encode)
            self.store_json_list_subtitle_files(info_video, video_to_encode)
            self.store_json_list_thumbnail_files(info_video, video_to_encode)
            self.store_json_list_overview_files(info_video, video_to_encode)

            return video_to_encode

            # TODO : Without podfile

    def encode_video(self):
        self.start_encode()
