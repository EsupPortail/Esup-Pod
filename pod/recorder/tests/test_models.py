"""Unit tests for Pod recorder."""

from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils import timezone
from pod.video.models import Type
from ..models import Recording, RecordingFile, Recorder, RecordingFileTreatment


class RecorderTestCase(TestCase):
    """Test case for Pod Recorder."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create models to be tested."""
        other_type = Type.objects.create(title="others")
        user = User.objects.create(username="pod")
        user1 = User.objects.create(username="pod1")
        user2 = User.objects.create(username="pod2")
        group = Group.objects.create(name="Test group")
        recorder1 = Recorder.objects.create(
            id=1,
            user=user,
            name="recorder1",
            address_ip="16.3.10.37",
            type=other_type,
            cursus="0",
            is_draft=False,
            is_restricted=True,
            password="secret",
            directory="dir1",
            salt="pepper",
            credentials_login="simplelogin",
            credentials_password="randompassword",
        )
        recorder1.additional_users.add(user1)
        recorder1.additional_users.add(user2)
        recorder1.restrict_access_to_groups.add(group)

    def test_attributes(self):
        """Test model attributes."""
        recorder1 = Recorder.objects.get(id=1)
        self.assertEqual(recorder1.name, "recorder1")
        self.assertEqual(recorder1.address_ip, "16.3.10.37")
        self.assertEqual(recorder1.directory, "dir1")
        self.assertEqual(recorder1.is_draft, False)
        self.assertEqual(recorder1.is_restricted, True)
        self.assertEqual(recorder1.password, "secret")
        self.assertEqual(recorder1.additional_users.count(), 2)
        self.assertEqual(recorder1.restrict_access_to_groups.count(), 1)
        self.assertEqual(recorder1.salt, "pepper")
        self.assertEqual(recorder1.credentials_login, "simplelogin")
        self.assertEqual(recorder1.credentials_password, "randompassword")
        print("   --->  test_attributes of RecorderTestCase: OK!")

    def test_clean_method(self):
        """Test method clean()."""
        # credential are not defined: clean is fine
        recorder1 = Recorder.objects.get(id=1)
        recorder1.credentials_login = ""
        recorder1.credentials_password = ""
        recorder1.clean()
        print("   --->  test_clean_raise_exception of RecorderTestCase: OK!")

        #  credentials_login needed if credentials_password set
        recorder1 = Recorder.objects.get(id=1)
        recorder1.credentials_login = ""
        self.assertRaises(ValidationError, recorder1.clean)
        print("   --->  test_clean_raise_exception of RecorderTestCase: OK!")

        #  credentials_password needed if credentials_login set
        recorder1 = Recorder.objects.get(id=1)
        recorder1.credentials_password = ""
        self.assertRaises(ValidationError, recorder1.clean)
        print("   --->  test_clean_raise_exception of RecorderTestCase: OK!")

        # check exception content
        recorder1 = Recorder.objects.get(id=1)
        recorder1.salt = ""
        recorder1.credentials_login = ""
        with self.assertRaises(Exception) as context:
            recorder1.clean()
        self.assertTrue("credentials_password" in str(context.exception))
        self.assertTrue("credentials_login" in str(context.exception))
        self.assertTrue("salt" in str(context.exception))

    def test_ip_under(self):
        """Test method ipunder()."""
        recorder1 = Recorder.objects.get(id=1)
        self.assertEqual(recorder1.ipunder(), "16_3_10_37")
        print("   --->  test_ip_under of RecorderTestCase: OK!")

    def test_delete_object(self):
        """Test model delete."""
        Recorder.objects.filter(name="recorder1").delete()
        self.assertEqual(Recorder.objects.all().count(), 0)
        print("   --->  test_delete_object of RecorderTestCase: OK!")


