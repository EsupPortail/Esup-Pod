from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
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

    def setUp(self) -> None:
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

    def test_get_add_category_modal(self) -> None:
        """Test get add new category modal."""
        self.client.force_login(self.owner_user)
        url = reverse("video:add_category")
        response = self.client.get(url, headers={"x-requested-with": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "videos/category_modal.html")
        print(" --->  test_get_add_category_modal of TestCategory: OK!")

    def test_post_add_category(self) -> None:
        """Test perform add new category."""
        data = {
            "title": json.dumps("Test new category"),
            "videos": json.dumps([self.video_2.slug]),
        }

        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.post(reverse("video:add_category"), data)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

        # not Ajax request, should return HttpResponseForbidden:403
        self.client.force_login(self.owner_user)
        response = self.client.post(reverse("video:add_category"), data)

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        # Ajax POST request, should return HttpResponse:200 with category data
        response = self.client.post(
            reverse("video:add_category"),
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        response_data = json.loads(response.content)
        expected_data = {
            "success": True,
            "title": "Test new category",
            "slug": "%s-%s" % (self.owner_user.id, slugify("Test new category")),
            "video": [self.video_2],
        }
        actual_data = Category.objects.filter(
            owner=self.owner_user, title="Test new category"
        )
        actual_cat = actual_data.first()

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["success"], True)
        self.assertEqual(response_data["message"], "Category successfully added.")
        self.assertEqual(actual_data.count(), 1)
        self.assertEqual(actual_cat.title, expected_data["title"])
        self.assertEqual(actual_cat.slug, expected_data["slug"])
        self.assertEqual(actual_cat.video.count(), 1)
        self.assertEqual(list(actual_cat.video.all()), expected_data["video"])

        # Add video in another category
        # should return HttpResponseBadRequest:400
        response = self.client.post(
            reverse("video:add_category"),
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )

        response_data = json.loads(response.content)
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response_data["success"])
        self.assertEqual(
            response_data["message"],
            "One or many videos already have a category.",
        )

        # Ajax POST request whitout required field(s),
        # should return HttpResponseBadRequest:400
        del data["title"]
        response = self.client.post(
            reverse("video:add_category"),
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )

        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(response.status_code, 400)

        # Ajax POST request, should return HttpResponse:409
        # category already exists
        data = {"title": json.dumps("Test new category"), "videos": json.dumps([])}

        response = self.client.post(
            reverse("video:add_category"),
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 409)
        print(" --->  test_post_add_category of TestCategory: OK!")

    def test_get_edit_category_modal(self) -> None:
        """Test get edit existent category modal."""
        self.client.force_login(self.owner_user)
        url = reverse("video:edit_category", args=[self.cat_1.slug])
        response = self.client.get(url, headers={"x-requested-with": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "videos/category_modal.html")
        print(" --->  test_get_edit_category_modal of TestCategory: OK!")

    def test_post_edit_category(self) -> None:
        """Test perform edit existent category."""
        data = {
            "title": json.dumps("New Category title"),
            "videos": json.dumps([self.video_2.slug]),
        }
        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_1.slug}),
            data,
        )

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

        # not Ajax request, should return HttpResponseForbidden:403
        self.client.force_login(self.owner_user)
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_1.slug}),
            data,
        )

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        # Ajax request but with other user should return HttpResponseForbidden:403
        self.client.force_login(self.simple_user)
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_1.slug}),
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.content)["message"],
            "You do not have rights to edit this category",
        )

        # Ajax POST request, should return HttpResponse:200 with category data
        self.client.force_login(self.owner_user)
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_1.slug}),
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        response_data = json.loads(response.content)
        expected_data = {
            "success": True,
            "title": "New Category title",
            "slug": "%s-%s" % (self.owner_user.id, slugify("New Category title")),
            "videos": [self.video_2],
        }
        actual_data = Category.objects.filter(
            owner=self.owner_user, slug=expected_data["slug"]
        )
        actual_cat = actual_data.first()

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Category updated successfully.")
        self.assertEqual(actual_cat.title, expected_data["title"])
        self.assertEqual(actual_cat.slug, expected_data["slug"])
        self.assertEqual(actual_cat.video.count(), 1)
        self.assertEqual(actual_cat.video.all().first(), self.video_2)
        self.assertCountEqual(list(actual_cat.video.all()), expected_data["videos"])

        # Add video in another category
        # should return HttpResponseBadRequest:400
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": self.cat_2.slug}),
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        response_data = json.loads(response.content)

        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response_data["success"])
        self.assertEqual(
            response_data["message"],
            "One or many videos already have a category.",
        )

        # Ajax POST request whitout required field(s),
        # should return HttpResponseBadRequest:400
        del data["title"]
        response = self.client.post(
            reverse("video:edit_category", kwargs={"c_slug": expected_data["slug"]}),
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(response.status_code, 400)
        print(" --->  test_post_edit_category of TestCategory: OK!")

    def test_get_categories(self) -> None:
        """Test get categories from dashboard."""
        self.client.force_login(self.owner_user)
        url = reverse("video:dashboard")
        response = self.client.get(url, {"categories": [self.cat_1.slug]})
        response_data = response.context
        all_categories_videos = json.loads(response_data["all_categories_videos"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["videos"].paginator.count, 1)
        self.assertEqual(response_data["categories"].count(), 2)
        self.assertEqual(len(all_categories_videos[self.cat_1.slug]), 1)
        self.assertEqual(all_categories_videos[self.cat_1.slug][0], self.video.slug)
        print(" --->  test_get_categories of TestCategory: OK!")

    def test_get_categories_aside(self) -> None:
        """Test get categories for filter aside elements."""
        self.client.force_login(self.owner_user)
        url = reverse("video:get_categories_list")
        response = self.client.get(url, headers={"x-requested-with": "XMLHttpRequest"})
        response_data = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "videos/filter_aside_categories_list.html")
        self.assertEqual(response_data["categories"].count(), 2)
        print(" --->  test_get_categories_aside of TestCategory: OK!")

    def test_get_delete_category_modal(self) -> None:
        """Test get delete existent category modal."""
        self.client.force_login(self.owner_user)
        url = reverse("video:delete_category", args=[self.cat_1.slug])
        response = self.client.get(url, headers={"x-requested-with": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "videos/category_modal.html")
        print(" --->  test_get_delete_category_modal of TestCategory: OK!")

    def test_post_delete_category(self) -> None:
        """Test perform delete existent category."""
        # not Authenticated, should return HttpResponseRedirect:302
        response = self.client.post(
            reverse("video:delete_category", kwargs={"c_slug": self.cat_1.slug}),
            content_type="application/json",
        )

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

        # not Ajax request, should return HttpResponseForbidden:403
        self.client.force_login(self.owner_user)
        response = self.client.post(
            reverse("video:delete_category", kwargs={"c_slug": self.cat_1.slug}),
            content_type="application/json",
        )

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

        # Ajax POST request but not category's owner,
        # should return HttpResponseForbidden:403
        self.client.force_login(self.simple_user)
        response = self.client.post(
            reverse("video:delete_category", kwargs={"c_slug": self.cat_1.slug}),
            headers={"x-requested-with": "XMLHttpRequest"},
        )

        self.client.force_login(self.owner_user)
        # Ajax POST request, should return HttpResponse:200 with category data
        response = self.client.post(
            reverse("video:delete_category", kwargs={"c_slug": self.cat_1.slug}),
            content_type="application/json",
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        response_data = json.loads(response.content)

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"],
            "Category successfully deleted.",
        )
        self.assertEqual(Category.objects.filter(slug=self.cat_1.slug).count(), 0)
        print(" --->  test_post_delete_category of TestCategory: OK!")

    def tearDown(self) -> None:
        del self.video
        del self.owner_user
        del self.admin_user
        del self.simple_user
        del self.client
        del self.t1
