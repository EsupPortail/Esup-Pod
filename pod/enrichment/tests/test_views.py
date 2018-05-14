"""
Unit tests for enrichment views
"""
from django.apps import apps
from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from pod.video.models import Video
from pod.enrichment.models import Enrichment
if apps.is_installed('pod.filepicker'):
    from pod.filepicker.models import CustomImageModel
    from pod.filepicker.models import UserDirectory
    from datetime import datetime
    FILEPICKER = True


class EnrichmentViewsTestCase(TestCase):

    def setUp(self):
        owner = User.objects.create(
            username='test', password='azerty', is_staff=True)
        owner.set_password('hello')
        owner.save()
        Video.objects.create(
            title='videotest',
            owner=owner,
            video='test.mp4',
            duration=20
        )

    def test_video_enrichment(self):
        video = Video.objects.get(id=1)
        response = self.client.get('/video_enrichment/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/video_enrichment/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_enrichment.html')
        self.assertContains(response, 'videotest')
        self.assertContains(response, 'list_enrich')

        print(" ---> test_video_enrichment : OK!")

    def test_video_enrichment_new(self):
        video = Video.objects.get(id=1)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_enrichment/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_enrichment.html')
        self.assertContains(response, 'videotest')
        self.assertContains(response, 'list_enrich')
        self.assertContains(response, 'form_enrich')
        response = self.client.post(
            '/video_enrichment/{0}/'.format(video.slug),
            data={'action': 'save',
                  'enrich_id': None,
                  'video': 1,
                  'title': 'testenrich',
                  'start': 1,
                  'end': 2,
                  'type': 'weblink',
                  'weblink': 'http://test.com'})
        self.assertEqual(response.status_code, 200)
        result = Enrichment.objects.all()
        self.assertTrue(result)
        self.assertTemplateUsed('video_enrichment.html')
        self.assertContains(response, 'videotest')
        self.assertContains(response, 'list_enrich')
        self.assertContains(response, 'testenrich')

        print(" ---> test_video_enrichment_new : OK!")
        print(" [ END ENRICHMENT VIEWS ] ")

    def test_video_enrichment_edit(self):
        video = Video.objects.get(id=1)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_enrichment/{0}/'.format(video.slug),
            data={'action': 'save',
                  'enrich_id': None,
                  'video': 1,
                  'title': 'testenrich',
                  'start': 1,
                  'end': 2,
                  'type': 'weblink',
                  'weblink': 'http://test.com'})
        self.assertEqual(response.status_code, 200)
        result = Enrichment.objects.all()
        self.assertTrue(result)
        result = Enrichment.objects.get(id=1)
        response = self.client.post(
            '/video_enrichment/{0}/'.format(video.slug),
            data={'action': 'save',
                  'enrich_id': result.id,
                  'video': 1,
                  'title': 'testenrich2',
                  'start': 2,
                  'end': 3,
                  'type': 'weblink',
                  'weblink': 'http://test.com'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('video_enrichment.html')
        self.assertContains(response, 'videotest')
        self.assertContains(response, 'list_enrich')
        self.assertContains(response, 'testenrich2')

        print(" ---> test_video_enrichment_edit : OK!")

    def test_video_chapter_delete(self):
        video = Video.objects.get(id=1)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_enrichment/{0}/'.format(video.slug),
            data={'action': 'save',
                  'enrich_id': None,
                  'video': 1,
                  'title': 'testenrich',
                  'start': 1,
                  'end': 2,
                  'type': 'weblink',
                  'weblink': 'http://test.com'})
        self.assertEqual(response.status_code, 200)
        result = Enrichment.objects.all()
        self.assertTrue(result)
        result = Enrichment.objects.get(id=1)
        response = self.client.post(
            '/video_enrichment/{0}/'.format(video.slug),
            data={'action': 'delete',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        result = Enrichment.objects.all()
        self.assertFalse(result)

        print(" [ BEGIN ENRICHMENT VIEWS ] ")
        print(" ---> test_video_enrichment_delete : OK!")