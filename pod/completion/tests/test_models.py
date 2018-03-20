"""
Unit tests for completion models
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from pod.video.models import Type
from pod.video.models import Video
from pod.authentication.models import Owner
from pod.completion.models import Contributor
from pod.completion.models import Document
try:
    __import__('pod.filepicker')
    FILEPICKER = True
except:
    FILEPICKER = False
    pass

import datetime


class ContributorModelTestCase(TestCase):

    def setUp(self):
        test = User.objects.create(username='test')
        owner = Owner.objects.get(user__username='test')
        video = Video.objects.create(
            title='video',
            owner=owner,
            video='test.mp4'
        )
        Contributor.objects.create(
            video=video,
            name='contributor',
            email_address='contributor@pod.com',
            role='actor',
            weblink='http://pod.com'
        )
        Contributor.objects.create(
            video=video,
            name='contributor2'
        )

    def test_attributs_full(self):
        contributor = Contributor.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(contributor.video, video)
        self.assertEqual(contributor.name, 'contributor')
        self.assertEqual(contributor.email_address, 'contributor@pod.com')
        self.assertEqual(contributor.role, 'actor')
        self.assertEqual(contributor.weblink, 'http://pod.com')

        print(" ---> test_attributs_full : OK !")

    def test_attributs(self):
        contributor = Contributor.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(contributor.video, video)
        self.assertEqual(contributor.name, 'contributor2')
        self.assertEqual(contributor.email_address, '')
        self.assertEqual(contributor.role, 'author')
        self.assertEqual(contributor.weblink, None)

        print(" ---> test_attributs : OK !")

    def test_clean(self):
        print(" [ContributorModel --- END] ")


class DocumentModelTestCase(TestCase):

    def setUp(self):
        user = User.objects.create(username='test')
        owner = Owner.objects.get(user__username='test')
        video = Video.objects.create(
            title='video',
            owner=owner,
            video='test.mp4'
        )
        if FILEPICKER:
            Document.objects.create(
                video=video,
                document='/media/files/' + owner.hashkey + '/testfile.txt'
            )
        else:
            file = SimpleUploadedFile(
                name='testfile.txt',
                content=open(
                    './pod/filepicker/tests/testfile.txt', 'rb').read(),
                content_type='text/plain')
            Document.objects.create(
                video=video,
                document=file)
        Document.objects.create(
            video=video
        )

    def test_attributs_full(self):
        document = Document.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(document.video, video)
        if FILEPICKER:
        	self.assertTrue(isinstance(document.document, str))
        else:
        	self.assertTrue(document.document.name, 'testfile.txt')

        print(" ---> test_attributs_full : OK !")

    def test_attributs(self):
        document = Document.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(document.video, video)
        self.assertEqual(document.document, None)

        print(" ---> test_attributs : OK !")

    def test_clean(self):
    	print(" [DocumentModel --- END] ")
