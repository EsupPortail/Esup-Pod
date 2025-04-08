"""Video Models test cases."""

from django.test import TestCase
from django.contrib.auth.models import User
from ..models import Video, Type

from ..context_processors import __AVAILABLE_VIDEO_FILTER__
from ..context_processors import get_available_videos

from pod.video_encode_transcript.models import EncodingVideo
from pod.video_encode_transcript.models import PlaylistVideo
from pod.video_encode_transcript.models import EncodingAudio
from pod.video_encode_transcript.models import VideoRendition


class VideoAvailableTestCase(TestCase):
    """Test the video available."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create videos to be tested."""
        user = User.objects.create(username="pod", password="pod1234pod")

        # Video 1 with minimum attributes
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        Video.objects.create(
            title="Video2",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        Video.objects.create(
            title="Video3",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )

    def test_available_video_filter(self):
        """Test available filter for videos."""
        self.assertEqual(Video.objects.all().count(), 3)
        vids = Video.objects.filter(**__AVAILABLE_VIDEO_FILTER__)
        self.assertEqual(vids.count(), 0)
        vid1 = Video.objects.get(id=1)
        vid1.is_draft = False
        vid1.save()
        vids = Video.objects.filter(**__AVAILABLE_VIDEO_FILTER__)
        self.assertEqual(vids.count(), 1)
        vid1.encoding_in_progress = True
        vid1.save()
        vids = Video.objects.filter(**__AVAILABLE_VIDEO_FILTER__)
        self.assertEqual(vids.count(), 0)

    def test_video_filter_encoding(self):
        """Test available videos for encoding."""
        vid1 = Video.objects.get(id=1)
        vid2 = Video.objects.get(id=2)
        vid3 = Video.objects.get(id=3)

        vid1.is_draft = False
        vid1.save()
        vids = Video.objects.filter(**__AVAILABLE_VIDEO_FILTER__)
        self.assertEqual(vids.count(), 1)
        EncodingVideo.objects.create(
            video=vid1,
            encoding_format="video/mp4",
            rendition=VideoRendition.objects.get(id=1),
        )
        vids = get_available_videos()
        self.assertEqual(vids.count(), 1)
        vid1.is_draft = True
        vid1.save()
        vids = get_available_videos()
        self.assertEqual(vids.count(), 0)
        plvid2 = PlaylistVideo.objects.create(
            video=vid2, name="playlist", encoding_format="application/x-mpegURL"
        )
        vids = get_available_videos()
        self.assertEqual(vids.count(), 0)
        vid2.is_draft = False
        vid2.save()
        vids = get_available_videos()
        self.assertEqual(vids.count(), 1)
        vid1.is_draft = False
        vid1.save()
        vids = get_available_videos()
        self.assertEqual(vids.count(), 2)
        eavid3 = EncodingAudio.objects.create(
            video=vid3, name="audio", encoding_format="video/mp4"
        )
        vids = get_available_videos()
        self.assertEqual(vids.count(), 2)
        vid3.is_draft = False
        vid3.save()
        vids = get_available_videos()
        self.assertEqual(vids.count(), 3)
        plvid1 = PlaylistVideo.objects.create(
            video=vid1, name="playlist", encoding_format="application/x-mpegURL"
        )
        vids = get_available_videos()
        self.assertEqual(vids.count(), 3)
        plvid2.delete()
        vids = get_available_videos()
        self.assertEqual(vids.count(), 2)
        eavid3.delete()
        vids = get_available_videos()
        self.assertEqual(vids.count(), 1)
        plvid1.delete()
        vids = get_available_videos()
        self.assertEqual(vids.count(), 1)
