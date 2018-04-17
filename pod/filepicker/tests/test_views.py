"""
Unit tests for filepicker views
"""
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.files.uploadedfile import SimpleUploadedFile
from pod.filepicker.models import CustomFileModel
from pod.filepicker.models import CustomImageModel
from pod.filepicker.models import UserDirectory
from datetime import datetime

import json
import shutil
import os

##
# FILE VIEWS
#


class FileViewsTestCase(TestCase):

    def setUp(self):
        user = User.objects.create(username='test', password='azerty')
        user.set_password('hello')
        user.save()
        UserDirectory.objects.create(owner=user, name='Home')

    def test_home(self):
        UserDirectory.objects.get(id=1).delete()
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/directories/')
        self.assertTrue(response.status_code, 200)
        self.assertTrue(UserDirectory.objects.get(owner=user, name='Home'))
        response = self.client.get('/file-picker/img/directories/')
        self.assertTrue(response.status_code, 200)
        self.assertTrue(UserDirectory.objects.get(owner=user, name='Home'))

        print(" ---> test_home : OK !")

    def test_upload_files(self):
        directory = UserDirectory.objects.get(id=1)
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/upload/file/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in str(response.content))
        with open('./pod/filepicker/tests/testfile.txt', 'rb') as testfile:
            response = self.client.post(
                '/file-picker/file/upload/file/', data={'userfile': testfile})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('name' in str(response.content))
        newfile = json.loads(response.content)['name']
        response = self.client.post('/file-picker/file/upload/file/', data={
            'name': 'testfile',
            'created_by': user.id,
            'description': 'testfile',
            'directory': directory.id,
            'file': newfile,
            '': 'Submit'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('link_content' in str(response.content))

        print(" ---> test_upload_files : OK !")

    def test_upload_images(self):
        directory = UserDirectory.objects.get(id=1)
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/img/upload/file/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in str(response.content))
        with open('./pod/filepicker/tests/testimage.jpg', 'rb') as testimage:
            response = self.client.post(
                '/file-picker/file/upload/file/', data={'userfile': testimage})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('name' in str(response.content))
        newfile = json.loads(response.content)['name']
        response = self.client.post('/file-picker/img/upload/file/', data={
            'name': 'testimage',
            'created_by': user.id,
            'description': 'testimage',
            'directory': directory.id,
            'file': newfile,
            '': 'Submit'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('link_content' in str(response.content))

        print(" ---> test_upload_images : OK !")
        print(" [ END FILE VIEWS ] ")

    def test_list_files(self):
        home = UserDirectory.objects.get(id=1)
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/files/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue(len(result) == 0)
        file = SimpleUploadedFile(
            name='testfile.txt',
            content=open('./pod/filepicker/tests/testfile.txt', 'rb').read(),
            content_type='text/plain')
        CustomFileModel.objects.create(
            name='testfile',
            description='',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=user,
            modified_by=user,
            directory=home,
            file=file)
        response = self.client.get('/file-picker/file/files/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue(len(result) == 1)

        print(" ---> test_list_files : OK!")

    def test_list_images(self):
        home = UserDirectory.objects.get(id=1)
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/img/files/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue(len(result) == 0)
        file = SimpleUploadedFile(
            name='testimage.jpg',
            content=open('./pod/filepicker/tests/testimage.jpg', 'rb').read(),
            content_type='image/jpeg')
        CustomImageModel.objects.create(
            name='testimage',
            description='',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=user,
            modified_by=user,
            directory=home,
            file=file)
        response = self.client.get('/file-picker/img/files/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue(len(result) == 1)

        print(" ---> test_list_images : OK!")

    def test_delete_files(self):
        home = UserDirectory.objects.get(id=1)
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        file = SimpleUploadedFile(
            name='testfile.txt',
            content=open('./pod/filepicker/tests/testfile.txt', 'rb').read(),
            content_type='text/plain')
        CustomFileModel.objects.create(
            name='testfile',
            description='',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=user,
            modified_by=user,
            directory=home,
            file=file)
        response = self.client.get('/file-picker/file/delete/file/1/')
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/file-picker/file/delete/file/1/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomFileModel.objects.all())

        print(" [ BEGIN FILEPICKER_FILE VIEWS ] ")
        print(". ---> test_delete_files : OK!")

    def test_delete_images(self):
        home = UserDirectory.objects.get(id=1)
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        file = SimpleUploadedFile(
            name='testimage.jpg',
            content=open('./pod/filepicker/tests/testimage.jpg', 'rb').read(),
            content_type='image/jpeg')
        CustomImageModel.objects.create(
            name='testimage',
            description='',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=user,
            modified_by=user,
            directory=home,
            file=file)
        response = self.client.get('/file-picker/img/delete/file/1/')
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/file-picker/img/delete/file/1/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomFileModel.objects.all())

        print(" ---> test_delete_images : OK!")

    def test_search(self):
        home = UserDirectory.objects.get(id=1)
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/files/?search=testfile')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue(len(result) == 0)
        file = SimpleUploadedFile(
            name='testfile.txt',
            content=open('./pod/filepicker/tests/testfile.txt', 'rb').read(),
            content_type='text/plain')
        CustomFileModel.objects.create(
            name='testfile',
            description='',
            date_created=datetime.now(),
            date_modified=datetime.now(),
            created_by=user,
            modified_by=user,
            directory=home,
            file=file)
        response = self.client.get('/file-picker/file/files/?search=testfile')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue(len(result) == 1)
        response = self.client.get('/file-picker/file/files/?search=test')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue(len(result) == 1)
        response = self.client.get('/file-picker/file/files/?search=file')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue(len(result) == 1)
        response = self.client.get('/file-picker/file/files/?search=teestfile')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue(len(result) == 0)

        print(" ---> test_search : OK!")

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

##
# DIRECTORY VIEWS
#


class DirectoryViewTestCase(TestCase):

    def setUp(self):
        user = User.objects.create(username='test', password='azerty')
        user.set_password('hello')
        user.save()
        home = UserDirectory.objects.create(owner=user, name='Home')
        UserDirectory.objects.create(owner=user, name='Child', parent=home)

    def test_list_directories(self):
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/directories/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue('Home' in result)
        self.assertTrue(len(result['Home']) == 1)
        response = self.client.get('/file-picker/img/directories/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue('Home' in result)
        self.assertTrue(len(result['Home']) == 1)
        response = self.client.get(
            '/file-picker/file/directories/?directory=2')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['result']
        self.assertTrue('Child' in result)
        self.assertTrue(len(result['Child']) == 0)

        print(" ---> test_list_directories : OK!")

    def test_edit_directory(self):
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/directories/configure/')
        self.assertTrue(response.status_code, 400)
        response = self.client.get(
            '/file-picker/file/directories/configure/?action=edit&id=2')
        self.assertTrue(response.status_code, 200)
        result = json.loads(response.content)['id']
        self.assertTrue(result == 2)
        result = json.loads(response.content)['form']
        self.assertTrue('Child' in result)
        response = self.client.post(
            '/file-picker/file/directories/configure/',
            data={'id': 2,
                  'name': 'Chiild',
                  'owner': 1,
                  'parent': 1,
                  'action': 'edit',
                  ':': 'Submit'})
        self.assertTrue(response.status_code, 200)
        directory = UserDirectory.objects.get(id=2)
        self.assertEqual(directory.name, 'Chiild')
        response = self.client.post(
            '/file-picker/file/directories/configure/',
            data={'id': 2,
                  'name': 'Home',
                  'owner': 1,
                  'parent': 1,
                  'action': 'edit',
                  ':': 'Submit'})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)['errors']
        self.assertTrue(len(result['__all__']) == 1)

        print(". ---> test_edit_directory : OK !")

    def test_new_directory(self):
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/directories/configure/')
        self.assertTrue(response.status_code, 400)
        response = self.client.get(
            '/file-picker/file/directories/configure/?action=new&id=2')
        self.assertTrue(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue('form' in result)
        response = self.client.post(
            '/file-picker/file/directories/configure/',
            data={'name': 'Child2',
                  'owner': 1,
                  'parent': 2,
                  'action': 'new',
                  ':': 'Submit'})
        self.assertTrue(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue('parent' in result)
        self.assertTrue('Child' in result['parent'])
        response = self.client.post(
            '/file-picker/file/directories/configure/',
            data={'name': 'Child',
                  'owner': 1,
                  'parent': 1,
                  'action': 'new',
                  ':': 'Submit'})
        self.assertTrue(response.status_code, 200)
        result = json.loads(response.content)['errors']
        self.assertTrue(len(result['__all__']) == 1)
        response = self.client.post(
            '/file-picker/file/directories/configure/',
            data={'name': 'Home',
                  'owner': 1,
                  'parent': 2,
                  'action': 'new',
                  ':': 'Submit'})
        self.assertTrue(response.status_code, 200)
        result = json.loads(response.content)['errors']
        self.assertTrue(len(result['__all__']) == 1)

        print(" ---> test_new_directory : OK!")
        print(" [ END FILEPICKER_DIRECTORY VIEWS ] ")

    def test_delete_directory(self):
        user = User.objects.get(id=1)
        user = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/directories/configure/')
        self.assertTrue(response.status_code, 400)
        response = self.client.get(
            '/file-picker/file/directories/configure/?action=delete&id=2')
        self.assertTrue(response.status_code, 200)
        response = self.client.post(
            '/file-picker/file/directories/configure/',
            data={'id': 2,
                  'action': 'delete',
                  ':': 'Yes'})
        self.assertTrue(response.status_code, 200)
        self.assertFalse(UserDirectory.objects.filter(name='Child'))
        response = self.client.post(
            '/file-picker/file/directories/configure/',
            data={'id': 1,
                  'action': 'delete',
                  ':': 'Yes'})
        self.assertTrue(response.status_code, 400)

        print(" [ BEGIN FILEPICKER_DIRECTORY VIEWS ] ")
        print(" ---> test_delete_directory : OK!")