class RecordingTestCase(TestCase):
    """Test case for Pod Recording."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create models to be tested."""
        other_type = Type.objects.create(title="others")
        user = User.objects.create(username="pod")
        recorder1 = Recorder.objects.create(
            id=1,
            user=user,
            name="recorder1",
            address_ip="16.3.10.37",
            type=other_type,
            cursus="0",
            directory="dir1",
        )
        source_file = "/home/pod/files/video.mp4"
        video_type = "video"
        recording = Recording.objects.create(
            user=user,
            title="media1",
            type=video_type,
            source_file=source_file,
            recorder=recorder1,
        )
        recording.save()

        print(" --->  SetUp of RecordingTestCase: OK!")

    def test_attributes(self):
        """Test model attributes."""
        recording = Recording.objects.get(id=1)
        recorder = Recorder.objects.get(id=1)
        self.assertEqual(recording.title, "media1")
        self.assertEqual(recording.type, "video")
        self.assertEqual(recording.source_file, "/home/pod/files/video.mp4")
        self.assertEqual(recording.recorder, recorder)
        date = timezone.now()
        self.assertEqual(recording.date_added.year, date.year)
        self.assertEqual(recording.date_added.month, date.month)
        self.assertEqual(recording.date_added.day, date.day)
        print("   --->  test_attributes of RecordingTestCase: OK!")

    # Testing the two if cases of verify_attibuts method
    def test_verifying_attributs_fst_cases(self):
        """Test method verifying_attributs()."""
        recording = Recording.objects.get(id=1)
        recording.type = ""
        recording.source_file = ""
        recording.save()
        self.assertEqual(2, len(recording.verify_attributs()))
        print(
            "   --->  test_verifying_attributs_fst_cases \
            of RecordingTestCase: OK!"
        )

    # Testing the two elif cases of verify_attibuts method
    def test_verifying_attributs_snd_cases(self):
        """Test method verifying_attributs()."""
        recording = Recording.objects.get(id=1)
        recording.type = "something"
        recording.source_file = "/home/pod/files/somefile.mp4"
        recording.save()
        self.assertEqual(2, len(recording.verify_attributs()))
        print(
            "   --->  test_verifying_attributs_snd_cases \
            of RecordingTestCase: OK!"
        )

    def test_clean_raise_exception(self):
        """Test method clean()."""
        recording = Recording.objects.get(id=1)
        recording.type = "something"
        recording.save()
        self.assertRaises(ValidationError, recording.clean)
        print("   --->  test_clean_raise_exception of RecordingTestCase: OK!")

    def test_delete_object(self):
        """Test method delete()."""
        Recording.objects.filter(title="media1").delete()
        self.assertEqual(Recording.objects.all().count(), 0)

        print("   --->  test_delete_object of RecordingTestCase: OK!")


class RecordingFileTreatmentTestCase(TestCase):
    """Test case for Pod RecordingFileTreatment."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create models to be tested."""
        other_type = Type.objects.create(title="others")
        user1 = User.objects.create(username="pod")
        recorder1 = Recorder.objects.create(
            id=1,
            user=user1,
            name="recorder1",
            address_ip="16.3.10.37",
            cursus="0",
            type=other_type,
            directory="dir1",
        )
        recording_file = RecordingFileTreatment.objects.create(
            type="video",
            file="/home/pod/files/somefile.mp4",
            recorder=recorder1,
        )
        recording_file.save()
        print(" --->  SetUp of RecordingFileTestCase: OK!")

    def test_attributes(self):
        """Test model attributes."""
        recording_file = RecordingFileTreatment.objects.get(id=1)
        recorder = Recorder.objects.get(id=1)
        self.assertEqual(recording_file.type, "video")
        self.assertEqual(recording_file.file, "/home/pod/files/somefile.mp4")
        self.assertEqual(recording_file.filename(), "somefile.mp4")
        self.assertEqual(recording_file.recorder, recorder)
        date = timezone.now()
        self.assertEqual(recording_file.date_added.year, date.year)
        self.assertEqual(recording_file.date_added.month, date.month)
        self.assertEqual(recording_file.date_added.day, date.day)
        print("   --->  test_attributes of RecordingFileTreatmentTestCase: OK!")

    def test_delete_object(self):
        """Test method delete()."""
        filepath = "/home/pod/files/somefile.mp4"
        RecordingFileTreatment.objects.filter(file=filepath).delete()
        self.assertEqual(RecordingFileTreatment.objects.all().count(), 0)

        print("--->  test_delete_object of RecordingFileTreatmentTestCase: OK!")


class RecordingFileTestCase(TestCase):
    """Test case for Pod RecordingFile."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create models to be tested."""
        other_type = Type.objects.create(title="others")
        user1 = User.objects.create(username="pod")
        recorder1 = Recorder.objects.create(
            id=1,
            user=user1,
            name="recorder1",
            address_ip="16.3.10.37",
            cursus="0",
            type=other_type,
            directory="dir1",
        )
        recording_file = RecordingFile.objects.create(recorder=recorder1)
        recording_file.file = "/home/pod/files/somefile.mp4"
        recording_file.save()
        print(" --->  SetUp of RecordingFileTestCase: OK!")

    def test_attributes(self):
        """Test model attributes."""
        recording_file = RecordingFile.objects.get(id=1)
        self.assertEqual(recording_file.file, "/home/pod/files/somefile.mp4")
        print("   --->  test_attributs of RecordingFileTestCase: OK!")

    def test_delete_object(self):
        """Test method delete()."""
        filepath = "/home/pod/files/somefile.mp4"
        RecordingFile.objects.filter(file=filepath).delete()
        self.assertEqual(RecordingFile.objects.all().count(), 0)

        print("   --->  test_delete_object of RecordingFileTestCase: OK!")
