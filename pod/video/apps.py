"""Esup-Pod Video App."""
from django.apps import AppConfig
from django.db.models.signals import post_migrate, pre_migrate
from django.utils.translation import gettext_lazy as _
from django.db import connection


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

    site = Site.objects.get_current()
    for vid in Video.objects.all():
        apply_default_site(vid, site)
    for chan in Channel.objects.all():
        apply_default_site_fk(chan, site)
    for dis in Discipline.objects.all():
        apply_default_site_fk(chan, site)
    for typ in Type.objects.all():
        apply_default_site(typ, site)
    for vr in VideoRendition.objects.all():
        apply_default_site(vr, site)


VIDEO_RENDITION = {}
ENCODING_VIDEO = {}
ENCODING_AUDIO = {}
ENCODING_LOG = {}
ENCODING_STEP = {}


class VideoConfig(AppConfig):
    name = "pod.video"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Videos")

    def ready(self):
        post_migrate.connect(set_default_site, sender=self)
        pre_migrate.connect(self.save_previous_data, sender=self)
        post_migrate.connect(self.send_previous_data, sender=self)

    def save_previous_data(self, sender, **kwargs):
        try:
            with connection.cursor() as c:
                c.execute('SELECT "video_videorendition"."id","video_videorendition"."resolution", "video_videorendition"."minrate", "video_videorendition"."video_bitrate", "video_videorendition"."maxrate", "video_videorendition"."encoding_resolution_threshold", "video_videorendition"."audio_bitrate", "video_videorendition"."encode_mp4" FROM "video_videorendition" ORDER BY "video_videorendition"."name" ASC')
                results = c.fetchall()
                for res in results:
                    VIDEO_RENDITION["%s" % res[0]] = [res[1], res[2], res[3], res[4], res[5], res[6], res[7]]
        except Exception:
            pass

        try:
            with connection.cursor() as c:
                c.execute('SELECT "video_encodingvideo"."id", "video_encodingvideo"."name", "video_encodingvideo"."video_id", "video_encodingvideo"."rendition_id", "video_encodingvideo"."encoding_format", "video_encodingvideo"."source_file" FROM "video_encodingvideo" ORDER BY "video_encodingvideo"."name" ASC')
                results = c.fetchall()
                for res in results:
                    ENCODING_VIDEO["%s" % res[0]] = [res[1], res[2], res[3], res[4], res[5]]
        except Exception:
            pass
        
        try:
            with connection.cursor() as c:
                c.execute('SELECT "video_encodingstep"."id", "video_encodingstep"."video_id", "video_encodingstep"."num_step", "video_encodingstep"."desc_step" FROM "video_encodingstep" INNER JOIN "video_video" ON ("video_encodingstep"."video_id" = "video_video"."id") ORDER BY "video_video"."date_added" DESC, "video_video"."id" DESC')
                results = c.fetchall()
                for res in results:
                    ENCODING_STEP["%s" % res[0]] = [res[1], res[2], res[3]]
        except Exception:
            pass
        
        try:
            with connection.cursor() as c:
                c.execute('SELECT "video_encodinglog"."id", "video_encodinglog"."video_id", "video_encodinglog"."log", "video_encodinglog"."logfile" FROM "video_encodinglog" INNER JOIN "video_video" ON ("video_encodinglog"."video_id" = "video_video"."id") ORDER BY "video_video"."date_added" DESC, "video_video"."id" DESC')
                results = c.fetchall()
                for res in results:
                    ENCODING_LOG["%s" % res[0]] = [res[1], res[2], res[3]]
        except Exception:
            pass
        
        try:
            with connection.cursor() as c:
                c.execute('SELECT "video_encodingaudio"."id", "video_encodingaudio"."name", "video_encodingaudio"."video_id", "video_encodingaudio"."encoding_format", "video_encodingaudio"."source_file" FROM "video_encodingaudio" ORDER BY "video_encodingaudio"."name" ASC')
                results = c.fetchall()
                for res in results:
                    ENCODING_AUDIO["%s" % res[0]] = [res[1], res[2], res[3], res[4]]
        except Exception:
            pass
        


    def send_previous_data(self, sender, **kwargs):
        from pod.video_encode_transcript.models import (
            VideoRendition,
            EncodingVideo,
            EncodingStep,
            EncodingLog,
            EncodingAudio,
        )

        for id in VIDEO_RENDITION:
            vr = VideoRendition.objects.create(
                id=id,
                resolution=VIDEO_RENDITION[id][0],
                minrate=VIDEO_RENDITION[id][1],
                video_bitrate=VIDEO_RENDITION[id][2],
                maxrate=VIDEO_RENDITION[id][3],
                encoding_resolution_threshold=VIDEO_RENDITION[id][4],
                audio_bitrate=VIDEO_RENDITION[id][5],
                encode_mp4=VIDEO_RENDITION[id][6],
            )
            vr.save()
        for id in ENCODING_VIDEO:
            ev = EncodingVideo.objects.create(
                id=id,
                name=ENCODING_VIDEO[id][0],
                video_id=ENCODING_VIDEO[id][1],
                rendition_id=ENCODING_VIDEO[id][2],
                encoding_format=ENCODING_VIDEO[id][3],
                source_file=ENCODING_VIDEO[id][4],
            )
            ev.save()
        for id in ENCODING_STEP:
            ea = EncodingStep.objects.create(
                id=id,
                video_id=ENCODING_STEP[id][0],
                num_step=ENCODING_STEP[id][1],
                desc_step=ENCODING_STEP[id][2],
            )
            ea.save()
        for id in ENCODING_LOG:
            el = EncodingLog.objects.create(
                id=id,
                video_id=ENCODING_LOG[id][0],
                log=ENCODING_LOG[id][1],
                logfile=ENCODING_LOG[id][2],
            )
            el.save()
        for id in ENCODING_AUDIO:
            es = EncodingAudio.objects.create(
                id=id,
                name=ENCODING_AUDIO[id][0],
                video_id=ENCODING_AUDIO[id][1],
                encoding_format=ENCODING_AUDIO[id][2],
                source_file=ENCODING_AUDIO[id][3],
            )
            es.save()
