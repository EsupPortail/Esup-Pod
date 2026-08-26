"""
Esup-Pod - Video models tests.
"""

import os
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from src.apps.video.models import (
    Video,
    ViewCount,
    Comment,
    Subtitle,
    VideoHyperlink,
    VideoCut,
)
from src.apps.encoding.models.EncodingVideo import EncodingVideo
from src.apps.collection.models.Channel import Channel
import datetime

from src.apps.video.apps import sync_metadata

User = get_user_model()


class VideoModelTests(TestCase):
    """
    Tests for the Video application models.
    """

    def setUp(self):
        """Sets up a video and an owner for model testing."""
        sync_metadata(sender=None)
        self.user = User.objects.create_user(username="owner", password="password")
        self.video = Video.objects.create(
            title="Model Test Video",
            owner=self.user,
            description="A description",
            status=Video.Status.PUBLISHED,
            license_id="CC-BY",
        )

    def test_get_dublin_core(self):
        """Verifies the Dublin Core metadata generation."""
        dc = self.video.get_dublin_core()
        self.assertEqual(dc["title"], "Model Test Video")
        self.assertEqual(dc["description"], "A description")
        self.assertEqual(dc["creator"], "owner")
        self.assertEqual(dc["format"], "video/mp4")
        self.assertEqual(dc["rights"], "CC-BY")

    def test_view_count_creation(self):
        """Verifies daily view count records and their string representation."""
        view_count = ViewCount.objects.create(
            video=self.video, date=datetime.date(2026, 1, 1), count=5
        )
        self.assertEqual(view_count.video, self.video)
        self.assertEqual(view_count.count, 5)
        self.assertEqual(str(view_count), "Model Test Video - 2026-01-01: 5")

    def test_video_str(self):
        """Verifies the video's string representation."""
        self.assertEqual(str(self.video), "Model Test Video (Published (Public))")

    def test_create_video_hyperlink(self):
        """Verifies that a VideoHyperlink can be created and linked to a video."""
        VideoHyperlink.objects.create(
            video=self.video,
            url="https://example.com",
            text="Example",
            time_start=10,
            time_end=30,
        )
        self.assertEqual(self.video.hyperlinks.count(), 1)
        self.assertEqual(self.video.hyperlinks.first().url, "https://example.com")
        self.assertEqual(self.video.hyperlinks.first().text, "Example")

    def test_video_hyperlink_str(self):
        """Verifies the string representation of a VideoHyperlink."""
        self.assertEqual(
            str(
                VideoHyperlink.objects.create(
                    video=self.video,
                    url="https://example.com",
                    text="Example",
                    time_start=10,
                    time_end=30,
                )
            ),
            "Model Test Video - Example (10s -> 30s)",
        )

    def test_video_hyperlink_optional_fields(self):
        """Verifies that icon and position are optional."""
        hyperlink = VideoHyperlink.objects.create(
            video=self.video,
            url="https://example.com",
            text="No icon",
            time_start=0,
            time_end=10,
        )
        self.assertIsNone(hyperlink.icon)
        self.assertIsNone(hyperlink.position)

    def test_video_hyperlink_ordering(self):
        """Verifies that hyperlinks are ordered by time_start."""
        VideoHyperlink.objects.create(
            video=self.video, url="https://b.com", text="B", time_start=20, time_end=40
        )
        VideoHyperlink.objects.create(
            video=self.video, url="https://a.com", text="A", time_start=5, time_end=15
        )
        hyperlinks = list(self.video.hyperlinks.all())
        self.assertEqual(hyperlinks[0].text, "A")
        self.assertEqual(hyperlinks[1].text, "B")

    def test_video_hyperlink_cascade_delete(self):
        """Verifies that hyperlinks are deleted when the video is deleted."""
        VideoHyperlink.objects.create(
            video=self.video,
            url="https://example.com",
            text="Gone",
            time_start=0,
            time_end=5,
        )
        self.assertEqual(VideoHyperlink.objects.count(), 1)
        self.video.delete()
        self.assertEqual(VideoHyperlink.objects.count(), 0)


class VideoCutTests(TestCase):
    """Tests for VideoCut model."""

    def setUp(self):
        """Sets up a video for cut testing."""
        sync_metadata(sender=None)

        self.user = User.objects.create_user(
            username="cut_owner",
            password="password",
        )

        self.video = Video.objects.create(
            title="Cut Test Video",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )

    def test_create_video_cut(self):
        """Verifies that a VideoCut can be created and linked to a video."""
        cut = VideoCut.objects.create(
            video=self.video,
            time_start=10,
            time_end=50,
        )

        self.assertEqual(cut.video, self.video)
        self.assertEqual(cut.time_start, 10)
        self.assertEqual(cut.time_end, 50)

        # reverse relation
        self.assertEqual(self.video.cut, cut)

    def test_video_cut_str(self):
        """Verifies the string representation of VideoCut."""
        cut = VideoCut.objects.create(
            video=self.video,
            time_start=5,
            time_end=20,
        )

        self.assertIn("Cut Test Video", str(cut))
        self.assertIn("5", str(cut))
        self.assertIn("20", str(cut))

    def test_one_cut_per_video(self):
        """Ensures OneToOne constraint replaces existing cut logic (manual simulation)."""
        VideoCut.objects.create(
            video=self.video,
            time_start=10,
            time_end=30,
        )

        # simulate replacement like API does
        VideoCut.objects.filter(video=self.video).delete()

        new_cut = VideoCut.objects.create(
            video=self.video,
            time_start=40,
            time_end=80,
        )

        self.assertEqual(VideoCut.objects.filter(video=self.video).count(), 1)
        self.assertEqual(new_cut.time_start, 40)


