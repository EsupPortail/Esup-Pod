"""Unit tests for podfile views."""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.encoding import force_str
from django.urls import reverse
from django.test import Client

from ..models import CustomFileModel
from ..models import CustomImageModel
from ..models import UserFolder
from django.contrib.sites.models import Site
from datetime import datetime

import json
import os
import ast


class FolderViewTestCase(TestCase):
    """FOLDER VIEWS test case."""

    def setUp(self) -> None:
        """Init some values before FolderView tests."""
        user = User.objects.create(username="pod", password="azerty")
        UserFolder.objects.get(owner=user, name="home")
        child = UserFolder.objects.create(owner=user, name="Child")
        user2 = User.objects.create(username="pod2", password="azerty")

        # We add a simplefile in child folder so it is not empty
        currentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        simplefile = SimpleUploadedFile(
            name="testfile.txt",
            content=open(os.path.join(currentdir, "tests", "testfile.txt"), "rb").read(),
            content_type="text/plain",
        )
        CustomFileModel.objects.create(
            name="testfile",
            description="testfile",
            uploaded_at=datetime.now(),
            created_by=user,
            folder=child,
            file=simplefile,
        )

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()

    def test_list_folders(self) -> None:
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/podfile/ajax_calls/user_folders/")
        self.assertEqual(response.status_code, 302)  # user is not staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get("/podfile/ajax_calls/user_folders/")
        self.assertEqual(response.status_code, 200)  # user is staff

        response_content = response.content.decode("UTF-8")
        response_content = ast.literal_eval(response_content)
        self.assertEqual(
            response_content,
            {
                "current_page": 1,
                "next_page": -1,
                "total_pages": 1,
                "folders": [{"name": "Child", "id": 2}],
                "search": "",
            },
        )

        response = self.client.get(reverse("podfile:home", kwargs={"type": "file"}))
        self.assertEqual(
            response.context["user_home_folder"],
            UserFolder.objects.get(owner=self.user, name="home"),
        )
        self.assertEqual(response.context["type"], "file")
        self.assertEqual(
            response.context["current_session_folder"],
            UserFolder.objects.get(owner=self.user, name="home"),
        )
        response = self.client.get(reverse("podfile:home", kwargs={"type": "image"}))
        self.assertEqual(response.status_code, 200)  # type image ok

        response = self.client.get(reverse("podfile:home", kwargs={"type": "toto"}))
        # type nok SuspiciousOperation
        self.assertEqual(response.status_code, 400)

        print(" ---> test_list_folders: OK!")

    def test_edit_folders(self) -> None:
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("podfile:editfolder"),
            {
                "name": "NewFolder",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserFolder.objects.get(owner=self.user, name="NewFolder"))
        self.assertEqual(response.context["user_folder"].count(), 2)
        response = self.client.post(
            reverse("podfile:editfolder"),
            {
                "name": "NewFolder2",
                "folderid": UserFolder.objects.get(owner=self.user, name="NewFolder").id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserFolder.objects.get(owner=self.user, name="NewFolder2"))
        self.assertEqual(response.context["user_folder"].count(), 2)
        print(" ---> test_edit_folders: OK!")

    def test_delete_folders(self) -> None:
        self.client = Client()
        self.user = User.objects.get(username="pod2")
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("podfile:deletefolder"),
            {"id": UserFolder.objects.get(owner=self.user, name="home").id},
            follow=True,
        )
        self.assertEqual(response.status_code, 403)  # forbidden name=home!

        response = self.client.post(
            reverse("podfile:deletefolder"),
            {
                "id": UserFolder.objects.get(
                    owner=User.objects.get(username="pod"), name="Child"
                ).id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 403)  # forbidden name=home!

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("podfile:deletefolder"),
            {"id": UserFolder.objects.get(owner=self.user, name="Child").id},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        print(" ---> test_delete_folders: OK!")


class FileViewTestCase(TestCase):
    """File view test case."""

    def setUp(self) -> None:
        pod = User.objects.create(username="pod", password="azerty")
        home = UserFolder.objects.get(owner=pod, name="home")
        child = UserFolder.objects.create(owner=pod, name="Child")
        pod2 = User.objects.create(username="pod2", password="azerty")

        pod.owner.sites.add(Site.objects.get_current())
        pod.owner.save()

        pod2.owner.sites.add(Site.objects.get_current())
        pod2.owner.save()

        currentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        simplefile = SimpleUploadedFile(
            name="testfile.txt",
            content=open(os.path.join(currentdir, "tests", "testfile.txt"), "rb").read(),
            content_type="text/plain",
        )
        simpleImage = SimpleUploadedFile(
            name="testimage.jpg",
            content=open(os.path.join(currentdir, "tests", "testimage.jpg"), "rb").read(),
            content_type="image/jpeg",
        )
        CustomFileModel.objects.create(
            name="testfile", created_by=pod, folder=home, file=simplefile
        )
        CustomImageModel.objects.create(
            name="testimage", created_by=pod, folder=home, file=simpleImage
        )
        CustomFileModel.objects.create(
            name="testfile2", created_by=pod, folder=child, file=simplefile
        )
        CustomFileModel.objects.create(
            name="testfile2",
            created_by=pod2,
            folder=UserFolder.objects.get(owner=pod2, name="home"),
            file=simplefile,
        )

    def test_list_files(self) -> None:
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "podfile:get_folder_files",
                kwargs={"id": UserFolder.objects.get(owner=self.user, name="home").id},
            )
        )
        self.assertEqual(response.status_code, 302)  # user is not staff
        self.user.is_staff = True
        self.user.save()

        response = self.client.get(
            reverse(
                "podfile:get_folder_files",
                kwargs={"id": UserFolder.objects.get(owner=self.user, name="home").id},
            )
        )
        self.assertEqual(response.status_code, 200)  # user is staff

        self.assertEqual(
            response.context["folder"],
            UserFolder.objects.get(owner=self.user, name="home"),
        )

        response = self.client.get(
            reverse(
                "podfile:get_folder_files",
                kwargs={"id": UserFolder.objects.get(owner=self.user, name="Child").id},
            )
        )
        self.assertEqual(response.status_code, 200)  # user is staff
        self.assertEqual(
            response.context["folder"],
            UserFolder.objects.get(owner=self.user, name="Child"),
        )

        print(" ---> test_list_files: OK!")

    def test_edit_files(self) -> None:
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        folder = UserFolder.objects.get(owner=self.user, name="home")

        # save file
        nbfile = folder.customfilemodel_set.all().count()
        textfile = SimpleUploadedFile(
            "textfile.txt", b"file_content", content_type="text/plain"
        )

        response = self.client.post(
            reverse("podfile:uploadfiles"),
            {
                "ufile": textfile,
                "folderid": folder.id,
            },
            follow=True,
            headers={"x-requested-with": "XMLHttpRequest"},
        )

        self.assertEqual(response.status_code, 200)  # ajax with post data

        result = json.loads(force_str(response.content))

        self.assertTrue(result["list_element"])
        self.assertEqual(folder.customfilemodel_set.all().count(), nbfile + 1)

        self.assertTrue(
            CustomFileModel.objects.get(
                name="textfile",
                created_by=self.user,
                folder=folder,
            )
        )

        textfile = SimpleUploadedFile(
            "textfile.txt", b"file_content", content_type="text/plain"
        )
        response = self.client.post(
            reverse("podfile:uploadfiles"),
            {
                "file": textfile,
                "folderid": 999,
            },
            follow=True,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 404)  # folder not exist
