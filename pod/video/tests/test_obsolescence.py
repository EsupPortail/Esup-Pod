"""Test the Obsolete videos."""
from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import gettext as _

from ..models import Video, Type, VideoToDelete
from pod.authentication.models import Owner

from datetime import date, timedelta
import os
from django.contrib.sites.models import Site

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

    def test_check_video_date_delete(self):
        """Check that the videos deletion date complies with the settings."""
        video = Video.objects.get(id=1)
        date1 = date(
            date.today().year + DEFAULT_YEAR_DATE_DELETE,
            date.today().month,
            date.today().day,
        )
        self.assertEqual(video.date_delete, date1)

        video2 = Video.objects.get(id=2)
        date2 = date(
            date.today().year
            + settings.ACCOMMODATION_YEARS[video2.owner.owner.affiliation],
            date.today().month,
            date.today().day,
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
        print(
            "--->  test_notify_user_obsolete_video of \
            ObsolescenceTestCase: OK"
        )

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

    def test_delete_video(self):
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

        # on verifie que la vidéo archivée est bien archivée
        video_to_archive = Video.objects.get(id=6)
        archive_user, created = User.objects.get_or_create(
            username=ARCHIVE_OWNER_USERNAME,
        )
        self.assertTrue(_("Archived") in video_to_archive.title)
        self.assertTrue(video_to_archive.is_draft)
        self.assertTrue(video_to_archive.owner == archive_user)

        vid_delete = VideoToDelete.objects.get(date_deletion=video_to_archive.date_delete)
        self.assertTrue(video_to_archive in vid_delete.video.all())

        # On vérifie que la video supprimée est bien supprimée
        self.assertEqual(Video.objects.filter(id=7).count(), 0)

        # On verifie que les fichiers csv sont bien créés
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

        print("--->  test_obsolete_video of ObsolescenceTestCase: OK")

    def tearDown(self):
        """Cleanup all created stuffs."""
        try:
            os.remove("%s/%s.csv" % (settings.LOG_DIRECTORY, "deleted"))
            os.remove("%s/%s.csv" % (settings.LOG_DIRECTORY, "archived"))
        except FileNotFoundError:
            pass
