"""Unit tests for enrichment models."""

from django.contrib.sites.models import Site
from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError

from pod.video.models import Video
from pod.video.models import Type
from ..models import Enrichment, EnrichmentVtt, EnrichmentGroup

import os

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder

    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


class EnrichmentGroupModelTestCase(TestCase):
    """Test case for Pod enrichment models."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        owner = User.objects.create(username="test")
        videotype = Type.objects.create(title="others")
        Video.objects.create(
            title="video",
            type=videotype,
            owner=owner,
            video="test.mp4",
            duration=20,
        )
        Group.objects.create(name="group1")
        Group.objects.create(name="group2")

    def test_create_enrichmentGroup(self):
        video = Video.objects.get(id=1)
        self.assertTrue(not hasattr(video, "enrichmentgroup"))
        EnrichmentGroup.objects.create(video=video)
        self.assertTrue(video.enrichmentgroup)
        with self.assertRaises(IntegrityError):
            EnrichmentGroup.objects.create(video=video)
        print(" ---> test_create_enrichmentGroup: OK! --- EnrichmentGroupModel")

    def test_modify_enrichmentGroup(self):
        video = Video.objects.get(id=1)
        eng = EnrichmentGroup.objects.create(video=video)
        self.assertEqual(video.enrichmentgroup.groups.all().count(), 0)
        eng.groups.add(Group.objects.get(id=1))
        self.assertEqual(video.enrichmentgroup.groups.all().count(), 1)
        eng.groups.add(Group.objects.get(id=2))
        self.assertEqual(video.enrichmentgroup.groups.all().count(), 2)
        eng.groups.remove(Group.objects.get(id=2))
        self.assertEqual(video.enrichmentgroup.groups.all().count(), 1)
        eng.groups.add(Group.objects.get(id=2))
        self.assertEqual(video.enrichmentgroup.groups.all().count(), 2)
        Group.objects.get(id=2).delete()
        self.assertEqual(video.enrichmentgroup.groups.all().count(), 1)
        print(" ---> test_modify_enrichmentGroup: OK! --- EnrichmentGroupModel")

    def test_delete_enrichmentGroup(self):
        video = Video.objects.get(id=1)
        eng = EnrichmentGroup.objects.create(video=video)
        eng.groups.add(Group.objects.get(id=1))
        eng.groups.add(Group.objects.get(id=2))
        eng.delete()
        with self.assertRaises(ObjectDoesNotExist):
            EnrichmentGroup.objects.get(video=video)
        self.assertEqual(video.enrichmentgroup.id, None)
        self.assertTrue(Video.objects.filter(id=1).exists())
        self.assertTrue(Group.objects.filter(id=1).exists())
        self.assertTrue(Group.objects.filter(id=2).exists())
        print(" ---> test_delete_enrichmentGroup: OK! --- EnrichmentGroupModel")


class EnrichmentModelTestCase(TestCase):
    """Test case for Enrichment model tests."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Set up for Enrichment model tests."""
        owner = User.objects.create(username="test")
        video_type = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video",
            type=video_type,
            owner=owner,
            video="test.mp4",
            duration=20,
        )
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        simple_file = SimpleUploadedFile(
            name="testimage.jpg",
            content=open(
                os.path.join(current_dir, "tests", "testimage.jpg"), "rb"
            ).read(),
            content_type="image/jpeg",
        )

        if FILEPICKER:
            home = UserFolder.objects.get(name="home", owner=owner)
            custom_image = CustomImageModel.objects.create(
                name="testimage",
                description="testimage",
                created_by=owner,
                folder=home,
                file=simple_file,
            )
        else:
            custom_image = CustomImageModel.objects.create(file=simple_file)
        Enrichment.objects.create(
            video=video,
            title="testimg",
            start=1,
            end=2,
            stop_video=True,
            type="image",
            image=custom_image,
        )
        Enrichment.objects.create(
            video=video,
            title="testlink",
            type="weblink",
            weblink="http://test.com",
        )

    def test_attributs_full(self):
        """Test the attributs of the Enrichment model."""
        enrichment = Enrichment.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(enrichment.video, video)
        self.assertEqual(enrichment.title, "testimg")
        self.assertEqual(enrichment.start, 1)
        self.assertEqual(enrichment.end, 2)
        self.assertTrue(enrichment.stop_video)
        self.assertEqual(enrichment.type, "image")
        self.assertTrue("testimage" in enrichment.image.name)
        print(" ---> test_attributs_full: OK! --- EnrichmentModel")

    def test_attributs(self):
        """Test the attributs of the Enrichment model."""
        enrichment = Enrichment.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(enrichment.video, video)
        self.assertEqual(enrichment.title, "testlink")
        self.assertEqual(enrichment.start, 0)
        self.assertEqual(enrichment.end, 1)
        self.assertFalse(enrichment.stop_video)
        self.assertEqual(enrichment.type, "weblink")
        self.assertEqual(enrichment.weblink, "http://test.com")

        print(" [ BEGIN ENRICHMENT_TEST MODEL ] ")
        print(" ---> test_attributs: OK! --- EnrichmentModel")

    def test_type(self):
        """Test the type of the Enrichment model."""
        video = Video.objects.get(id=1)
        enrichment = Enrichment()
        enrichment.title = "test"
        enrichment.video = video
        enrichment.type = "badtype"
        self.assertRaises(ValidationError, enrichment.clean)

        print(" ---> test_type: OK! --- EnrichmentModel")
        print(" [ END ENRICHMENT_TEST MODEL ] ")

    def test_bad_attributs(self):
        """Test the bad attributs of the Enrichment model."""
        video = Video.objects.get(id=1)
        enrichment = Enrichment()
        enrichment.video = video
        enrichment.type = "image"
        enrichment.start = 1
        enrichment.end = 2
        self.assertRaises(ValidationError, enrichment.clean)
        enrichment.title = "t"
        self.assertRaises(ValidationError, enrichment.clean)
        enrichment.start = None
        self.assertRaises(ValidationError, enrichment.clean)
        enrichment.start = -1
        self.assertRaises(ValidationError, enrichment.clean)
        enrichment.start = 21
        self.assertRaises(ValidationError, enrichment.clean)

        print(" ---> test_bad_attributs: OK! --- EnrichmentModel")

    def test_overlap(self):
        """Test overlap."""
        video = Video.objects.get(id=1)
        enrichment = Enrichment()
        enrichment.video = video
        enrichment.type = "image"
        enrichment.title = "test"
        enrichment.start = 1
        enrichment.end = 3
        self.assertRaises(ValidationError, enrichment.clean)
        print(" ---> test_overlap: OK! --- EnrichmentModel")

    def test_delete(self):
        """Test the delete method of the Enrichment model."""
        video = Video.objects.get(id=1)
        list_enrichment = video.enrichment_set.all()
        self.assertEqual(list_enrichment.count(), 2)
        self.assertEqual(EnrichmentVtt.objects.filter(video=video).count(), 1)
        Enrichment.objects.get(id=1).delete()
        Enrichment.objects.get(id=2).delete()
        self.assertTrue(Enrichment.objects.all().count() == 0)
        self.assertEqual(EnrichmentVtt.objects.filter(video=video).count(), 0)
        print(" ---> test_delete: OK! --- EnrichmentModel")

    def test_sites_property__not_empty(self):
        """Test the sites property of the Enrichment model when the video has site."""
        video = Video.objects.get(id=1)
        video.sites.add(Site.objects.get(pk=1))
        video.save()
        enrichment = Enrichment.objects.get(id=1)
        self.assertEqual(enrichment.sites, video.sites)
        print(" ---> test_sites_property__not_empty: OK! --- EnrichmentModel")

    def test_sites_property__empty(self):
        """Test the sites property of the Enrichment model when the video has no site."""
        video = Video.objects.get(id=1)
        video.sites.clear()
        enrichment = Enrichment.objects.get(id=1)
        self.assertEqual(enrichment.sites, video.sites)
        self.assertEqual(enrichment.sites.count(), 0)
        self.assertEqual(video.sites.count(), 0)
        print(" ---> test_sites_property__empty: OK! --- EnrichmentModel")

    def test_str(self):
        """Test the str method of the Enrichment model."""
        enrichment = Enrichment.objects.get(id=1)
        self.assertEqual(
            str(enrichment), f"Media: {enrichment.title} - Video: {enrichment.video}"
        )
        print(" ---> test_str: OK! --- EnrichmentModel")
