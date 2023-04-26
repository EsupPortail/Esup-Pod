from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from pod.favorite.models import Favorite
from pod.video.models import Type, Video


class TestShowStarTestCase(TestCase):
    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.user_with_favorite = User.objects.create(
            username="pod", password="pod1234pod")
        self.user_without_favorite = User.objects.create(
            username="pod2", password="pod1234pod2")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user_without_favorite,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        Favorite.objects.create(
            owner=self.user_with_favorite,
            video=self.video,
            rank=1,
        )
        self.url = reverse("video:video", args=[self.video.slug])

    def test_show_star_unfill(self) -> None:
        """Test if the star is unfill when the video isn't favorite"""
        self.client.force_login(self.user_without_favorite)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200 when the video isn't favorite",
        )
        self.assertTrue(
            'bi-star' in response.content.decode(),
            "Test if the star is correctly present when the video isn't favorite",
        )
        self.client.logout()
        print(" --->  test_show_star_unfill ok")

    def test_show_star_fill(self) -> None:
        """Test if the star is fill when the video is favorite"""
        self.client.force_login(self.user_with_favorite)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200 when the video is favorite",
        )
        self.assertTrue(
            'bi-star-fill' in response.content.decode(),
            "Test if the star is correctly present when the video is favorite",
        )
        self.client.logout()
        print(" --->  test_show_star_fill ok")

    def test_show_star_hidden(self) -> None:
        """Test if the star is hidden when the user is disconnected"""
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200 when the user is disconnected",
        )
        self.assertFalse(
            'bi-star' in response.content.decode(),
            "Test if the star is hidden when the user is disconnected",
        )
        print(" --->  test_show_star_hidden ok")

    def test_show_star_404_error(self) -> None:
        """Test if we can't navigate in the `favorite/` route with GET method"""
        response = self.client.get(reverse("favorite:add-or-remove"))
        self.assertEqual(
            response.status_code,
            404,
            '''
            Test if status code equal 404 when we try to navigate in
             the `favorite/` route with GET method
            ''',
        )
        print(" --->  test_show_star_404_error ok")


class TestFavoriteVideoListTestCase(TestCase):
    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.user_with_favorite = User.objects.create(
            username="pod", password="pod1234pod")
        self.user_without_favorite = User.objects.create(
            username="pod2", password="pod1234pod2")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user_without_favorite,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        Favorite.objects.create(
            owner=self.user_with_favorite,
            video=self.video,
            rank=1,
        )
        self.url = reverse("favorite:list")

    def test_favorite_video_list_not_empty(self) -> None:
        """Test if the favorite video list isn't empty when the user has favorites"""
        self.client.force_login(self.user_with_favorite)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200 when the favorite video list isn't empty",
        )
        self.assertTrue(
            'data-countvideos="1"' in response.content.decode(),
            "Test if the favorite video list isn't correctly empty",
        )
        self.client.logout()
        print(" --->  test_favorite_video_list_not_empty ok")

    def test_favorite_video_list_empty(self) -> None:
        """Test if the favorite video list is empty when the user has favorites"""
        self.client.force_login(self.user_without_favorite)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200 when the favorite video list isn't empty",
        )
        self.assertTrue(
            'data-countvideos="0"' in response.content.decode(),
            "Test if the favorite video list is correctly empty",
        )
        self.client.logout()
        print(" --->  test_favorite_video_list_empty ok")
