# -*- coding: utf-8 -*-
"""
Unit tests for podfile views
"""
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.encoding import force_text
from django.urls import reverse
from django.test import Client
from django.conf.urls import url
from django.conf.urls import include
from django.contrib.auth import authenticate
from pod.video.models import Type
from ..models import Recorder, Recording, Job
from pod.urls import urlpatterns

import json
import os

@override_settings(
    ROOT_URLCONF=__name__,
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    },
    LANGUAGE_CODE='en'
)
class Mediacourse(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        # user is staff but user2 not
        user = User.objects.create(username='remi', password='12345', is_active=True, is_staff=True)
        user.set_password('hello')
        user.save()

        user2 = User.objects.create(username='remi2', password='12345', is_active=True)
        user2.set_password('hello')
        user2.save()

        # add recorder
        videotype = Type.objects.create(title='others')
        recorder1 = Recorder.objects.create(id=1, user=user, name="recorder1", address_ip="1.1.1.1", type=videotype, salt="production", directory="dir1")
        recorder1.save()

        print(" --->  SetUp of Mediacourse : OK !")

    def test_access_user_staff_mediacourse_add(self):
        self.client = Client()
        user = User.objects.get(username="remi")
        user = authenticate(username='remi', password='hello')
        login = self.client.login(username='remi', password='hello')
        self.assertEqual(login, True)
        response = self.client.get("/mediacourses_add/?mediapath=abcdefg.zip&recorder=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.client.logout()
        self.assertTrue(self.client.session.get('_auth_user_id') == None)
        print("   --->  test_access_user_staff_mediacourse_add of Mediacourse : OK !")

    def test_access_user_mediacourse_add_without_args(self):
        self.client = Client()
        user = User.objects.get(username="remi")
        user = authenticate(username='remi', password='hello')
        login = self.client.login(username='remi', password='hello')
        self.assertEqual(login, True)
        # Without recorder argument
        response = self.client.get("/mediacourses_add/?mediapath=abcdefg.zip")
        self.assertEqual(response.status_code, 403)
        # Without recorder and mediapath arguments
        response = self.client.get("/mediacourses_add/")
        self.assertEqual(response.status_code, 403)
        print("   --->  test_access_user_mediacourse_add_without_args of Mediacourse : OK !")

class Mediacourse_notify(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        user1 = User.objects.create(username="pod")
        videotype = Type.objects.create(title='others')
        # add recorder
        recorder1 = Recorder.objects.create(id=1,user=user1, name="recorder1", address_ip="1.1.1.1", type=videotype, salt="test", directory="dir1")
        recorder1.save()
        print(" --->  SetUp of Mediacourse_notify : OK !")

    def test_mediacourse_notify_args(self):
        response = self.client.get("/mediacourses_notify/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "nok : recordingPlace or mediapath or key are missing".encode('utf-8'))
        response = self.client.get("/mediacourses_notify/?toto=toto")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "nok : recordingPlace or mediapath or key are missing".encode('utf-8'))
        response = self.client.get("/mediacourses_notify/?recordingPlace=19_16_1_59")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "nok : recordingPlace or mediapath or key are missing".encode('utf-8'))
        response = self.client.get("/mediacourses_notify/?recordingPlace=19_16_1_59&mediapath=4b2652fb-d890-46d4-bb15-9a47c6666239.zip")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "nok : recordingPlace or mediapath or key are missing".encode('utf-8'))
        response = self.client.get("/mediacourses_notify/?recordingPlace=19_16_1_59&mediapath=4b2652fb-d890-46d4-bb15-9a47c6666239.zip&key=badhashkey")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "nok : address_ip not valid".encode('utf-8'))
        print("   --->  test_mediacourse_notify_args of mediacourse_notify : OK !")

    def test_mediacourse_notify_without_good_recorder(self):
        import hashlib
        m = hashlib.md5()
        m.update("19_16_1_10test".encode('utf-8'))
        response = self.client.get("/mediacourses_notify/?recordingPlace=1_1_1_1&mediapath=4b2652fb-d890-46d4-bb15-9a47c6666239.zip&key=%s" % m.hexdigest())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "nok : key is not valid".encode('utf-8'))
        print("   --->  test_mediacourse_notify_without_good_recorder of mediacourse_notify : OK !")

    def test_mediacourse_notify_good(self):
        import hashlib
        m = hashlib.md5()
        m.update("1_1_1_1test".encode('utf-8'))
        response = self.client.get("/mediacourses_notify/?recordingPlace=1_1_1_1&mediapath=4b2652fb-d890-46d4-bb15-9a47c6666239.zip&key=%s" % m.hexdigest())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "ok".encode('utf-8'))
        print("   --->  test_mediacourse_notify_good of mediacourse_notify : OK !")