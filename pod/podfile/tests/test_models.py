"""Unit tests for podfile models."""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import CustomFileModel
from ..models import CustomImageModel
from ..models import UserFolder
from datetime import datetime

import os


class CustomFileModelTestCase(TestCase):
    """Test case for Pod CustomFile model."""

    def setUp(self) -> None:
        """Init some values before CustomFileModel tests."""
        test = User.objects.create(username="test")
        currentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        simplefile = SimpleUploadedFile(
            name="testfile.txt",
            content=open(os.path.join(currentdir, "tests", "testfile.txt"), "rb").read(),
            content_type="text/plain",
        )
        home = UserFolder.objects.get(name="home", owner=test)
        CustomFileModel.objects.create(
            name="testfile",
            description="testfile",
            uploaded_at=datetime.now(),
            created_by=test,
            folder=home,
            file=simplefile,
        )
        CustomFileModel.objects.create(
            name="testfile2",
            description="",
            uploaded_at=datetime.now(),
            created_by=test,
            folder=home,
            file=simplefile,
        )

    def test_attributs_full(self) -> None:
        user = User.objects.get(id=1)
        file = CustomFileModel.objects.get(id=1)
        self.assertEqual(file.name, "testfile")
        self.assertEqual(file.description, "testfile")
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, "text/plain")
        self.assertEqual(file.file_ext, "txt")
        self.assertTrue(isinstance(file.uploaded_at, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.folder.name, "home")
        if user.owner:
            self.assertTrue(user.owner.hashkey in file.file.path)
        else:
            self.assertTrue(user.username in file.file.path)

        print(" ---> test_attributs_full: OK! --- CustomFileModel")

    def test_attributs(self) -> None:
        user = User.objects.get(id=1)
        file = CustomFileModel.objects.get(id=2)
        self.assertTrue(file.name, "testfile")
        self.assertEqual(file.description, "")
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, "text/plain")
        self.assertEqual(file.file_ext, "txt")
        self.assertTrue(isinstance(file.uploaded_at, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.folder.name, "home")
        if user.owner:
            self.assertTrue(user.owner.hashkey in file.file.path)
        else:
            self.assertTrue(user.username in file.file.path)

        print(" [ BEGIN FILEPICKER_TEST_MODELS ] ")
        print(" ---> test_attributs: OK! --- CustomFileModel")

    def test_delete(self) -> None:
        CustomFileModel.objects.get(id=1).delete()
        CustomFileModel.objects.get(id=2).delete()
        self.assertFalse(CustomFileModel.objects.all())

        print(" ---> test_delete: OK! --- CustomFileModel")


class CustomImageModelTestCase(TestCase):
    def setUp(self) -> None:
        """Init some values before CustomImageModel tests."""
        test = User.objects.create(username="test")
        currentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        simplefile = SimpleUploadedFile(
            name="testimage.jpg",
            content=open(os.path.join(currentdir, "tests", "testimage.jpg"), "rb").read(),
            content_type="image/jpeg",
        )
        home = UserFolder.objects.get(name="home", owner=test)
        CustomImageModel.objects.create(
            name="testimage",
            description="testimage",
            uploaded_at=datetime.now(),
            created_by=test,
            folder=home,
            file=simplefile,
        )
        CustomImageModel.objects.create(
            name="testimage2",
            description="",
            uploaded_at=datetime.now(),
            created_by=test,
            folder=home,
            file=simplefile,
        )

    def test_attributs_full(self) -> None:
        user = User.objects.get(id=1)
        file = CustomImageModel.objects.get(id=1)
        self.assertEqual(file.name, "testimage")
        self.assertEqual(file.description, "testimage")
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, "image/jpeg")
        self.assertTrue(isinstance(file.uploaded_at, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.folder.name, "home")
        if user.owner:
            self.assertTrue(user.owner.hashkey in file.file.path)
        else:
            self.assertTrue(user.username in file.file.path)

        print(" ---> test_attributs_full: OK! --- CustomImageModel")

    def test_attributs(self) -> None:
        user = User.objects.get(id=1)
        file = CustomImageModel.objects.get(id=2)
        self.assertTrue(file.name, "testimage")
        self.assertEqual(file.description, "")
        self.assertEqual(file.file_size, file.file.size)
        self.assertEqual(file.file_type, "image/jpeg")
        self.assertTrue(isinstance(file.uploaded_at, datetime))
        self.assertEqual(file.created_by, user)
        self.assertEqual(file.folder.name, "home")
        if user.owner:
            self.assertTrue(user.owner.hashkey in file.file.path)
        else:
            self.assertTrue(user.username in file.file.path)

        print(" ---> test_attributs: OK! --- CustomImageModel")

    def test_delete(self) -> None:
        CustomImageModel.objects.get(id=1).delete()
        CustomImageModel.objects.get(id=2).delete()
        self.assertFalse(CustomImageModel.objects.all())

        print(" ---> test_delete: OK! --- CustomImageModel")


class UserFolderTestCase(TestCase):
    """Test case for UserFolder."""

    def setUp(self) -> None:
        """Create UserFolders to be tested."""
        test = User.objects.create(username="test")
        UserFolder.objects.get(name="home", owner=test)
        UserFolder.objects.create(name="Images", owner=test)
        UserFolder.objects.create(name="Documents", owner=test)

    def test_attributs_full(self) -> None:
        """Test UserFolder attributes."""
        user = User.objects.get(id=1)
        child = UserFolder.objects.get(id=2)
        self.assertEqual(child.name, "Images")
        self.assertEqual(child.owner, user)

        print(" ---> test_attributs_full: OK! --- UserFolder")

    def test_attributs(self) -> None:
        """Test UserFolder attributes."""
        user = User.objects.get(id=1)
        home = UserFolder.objects.get(id=1)
        self.assertEqual(home.name, "home")
        self.assertEqual(home.owner, user)

        print(" ---> test_attributs: OK! --- UserFolder")

    def test_delete(self) -> None:
        """Test UserFolder deletion."""
        UserFolder.objects.get(id=1).delete()
        UserFolder.objects.get(id=2).delete()
        UserFolder.objects.get(id=3).delete()
        self.assertFalse(UserFolder.objects.all())

        print(" ---> test_delete: OK! --- UserFolder")
