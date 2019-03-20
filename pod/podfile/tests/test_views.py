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

from ..models import CustomFileModel
from ..models import CustomImageModel
from ..models import UserFolder

from pod.urls import urlpatterns

import json
import os

urlpatterns += [url(r'^podfile/', include('pod.podfile.urls')), ]

##
# FOLDER VIEWS
#


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
class FolderViewTestCase(TestCase):

    def setUp(self):
        user = User.objects.create(username='pod', password='azerty')
        UserFolder.objects.get(owner=user, name='home')
        UserFolder.objects.create(owner=user, name='Child')
        User.objects.create(username='pod2', password='azerty')

    def test_list_folders(self):

        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(reverse('podfile:folder',
                                           kwargs={'type': 'file'}))
        self.assertEqual(response.status_code, 302)  # user is not staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('podfile:folder',
                                           kwargs={'type': 'file'}))
        self.assertEqual(response.status_code, 200)  # user is staff
        self.assertEqual(
            response.context["list_folder"].paginator.count,
            1)
        self.assertEqual(
            response.context["user_home_folder"],
            UserFolder.objects.get(owner=self.user, name='home'))
        self.assertEqual(
            response.context["type"],
            "file")
        self.assertEqual(
            response.context["current_folder"],
            UserFolder.objects.get(owner=self.user, name='home'))
        response = self.client.get(
            reverse('podfile:folder',  kwargs={'type': 'file', 'id': 2}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["current_folder"],
            UserFolder.objects.get(owner=self.user, name='Child'))
        response = self.client.get(
            reverse('podfile:folder',  kwargs={'type': 'image'}))
        self.assertEqual(response.status_code, 200)  # type image ok
        response = self.client.get(
            reverse('podfile:folder',  kwargs={'type': 'toto'}))
        # type nok SuspiciousOperation
        self.assertEqual(response.status_code, 400)

        print(" ---> test_list_folders : OK!")

    def test_edit_folders(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('podfile:folder', kwargs={'type': 'file'}), {
                'name': "NewFolder",
            }, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('podfile:folder',
                                           kwargs={'type': 'file'}))
        self.assertEqual(response.status_code, 200)  # user is staff
        self.assertTrue(
            UserFolder.objects.get(owner=self.user, name='NewFolder'))
        self.assertEqual(
            response.context["list_folder"].paginator.count,
            2)
        response = self.client.post(
            reverse('podfile:folder', kwargs={'type': 'file'}), {
                'name': "NewFolder2",
                'id_folder': UserFolder.objects.get(
                    owner=self.user, name='NewFolder').id
            }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            UserFolder.objects.get(owner=self.user, name='NewFolder2'))
        self.assertEqual(
            response.context["list_folder"].paginator.count,
            2)
        print(" ---> test_edit_folders : OK!")

    def test_delete_folders(self):
        self.client = Client()
        self.user = User.objects.get(username="pod2")
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('podfile:folder', kwargs={'type': 'file'}), {
                'action': "delete",
                'id': UserFolder.objects.get(owner=self.user, name='home').id
            }, follow=True)
        self.assertEqual(response.status_code, 403)  # forbidden name=home !

        response = self.client.post(
            reverse('podfile:folder', kwargs={'type': 'file'}), {
                'action': "delete",
                'id': UserFolder.objects.get(
                    owner=User.objects.get(username="pod"), name='Child').id
            }, follow=True)
        self.assertEqual(response.status_code, 403)  # forbidden name=home !

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('podfile:folder', kwargs={'type': 'file'}), {
                'action': "delete",
                'id': UserFolder.objects.get(
                    owner=self.user, name='Child').id
            }, follow=True)
        self.assertEqual(response.status_code, 200)

        print(" ---> test_delete_folders : OK!")


