"""
Unit tests for filepicker models
"""
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from pod.filepicker.models import CustomFileModel
from pod.filepicker.models import CustomImageModel
from pod.filepicker.models import UserDirectory
from datetime import datetime

import os
import shutil


class CustomFileModelTestCase(TestCase):

    def setUp(self):
        test = User.objects.create(username='test')
        file = SimpleUploadedFile(
            name='testfile.txt',
            content=open('./pod/filepicker/tests/testfile.txt', 'rb').read(),
            content_type='text/plain')
        home = UserDirectory.objects.create(name='Home', owner=test)
        CustomFileModel.objects.create(
            name='testfile',
            description='testfile',
            file_size=15,
            file_type='TXT',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=test,
            modified_by=test,
            directory=home,
            file=file)
        CustomFileModel.objects.create(
            name='testfile2',
            description='',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=test,
            modified_by=test,
            directory=home,
            file=file)

    def test_attributs_full(self):
        user = User.objects.get(id=1)
        file = CustomFileModel.objects.get(id=1)
        self.assertEqual(file.name, 'testfile')
        self.assertEqual(file.description, 'testfile')
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, 'TXT')
        self.assertTrue(isinstance(file.date_created, datetime))
        self.assertTrue(isinstance(file.date_modified, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.modified_by, user)
        if user.owner:
            self.assertTrue('files/' + user.owner.hashkey +
                            '/Home/testfile' in file.file.path)
        else:
            self.assertTrue('files/test/Home/testfile' in file.file.path)

        print(" ---> test_attributs_full : OK ! --- CustomFileModel")

    def test_attributs(self):
        user = User.objects.get(id=1)
        file = CustomFileModel.objects.get(id=2)
        self.assertTrue(file.name, 'testfile2')
        self.assertEqual(file.description, '')
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, 'TXT')
        self.assertTrue(isinstance(file.date_created, datetime))
        self.assertTrue(isinstance(file.date_modified, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.modified_by, user)
        if user.owner:
            self.assertTrue('files/' + user.owner.hashkey +
                            '/Home/testfile' in file.file.path)
        else:
            self.assertTrue('files/test/Home/testfile' in file.file.path)

        print(" [ BEGIN FILEPICKER_TEST_MODELS ] ")
        print(". ---> test_attributs : OK ! --- CustomFileModel")

    def tearDown(self):
        user = User.objects.get(id=1)
        if user.owner:
            hashkey = user.owner.hashkey
            if os.path.exists(os.path.join(
                    settings.MEDIA_ROOT, 'files', hashkey)):
                shutil.rmtree(os.path.join(
                    settings.MEDIA_ROOT, 'files', hashkey))
        else:
            username = user.username
            if os.path.exists(os.path.join(
                    settings.MEDIA_ROOT, 'files', username)):
                shutil.rmtree(os.path.join(
                    settings.MEDIA_ROOT, 'files', username))


class CustomImageModelTestCase(TestCase):

    def setUp(self):
        test = User.objects.create(username='test')
        file = SimpleUploadedFile(
            name='testimage.jpg',
            content=open('./pod/filepicker/tests/testimage.jpg', 'rb').read(),
            content_type='image/jpeg')
        home = UserDirectory.objects.create(name='Home', owner=test)
        CustomImageModel.objects.create(
            name='testimage',
            description='testimage',
            file_size=15,
            file_type='JPG',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=test,
            modified_by=test,
            directory=home,
            file=file)
        CustomImageModel.objects.create(
            name='testimage2',
            description='',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=test,
            modified_by=test,
            directory=home,
            file=file)

    def test_attributs_full(self):
        user = User.objects.get(id=1)
        file = CustomImageModel.objects.get(id=1)
        self.assertEqual(file.name, 'testimage')
        self.assertEqual(file.description, 'testimage')
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, 'JPG')
        self.assertTrue(isinstance(file.date_created, datetime))
        self.assertTrue(isinstance(file.date_modified, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.modified_by, user)
        if user.owner:
            self.assertTrue('files/' + user.owner.hashkey +
                            '/Home/testimage' in file.file.path)
        else:
            self.assertTrue('files/test/Home/testimage' in file.file.path)

        print(" ---> test_attributs_full : OK ! --- CustomImageModel")

    def test_attributs(self):
        user = User.objects.get(id=1)
        file = CustomImageModel.objects.get(id=2)
        self.assertTrue(file.name, 'testimage2')
        self.assertEqual(file.description, '')
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, 'JPG')
        self.assertTrue(isinstance(file.date_created, datetime))
        self.assertTrue(isinstance(file.date_modified, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.modified_by, user)
        if user.owner:
            self.assertTrue('files/' + user.owner.hashkey +
                            '/Home/testimage' in file.file.path)
        else:
            self.assertTrue('files/test/Home/testimage' in file.file.path)

        print(" ---> test_attributs : OK ! --- CustomImageModel")

    def tearDown(self):
        user = User.objects.get(id=1)
        if user.owner:
            hashkey = user.owner.hashkey
            if os.path.exists(os.path.join(
                    settings.MEDIA_ROOT, 'files', hashkey)):
                shutil.rmtree(os.path.join(
                    settings.MEDIA_ROOT, 'files', hashkey))
        else:
            username = user.username
            if os.path.exists(os.path.join(
                    settings.MEDIA_ROOT, 'files', username)):
                shutil.rmtree(os.path.join(
                    settings.MEDIA_ROOT, 'files', username))


class UserDirectoryTestCase(TestCase):

    def setUp(self):
        test = User.objects.create(username='test')
        home = UserDirectory.objects.create(name='Home', owner=test)
        UserDirectory.objects.create(name='Images', owner=test, parent=home)
        UserDirectory.objects.create(name='Documents', owner=test, parent=home)

    def test_attributs_full(self):
        user = User.objects.get(id=1)
        parent = UserDirectory.objects.get(id=1)
        child = UserDirectory.objects.get(id=2)
        self.assertEqual(child.name, 'Images')
        self.assertEqual(child.owner, user)
        self.assertEqual(child.parent, parent)

        print(" ---> test_attributs_full : OK ! --- UserDirectory")

    def test_attributs(self):
        user = User.objects.get(id=1)
        home = UserDirectory.objects.get(id=1)
        self.assertEqual(home.name, 'Home')
        self.assertEqual(home.owner, user)
        self.assertEqual(home.parent, None)

        print(" ---> test_attributs : OK ! --- UserDirectory")

    def test_same_parent(self):
        user = User.objects.get(id=1)
        home = UserDirectory.objects.get(id=1)
        UserDirectory.objects.filter(id=1).update(parent=home)
        self.assertEqual(home.parent, None)

        print(" ---> test_same_parent : OK ! --- UserDirectory")
        print(" [ END FILEPICKER_TEST_MODELS ] ")

    def test_path(self):
        home = UserDirectory.objects.get(id=1)
        images = UserDirectory.objects.get(id=2)
        documents = UserDirectory.objects.get(id=3)
        self.assertEqual(home.get_path(), 'Home/')
        self.assertEqual(images.get_path(), 'Home/Images/')
        self.assertEqual(documents.get_path(), 'Home/Documents/')

        print(" ---> test_path : OK ! --- UserDirectory")

    def tearDown(self):
        UserDirectory.objects.get(id=1).delete()
        self.assertFalse(UserDirectory.objects.all())
