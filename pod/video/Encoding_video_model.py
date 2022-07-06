import os
from django.conf import settings
from .models import EncodingVideo
from .models import EncodingAudio
from .models import PlaylistVideo
from .models import Video
from .utils import create_outputdir, change_encoding_step, fix_video_duration, send_email_encoding
from .Encoding_video import Encoding_video, FFMPEG_MP4_ENCODE
import json
import time

FFMPEG_MP4_ENCODE = getattr(settings, "FFMPEG_MP4_ENCODE", FFMPEG_MP4_ENCODE)
EMAIL_ON_ENCODING_COMPLETION = getattr(settings, "EMAIL_ON_ENCODING_COMPLETION", True)
TRANSCRIPT = getattr(settings, "USE_TRANSCRIPTION", False)

if TRANSCRIPT:
    from . import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

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

    def store_encoding_video(self, video_to_store):
        video = Video.objects.get(id=video_to_store)
        output_dir = create_outputdir(video_to_store, video.video.path)
        info_video = {}

        with open(output_dir + "/info_video.json") as json_file:
            info_video = json.load(json_file)

        video.duration = info_video["duration"]
        video.encoding_in_progress = True
        video.save()

        video = Video.objects.get(id=video_to_store)  # refresh given object

        # remote_video_part(video_to_encode, info_video, output_dir)
        # remote_audio_part(video_to_encode, info_video, output_dir)

        if not info_video["has_stream_video"]:
            video.is_video = False
            video.save()

        change_encoding_step(video_to_store, 0, "done")

        video.encoding_in_progress = False
        video.save()

        fix_video_duration(video.id, output_dir)

        with open(output_dir + "/encoding.log", "a") as f:
            f.write("\n\nEnd : %s" % time.ctime())

        # envois mail fin encodage
        if EMAIL_ON_ENCODING_COMPLETION:
            send_email_encoding(video)

        # Transcript
        if TRANSCRIPT and video.transcript:
            transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
            transcript_video(video_to_store, False)

        print("ALL is DONE")