from datetime import datetime

from django.contrib.sites.models import Site
from django.test import TestCase, RequestFactory, Client

from pod.authentication.backends import User
from pod.video.models import Video, Type
from pod.video.views import bulk_update


class BulkUpdateTestCase(TestCase):
    """Test the videos bulk update."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create videos to be tested."""
        self.factory = RequestFactory()
        self.client = Client()

        site = Site.objects.get(id=1)
        user1 = User.objects.create(
            username="pod1", password="pod1234pod", email="pod@univ.fr"
        )
        user2 = User.objects.create(
            username="pod2", password="pod1234pod", email="pod@univ.fr"
        )
        user3 = User.objects.create(
            username="pod3", password="pod1234pod", email="pod@univ.fr"
        )

        type1 = Type.objects.create(title="type1")
        type2 = Type.objects.create(title="type2")

        Video.objects.create(
            type=type1,
            title="Video1",
            password=None,
            date_added=datetime.today(),
            encoding_in_progress=False,
            owner=user1,
            date_evt=datetime.today(),
            video="test.mp4",
            allow_downloading=True,
            description="test",
            is_draft=False,
            duration=3,
        )

        Video.objects.create(
            type=type1,
            title="Video2",
            password=None,
            date_added=datetime.today(),
            encoding_in_progress=False,
            owner=user2,
            date_evt=datetime.today(),
            video="test.mp4",
            allow_downloading=True,
            description="test",
            is_draft=False,
            duration=3,
        )

        Video.objects.create(
            type=type2,
            title="Video3",
            password=None,
            date_added=datetime.today(),
            encoding_in_progress=False,
            owner=user2,
            date_evt=datetime.today(),
            video="test.mp4",
            allow_downloading=True,
            description="test",
            is_draft=False,
            duration=3,
        )

        Video.objects.create(
            type=type2,
            title="Video4",
            password=None,
            date_added=datetime.today(),
            encoding_in_progress=False,
            owner=user3,
            date_evt=datetime.today(),
            video="test.mp4",
            allow_downloading=True,
            description="test",
            is_draft=False,
            duration=3,
        )

        Video.objects.create(
            type=type2,
            title="Video5",
            password=None,
            date_added=datetime.today(),
            encoding_in_progress=False,
            owner=user3,
            date_evt=datetime.today(),
            video="test.mp4",
            allow_downloading=True,
            description="test",
            is_draft=False,
            duration=3,
        )

        for vid in Video.objects.all():
            vid.sites.add(site)

        print(" --->  SetUp of BulkUpdateTestCase: OK!")

    def test_bulk_update_title(self):
        video1 = Video.objects.get(id=1)
        video2 = Video.objects.get(id=2)

        user1 = User.objects.get(username="pod1")
        selected_videos = [video1.slug, video2.slug]
        update_fields = ['title']

        self.client.force_login(user1)

        post_request = self.factory.post(
            '/bulk_update/',
            {
                'title': 'Test Title',
                'selected_videos': selected_videos,
                'update_fields': update_fields,
                'update_action': "fields",
            },
            content_type='application/json'
        )
        response = bulk_update(post_request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Video.objects.filter(title="Test Title"), 2)

        print(
            "--->  test_bulk_update_title of \
            BulkUpdateTestCase: OK"
        )
        self.client.logout()
