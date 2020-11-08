from django.http import JsonResponse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.test import TestCase, Client
from django.urls import reverse
from pod.authentication.models import User
from pod.video.models import Category, Video, Type
from django.contrib.sites.models import Site
from pod.video.views import get_categories, add_category
from pod.video.views import edit_category, delete_category
import ast, json

import logging


class TestComment(TestCase):
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
        self.cat_1 = Category.objects.create(
                title='testCategory',
                owner=self.owner_user)
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
        expected_data =json.loads(JsonResponse({
                "success": True,
                "categories": [
                    {"title": 'testCategory', "id": 1, "video": None},
                    {"title": 'test2Category', "id": 2, "video": None}
                ]}, safe=False).content.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(actual_data.keys(), expected_data.keys())
        self.assertTrue(expected_data['success'])
        self.assertCountEqual(actual_data['categories'], expected_data['categories'])


    def tearDown(self):
        del self.video
        del self.owner_user
        del self.admin_user
        del self.simple_user
        del self.client
        del self.t1
