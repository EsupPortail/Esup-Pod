from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.test import TestCase, Client
from django.urls import reverse
from pod.authentication.models import User
from pod.video.models import Category, Video, Type
import json
import logging


class TestCategory(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        self.logger = logging.getLogger("django.request")
        # self.previous_level = self.logger.getEffectiveLevel()
        # Remove warning log
        self.logger.setLevel(logging.ERROR)

        self.client = Client()
        self.t1 = Type.objects.get(id=1)
        self.owner_user = User.objects.create(
                username="doejohn",
                first_name="John",
                last_name="DOE",
                password="Toto1234_4321")
        self.simple_user = User.objects.create(
                username="visitorpod",
                first_name="Visitor",
                last_name="Pod",
                password="Visitor1234*")
        self.admin_user = User.objects.create(
                username="SuperUser",
                first_name="Super",
                last_name="User",
                password="SuperPassword1234",
                is_superuser=True)
        self.video = Video.objects.create(
                title="Test category video",
                is_draft=False,
                encoding_in_progress=False,
                owner=self.owner_user,
                video="testvideocategory.mp4",
                type=self.t1)
        self.video_2 = Video.objects.create(
                title="Test category video 2",
                is_draft=False,
                encoding_in_progress=False,
                owner=self.owner_user,
                video="testvideo2category.mp4",
                type=self.t1)

        self.cat_1 = Category.objects.create(
                title='testCategory',
                owner=self.owner_user)
        self.cat_1.video.add(self.video)
        self.cat_1.video.add(self.video_2)
        self.cat_1.save()
        self.cat_2 = Category.objects.create(
                title='test2Category',
                owner=self.owner_user)

    def test_getCategories(self):
        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.get(reverse('get_categories'))
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

        # not Ajax request, should return HttpResponseForbidden:403
        self.client.force_login(self.owner_user)
        response = self.client.get(reverse('get_categories'))
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        # Ajax request, should return HttpResponse:200 with all categories
        response = self.client.get(
                reverse('get_categories'),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        actual_data = json.loads(response.content.decode('utf-8'))
        expected_data = json.loads(JsonResponse({
                "success": True,
                "categories": [
                    {
                        "title": 'testCategory',
                        "slug": self.cat_1.slug,
                        "videos": list(
                            self.cat_1.video.values_list('slug', flat=True))},
                    {
                        "title": 'test2Category',
                        "slug": self.cat_2.slug,
                        "videos": []
                    }
                ]}, safe=False).content.decode('utf-8'))

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(actual_data.keys(), expected_data.keys())
        self.assertTrue(expected_data['success'])
        self.assertCountEqual(
                actual_data['categories'],
                expected_data['categories'])

        # Ajax request, should return HttpResponse:200 with one category
        response = self.client.get(
                reverse('get_category', kwargs={"c_slug": self.cat_1.slug}),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        actual_data = json.loads(response.content.decode('utf-8'))
        expected_data = json.loads(JsonResponse({
                "success": True,
                "category_id": self.cat_1.id,
                "category_title": self.cat_1.title,
                "category_owner": self.cat_1.owner.id,
                "videos": list(self.cat_1.video.values_list('slug', flat=True))
                }, safe=False).content.decode('utf-8'))

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(actual_data, expected_data)

    def test_addCategory(self):
        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.get(reverse('add_category'))
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

    def tearDown(self):
        del self.video
        del self.owner_user
        del self.admin_user
        del self.simple_user
        del self.client
        del self.t1
