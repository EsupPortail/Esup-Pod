"""Esup-Pod Video App."""
from django.apps import AppConfig
from django.db.models.signals import post_migrate, pre_migrate
from django.utils.translation import gettext_lazy as _
from django.db import connection
import time

VIDEO_RENDITION = {}
ENCODING_VIDEO = {}
ENCODING_AUDIO = {}
ENCODING_LOG = {}
ENCODING_STEP = {}
PLAYLIST_VIDEO = {}


def apply_default_site(obj, site):
    if len(obj.sites.all()) == 0:
        obj.sites.add(site)
        obj.save()


def apply_default_site_fk(obj, site):
    if obj.site is None:
        obj.site = site
        obj.save()


def set_default_site(sender, **kwargs):
    from pod.video.models import Video
    from pod.video.models import Channel
    from pod.video.models import Discipline
    from pod.video_encode_transcript.models import VideoRendition
    from pod.video.models import Type
    from django.contrib.sites.models import Site

    print("Start set_default_site")
    site = Site.objects.get_current()
    for vid in Video.objects.filter(sites__isnull=True):
        apply_default_site(vid, site)
    for chan in Channel.objects.filter(site=None):
        apply_default_site_fk(chan, site)
    for dis in Discipline.objects.filter(site=None):
        apply_default_site_fk(dis, site)
    for typ in Type.objects.filter(sites__isnull=True):
        apply_default_site(typ, site)
    for vr in VideoRendition.objects.filter(sites__isnull=True):
        apply_default_site(vr, site)
    print("set_default_site --> OK")


def fix_transcript(sender, **kwargs):
    """
    Transcript field change from boolean to charfield since the version 3.2.0
    This fix change value to set the default lang value if necessary
    """
    from pod.video.models import Video
    from django.db.models import F

    print("Start fix_transcript")
    Video.objects.filter(transcript="1").update(transcript=F("main_lang"))
    Video.objects.filter(transcript="0").update(transcript="")
    print("fix_transcript --> OK")


def update_video_passwords(sender, **kwargs):
    """Encrypt all video passwords."""
    from pod.video.models import Video
    from django.contrib.auth.hashers import make_password
    from django.db.models import Q

    print("Start update_video_passwords")
    # Filter insecure protected videos
    videos_to_update = Video.objects.exclude(
        Q(password__isnull=True) | Q(password__startswith=("pbkdf2_sha256$"))
    )
    for video in videos_to_update:
        video.password = make_password(video.password, hasher="pbkdf2_sha256")
        video.save()
    print("update_video_passwords --> OK")


