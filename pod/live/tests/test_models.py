from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User

from pod.video.models import Type
from pod.video.models import Video
from ..models import Building, Broadcaster

if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


class BuildingTestCase(TestCase):

    def setUp(self):
        Building.objects.create(name="building1")
        print(" --->  SetUp of BuildingTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
        building = Building.objects.get(id=1)
        self.assertEqual(building.name, "building1")
        building.gmapurl = "b"
        building.save()
        self.assertEqual(building.gmapurl, "b")
        if FILEPICKER:
            user = User.objects.create(username="pod")
            homedir, created = UserFolder.objects.get_or_create(
                name='Home',
                owner=user)
            headband = CustomImageModel.objects.create(
                folder=homedir,
                created_by=user,
                file="blabla.jpg")
        else:
            headband = CustomImageModel.objects.create(file="blabla.jpg")
        building.headband = headband
        building.save()
        self.assertTrue("blabla" in building.headband.name)
        print(
            "   --->  test_attributs of BuildingTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Building.objects.get(id=1).delete()
        self.assertEquals(Building.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of BuildingTestCase : OK !")


"""
    test recorder object
"""


class BroadcasterTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        building = Building.objects.create(name="building1")
        if FILEPICKER:
            user = User.objects.create(username="pod")
            homedir, created = UserFolder.objects.get_or_create(
                name='Home',
                owner=user)
            poster = CustomImageModel.objects.create(
                folder=homedir,
                created_by=user,
                file="blabla.jpg")
        else:
            poster = CustomImageModel.objects.create(file="blabla.jpg")
        Broadcaster.objects.create(
            name="broadcaster1",
            poster=poster,
            url="http://test.live",
            status=True,
            is_restricted=True,
            building=building,
            iframe_url="http://iframe.live",
            iframe_height=120,
            public=False)
        # Test with a video on hold
        video_on_hold = Video.objects.create(
            title="VideoOnHold", owner=user, video="test.mp4",
            type=Type.objects.get(id=1))
        Broadcaster.objects.create(
            name="broadcaster2",
            poster=poster,
            url="http://test2.live",
            status=True,
            is_restricted=False,
            video_on_hold=video_on_hold,
            building=building,
            iframe_url="http://iframe2.live",
            iframe_height=140,
            password="mot2passe")
        print(" --->  SetUp of BroadcasterTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
        broadcaster = Broadcaster.objects.get(id=1)
        self.assertEqual(broadcaster.name, "broadcaster1")
        self.assertTrue("blabla" in broadcaster.poster.name)
        self.assertEqual(broadcaster.url, "http://test.live")
        self.assertEqual(broadcaster.iframe_url, "http://iframe.live")
        self.assertEqual(broadcaster.iframe_height, 120)
        self.assertEqual(broadcaster.status, True)
        self.assertEqual(broadcaster.public, False)
        self.assertEqual(broadcaster.is_restricted, True)
        self.assertEqual(broadcaster.building.id, 1)
        self.assertEqual(broadcaster.__str__(), "%s - %s" %
                         (broadcaster.name, broadcaster.url))
        broadcaster2 = Broadcaster.objects.get(id=2)
        self.assertEqual(broadcaster2.video_on_hold.id, 1)
        self.assertEqual(broadcaster2.password, "mot2passe")
        print(
            "   --->  test_attributs of BroadcasterTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Broadcaster.objects.get(id=1).delete()
        Broadcaster.objects.get(id=2).delete()
        self.assertEquals(Broadcaster.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of BroadcasterTestCase : OK !")
