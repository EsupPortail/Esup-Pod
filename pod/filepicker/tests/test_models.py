"""
Unit tests for filepicker models
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from pod.authentication.models import Owner
from pod.filepicker.models import CustomFileModel
from pod.filepicker.models import CustomImageModel
from datetime import datetime


class CustomFileModelTestCase(TestCase):

    def setUp(self):
        test = User.objects.create(username='test')
        file = SimpleUploadedFile(
            name='testfile.txt',
            content=open('./pod/filepicker/tests/testfile.txt', 'rb').read(),
            content_type='text/plain')
        CustomFileModel.objects.create(
            name='testfile',
            description='testfile',
            file_size=15,
            file_type='TXT',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=test,
            modified_by=test,
            file=file)
        CustomFileModel.objects.create(
            name='testfile2',
            description='',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=test,
            modified_by=test,
            file=file)

    def test_attributs_full(self):
        user = User.objects.get(id=1)
        owner = Owner.objects.get(user__username='test')
        file = CustomFileModel.objects.get(id=1)
        self.assertEqual(file.name, 'testfile')
        self.assertEqual(file.description, 'testfile')
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, 'TXT')
        self.assertTrue(isinstance(file.date_created, datetime))
        self.assertTrue(isinstance(file.date_modified, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.modified_by, user)
        self.assertTrue(owner.hashkey in file.file.path)

        print(" ---> test_attributs_full : OK !")

    def test_attributs(self):
        user = User.objects.get(id=1)
        owner = Owner.objects.get(user__username='test')
        file = CustomFileModel.objects.get(id=2)
        self.assertTrue(file.name, 'testfile2')
        self.assertEqual(file.description, '')
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, 'TXT')
        self.assertTrue(isinstance(file.date_created, datetime))
        self.assertTrue(isinstance(file.date_modified, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.modified_by, user)
        self.assertTrue(owner.hashkey in file.file.path)

        print(" ---> test_attributs : OK !")

    def test_clean(self):
        print(" [CustomFileModel --- END ] ")


class CustomImageModelTestCase(TestCase):

    def setUp(self):
        test = User.objects.create(username='test')
        file = SimpleUploadedFile(
            name='testimage.jpg',
            content=open('./pod/filepicker/tests/testimage.jpg', 'rb').read(),
            content_type='image/jpeg')
        CustomImageModel.objects.create(
            name='testfile',
            description='testfile',
            file_size=15,
            file_type='JPG',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=test,
            modified_by=test,
            file=file)
        CustomImageModel.objects.create(
            name='testfile2',
            description='',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=test,
            modified_by=test,
            file=file)

    def test_attributs_full(self):
        user = User.objects.get(id=1)
        owner = Owner.objects.get(user__username='test')
        file = CustomImageModel.objects.get(id=1)
        self.assertEqual(file.name, 'testfile')
        self.assertEqual(file.description, 'testfile')
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, 'JPG')
        self.assertTrue(isinstance(file.date_created, datetime))
        self.assertTrue(isinstance(file.date_modified, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.modified_by, user)
        self.assertTrue(owner.hashkey in file.file.path)

        print(" ---> test_attributs_full : OK !")

    def test_attributs(self):
        user = User.objects.get(id=1)
        owner = Owner.objects.get(user__username='test')
        file = CustomImageModel.objects.get(id=2)
        self.assertTrue(file.name, 'testfile2')
        self.assertEqual(file.description, '')
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, 'JPG')
        self.assertTrue(isinstance(file.date_created, datetime))
        self.assertTrue(isinstance(file.date_modified, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.modified_by, user)
        self.assertTrue(owner.hashkey in file.file.path)

        print(" ---> test_attributs : OK !")

    def test_clean(self):
        print(" [CustomImageModel --- END ] ")
