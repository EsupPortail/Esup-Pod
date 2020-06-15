
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from pod.video.models import Type
from ..models import Recording, RecordingFile, Recorder, RecordingFileTreatment


class RecorderTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        videotype = Type.objects.create(title='others')
        user = User.objects.create(username="pod")
        Recorder.objects.create(id=1, user=user, name="recorder1",
                                address_ip="16.3.10.37",
                                type=videotype,
                                directory="dir1")

    def test_attributs(self):
        recorder1 = Recorder.objects.get(id=1)
        self.assertEqual(recorder1.name, "recorder1")
        self.assertEqual(recorder1.address_ip, "16.3.10.37")
        self.assertEqual(recorder1.directory, "dir1")

        print(
            "   --->  test_attributs of RecorderTestCase: OK !")

    def test_ipunder(self):
        recorder1 = Recorder.objects.get(id=1)
        self.assertEqual(recorder1.ipunder(), "16_3_10_37")
        print(
            "   --->  test_ipunder of RecorderTestCase: OK !")

    def test_delete_object(self):
        Recorder.objects.filter(name="recorder1").delete()
        self.assertEquals(Recorder.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of RecorderTestCase : OK !")


class RecordingTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        videotype = Type.objects.create(title='others')
        user = User.objects.create(username="pod")
        recorder1 = Recorder.objects.create(id=1, user=user, name="recorder1",
                                            address_ip="16.3.10.37",
                                            type=videotype,
                                            directory="dir1")
        source_file = "/home/pod/files/video.mp4"
        type = "video"
        recording = Recording.objects.create(user=user, title="media1",
                                             type=type,
                                             source_file=source_file,
                                             recorder=recorder1)
        recording.save()

        print(" --->  SetUp of RecordingTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
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
        print(
            "   --->  test_attributs of RecordingTestCase : OK !")

    # Testing the two if cases of verify_attibuts method
    def test_verifying_attributs_fst_cases(self):
        recording = Recording.objects.get(id=1)
        recording.type = ""
        recording.source_file = ""
        recording.save()
        self.assertEqual(2, len(recording.verify_attributs()))
        print(
            "   --->  test_verifying_attributs_fst_cases \
            of RecordingTestCase : OK !")

    # Testing the two elif cases of verify_attibuts method
    def test_verifying_attributs_snd_cases(self):
        recording = Recording.objects.get(id=1)
        recording.type = "something"
        recording.source_file = "/home/pod/files/somefile.mp4"
        recording.save()
        self.assertEqual(2, len(recording.verify_attributs()))
        print(
            "   --->  test_verifying_attributs_snd_cases \
            of RecordingTestCase : OK !")

    def test_clean_raise_exception(self):
        recording = Recording.objects.get(id=1)
        recording.type = "something"
        recording.save()
        self.assertRaises(ValidationError, recording.clean)
        print(
            "   --->  test_clean_raise_exception of RecordingTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Recording.objects.filter(title="media1").delete()
        self.assertEquals(Recording.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of RecordingTestCase : OK !")


class RecordingFileTreatmentTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        videotype = Type.objects.create(title='others')
        user1 = User.objects.create(username="pod")
        recorder1 = Recorder.objects.create(id=1, user=user1, name="recorder1",
                                            address_ip="16.3.10.37",
                                            type=videotype, directory="dir1")
        recording_file = RecordingFileTreatment.objects.create(
            type='video',
            file="/home/pod/files/somefile.mp4",
            recorder=recorder1)
        recording_file.save()
        print(" --->  SetUp of RecordingFileTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
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
        print(
            "   --->  test_attributs of RecordingFileTreatmentTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        filepath = "/home/pod/files/somefile.mp4"
        RecordingFileTreatment.objects.filter(file=filepath).delete()
        self.assertEquals(RecordingFileTreatment.objects.all().count(), 0)

        print(
            "--->  test_delete_object of RecordingFileTreatmentTestCase : OK "
            "!")


class RecordingFileTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        videotype = Type.objects.create(title='others')
        user1 = User.objects.create(username="pod")
        recorder1 = Recorder.objects.create(id=1, user=user1, name="recorder1",
                                            address_ip="16.3.10.37",
                                            type=videotype, directory="dir1")
        recording_file = RecordingFile.objects.create(recorder=recorder1)
        recording_file.file = "/home/pod/files/somefile.mp4"
        recording_file.save()
        print(" --->  SetUp of RecordingFileTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
        recording_file = RecordingFile.objects.get(id=1)
        self.assertEqual(recording_file.file, "/home/pod/files/somefile.mp4")
        print(
            "   --->  test_attributs of RecordingFileTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        filepath = "/home/pod/files/somefile.mp4"
        RecordingFile.objects.filter(file=filepath).delete()
        self.assertEquals(RecordingFile.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of RecordingFileTestCase : OK !")
