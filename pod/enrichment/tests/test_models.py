"""
Unit tests for enrichment models
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from pod.video.models import Video
from pod.video.models import Type
from ..models import Enrichment, EnrichmentVtt
from django.conf import settings
from django.test import override_settings
import os

if getattr(settings, 'USE_PODFILE', False):
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


@override_settings(
    THIRD_PARTY_APPS=["enrichment"],
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    },
    LANGUAGE_CODE='en'
)
class EnrichmentModelTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        owner = User.objects.create(username='test')
        videotype = Type.objects.create(title='others')
        video = Video.objects.create(
            title='video',
            type=videotype,
            owner=owner,
            video='test.mp4',
            duration=20
        )
        currentdir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        simplefile = SimpleUploadedFile(
            name='testimage.jpg',
            content=open(
                os.path.join(
                    currentdir, 'tests', 'testimage.jpg'), 'rb').read(),
            content_type='image/jpeg')

        if FILEPICKER:
            home = UserFolder.objects.get(name='home', owner=owner)
            customImage = CustomImageModel.objects.create(
                name='testimage',
                description='testimage',
                created_by=owner,
                folder=home,
                file=simplefile)
        else:
            customImage = CustomImageModel.objects.create(
                file=simplefile)
        Enrichment.objects.create(
            video=video,
            title='testimg',
            start=1,
            end=2,
            stop_video=True,
            type='image',
            image=customImage)
        Enrichment.objects.create(
            video=video,
            title='testlink',
            type='weblink',
            weblink='http://test.com')

    def test_attributs_full(self):
        enrichment = Enrichment.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(enrichment.video, video)
        self.assertEqual(enrichment.title, 'testimg')
        self.assertEqual(enrichment.start, 1)
        self.assertEqual(enrichment.end, 2)
        self.assertTrue(enrichment.stop_video)
        self.assertEqual(enrichment.type, 'image')
        self.assertTrue('testimage' in enrichment.image.name)
        print(" ---> test_attributs_full : OK ! --- EnrichmentModel")

    def test_attributs(self):
        enrichment = Enrichment.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(enrichment.video, video)
        self.assertEqual(enrichment.title, 'testlink')
        self.assertEqual(enrichment.start, 0)
        self.assertEqual(enrichment.end, 1)
        self.assertFalse(enrichment.stop_video)
        self.assertEqual(enrichment.type, 'weblink')
        self.assertEqual(enrichment.weblink, 'http://test.com')

        print(" [ BEGIN ENRICHMENT_TEST MODEL ] ")
        print(" ---> test_attributs : OK ! --- EnrichmentModel")

    def test_type(self):
        video = Video.objects.get(id=1)
        enrichment = Enrichment()
        enrichment.title = 'test'
        enrichment.video = video
        enrichment.type = 'badtype'
        self.assertRaises(ValidationError, enrichment.clean)

        print(" ---> test_type : OK ! --- EnrichmentModel")
        print(" [ END ENRICHMENT_TEST MODEL ] ")

    def test_bad_attributs(self):
        video = Video.objects.get(id=1)
        enrichment = Enrichment()
        enrichment.video = video
        enrichment.type = 'image'
        enrichment.start = 1
        enrichment.end = 2
        self.assertRaises(ValidationError, enrichment.clean)
        enrichment.title = 't'
        self.assertRaises(ValidationError, enrichment.clean)
        enrichment.start = None
        self.assertRaises(ValidationError, enrichment.clean)
        enrichment.start = -1
        self.assertRaises(ValidationError, enrichment.clean)
        enrichment.start = 21
        self.assertRaises(ValidationError, enrichment.clean)

        print(" ---> test_bad_attributs : OK ! --- EnrichmentModel")

    def test_overlap(self):
        video = Video.objects.get(id=1)
        enrichment = Enrichment()
        enrichment.video = video
        enrichment.type = 'image'
        enrichment.title = 'test'
        enrichment.start = 1
        enrichment.end = 3
        self.assertRaises(ValidationError, enrichment.clean)
        print(" ---> test_overlap : OK ! --- EnrichmentModel")

    def test_delete(self):
        video = Video.objects.get(id=1)
        list_enrichment = video.enrichment_set.all()
        self.assertEqual(list_enrichment.count(), 2)
        self.assertEqual(EnrichmentVtt.objects.filter(video=video).count(), 1)
        Enrichment.objects.get(id=1).delete()
        Enrichment.objects.get(id=2).delete()
        self.assertTrue(Enrichment.objects.all().count() == 0)
        self.assertEqual(EnrichmentVtt.objects.filter(video=video).count(), 0)
        print(" ---> test_delete : OK ! --- EnrichmentModel")
