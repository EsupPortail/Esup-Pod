"""
Unit tests for recorder views
"""
import os

from django.conf import settings
from django.test import override_settings
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied


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
class recorderViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        User.objects.create(username='pod', password='podv2')
        print(" --->  SetUp of recorderViewsTestCase : OK !")

    def test_add_recording(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/add_recording/")
        self.assertRaises(PermissionDenied)  # No mediapath and user is not SU

        self.user.is_superuser = True
        self.user.save()
        response = self.client.get("/add_recording/",
                                   {'mediapath': 'video.mp4',
                                    'type': 'something'})
        self.assertEqual(response.status_code, 302)  # User is not staff

        self.user.is_staff = True
        self.user.save()
        response = self.client.get("/add_recording/",
                                   {'mediapath': 'video.mp4',
                                    'type': 'something'})
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'recorder/add_recording.html')

        print(
            "   --->  test_add_recording of recorderViewsTestCase : OK !")