class VideoConfig(AppConfig):
    name = "pod.video"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Videos")

    def ready(self):
        pre_migrate.connect(self.save_previous_data, sender=self)
        post_migrate.connect(set_default_site, sender=self)
        post_migrate.connect(self.send_previous_data, sender=self)
        post_migrate.connect(fix_transcript, sender=self)
        post_migrate.connect(update_video_passwords, sender=self)

    def execute_query(self, query, mapping_dict):
        """
        Execute the given query and populate the mapping dictionary with the results.

        Args:
            query (str): The given query to execute
            mapping_dict (dict): The dictionary.
        """
        try:
            with connection.cursor() as c:
                c.execute(query)
                results = c.fetchall()
                for res in results:
                    mapping_dict["%s" % res[0]] = [res[i] for i in range(1, len(res))]
        except Exception:
            # print(e)
            pass

    def save_previous_data(self, sender, **kwargs):
        """Save previous data from various database tables."""
        print("pre_migrate - Start save_previous_data")
        self.execute_query(
            """
            SELECT id,
            resolution,
            minrate,
            video_bitrate,
            maxrate,
            encoding_resolution_threshold,
            audio_bitrate,
            encode_mp4
            FROM video_videorendition
            ORDER BY resolution ASC
            """,
            VIDEO_RENDITION,
        )
        if len(VIDEO_RENDITION) > 0:
            print("%s VIDEO_RENDITION saved" % len(VIDEO_RENDITION))
        self.execute_query(
            """
            SELECT id,
            name,
            video_id,
            rendition_id,
            encoding_format,
            source_file
            FROM video_encodingvideo
            ORDER BY name ASC
            """,
            ENCODING_VIDEO,
        )
        if len(ENCODING_VIDEO) > 0:
            print("%s ENCODING_VIDEO saved" % len(ENCODING_VIDEO))
        self.execute_query(
            """
            SELECT id,
            video_id,
            num_step,
            desc_step
            FROM video_encodingstep
            """,
            ENCODING_STEP,
        )
        if len(ENCODING_STEP) > 0:
            print("%s ENCODING_STEP saved" % len(ENCODING_STEP))
        self.execute_query(
            """
            SELECT id,
            video_id,
            log,
            logfile
            FROM video_encodinglog
            """,
            ENCODING_LOG,
        )
        if len(ENCODING_LOG) > 0:
            print("%s ENCODING_LOG saved" % len(ENCODING_LOG))
        self.execute_query(
            """
            SELECT id,
            name,
            video_id,
            encoding_format,
            source_file
            FROM video_encodingaudio
            ORDER BY name ASC
            """,
            ENCODING_AUDIO,
        )
        if len(ENCODING_AUDIO) > 0:
            print("%s ENCODING_AUDIO saved" % len(ENCODING_AUDIO))
        # PLAYLIST_VIDEO
        self.execute_query(
            """
            SELECT id,
            name,
            video_id,
            encoding_format,
            source_file
            FROM video_playlistvideo
            ORDER BY name ASC
            """,
            PLAYLIST_VIDEO,
        )
        if len(PLAYLIST_VIDEO) > 0:
            print("%s PLAYLIST_VIDEO saved" % len(PLAYLIST_VIDEO))
        print("pre_migrate - save_previous_data --> OK")

    def send_previous_data(self, sender, **kwargs):
        """Send previous data from various database tables."""
        print("post_migrate - Start send_previous_data")
        nb_batch = 1000
        if (
            len(VIDEO_RENDITION) > 0
            or len(ENCODING_VIDEO) > 0
            or len(ENCODING_AUDIO) > 0
            or len(ENCODING_LOG) > 0
            or len(ENCODING_STEP) > 0
            or len(PLAYLIST_VIDEO) > 0
        ):
            print("send_previous_data : batch size = %s" % nb_batch)
            self.import_data(nb_batch)
        else:
            return

    def import_data(self, nb_batch):
        """Call method to put data if data saved."""
        if len(VIDEO_RENDITION) > 0:
            self.import_video_rendition(nb_batch)

        if len(ENCODING_VIDEO) > 0:
            self.import_encoding_video(nb_batch)

        if len(ENCODING_STEP) > 0:
            self.import_encoding_step(nb_batch)

        if len(ENCODING_LOG) > 0:
            self.import_encoding_log(nb_batch)

        if len(ENCODING_AUDIO) > 0:
            self.import_encoding_audio(nb_batch)

        if len(PLAYLIST_VIDEO) > 0:
            self.import_playlist_video(nb_batch)

    def import_video_rendition(self, nb_batch):
        """Import video rendition data in DB."""
        from pod.video_encode_transcript.models import VideoRendition

        print("pushing %s VIDEO_RENDITION" % len(VIDEO_RENDITION))
        print("Start at: %s" % time.ctime())
        video_renditions = []
        for id in VIDEO_RENDITION:
            vr = VideoRendition(
                id=id,
                resolution=VIDEO_RENDITION[id][0],
                minrate=VIDEO_RENDITION[id][1],
                video_bitrate=VIDEO_RENDITION[id][2],
                maxrate=VIDEO_RENDITION[id][3],
                encoding_resolution_threshold=VIDEO_RENDITION[id][4],
                audio_bitrate=VIDEO_RENDITION[id][5],
                encode_mp4=VIDEO_RENDITION[id][6],
            )
            video_renditions.append(vr)
        VideoRendition.objects.bulk_create(video_renditions, batch_size=nb_batch)

    def import_encoding_video(self, nb_batch):
        """Import encoding video data in DB."""
        from pod.video_encode_transcript.models import EncodingVideo

        print("pushing %s ENCODING_VIDEO" % len(ENCODING_VIDEO))
        print("Start at: %s" % time.ctime())
        encoding_videos = []
        for id in ENCODING_VIDEO:
            ev = EncodingVideo(
                id=id,
                name=ENCODING_VIDEO[id][0],
                video_id=ENCODING_VIDEO[id][1],
                rendition_id=ENCODING_VIDEO[id][2],
                encoding_format=ENCODING_VIDEO[id][3],
                source_file=ENCODING_VIDEO[id][4],
            )
            encoding_videos.append(ev)
        EncodingVideo.objects.bulk_create(encoding_videos, batch_size=nb_batch)

    def import_encoding_step(self, nb_batch):
        """Import encoding step data in DB."""
        from pod.video_encode_transcript.models import EncodingStep

        print("pushing %s ENCODING_STEP" % len(ENCODING_STEP))
        print("Start at: %s" % time.ctime())
        encoding_steps = []
        for id in ENCODING_STEP:
            ea = EncodingStep(
                id=id,
                video_id=ENCODING_STEP[id][0],
                num_step=ENCODING_STEP[id][1],
                desc_step=ENCODING_STEP[id][2],
            )
            encoding_steps.append(ea)
        EncodingStep.objects.bulk_create(encoding_steps, batch_size=nb_batch)

    def import_encoding_log(self, nb_batch):
        """Import encoding log data in DB."""
        from pod.video_encode_transcript.models import EncodingLog

        print("pushing %s ENCODING_LOG" % len(ENCODING_LOG))
        print("Start at: %s" % time.ctime())
        encoding_logs = []
        for id in ENCODING_LOG:
            el = EncodingLog(
                id=id,
                video_id=ENCODING_LOG[id][0],
                log=ENCODING_LOG[id][1],
                logfile=ENCODING_LOG[id][2],
            )
            encoding_logs.append(el)
        EncodingLog.objects.bulk_create(encoding_logs, batch_size=nb_batch)

    def import_encoding_audio(self, nb_batch):
        """Import encoding audio data in DB."""
        from pod.video_encode_transcript.models import EncodingAudio

        print("pushing %s ENCODING_AUDIO" % len(ENCODING_AUDIO))
        print("Start at: %s" % time.ctime())
        encoding_audios = []
        for id in ENCODING_AUDIO:
            es = EncodingAudio(
                id=id,
                name=ENCODING_AUDIO[id][0],
                video_id=ENCODING_AUDIO[id][1],
                encoding_format=ENCODING_AUDIO[id][2],
                source_file=ENCODING_AUDIO[id][3],
            )
            encoding_audios.append(es)
        EncodingAudio.objects.bulk_create(encoding_audios, batch_size=nb_batch)

    def import_playlist_video(self, nb_batch):
        """Import playlist video data in DB."""
        from pod.video_encode_transcript.models import PlaylistVideo

        print("pushing %s PLAYLIST_VIDEO" % len(PLAYLIST_VIDEO))
        print("Start at: %s" % time.ctime())
        playlist_videos = []
        for id in PLAYLIST_VIDEO:
            es = PlaylistVideo(
                id=id,
                name=PLAYLIST_VIDEO[id][0],
                video_id=PLAYLIST_VIDEO[id][1],
                encoding_format=PLAYLIST_VIDEO[id][2],
                source_file=PLAYLIST_VIDEO[id][3],
            )
            playlist_videos.append(es)
        PlaylistVideo.objects.bulk_create(playlist_videos, batch_size=nb_batch)
