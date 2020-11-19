from django.http import HttpResponse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.template.defaultfilters import slugify
from django.test import TestCase, Client
from django.urls import reverse
from pod.authentication.models import User
from pod.video.models import Category, Video, Type
import json
import logging


class TestCategory(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        self.maxDiff = None
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
        expected_data = {
            "success": True,
            "categories": [
                {
                    "title": 'test2Category',
                    "slug": self.cat_2.slug,
                    "videos": []
                },
                {
                    "title": 'testCategory',
                    "slug": self.cat_1.slug,
                    "videos": list(
                        self.cat_1.video.values_list('id', flat=True))
                }
            ]
        }
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(expected_data['success'])
        for i in range(2):
            self.assertEqual(
                    actual_data['categories'][i]['title'],
                    expected_data['categories'][i]['title'])
            self.assertEqual(
                    actual_data['categories'][i]['slug'],
                    expected_data['categories'][i]['slug'])
            self.assertCountEqual(
                    actual_data['categories'][i]['videos'],
                    expected_data['categories'][i]['videos'])

        # Ajax request, should return HttpResponse:200 with one category
        response = self.client.get(
                reverse('get_category', kwargs={"c_slug": self.cat_1.slug}),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        actual_data = json.loads(response.content.decode('utf-8'))
        expected_data = {
            "success": True,
            "category_id": self.cat_1.id,
            "category_title": self.cat_1.title,
            "category_owner": self.cat_1.owner.id,
            "videos": list(map(lambda v: {
                    "slug": v.slug,
                    "title": v.title,
                    "duration": v.duration_in_time,
                    "thumbnail": v.get_thumbnail_card(),
                    "is_video": v.is_video,
                    "is_draft": v.is_draft,
                    "is_restricted": v.is_restricted,
                    "has_chapter": v.chapter_set.all().count()>0,
                    "has_password": bool(v.password),
                    }, self.cat_1.video.all()))
        }

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
                list(actual_data.keys()),
                list(expected_data.keys()))
        self.assertCountEqual(
                list(actual_data.values()),
                list(expected_data.values()))

    def test_addCategory(self):
        data = {
            "title": "Test new catgeory",
            "videos": self.video.slug + "," + self.video_2.slug
        }

        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.post(reverse('add_category'), data)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

        # not Ajax request, should return HttpResponseForbidden:403
        self.client.force_login(self.owner_user)
        response = self.client.post(reverse('add_category'), data)
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        # Ajax POST request, should return HttpResponse:200 with category data
        response = self.client.post(
                reverse('add_category'),
                data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        actual_data = json.loads(response.content.decode('utf-8'))
        expected_data = {
            "success": True,
            "title": data["title"],
            "slug": "%s-%s" % (self.owner_user.id, slugify(data["title"])),
            "videos": data["videos"].split(',')
        }

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(actual_data['success'])
        self.assertEqual(actual_data['title'], expected_data['title'])
        self.assertEqual(actual_data['slug'], expected_data['slug'])
        self.assertCountEqual(actual_data['videos'], expected_data['videos'])

    def tearDown(self):
        del self.video
        del self.owner_user
        del self.admin_user
        del self.simple_user
        del self.client
        del self.t1
