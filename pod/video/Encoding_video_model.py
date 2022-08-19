import os
from django.conf import settings
from .models import EncodingVideo
from .models import EncodingAudio
from .models import VideoRendition
from .models import PlaylistVideo
from .models import EncodingLog
from .models import Video

from .Encoding_video import Encoding_video, FFMPEG_MP4_ENCODE
import json

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

    def get_encoding_choice_from_filename(self, filename):
        choices = {}
        for choice in ENCODING_CHOICES:
            choices[choice[0][:3]] = choice[0]
        return choices.get(filename[:3], "360p")

    def store_json_info(self):
        video_to_encode = Video.objects.get(id=self.id)

        with open(self.get_output_dir() + "/info_video.json") as json_file:
            info_video = json.load(json_file)
            video_to_encode.duration = info_video["duration"]
            video_to_encode.save()

            mp3_files = info_video["list_mp3_files"]
            for audio_file in mp3_files:
                encoding, created = EncodingAudio.objects.get_or_create(
                    name="audio",
                    video=video_to_encode,
                    encoding_format="audio/mp3",
                    # need to double check path
                    source_file=os.path.join(settings.MEDIA_ROOT, mp3_files[audio_file])
                )

            for list_video in ['list_hls_files', "list_mp4_files"]:
                mp4_files = info_video[list_video]
                for video_file in mp4_files:
                    rendition = VideoRendition.objects.get(resolution__contains="x" + video_file)
                    encod_name = self.get_encoding_choice_from_filename(mp4_files[video_file])
                    encoding, created = EncodingVideo.objects.get_or_create(
                        name=encod_name,
                        video=video_to_encode,
                        rendition=rendition,
                        encoding_format="video/mp4",
                        # need to double check path
                        source_file=os.path.join(settings.MEDIA_ROOT, mp4_files[video_file])
                    )

            log_to_text = ""
            logs = info_video['encoding_log']
            log_to_text = log_to_text + "Start : " + str(info_video['start'])
            for log in logs:
                log_to_text = log_to_text + "[" + log + "]\n\n"
                logdetails = logs[log]
                for logcate in logdetails:
                    log_to_text = log_to_text + "- " + logcate + " : \n" + str(logdetails[logcate]) + "\n"
            log_to_text = log_to_text + "End : " + str(info_video['stop'])


            list_videos_track = info_video["list_video_track"]
            for track in list_videos_track:
                #I don't know what to do with these values
                width = list_videos_track[track]['width']
                height = list_videos_track[track]['height']

            list_audio_track = info_video["list_audio_track"]
            for track in list_audio_track:
                #I don't know what to do with these values
                sample_rate = list_audio_track[track]['sample_rate']
                channels = list_audio_track[track]['channels']

            list_subtitle_track = info_video["list_subtitle_track"]
            for track in list_subtitle_track:
                #I don't know what to do with these values
                language = list_subtitle_track[track]['language']

            list_image_track = info_video["list_image_track"]
            for track in list_subtitle_track:
                print("nothing")
                #I don't know what to do with these values

            encoding_log, created = EncodingLog.objects.get_or_create(
                video=video_to_encode,
                log=log_to_text)

    def encode_video(self):
        self.start_encode()
