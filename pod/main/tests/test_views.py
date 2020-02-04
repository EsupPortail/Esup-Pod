"""
Unit tests for main views
"""
from django.test import override_settings
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from captcha.models import CaptchaStore

import tempfile
import os


class MainViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        User.objects.create(username='pod', password='podv2')
        print(" --->  SetUp of MainViewsTestCase : OK !")

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_download_file(self):
        self.client = Client()

        # GET method is used
        response = self.client.get('/download/')
        self.assertRaises(PermissionDenied)

        # POST method is used
        # filename is not set
        response = self.client.post('/download/')
        self.assertRaises(PermissionDenied)
        # filename is properly set
        temp_file = tempfile.NamedTemporaryFile()
        response = self.client.post('/download/',
                                    {'filename': temp_file.name})
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="%s"' % (
            os.path.basename(temp_file.name)))
        self.assertEqual(response.status_code, 200)

        print(
            "   --->  download_file of mainViewsTestCase : OK !")

    def test_contact_us(self):
        self.client = Client()

        # GET method is used
        response = self.client.get('/contact_us/')
        self.assertTemplateUsed(response, 'contact_us.html')

        # POST method is used
        # Form is valid
        hashcode = CaptchaStore.generate_key()
        captcha = CaptchaStore.objects.get(hashkey=hashcode)  # Forcing captcha
        response = self.client.post('/contact_us/',
                                    {'name': 'pod',
                                     'email': 'pod@univ.fr',
                                     'subject': 'info',
                                     'description': 'pod',
                                     'captcha_0': captcha.hashkey,
                                     'captcha_1': captcha.response,
                                     'url_referrer': 'http://localhost:8000/'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), u'Your message have been sent.')
        self.assertRedirects(response, 'http://localhost:8000/')
        print(
            "   --->  test_contact_us of mainViewsTestCase : OK !")
        # Form is not valid
        #  /!\  voir fonction clean de ContactUsForm segment if
        response = self.client.post('/contact_us/',
                                    {'name': '',
                                     'email': '',
                                     'subject': 'info',
                                     'description': '',
                                     'captcha': ''})
        self.assertTemplateUsed(response, 'contact_us.html')
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         u'One or more errors have been found in the form.')
        self.assertTemplateUsed(response, 'contact_us.html')

        print(
            "   --->  test_contact_us of mainViewsTestCase : OK !")
