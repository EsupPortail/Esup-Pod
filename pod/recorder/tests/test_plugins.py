import os
import shutil
import importlib
from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from pod.video.models import Video, Type
from ..models import Recording, Recorder

VIDEO_TEST = getattr(settings, "VIDEO_TEST", "pod/main/static/video_test/pod.mp4")

AUDIOVIDEOCAST_TEST = getattr(
    settings, "AUDIOVIDEOCAST_TEST", "pod/main/static/video_test/pod.zip"
)


class PluginVideoTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        mediatype = Type.objects.create(title="others")
        user = User.objects.create(username="pod", is_staff=True)
        # Setup recorder and recording for Video
        recorder1 = Recorder.objects.create(
            user=user,
            name="recorder1",
            address_ip="16.3.10.47",
            type=mediatype,
            cursus="0",
            directory="dirVideo",
        )
        source_file1 = os.path.join(settings.MEDIA_ROOT, os.path.basename(VIDEO_TEST))
        Recording.objects.create(
            id=1,
            user=user,
            title="media1",
            type="video",
            source_file=source_file1,
            recorder=recorder1,
        )
        # Setup recorder and recording for AudioVideoCast
        recorder2 = Recorder.objects.create(
            user=user,
            name="recorder2",
            address_ip="16.3.10.48",
            type=mediatype,
            cursus="0",
            directory="dirAudioVideoCast",
        )
        source_file2 = os.path.join(
            settings.MEDIA_ROOT, os.path.basename(AUDIOVIDEOCAST_TEST)
        )
        Recording.objects.create(
            id=2,
            user=user,
            title="media2",
            type="audiovideocast",
            source_file=source_file2,
            recorder=recorder2,
        )

        print(" --->  SetUp of PluginVideoTestCase : OK !")

    def test_type_video_published_attributs(self):
        recording = Recording.objects.get(id=1)
        recorder = recording.recorder
        shutil.copyfile(VIDEO_TEST, recording.source_file)
        mod = importlib.import_module("pod.recorder.plugins.type_%s" % ("video"))
        nbnow = Video.objects.all().count()
        nbtest = nbnow + 1
        mod.encode_recording(recording)
        # print("Number of video after encode : ", Video.objects.all().count())
        self.assertEqual(Video.objects.all().count(), nbtest)
        video = Video.objects.last()
        self.assertEqual(video.is_draft, recorder.is_draft)
        self.assertEqual(video.channel.all().count(), recorder.channel.all().count())
        self.assertEqual(video.theme.all().count(), recorder.theme.all().count())
        self.assertEqual(
            video.discipline.all().count(), recorder.discipline.all().count()
        )
        self.assertEqual(video.main_lang, recorder.main_lang)
        self.assertEqual(video.cursus, recorder.cursus)
        self.assertEqual(video.tags, recorder.tags)

        print("   --->  test_type_video_published_attributs of PluginVideoTestCase: OK!")

    def test_type_audiovideocast_published_attributs(self):
        recording = Recording.objects.get(id=2)
        recorder = recording.recorder
        shutil.copyfile(AUDIOVIDEOCAST_TEST, recording.source_file)
        mod = importlib.import_module("pod.recorder.plugins.type_%s" % ("audiovideocast"))
        nbnow = Video.objects.all().count()
        nbtest = nbnow + 1
        mod.encode_recording(recording)
        # print("Number of video after encode : ", Video.objects.all().count())
        self.assertEqual(Video.objects.all().count(), nbtest)
        video = Video.objects.last()
        # print("Number of slide after encode : ",
        #       video.enrichment_set.all().count())
        self.assertEqual((video.enrichment_set.all().count() > 0), True)
        self.assertEqual(video.is_draft, recorder.is_draft)
        self.assertEqual(video.channel.all().count(), recorder.channel.all().count())
        self.assertEqual(video.theme.all().count(), recorder.theme.all().count())
        self.assertEqual(
            video.discipline.all().count(), recorder.discipline.all().count()
        )
        self.assertEqual(video.main_lang, recorder.main_lang)
        self.assertEqual(video.cursus, recorder.cursus)
        self.assertEqual(video.tags, recorder.tags)
        print(
            "   --->  test_type_video_published_attributs "
            "of PluginAudioVideoCastTestCase: OK !"
        )
