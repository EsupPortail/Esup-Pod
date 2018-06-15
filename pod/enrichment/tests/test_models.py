"""
Unit tests for enrichment models
"""
from django.apps import apps
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from pod.video.models import Video
from pod.video.models import Type
from pod.enrichment.models import Enrichment
if apps.is_installed('pod.filepicker'):
    from pod.filepicker.models import CustomImageModel
    from pod.filepicker.models import UserDirectory
    from datetime import datetime
    FILEPICKER = True


class EnrichmentModelTestCase(TestCase):

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
        if FILEPICKER:
            testfile = SimpleUploadedFile(
                name='testimage.jpg',
                content=open(
                    './pod/enrichment/tests/testimage.jpg', 'rb').read(),
                content_type='text/plain')
            home = UserDirectory.objects.create(name='Home', owner=owner)
            file = CustomImageModel.objects.create(
                name='testimage',
                date_created=datetime.now(),
                date_modified=datetime.now(),
                created_by=owner,
                modified_by=owner,
                directory=home,
                file=testfile
            )
        else:
            file = SimpleUploadedFile(
                name='testimage.jpg',
                content=open(
                    './pod/enrichment/tests/testimage.jpg', 'rb').read(),
                content_type='text/plain')
        Enrichment.objects.create(
            video=video,
            title='testimg',
            start=1,
            end=2,
            stop_video=True,
            type='image',
            image=file)
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
        if FILEPICKER:
            self.assertEqual(enrichment.image.name, 'testimage')
        else:
            self.assertEqual(enrichment.image.name, 'testimage.jpg')

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
        Enrichment.objects.get(id=1).delete()
        Enrichment.objects.get(id=2).delete()
        self.assertTrue(Enrichment.objects.all().count() == 0)

        print(" ---> test_delete : OK ! --- EnrichmentModel")
