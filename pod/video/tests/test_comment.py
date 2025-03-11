"""Tests for video comments and votes."""

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse, HttpResponse
from django.test import TestCase, Client
from django.urls import reverse
from pod.authentication.models import User
from pod.video.models import Comment, Video, Type
from django.contrib.sites.models import Site
from pod.video.views import get_comments, get_children_comment
from pod.video.views import add_comment, delete_comment
import ast
import json
import logging


class TestComment(TestCase):
    """Class containing Tests for video comments and votes."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Set up TestComment class."""
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
            title="Test comment video",
            is_draft=False,
            encoding_in_progress=False,
            owner=self.owner_user,
            video="testvideocomment.mp4",
            type=self.t1,
        )
        self.admin_comment = Comment.objects.create(
            author=self.admin_user,
            content="Admin parent comment",
            video=self.video,
        )
        self.simple_user_comment = Comment.objects.create(
            author=self.simple_user,
            content="Simple user parent comment",
            video=self.video,
        )
        self.owner_to_admin_comment = Comment.objects.create(
            author=self.owner_user,
            content="Video owner responds to admin parent comment",
            video=self.video,
            parent=self.admin_comment,
            direct_parent=self.admin_comment,
        )
        self.owner_to_simple_user_comment = Comment.objects.create(
            author=self.owner_user,
            content="Video owner responds to simple user parent comment",
            video=self.video,
            parent=self.simple_user_comment,
            direct_parent=self.simple_user_comment,
        )

        self.owner_user.owner.sites.add(Site.objects.get_current())
        self.owner_user.owner.save()

        self.simple_user.owner.sites.add(Site.objects.get_current())
        self.simple_user.owner.save()

        self.admin_user.owner.sites.add(Site.objects.get_current())
        self.admin_user.owner.save()

        self.ajax_header = {"HTTP_x-requested-with": "XMLHttpRequest"}

    def test_get_all_comment(self):
        """Try to get all comments."""
        url = reverse("video:get_comments", kwargs={"video_slug": self.video.slug})
        response = self.client.get(url)
        # Check that the view function is get_comments
        self.assertEqual(response.resolver_match.func, get_comments)
        # Check response is 200 OK and contents the expected comment
        self.assertContains(
            response,
            self.owner_to_admin_comment.content.encode("utf-8"),
            status_code=200,
        )
        self.assertContains(response, self.simple_user_comment.content.encode("utf-8"))

    def test_get_only_parent_comment(self):
        url = reverse("video:get_comments", kwargs={"video_slug": self.video.slug})
        response = self.client.get(
            url, {"only": "parents"}, headers={"accept": "application/json"}
        )
        self.assertEqual(response.resolver_match.func, get_comments)
        # Check response is 200 OK and contents the expected comment
        expected_response = HttpResponse(
            json.dumps(
                [
                    {
                        "author_name": "Super User",
                        "content": "Admin parent comment",
                        "is_owner": False,
                        "nbr_vote": 0,
                        "id": 1,
                        "added": self.admin_comment.added,
                        "nbr_child": 1,
                    },
                    {
                        "author_name": "Visitor Pod",
                        "content": "Simple user parent comment",
                        "is_owner": False,
                        "nbr_vote": 0,
                        "id": 2,
                        "added": self.simple_user_comment.added,
                        "nbr_child": 1,
                    },
                ],
                cls=DjangoJSONEncoder,
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.content.decode("UTF-8"),
            expected_response.content.decode("UTF-8"),
        )

    def test_get_comment_with_children(self):
        url = reverse(
            "video:get_comment",
            kwargs={
                "comment_id": self.admin_comment.id,
                "video_slug": self.video.slug,
            },
        )
        response = self.client.get(url, headers={"accept": "application/json"})
        self.assertEqual(response.resolver_match.func, get_children_comment)
        # Check response is 200 OK and contents the expected comment
        owner_user_full_name = "{0} {1}".format(
            self.owner_user.first_name, self.owner_user.last_name
        )
        direct_parent_id = self.owner_to_admin_comment.direct_parent.id
        expected_response = HttpResponse(
            json.dumps(
                {
                    "author_name": "Super User",
                    "content": "Admin parent comment",
                    "is_owner": False,
                    "nbr_vote": 0,
                    "id": self.admin_comment.id,
                    "added": self.admin_comment.added,
                    "nbr_child": 1,
                    "children": [
                        {
                            "id": self.owner_to_admin_comment.id,
                            "parent__id": self.owner_to_admin_comment.parent.id,
                            "direct_parent__id": direct_parent_id,
                            "author_name": owner_user_full_name,
                            "content": self.owner_to_admin_comment.content,
                            "is_owner": False,
                            "nbr_vote": 0,
                            "added": self.owner_to_admin_comment.added,
                        }
                    ],
                },
                cls=DjangoJSONEncoder,
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.content.decode("UTF-8"),
            expected_response.content.decode("UTF-8"),
        )

    def test_add_comment(self):
        """Test add parent comment."""
        pk = Comment.objects.all().count() + 1
        url = reverse("video:add_comment", kwargs={"video_slug": self.video.slug})
        self.client.logout()
        self.client.force_login(self.simple_user)
        response = self.client.post(
            url, {"content": "Third parent comment"}, **self.ajax_header
        )
        data = {
            "author_name": "{0} {1}".format(
                self.simple_user.first_name, self.simple_user.last_name
            ),
            "id": pk,
        }
        expected_content = JsonResponse(data, safe=False).content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func, add_comment)

        resp_content = response.content.decode("UTF-8")
        resp_content = ast.literal_eval(resp_content)

        exp_content = expected_content.decode("UTF-8")
        exp_content = ast.literal_eval(exp_content)

        self.assertEqual(resp_content, exp_content)
        p_comment = Comment.objects.get(id=pk)
        self.assertIsNone(p_comment.parent)

        # test add child comment
        pk = Comment.objects.all().count() + 1
        url = reverse(
            "video:add_child_comment",
            kwargs={"video_slug": self.video.slug, "comment_id": p_comment.id},
        )
        self.client.logout()
        self.client.force_login(self.owner_user)
        response = self.client.post(
            url, {"content": "Response to third comment"}, **self.ajax_header
        )
        data["author_name"] = "{0} {1}".format(
            self.owner_user.first_name, self.owner_user.last_name
        )
        data["id"] = pk
        expected_content = JsonResponse(data, safe=False).content

        resp_content = response.content.decode("UTF-8")
        resp_content = ast.literal_eval(resp_content)

        exp_content = expected_content.decode("UTF-8")
        exp_content = ast.literal_eval(exp_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func, add_comment)
        self.assertEqual(resp_content, exp_content)
        comment = Comment.objects.get(id=pk)
        self.assertEqual(comment.parent, p_comment)

        # test bad request
        self.client.logout()
        self.client.force_login(self.owner_user)
        response = self.client.post(url, HTTP_ACCEPT_LANGUAGE="en", **self.ajax_header)
        self.assertContains(response, b"<h1>Bad Request</h1>", status_code=400)

        # test method not allowed
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en", **self.ajax_header)
        self.assertContains(response, b"<h1>Method Not Allowed</h1>", status_code=405)

    def test_delete_comment(self):
        """simple_user cannot delete a comment that does not belongs to him."""
        url = reverse(
            "video:delete_comment",
            kwargs={
                "video_slug": self.video.slug,
                "comment_id": self.owner_to_admin_comment.id,
            },
        )
        self.client.logout()
        self.client.force_login(self.simple_user)
        response = self.client.post(url, HTTP_ACCEPT_LANGUAGE="en", **self.ajax_header)
        data = {
            "deleted": False,
            "message": "You do not have rights to delete this comment",
        }
        expected_content = JsonResponse(data, safe=False).content
        self.assertEqual(response.resolver_match.func, delete_comment)
        self.assertEqual(response.content, expected_content)
        # video owner can delete any comment
        url = reverse(
            "video:delete_comment",
            kwargs={
                "video_slug": self.video.slug,
                "comment_id": self.admin_comment.id,
            },
        )
        data = {"deleted": True, "comment_deleted": str(self.admin_comment.id)}
        expected_content = JsonResponse(data, safe=False).content
        self.client.logout()
        self.client.force_login(self.owner_user)
        response = self.client.post(url, **self.ajax_header)
        self.assertEqual(response.content, expected_content)
        # should also remove child comment
        comment = Comment.objects.filter(id=self.owner_to_admin_comment.id).first()
        self.assertIsNone(comment)
        # Admin user can delete any comment
        url = reverse(
            "video:delete_comment",
            kwargs={
                "video_slug": self.video.slug,
                "comment_id": self.simple_user_comment.id,
            },
        )
        data = {
            "deleted": True,
            "comment_deleted": str(self.simple_user_comment.id),
        }
        expected_content = JsonResponse(data, safe=False).content
        self.client.logout()
        self.client.force_login(self.admin_user)
        response = self.client.post(url, **self.ajax_header)
        self.assertEqual(response.content, expected_content)
        comment = Comment.objects.filter(id=self.owner_to_simple_user_comment.id).first()
        self.assertIsNone(comment)

    def test_get_votes(self):
        """VOTE TEST."""
        url = reverse("video:get_votes", kwargs={"video_slug": self.video.slug})
        self.client.logout()
        self.client.force_login(self.owner_user)
        response = self.client.get(url)
        data = {"comments_votes": []}
        expected_response = JsonResponse(data, safe=False).content
        self.assertEqual(response.content, expected_response)

        # test vote +1
        url = reverse(
            "video:add_vote",
            kwargs={
                "video_slug": self.video.slug,
                "comment_id": self.admin_comment.id,
            },
        )
        response = self.client.post(url, **self.ajax_header)
        data = {"voted": True}
        expected_response = JsonResponse(data, safe=False).content
        self.assertEqual(response.content, expected_response)

        # test vote -1
        response = self.client.post(url, **self.ajax_header)
        data["voted"] = False
        expected_response = JsonResponse(data, safe=False).content
        self.assertEqual(response.content, expected_response)

        # test method not allowed
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en", **self.ajax_header)
        self.assertContains(response, b"<h1>Method Not Allowed</h1>", status_code=405)

    def test_comment_without_ajax(self):
        """Verify that Pod will refuse a comment request done without AJAX http header."""
        # Ensure that comment owner is logged
        self.client.logout()
        self.client.force_login(self.owner_user)

        # Vote +1
        url = reverse(
            "video:add_vote",
            kwargs={
                "video_slug": self.video.slug,
                "comment_id": self.admin_comment.id,
            },
        )
        response = self.client.post(url)
        # Check that the response is 403 Forbidden.
        self.assertEqual(response.status_code, 403)

        # Delete comment
        url = reverse(
            "video:delete_comment",
            kwargs={
                "video_slug": self.video.slug,
                "comment_id": self.owner_to_admin_comment.id,
            },
        )
        response = self.client.post(url)
        # Check that the response is 403 Forbidden.
        self.assertEqual(response.status_code, 403)

        # Add a comment
        url = reverse("video:add_comment", kwargs={"video_slug": self.video.slug})
        response = self.client.post(url, {"content": "New parent comment"})
        # Check that the response is 403 Forbidden.
        self.assertEqual(response.status_code, 403)

    def tearDown(self):
        """Cleanup all created stuffs."""
        del self.video
        del self.owner_user
        del self.admin_user
        del self.simple_user
        del self.admin_comment
        del self.simple_user_comment
        del self.owner_to_admin_comment
        del self.owner_to_simple_user_comment
        del self.client
        del self.t1
