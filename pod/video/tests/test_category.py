from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseNotAllowed
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.template.defaultfilters import slugify
from django.test import TestCase, Client
from django.urls import reverse
from pod.authentication.models import User
from pod.video.models import Category, Video, Type
import json
import logging


class TestCategory(TestCase):

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        self.maxDiff = None
        self.logger = logging.getLogger("django.request")
        # self.previous_level = self.logger.getEffectiveLevel()
        # Remove warning log
        self.logger.setLevel(logging.ERROR)

        self.client = Client(json_encoder=DjangoJSONEncoder)
        self.t1 = Type.objects.get(id=1)
        self.owner_user = User.objects.create(
            username="doejohn",
            first_name="John",
            last_name="DOE",
            password="Toto1234_4321",
        )
        self.simple_user = User.objects.create(
            username="visitorpod",
            first_name="Visitor",
            last_name="Pod",
            password="Visitor1234*",
        )
        self.admin_user = User.objects.create(
            username="SuperUser",
            first_name="Super",
            last_name="User",
            password="SuperPassword1234",
            is_superuser=True,
        )
        self.video = Video.objects.create(
            title="Test category video",
            is_draft=False,
            encoding_in_progress=False,
            owner=self.owner_user,
            video="testvideocategory.mp4",
            type=self.t1,
        )
        self.video.additional_owners.add(self.simple_user)
        self.video.save()
        self.video_2 = Video.objects.create(
            title="Test category video 2",
            is_draft=False,
            encoding_in_progress=False,
            owner=self.owner_user,
            video="testvideo2category.mp4",
            type=self.t1,
        )
        self.cat_1 = Category.objects.create(title="testCategory", owner=self.owner_user)
        self.cat_1.video.add(self.video)
        self.cat_1.save()
        self.cat_2 = Category.objects.create(title="test2Category", owner=self.owner_user)
        self.cat_3 = Category.objects.create(
            title="test3Category", owner=self.simple_user
        )
        self.cat_3.video.add(self.video)

    def test_getCategories(self):
        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.get(reverse("video:get_categories"))
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

        # not Ajax request, should return HttpResponseForbidden:403
        self.client.force_login(self.owner_user)
        response = self.client.get(reverse("video:get_categories"))
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        # Ajax request, should return HttpResponse:200 with all categories
        response = self.client.get(
            reverse("video:get_categories"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        actual_data = json.loads(response.content.decode("utf-8"))
        expected_data = {
            "success": True,
            "categories": [
                {
                    "title": "test2Category",
                    "slug": self.cat_2.slug,
                    "videos": [],
                },
                {
                    "title": "testCategory",
                    "slug": self.cat_1.slug,
                    "videos": [
                        {
                            "slug": self.video.slug,
                            "title": self.video.title,
                            "duration": self.video.duration_in_time,
                            "thumbnail": self.video.get_thumbnail_card(),
                            "is_video": self.video.is_video,
                            "is_draft": self.video.is_draft,
                            "is_restricted": self.video.is_restricted,
                            "has_chapter": self.video.chapter_set.all().count() > 0,
                            "has_password": bool(self.video.password),
                        }
                    ],
                },
            ],
        }
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(expected_data["success"])
        for i in range(2):
            self.assertEqual(
                actual_data["categories"][i]["title"],
                expected_data["categories"][i]["title"],
            )
            self.assertEqual(
                actual_data["categories"][i]["slug"],
                expected_data["categories"][i]["slug"],
            )
            self.assertCountEqual(
                actual_data["categories"][i]["videos"],
                expected_data["categories"][i]["videos"],
            )

        # Ajax request, should return HttpResponse:200 with one category
        response = self.client.get(
            reverse("video:get_category", kwargs={"c_slug": self.cat_1.slug}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        actual_data = json.loads(response.content.decode("utf-8"))
        expected_data = {
            "success": True,
            "id": self.cat_1.id,
            "slug": self.cat_1.slug,
            "title": self.cat_1.title,
            "owner": self.cat_1.owner.id,
            "videos": list(
                map(
                    lambda v: {
                        "slug": v.slug,
                        "title": v.title,
                        "duration": v.duration_in_time,
                        "thumbnail": v.get_thumbnail_card(),
                        "is_video": v.is_video,
                        "is_draft": v.is_draft,
                        "is_restricted": v.is_restricted,
                        "has_chapter": v.chapter_set.all().count() > 0,
                        "has_password": bool(v.password),
                    },
                    self.cat_1.video.all(),
                )
            ),
        }

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(list(actual_data.keys()), list(expected_data.keys()))
        self.assertCountEqual(list(actual_data.values()), list(expected_data.values()))

        # GET category as additional owner
        # Ajax request, should return HttpResponse:200 with one category
        self.client.force_login(self.simple_user)
        response = self.client.get(
            reverse("video:get_category", kwargs={"c_slug": self.cat_3.slug}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        actual_data = json.loads(response.content.decode("utf-8"))
        expected_data = {
            "success": True,
            "id": self.cat_3.id,
            "slug": self.cat_3.slug,
            "title": self.cat_3.title,
            "owner": self.cat_3.owner.id,
            "videos": [
                {
                    "slug": self.video.slug,
                    "title": self.video.title,
                    "duration": self.video.duration_in_time,
                    "thumbnail": self.video.get_thumbnail_card(),
                    "is_video": self.video.is_video,
                    "is_draft": self.video.is_draft,
                    "is_restricted": self.video.is_restricted,
                    "has_chapter": self.video.chapter_set.all().count() > 0,
                    "has_password": bool(self.video.password),
                }
            ],
        }

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(actual_data, expected_data)

        # GET category as no longer additional owner
        # Ajax request, should return HttpResponse:200 with one category
        self.video.additional_owners.remove(self.simple_user)
        response = self.client.get(
            reverse("video:get_category", kwargs={"c_slug": self.cat_3.slug}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        actual_data = json.loads(response.content.decode("utf-8"))
        expected_data = {
            "success": True,
            "id": self.cat_3.id,
            "slug": self.cat_3.slug,
            "title": self.cat_3.title,
            "owner": self.cat_3.owner.id,
            "videos": [],
        }
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(actual_data, expected_data)

    def test_addCategory(self):
        data = {"title": "Test new category", "videos": [self.video_2.slug]}

        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.post(
            reverse("video:add_category"),
            json.dumps(data),
            content_type="application/json",
        )

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

        # not Ajax request, should return HttpResponseForbidden:403
        self.client.force_login(self.owner_user)
        response = self.client.post(
            reverse("video:add_category"),
            json.dumps(data),
            content_type="application/json",
        )

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        # Ajax GET request, should return HttpResponseNotAllowed:405
        response = self.client.get(
            reverse("video:add_category"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertIsInstance(response, HttpResponseNotAllowed)
        self.assertEqual(response.status_code, 405)

        # Ajax POST request, should return HttpResponse:200 with category data
        response = self.client.post(
            reverse("video:add_category"),
            json.dumps(data),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        actual_data = json.loads(response.content.decode("utf-8"))
        expected_data = {
            "success": True,
            "title": data["title"],
            "slug": "%s-%s" % (self.owner_user.id, slugify(data["title"])),
            "videos": [
                {
                    "slug": self.video_2.slug,
                    "title": self.video_2.title,
                    "duration": self.video_2.duration_in_time,
                    "thumbnail": self.video_2.get_thumbnail_card(),
                    "is_video": self.video_2.is_video,
                    "is_draft": self.video_2.is_draft,
                    "is_restricted": self.video_2.is_restricted,
                    "has_chapter": self.video_2.chapter_set.all().count() > 0,
                    "has_password": bool(self.video_2.password),
                }
            ],
        }
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(actual_data["success"])
        self.assertEqual(actual_data["category"]["title"], expected_data["title"])
        self.assertEqual(actual_data["category"]["slug"], expected_data["slug"])
        self.assertCountEqual(actual_data["category"]["videos"], expected_data["videos"])

        # Add video in another category
        # should return HttpResponseBadRequest:400
        response = self.client.post(
            reverse("video:add_category"),
            json.dumps(data),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        actual_data = json.loads(response.content.decode("utf-8"))
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(actual_data["success"])
        self.assertEqual(
            actual_data["message"],
            "One or many videos already have a category.",
        )

        # Ajax POST request whitout required field(s),
        # should return HttpResponseBadRequest:400
        del data["title"]
        response = self.client.post(
            reverse("video:add_category"),
            json.dumps(data),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(response.status_code, 400)

        # Ajax POST request, should return HttpResponse:409
        # category already exists
        data = {"title": "Test new category", "videos": []}
        response = self.client.post(
            reverse("video:add_category"),
            json.dumps(data),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 409)

    def test_editCategory(self):
        data = {"title": "New Category title", "videos": [self.video_2.slug]}
        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_1.slug}),
            json.dumps(data),
            content_type="application/json",
        )

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

        # not Ajax request, should return HttpResponseForbidden:403
        self.client.force_login(self.owner_user)
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_1.slug}),
            json.dumps(data),
            content_type="application/json",
        )

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        # Ajax GET request, should return HttpResponseNotAllowed:405
        response = self.client.get(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_1.slug}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertIsInstance(response, HttpResponseNotAllowed)
        self.assertEqual(response.status_code, 405)

        # Ajax POST request, should return HttpResponse:200 with category data
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_1.slug}),
            json.dumps(data),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        actual_data = json.loads(response.content.decode("utf-8"))
        expected_data = {
            "success": True,
            "title": data["title"],
            "slug": "%s-%s" % (self.owner_user.id, slugify(data["title"])),
            "videos": [
                {
                    "slug": self.video_2.slug,
                    "title": self.video_2.title,
                    "duration": self.video_2.duration_in_time,
                    "thumbnail": self.video_2.get_thumbnail_card(),
                    "is_video": self.video_2.is_video,
                    "is_draft": self.video_2.is_draft,
                    "is_restricted": self.video_2.is_restricted,
                    "has_chapter": self.video_2.chapter_set.all().count() > 0,
                    "has_password": bool(self.video_2.password),
                }
            ],
        }

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(actual_data["success"])
        self.assertEqual(actual_data["title"], expected_data["title"])
        self.assertEqual(actual_data["slug"], expected_data["slug"])
        self.assertCountEqual(actual_data["videos"], expected_data["videos"])

        # Add video in anthoer category
        # should return HttpResponseBadRequest:400
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_2.slug}),
            json.dumps(data),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        actual_data = json.loads(response.content.decode("utf-8"))
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(actual_data["success"])
        self.assertEqual(
            actual_data["message"],
            "One or many videos already have a category.",
        )

        # Ajax POST request whitout required field(s),
        # should return HttpResponseBadRequest:400
        del data["title"]
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": expected_data["slug"]}),
            json.dumps(data),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(response.status_code, 400)

    def test_deleteCategory(self):
        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.post(
            reverse("video:delete_category", kwargs={"c_id": self.cat_1.id}),
            content_type="application/json",
        )

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

        # not Ajax request, should return HttpResponseForbidden:403
        self.client.force_login(self.owner_user)
        response = self.client.post(
            reverse("video:delete_category", kwargs={"c_id": self.cat_1.id}),
            content_type="application/json",
        )

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        # Ajax GET request, should return HttpResponseNotAllowed:405
        response = self.client.get(
            reverse("video:delete_category", kwargs={"c_id": self.cat_1.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertIsInstance(response, HttpResponseNotAllowed)
        self.assertEqual(response.status_code, 405)

        # Ajax POST request but not category's owner,
        # should return HttpResponseForbidden:403
        self.client.force_login(self.simple_user)
        response = self.client.post(
            reverse("video:delete_category", kwargs={"c_id": self.cat_1.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        response = self.client.get(reverse("video:get_categories"))
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.owner_user)
        # Ajax POST request, should return HttpResponse:200 with category data
        response = self.client.post(
            reverse("video:delete_category", kwargs={"c_id": self.cat_1.id}),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        actual_data = json.loads(response.content.decode("utf-8"))

        self.assertTrue(actual_data["success"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(actual_data["id"], self.cat_1.id)
        self.assertCountEqual(
            actual_data["videos"],
            [
                {
                    "slug": self.video.slug,
                    "title": self.video.title,
                    "duration": self.video.duration_in_time,
                    "thumbnail": self.video.get_thumbnail_card(),
                    "is_video": self.video.is_video,
                }
            ],
        )

    def tearDown(self):
        del self.video
        del self.owner_user
        del self.admin_user
        del self.simple_user
        del self.client
        del self.t1
