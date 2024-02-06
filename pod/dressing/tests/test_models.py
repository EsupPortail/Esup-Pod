"""Unit tests for dressing models."""

import os
from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from pod.video.models import Type, Video
from pod.dressing.models import Dressing

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder

    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


class DressingModelTest(TestCase):
    """Test case for Pod dressing models."""

    def setUp(self):
        owner = User.objects.create(username="pod")
        currentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        simplefile = SimpleUploadedFile(
            name="testimage.jpg",
            content=open(os.path.join(currentdir, "tests", "testimage.jpg"), "rb").read(),
            content_type="image/jpeg",
        )

        home = UserFolder.objects.get(name="home", owner=owner)
        if FILEPICKER:
            home = UserFolder.objects.get(name="home", owner=owner)
            customImage = CustomImageModel.objects.create(
                name="testimage",
                description="testimage",
                created_by=owner,
                folder=home,
                file=simplefile,
            )
        else:
            customImage = CustomImageModel.objects.create(file=simplefile)
        videotype = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video",
            type=videotype,
            owner=owner,
            video="test.mp4",
            duration=20,
        )
        video2 = Video.objects.create(
            title="video2",
            type=videotype,
            owner=owner,
            video="test2.mp4",
            duration=20,
        )
        dressing = Dressing.objects.create(
            title="Test Dressing",
            watermark=customImage,
            position=Dressing.TOP_RIGHT,
            opacity=50,
            opening_credits=video,
            ending_credits=video2,
        )
        dressing.owners.set([owner])
        dressing.users.set([owner])

    def test_attributs_full(self):
        dressing = Dressing.objects.get(id=1)
        owner = User.objects.get(username="pod")
        video = Video.objects.get(id=1)
        video2 = Video.objects.get(id=2)
        self.assertEqual(dressing.title, "Test Dressing")
        self.assertEqual(list(dressing.owners.all()), [owner])
        self.assertEqual(list(dressing.users.all()), [owner])
        self.assertEqual(list(dressing.allow_to_groups.all()), [])
        self.assertTrue("testimage" in dressing.watermark.name)
        self.assertEqual(dressing.position, Dressing.TOP_RIGHT)
        self.assertEqual(dressing.opacity, 50)
        self.assertEqual(dressing.opening_credits, video)
        self.assertEqual(dressing.ending_credits, video2)
        print(" ---> test_attributs_full: OK! --- DressingModelTest")

    def test_dressing_to_json(self):
        dressing = Dressing.objects.get(id=1)
        dressing_json = dressing.to_json()
        owner = User.objects.get(username="pod")
        video = Video.objects.get(id=1)
        video2 = Video.objects.get(id=2)

        expected_json = {
            "id": dressing.id,
            "title": "Test Dressing",
            "allow_to_groups": [],
            "owners": [owner.id],
            "users": [owner.id],
            "watermark": dressing.watermark.file.url,
            "position": dressing.get_position_display(),
            "opacity": 50,
            "opening_credits": video.slug,
            "ending_credits": video2.slug,
        }
        self.assertEqual(dressing_json, expected_json)
        print(" ---> test_dressing_to_json: OK! --- DressingModelTest")
