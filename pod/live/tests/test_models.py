import os

from django.test import TestCase
from django.test import override_settings
from django.conf import settings
from django.contrib.auth.models import User

from ..models import Building, Broadcaster

if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    },
    LANGUAGE_CODE='en'
)
class BuildingTestCase(TestCase):

    def setUp(self):
        Building.objects.create(name="bulding1")
        print(" --->  SetUp of BuildingTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
        building = Building.objects.get(id=1)
        self.assertEqual(building.name, "bulding1")
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


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    },
    LANGUAGE_CODE='en'
)
class BroadcasterTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        building = Building.objects.create(name="bulding1")
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
            building=building)

        print(" --->  SetUp of BroadcasterTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
        broadcaster = Broadcaster.objects.get(id=1)
        self.assertEqual(broadcaster.name, "broadcaster1")
        self.assertTrue("blabla" in broadcaster.poster.name)
        self.assertEqual(broadcaster.url, "http://test.live")
        self.assertEqual(broadcaster.status, True)
        self.assertEqual(broadcaster.is_restricted, True)
        self.assertEqual(broadcaster.building.id, 1)
        self.assertEqual(broadcaster.__str__(), "%s - %s" %
                         (broadcaster.name, broadcaster.url))

        print(
            "   --->  test_attributs of BroadcasterTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Broadcaster.objects.get(id=1).delete()
        self.assertEquals(Broadcaster.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of BroadcasterTestCase : OK !")
