"""Test the Obsolete videos."""

import tempfile

from django.test import override_settings
from django.conf import settings
from django.utils.translation import gettext as _

from ..models import Video, Type, VideoToDelete
from pod.authentication.models import Owner

from datetime import date, timedelta
import os
from django.contrib.sites.models import Site

from ..utils import check_csv_header, read_archived_csv, archive_pack
from ..views import valid_form_respit

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.test import TestCase

from unittest.mock import patch

DEFAULT_YEAR_DATE_DELETE = getattr(settings, "DEFAULT_YEAR_DATE_DELETE", 2)
ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")


class ObsolescenceTestCase(TestCase):
    """Test the Obsolete videos."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Set up."""
        site = Site.objects.get(id=1)
        user = User.objects.create(
            username="pod", password="pod1234pod", email="pod@univ.fr"
        )

        user_faculty = User.objects.create(
            username="pod_faculty", password="pod1234pod", email="pod@univ.fr"
        )

        owner, owner_created = Owner.objects.get_or_create(user=user_faculty)
        owner.auth_type = "CAS"
        owner.affiliation = "faculty"
        owner.save()

        user_faculty = User.objects.get(username="pod_faculty")

        user1 = User.objects.create(
            username="pod1", password="pod1234pod", email="pod@univ.fr"
        )
        user2 = User.objects.create(
            username="pod2", password="pod1234pod", email="pod@univ.fr"
        )
        user3 = User.objects.create(
            username="pod3", password="pod1234pod", email="pod@univ.fr"
        )
        user4 = User.objects.create(
            username="pod4", password="pod1234pod", email="pod@univ.fr"
        )

        Video.objects.create(
            title="Video_default",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )

        Video.objects.create(
            title="Video_faculty_with_accomodation_year",
            owner=user_faculty,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )

        # pour les 3 vidéos suivantes, la date n'est pas changée à la création
        # car l'affiliation du prop n'est pas dans ACCOMMODATION_YEARS
        Video.objects.create(
            title="Video1_60",
            owner=user1,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        Video.objects.create(
            title="Video2_30",
            owner=user2,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        Video.objects.create(
            title="Video3_7",
            owner=user3,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )

        video60 = Video.objects.get(pk=3)
        video60.date_delete = date.today() + timedelta(days=60)
        video60.save()

        video30 = Video.objects.get(pk=4)
        video30.date_delete = date.today() + timedelta(days=30)
        video30.save()

        video7 = Video.objects.get(pk=5)
        video7.date_delete = date.today() + timedelta(days=7)
        video7.save()

        # On modifie la date après la création pour etre sur qu'elle soit bonne
        vid1 = Video.objects.create(
            title="Video_to_archive",
            owner=user_faculty,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        vid1.date_delete = date.today() - timedelta(days=1)
        vid1.is_draft = False
        vid1.save()

        vid2 = Video.objects.create(
            title="Video_to_delete",
            owner=user4,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        vid2.date_delete = date.today() - timedelta(days=1)
        vid2.save()

        for vid in Video.objects.all():
            vid.sites.add(site)

        print(" --->  SetUp of ObsolescenceTestCase: OK!")

    def test_check_video_date_delete(self) -> None:
        """Check that the videos deletion date complies with the settings."""
        video = Video.objects.get(id=1)
        date1 = date.today() + timedelta(days=DEFAULT_YEAR_DATE_DELETE * 365)
        self.assertEqual(video.date_delete, date1)

        video2 = Video.objects.get(id=2)
        date2 = date.today() + timedelta(
            days=settings.ACCOMMODATION_YEARS[video2.owner.owner.affiliation] * 365
        )
        self.assertEqual(video2.date_delete, date2)

        print("--->  check_video_date_delete of ObsolescenceTestCase: OK")

    def test_notify_user_obsolete_video(self):
        """Check user notification of obsolete video."""
        from pod.video.management.commands import check_obsolete_videos

        cmd = check_obsolete_videos.Command()
        # kwargs for your command -- lets you override stuff for testing...
        # opts = {}
        video60 = Video.objects.get(id=3)
        mail = cmd.notify_user(video60, 60)
        self.assertEqual(mail, 1)
        print("--->  test_notify_user_obsolete_video of \
            ObsolescenceTestCase: OK")

    def test_obsolete_video(self):
        """Check that videos with deletion date in 7,30 and 60 days will be notified."""
        from pod.video.management.commands import check_obsolete_videos

        cmd = check_obsolete_videos.Command()
        # kwargs for your command -- lets you override stuff for testing...
        # opts = {}
        list_video = cmd.get_video_treatment_and_notify_user()
        video60 = Video.objects.get(id=3)
        self.assertEqual(video60.title, "Video1_60")
        video30 = Video.objects.get(id=4)
        self.assertEqual(video30.title, "Video2_30")
        video7 = Video.objects.get(id=5)
        self.assertEqual(video7.title, "Video3_7")

        self.assertTrue(video60 in list_video["other"]["60"])
        self.assertTrue(video30 in list_video["other"]["30"])
        self.assertTrue(video7 in list_video["other"]["7"])
        print("--->  test_obsolete_video of ObsolescenceTestCase: OK")

    def test_delete_obsolete_video(self):
        """Check that obsolete videos are deleted."""
        from pod.video.management.commands import check_obsolete_videos

        cmd = check_obsolete_videos.Command()
        # kwargs for your command -- lets you override stuff for testing...
        # opts = {}
        video_to_archive = Video.objects.get(id=6)
        self.assertEqual(video_to_archive.title, "Video_to_archive")

        video_to_delete = Video.objects.get(id=7)
        self.assertEqual(video_to_delete.title, "Video_to_delete")
        title2 = "%s - %s" % (video_to_delete.id, video_to_delete.title)

        (
            list_video_to_delete,
            list_video_to_archive,
        ) = cmd.get_video_archived_deleted_treatment()

        self.assertTrue(title2 in list_video_to_delete["other"]["0"])
        self.assertTrue(video_to_archive in list_video_to_archive["other"]["0"])

        # Check that the archived video has been really archived
        video_to_archive = Video.objects.get(id=6)
        archive_user, created = User.objects.get_or_create(
            username=ARCHIVE_OWNER_USERNAME,
        )
        self.assertTrue(_("Archived") in video_to_archive.title)
        self.assertTrue(video_to_archive.is_draft)
        self.assertTrue(video_to_archive.owner == archive_user)

        vid_delete = VideoToDelete.objects.get(date_deletion=video_to_archive.date_delete)
        self.assertTrue(video_to_archive in vid_delete.video.all())

        # Check that the deleted video has been permanently deleted
        self.assertEqual(Video.objects.filter(id=7).count(), 0)

        # Check that csv file has been created
        file1 = "%s/%s.csv" % (settings.LOG_DIRECTORY, "deleted")
        self.assertTrue(os.path.isfile(file1))
        file2 = "%s/%s.csv" % (settings.LOG_DIRECTORY, "archived")
        self.assertTrue(os.path.isfile(file2))

        fd = open(file1, "r")
        n = 0
        while fd.readline():
            n += 1
        fd.close()
        self.assertEqual(n, 2)

        fd = open(file2, "r")
        n = 0
        while fd.readline():
            n += 1
        fd.close()
        self.assertEqual(n, 2)

        print("--->  test_delete_obsolete_video of ObsolescenceTestCase: OK")

    def tearDown(self):
        """Cleanup all created stuffs."""
        try:
            os.remove("%s/%s.csv" % (settings.LOG_DIRECTORY, "deleted"))
            os.remove("%s/%s.csv" % (settings.LOG_DIRECTORY, "archived"))
        except FileNotFoundError:
            pass


class ValidFormRespitTestCase(TestCase):

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.user.owner.affiliation = "faculty"
        self.user.owner.save()

        self.video1 = Video.objects.create(
            title="Video_to_delete",
            owner=self.user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )

    def test_archive_action(self):
        """Test archive option in the form"""
        # Connect the user
        self.client.force_login(self.user)

        # Simulates the submission of the form with archive action
        response = self.client.post(
            f"/video/valid/form/respit/{self.video1.slug}/", {"action": "Archive"}
        )
        # Check that HTTP code is 200
        self.assertEqual(response.status_code, 200)

        print("--->  test_archive_action of ValidFormRespitTestCase: OK")

    @override_settings(POD_ARCHIVE_AFFILIATION=["faculty"])
    def test_archive_option_hidden_if_user_not_authorized(self):
        """Test archive option is hidden when user affiliation is not allowed."""
        self.video1.date_delete = date.today() + timedelta(days=50)
        self.video1.save()

        self.user.owner.affiliation = "student"
        self.user.owner.save()
        self.client.force_login(self.user)

        response = self.client.get(f"/video/respit/{self.video1.slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'value="Archive"')

    @override_settings(POD_ARCHIVE_AFFILIATION=["faculty"])
    def test_archive_action_forbidden_if_user_not_authorized(self):
        """Test archive action returns bad request when user is not allowed."""
        self.user.owner.affiliation = "student"
        self.user.owner.save()
        self.client.force_login(self.user)

        response = self.client.post(
            f"/video/valid/form/respit/{self.video1.slug}/", {"action": "Archive"}
        )

        self.assertEqual(response.status_code, 400)

    @override_settings(PROLONGATION_GRANTED=True)
    def test_extend_action(self):
        """Test extend option in the form"""
        # Connect the user
        self.client.force_login(self.user)

        # Simulates the submission of the form with extend action
        response = self.client.post(
            f"/video/respit/{self.video1.slug}/", {"action": "Extend"}
        )
        # Check that HTTP code is 200
        self.assertEqual(response.status_code, 200)

        print("--->  test_extend_action of ValidFormRespitTestCase: OK")

    def test_delete_action(self):
        """Test delete option in the form"""
        # Simulates the submission of the form with archive delete
        request = self.factory.post(
            f"/video/respit/{self.video1.slug}/", {"action": "Delete"}
        )
        request.user = self.user
        response = valid_form_respit(request, self.video1.slug)
        # Check that HTTP code is 301
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.get("Location"), f"/video/delete/{self.video1.slug}")

        print("--->  test_delete_action of ValidFormRespitTestCase: OK")

    @patch("pod.video.views.ENABLE_PAGE_OBSO_MAIL", True)
    def test_go_prolong_action(self):
        """Test extend confirmation by the form"""
        self.video1.date_delete = date.today() + timedelta(days=50)
        self.video1.save()

        # Connect the user
        self.client.force_login(self.user)

        response = self.client.post(f"/video/go/prolong/{self.video1.slug}/")
        # Check that HTTP code is 301
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response.get("Location"), f"/video/well/prolonged/or/not/{self.video1.slug}"
        )

        print("--->  test_go_prolong_action of ValidFormRespitTestCase: OK")

    @patch("pod.video.views.ENABLE_PAGE_OBSO_MAIL", True)
    def test_go_archive_action(self):
        """Test archive confirmation by the form"""
        self.video1.date_delete = date.today() + timedelta(days=50)
        self.video1.save()

        # Connect the user
        self.client.force_login(self.user)

        response = self.client.post(f"/video/go/archive/{self.video1.slug}/")
        # Check that HTTP code is 301
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response.get("Location"), f"/video/well/archived/or/not/{self.video1.slug}"
        )

        print("--->  test_go_archive_action of ValidFormRespitTestCase: OK")

    def test_check_csv_header_action(self):
        """Test check_csv_header in utils.py directly"""
        initial_content = "col1;col2\nvalue1;value2\n"

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write(initial_content)
            tmp_path = tmp.name

        check_csv_header(tmp_path, ["col1", "col2", "col3"])

        with open(tmp_path, "r") as f:
            first_line = f.readline()

        self.assertEqual(first_line, "col1;col2;col3\n")

    def test_read_csv_action(self):
        """Test read_archived_csv in utils.py directly"""
        csv_content = "2024-01-01;John Doe;john@example.com;Affil;Estab;123;Title;url;type;2024-01-02\n"

        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(csv_content)
            tmp_path = tmp.name

        with patch("pod.video.utils.ARCHIVE_CSV", tmp_path):
            result = read_archived_csv()

        self.assertIn("123", result)
        self.assertEqual(result["123"]["User name"], "John Doe")

    @patch("pod.video.utils.move_video_to_archive")
    @patch("pod.video.utils.copy_archive_to")
    @patch("pod.video.utils.export_complement")
    @patch("pod.video.utils.store_as_dublincore")
    @patch("pod.video.utils.os.makedirs")
    def test_archive_pack_move_and_real_mode(
        self,
        mock_makedirs,
        mock_store_dc,
        mock_export,
        mock_copy_archive,
        mock_move_archive,
    ):
        archive_pack("/tmp/test", "John", self.video1, only_copy=False, dry_mode=False)

        # ✅ Folder created
        mock_makedirs.assert_called_once_with("/tmp/test", exist_ok=True)

        # ✅ Dublincore generated with object
        mock_store_dc.assert_called_once_with(self.video1, "/tmp/test", "John")

        # ✅ Move called with object
        mock_export.assert_any_call("/tmp/test", "Video", [self.video1], False)

        # Check if dry_mode=False is well spread everywhere
        for call in mock_export.call_args_list:
            self.assertFalse(call.args[-1])

        # ❌ No copy
        mock_copy_archive.assert_not_called()

        # ✅ Move called with object
        mock_move_archive.assert_called_once_with("/tmp/test", self.video1, False)

    def tearDown(self):
        """Cleanup all created stuffs."""
        try:
            os.remove("%s/%s.csv" % (settings.LOG_DIRECTORY, "archived"))
        except FileNotFoundError:
            pass
