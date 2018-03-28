"""
Unit tests for filepicker views
"""
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from pod.authentication.models import Owner

import json
import shutil
import os


class CustomFilePickerTestCase(TestCase):

    def setUp(self):
        user = User.objects.create(username='test', password='azerty')
        user.set_password('hello')
        user.save()
        user2 = User.objects.create(username='test2', password='azerty')
        user2.set_password('hello')
        user2.save()
        superuser = User.objects.create(
            username='superuser', password='azerty', is_superuser=True)
        superuser.set_password('hello')
        superuser.save()

    def test_CustomFilePicker_upload_file(self):
        test = User.objects.get(id=1)
        test = authenticate(username='test', password='hello')
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
            'created_by': test.id,
            'description': 'testfile',
            'file': newfile,
            '': 'Submit'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('link_content' in str(response.content))

        print(" ---> test_CustomFilePicker_upload_file : OK !")

    def test_CustomImagePicker_upload_file(self):
        test = User.objects.get(id=1)
        test = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/img/upload/file/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in str(response.content))
        with open('./pod/filepicker/tests/testimage.jpg', 'rb') as testimage:
            response = self.client.post(
                '/file-picker/img/upload/file/', data={'userfile': testimage})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('name' in str(response.content))
        newimage = json.loads(response.content)['name']
        response = self.client.post('/file-picker/img/upload/file/', data={
            'name': 'testimage',
            'created_by': test.id,
            'description': 'testimage',
            'file': newimage,
            '': 'Submit'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('link_content' in str(response.content))

        print(" ---> test_CustomImagePicker_upload_file : OK !")

    def test_CustomFilePicker_list_file(self):
        test = User.objects.get(id=1)
        test = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/files/')
        self.assertEqual(response.status_code, 200)
        search = json.loads(response.content)['result']
        self.assertTrue(len(search) == 0)

        with open('./pod/filepicker/tests/testfile.txt', 'rb') as testfile:
            response = self.client.post(
                '/file-picker/file/upload/file/', data={'userfile': testfile})
        newfile = json.loads(response.content)['name']
        response = self.client.post('/file-picker/file/upload/file/', data={
            'name': 'testfile',
            'created_by': test.id,
            'description': 'testfile',
            'file': newfile,
            '': 'Submit'
        })
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/file-picker/file/files/')
        self.assertEqual(response.status_code, 200)
        search = json.loads(response.content)['result']
        self.assertTrue(len(search) == 1)

        print(" ---> test_CustomFilePicker_list_file : OK !")

    def test_CustomImagePicker_list_file(self):
        test = User.objects.get(id=1)
        test = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/img/files/')
        self.assertEqual(response.status_code, 200)
        search = json.loads(response.content)['result']
        self.assertTrue(len(search) == 0)

        with open('./pod/filepicker/tests/testimage.jpg', 'rb') as testimage:
            response = self.client.post(
                '/file-picker/img/upload/file/', data={'userfile': testimage})
        newimage = json.loads(response.content)['name']
        response = self.client.post('/file-picker/img/upload/file/', data={
            'name': 'testimage',
            'created_by': test.id,
            'description': 'testimage',
            'file': newimage,
            '': 'Submit'
        })
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/file-picker/img/files/')
        self.assertEqual(response.status_code, 200)
        search = json.loads(response.content)['result']
        self.assertTrue(len(search) == 1)

        print(" ---> test_CustomImagePicker_list_file : OK !")

    def test_CustomFilePicker_delete_file(self):
        test = User.objects.get(id=1)
        test = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        with open('./pod/filepicker/tests/testfile.txt', 'rb') as testfile:
            response = self.client.post(
                '/file-picker/file/upload/file/', data={'userfile': testfile})
        newfile = json.loads(response.content)['name']
        response = self.client.post('/file-picker/file/upload/file/', data={
            'name': 'testfile',
            'created_by': test.id,
            'description': 'testfile',
            'file': newfile,
            '': 'Submit'
        })
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/file-picker/delete/file/1/TXT/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/file-picker/file/files/')
        self.assertEqual(response.status_code, 200)
        search = json.loads(response.content)['result']
        self.assertTrue(len(search) == 0)

        print(" ---> test_CustomFilePicker_delete_file : OK !")

    def test_CustomFilePicker_user(self):
        test = User.objects.get(id=1)
        test = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        with open('./pod/filepicker/tests/testfile.txt', 'rb') as testfile:
            response = self.client.post(
                '/file-picker/file/upload/file/', data={'userfile': testfile})
        newfile = json.loads(response.content)['name']
        response = self.client.post('/file-picker/file/upload/file/', data={
            'name': 'testfile',
            'created_by': test.id,
            'description': 'testfile',
            'file': newfile,
            '': 'Submit'
        })
        self.assertEqual(response.status_code, 200)

        # test2 = User.objects.get(id=2)
        # test2 = authenticate(username='test2', password='hello')
        login = self.client.login(username='test2', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/files/')
        self.assertEqual(response.status_code, 200)
        search = json.loads(response.content)['result']
        self.assertTrue(len(search) == 0)

        # superuser = User.objects.get(id=3)
        # superuser = authenticate(username='superuser', password='hello')
        login = self.client.login(username='superuser', password='hello')
        self.assertTrue(login)
        response = self.client.get('/file-picker/file/files/')
        self.assertEqual(response.status_code, 200)
        search = json.loads(response.content)['result']
        self.assertTrue(len(search) == 1)

        print(" ---> test_CustomFilePicker_user : OK !")

    def test_CustomFilePicker_search(self):
        test = User.objects.get(id=1)
        test = authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        with open('./pod/filepicker/tests/testfile.txt', 'rb') as testfile:
            response = self.client.post(
                '/file-picker/file/upload/file/', data={'userfile': testfile})
        newfile = json.loads(response.content)['name']
        response = self.client.post('/file-picker/file/upload/file/', data={
            'name': 'testfile',
            'created_by': test.id,
            'description': 'testfile',
            'file': newfile,
            '': 'Submit'
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/file-picker/file/files/?search=test')
        self.assertEqual(response.status_code, 200)
        search = json.loads(response.content)['result']
        self.assertTrue(len(search) == 1)
        response = self.client.get('/file-picker/file/files/?search=hello')
        self.assertEqual(response.status_code, 200)
        search = json.loads(response.content)['result']
        self.assertTrue(len(search) == 0)

        print(" ---> test_CustomFilePicker_search : OK !")

    def test_clean(self):
        test = Owner.objects.get(user__username='test')
        hashkey = test.hashkey
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'files', hashkey))

        print(" [CustomFilePickerViews --- END ] ")