##
# FILES VIEWS
#
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
class FileViewTestCase(TestCase):

    def setUp(self):
        pod = User.objects.create(username='pod', password='azerty')
        home = UserFolder.objects.get(owner=pod, name='home')
        child = UserFolder.objects.create(owner=pod, name='Child')
        pod2 = User.objects.create(username='pod2', password='azerty')
        currentdir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        simplefile = SimpleUploadedFile(
            name='testfile.txt',
            content=open(
                os.path.join(
                    currentdir, 'tests', 'testfile.txt'), 'rb').read(),
            content_type='text/plain')
        simpleImage = SimpleUploadedFile(
            name='testimage.jpg',
            content=open(
                os.path.join(
                    currentdir, 'tests', 'testimage.jpg'), 'rb').read(),
            content_type='image/jpeg')
        CustomFileModel.objects.create(
            name='testfile',
            created_by=pod,
            folder=home,
            file=simplefile)
        CustomImageModel.objects.create(
            name='testimage',
            created_by=pod,
            folder=home,
            file=simpleImage)
        CustomFileModel.objects.create(
            name='testfile2',
            created_by=pod,
            folder=child,
            file=simplefile)
        CustomFileModel.objects.create(
            name='testfile2',
            created_by=pod2,
            folder=UserFolder.objects.get(owner=pod2, name='home'),
            file=simplefile)

    def test_list_files(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                'podfile:get_files',
                kwargs={'type': 'file',
                        'id': UserFolder.objects.get(
                            owner=self.user, name='home').id}))
        self.assertEqual(response.status_code, 302)  # user is not staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(
            reverse(
                'podfile:get_files',
                kwargs={'type': 'file',
                        'id': UserFolder.objects.get(
                            owner=self.user, name='home').id}))
        self.assertEqual(response.status_code, 200)  # user is staff
        self.assertEqual(
            response.context["list_file"].count(),
            1)
        self.assertEqual(
            response.context["current_folder"],
            UserFolder.objects.get(owner=self.user, name='home'))
        self.assertEqual(
            response.context["type"],
            "file")
        response = self.client.get(
            reverse(
                'podfile:get_files',
                kwargs={'type': 'file',
                        'id': UserFolder.objects.get(
                            owner=self.user, name='Child').id}))
        self.assertEqual(response.status_code, 200)  # user is staff
        self.assertEqual(
            response.context["list_file"].count(),
            1)
        self.assertEqual(
            response.context["current_folder"],
            UserFolder.objects.get(owner=self.user, name='Child'))
        self.assertEqual(
            response.context["type"],
            "file")
        response = self.client.get(
            reverse(
                'podfile:get_files',
                kwargs={'type': 'image',
                        'id': UserFolder.objects.get(
                            owner=self.user, name='home').id}))
        self.assertEqual(response.status_code, 200)  # user is staff
        self.assertEqual(
            response.context["list_file"].count(),
            1)
        self.assertEqual(
            response.context["current_folder"],
            UserFolder.objects.get(owner=self.user, name='home'))
        self.assertEqual(
            response.context["type"],
            "image")
        print(" ---> test_list_files : OK!")

    def test_edit_files(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        folder = UserFolder.objects.get(
            owner=self.user, name='home')
        # New file
        response = self.client.post(
            reverse('podfile:editfile', kwargs={'id': folder.id}), {
                'action': "new"
            }, follow=True)

        self.assertEqual(response.status_code, 400)  # not ajax
        response = self.client.post(
            reverse('podfile:editfile', kwargs={'id': folder.id}), {
                'action': "new"
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)  # ajax with post data
        self.assertEqual(
            response.context["folder"],
            folder)
        self.assertTrue(
            response.context["form_file"])
        # New image
        response = self.client.post(
            reverse('podfile:editimage', kwargs={'id': folder.id}), {
                'action': "new"
            }, follow=True)

        self.assertEqual(response.status_code, 400)  # not ajax
        response = self.client.post(
            reverse('podfile:editimage', kwargs={'id': folder.id}), {
                'action': "new"
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)  # ajax with post data
        self.assertEqual(
            response.context["folder"],
            folder)
        self.assertTrue(
            response.context["form_image"])

        # modify
        # modify file
        customfile = CustomFileModel.objects.get(
            name='testfile',
            created_by=self.user,
            folder=folder,
        )
        customimage = CustomImageModel.objects.get(
            name='testimage',
            created_by=self.user,
            folder=folder)
        response = self.client.post(
            reverse('podfile:editfile', kwargs={'id': folder.id}), {
                'action': "modify",
                'id': customfile.id
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)  # ajax with post data
        self.assertEqual(
            response.context["folder"],
            folder)
        self.assertTrue(
            response.context["form_file"])
        # modify image
        response = self.client.post(
            reverse('podfile:editimage', kwargs={'id': folder.id}), {
                'action': "modify",
                'id': customimage.id
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)  # ajax with post data
        self.assertEqual(
            response.context["folder"],
            folder)
        self.assertTrue(
            response.context["form_image"])

        # save file
        nbfile = folder.customfilemodel_set.all().count()
        textfile = SimpleUploadedFile(
            "textfile.txt", b"file_content", content_type='text/plain')
        response = self.client.post(
            reverse('podfile:editfile', kwargs={'id': folder.id}), {
                'action': "save",
                'file': textfile,
                'folder': folder.id,
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)  # ajax with post data
        result = json.loads(force_text(response.content))
        self.assertTrue(result['list_element'])
        self.assertEqual(folder.customfilemodel_set.all().count(), nbfile + 1)
        self.assertTrue(CustomFileModel.objects.get(
            name='textfile',
            created_by=self.user,
            folder=folder,
        ))
        textfile = SimpleUploadedFile(
            "textfile.txt", b"file_content", content_type='text/plain')
        response = self.client.post(
            reverse('podfile:editfile', kwargs={'id': folder.id}), {
                'action': "save",
                'file': textfile,
                'folder': 999,
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)  # ajax with post data
        result = json.loads(force_text(response.content))
        self.assertTrue(result['errors'])  # folder not exist
        self.assertEqual(folder.customfilemodel_set.all().count(), nbfile + 1)

        textfile = SimpleUploadedFile(
            "textfile.txt", b"file_content", content_type='text/plain')
        response = self.client.post(
            reverse('podfile:editfile', kwargs={'id': folder.id}), {
                'action': "save",
                'file': textfile,
                'folder': 2,
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)   # folder must be the same

        # save image

        nbimage = folder.customimagemodel_set.all().count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        imagefile = SimpleUploadedFile(
            "image.gif", small_gif, content_type='image/gif')
        response = self.client.post(
            reverse('podfile:editimage', kwargs={'id': folder.id}), {
                'action': "save",
                'file': imagefile,
                'folder': folder.id,
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)  # ajax with post data
        result = json.loads(force_text(response.content))
        self.assertTrue(result['list_element'])
        self.assertEqual(
            folder.customimagemodel_set.all().count(), nbimage + 1)
        self.assertTrue(CustomImageModel.objects.get(
            name='image',
            created_by=self.user,
            folder=folder,
        ))
        response = self.client.post(
            reverse('podfile:editimage', kwargs={'id': folder.id}), {
                'action': "save",
                'file': imagefile,
                'folder': 999,
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)  # ajax with post data
        result = json.loads(force_text(response.content))
        self.assertTrue(result['errors'])  # folder not exist
        self.assertEqual(folder.customfilemodel_set.all().count(), nbfile + 1)

        imagefile = SimpleUploadedFile(
            "image.gif", small_gif, content_type='image/gif')
        response = self.client.post(
            reverse('podfile:editimage', kwargs={'id': folder.id}), {
                'action': "save",
                'file': imagefile,
                'folder': 2,
            }, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)  # folder must be the same
        print(" ---> test_edit_files : OK!")