class CommentBasicTests(TestCase):
    """Tests for the Comment model."""

    def setUp(self):
        """Sets up a video and a user for comment testing."""
        sync_metadata(sender=None)
        self.user = User.objects.create_user(username="commenter2", password="password")
        self.video = Video.objects.create(
            title="A Video", owner=self.user, status=Video.Status.PUBLISHED
        )

    def test_create_comment(self):
        """Verifies the creation of a comment."""
        comment = Comment.objects.create(
            author=self.user, video=self.video, content="Small test comment"
        )
        self.assertEqual(str(comment), "Small test comment")
        self.assertEqual(comment.number_vote, 0)


class FileCleanupTests(TestCase):
    """Tests for physical file cleanup on object deletion."""

    def setUp(self):
        """Sets up a test user and their owner profile for file cleanup testing."""
        self.user = User.objects.create_user(
            username="test_cleanup_user", password="password"
        )
        self.owner = self.user.owner

    def test_subtitle_file_cleanup(self):
        """Verifies that physical subtitle files are deleted when the object is deleted."""
        video = Video.objects.create(
            title="Video for subtitle test",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        subtitle_file = SimpleUploadedFile(
            "subtitle.vtt", b"WEBVTT\n\n00:00.000 --> 00:01.000\nHello"
        )
        subtitle = Subtitle.objects.create(video=video, language="fr", file=subtitle_file)
        file_path = subtitle.file.path
        self.assertTrue(os.path.exists(file_path))

        subtitle.delete()
        self.assertFalse(os.path.exists(file_path))

    def test_encoding_video_file_cleanup(self):
        """Verifies that encoded physical video files are deleted on deletion."""
        video = Video.objects.create(
            title="Video for encoding test",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        encoded_file = SimpleUploadedFile("encoded.mp4", b"dummy video content")
        encoding = EncodingVideo.objects.create(
            video=video, resolution="720p", file=encoded_file
        )
        file_path = encoding.file.path
        self.assertTrue(os.path.exists(file_path))

        encoding.delete()
        self.assertFalse(os.path.exists(file_path))

    def test_channel_files_cleanup(self):
        """Verifies that channel logo and banner files are deleted on deletion."""
        logo_file = SimpleUploadedFile("logo.png", b"dummy logo")
        banner_file = SimpleUploadedFile("banner.png", b"dummy banner")
        channel = Channel.objects.create(
            title="Test Channel", owner=self.user, logo=logo_file, banner=banner_file
        )
        logo_path = channel.logo.path
        banner_path = channel.banner.path
        self.assertTrue(os.path.exists(logo_path))
        self.assertTrue(os.path.exists(banner_path))

        channel.delete()
        self.assertFalse(os.path.exists(logo_path))
        self.assertFalse(os.path.exists(banner_path))

    def test_owner_picture_cleanup(self):
        """Verifies that the user's profile picture is deleted when profile is deleted."""
        picture_file = SimpleUploadedFile("profile.png", b"dummy avatar")
        self.owner.userpicture = picture_file
        self.owner.save()

        picture_path = self.owner.userpicture.path
        self.assertTrue(os.path.exists(picture_path))

        self.owner.delete()
        self.assertFalse(os.path.exists(picture_path))

    def test_video_source_cleanup_flag_true(self):
        """Verifies original source video is deleted when cleanup flag is enabled."""
        from src.apps.video.conf import video_settings

        video_settings.delete_source_on_video_delete = True

        video_file = SimpleUploadedFile("source.mp4", b"source content")
        video = Video.objects.create(
            title="Video true flag test", owner=self.user, video_file=video_file
        )
        file_path = video.video_file.path
        self.assertTrue(os.path.exists(file_path))

        video.delete()
        self.assertFalse(os.path.exists(file_path))

    def test_video_source_cleanup_flag_false(self):
        """Verifies original source video is kept when cleanup flag is disabled."""
        from src.apps.video.conf import video_settings

        video_settings.delete_source_on_video_delete = False

        video_file = SimpleUploadedFile("source.mp4", b"source content")
        video = Video.objects.create(
            title="Video false flag test", owner=self.user, video_file=video_file
        )
        file_path = video.video_file.path
        self.assertTrue(os.path.exists(file_path))

        video.delete()
        # Source should still exist
        self.assertTrue(os.path.exists(file_path))

        # Clean up manually to not leave test files
        if os.path.exists(file_path):
            os.remove(file_path)
