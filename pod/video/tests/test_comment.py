from django.http import JsonResponse
from django.test import TestCase, Client
from django.urls import reverse
from pod.authentication.models import User
from pod.video.models import Comment, Video, Type
from django.contrib.sites.models import Site
from pod.video.views import get_comments, add_comment, delete_comment
import ast

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
                title="Test comment video",
                is_draft=False,
                encoding_in_progress=False,
                owner=self.owner_user,
                video="testvideocomment.mp4",
                type=self.t1)
        self.admin_comment = Comment.objects.create(
                author=self.admin_user,
                content="Admin parent comment",
                video=self.video)
        self.simple_user_comment = Comment.objects.create(
                author=self.simple_user,
                content="Simple user parent comment",
                video=self.video)
        self.owner_responds_admin_comment = Comment.objects.create(
                author=self.owner_user,
                content="Video owner responds to admin parent comment",
                video=self.video,
                parent=self.admin_comment)
        self.owner_responds_simple_user_comment = Comment.objects.create(
                author=self.owner_user,
                content="Video owner responds to simple user parent comment",
                video=self.video,
                parent=self.simple_user_comment)

        self.owner_user.owner.sites.add(Site.objects.get_current())
        self.owner_user.owner.save()

        self.simple_user.owner.sites.add(Site.objects.get_current())
        self.simple_user.owner.save()

        self.admin_user.owner.sites.add(Site.objects.get_current())
        self.admin_user.owner.save()

    def test_get_all_comment(self):
        url = reverse(
                "get_comments",
                kwargs={"video_slug": self.video.slug})
        response = self.client.get(url)
        # Check that the view function is get_comments
        self.assertEqual(response.resolver_match.func, get_comments)
        # Check response is 200 OK and contents the expected comment
        self.assertContains(
                response,
                self.owner_responds_admin_comment.content.encode("utf-8"),
                status_code=200)
        self.assertContains(
                response,
                self.simple_user_comment.content.encode("utf-8"))

    def test_add_comment(self):
        # test add parent comment
        pk = Comment.objects.all().count() + 1
        url = reverse(
                "add_comment",
                kwargs={"video_slug": self.video.slug})
        self.client.logout()
        self.client.force_login(self.simple_user)
        response = self.client.post(url, {
            "content": "Third parent comment"})
        data = {
            "author__last_name": self.simple_user.last_name,
            "author__first_name": self.simple_user.first_name,
            "id": pk
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
                "add_child_comment",
                kwargs={
                    "video_slug": self.video.slug,
                    "comment_id": p_comment.id})
        self.client.logout()
        self.client.force_login(self.owner_user)
        response = self.client.post(url, {
            "content": "Response to third comment"})
        data['author__last_name'] = self.owner_user.last_name
        data['author__first_name'] = self.owner_user.first_name
        data['id'] = pk
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
        response = self.client.post(
                url,
                HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(
                response,
                b"<h1>Bad Request</h1>",
                status_code=400)

        # test method not allowed
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(
                response,
                b"<h1>Method Not Allowed</h1>",
                status_code=405)

    def test_delete_comment(self):
        # simple_user cannot delete a comment that does not belongs to him
        url = reverse(
                "delete_comment",
                kwargs={
                    "video_slug": self.video.slug,
                    "comment_id": self.owner_responds_admin_comment.id})
        self.client.logout()
        self.client.force_login(self.simple_user)
        response = self.client.post(
                url,
                HTTP_ACCEPT_LANGUAGE="en")
        data = {
                "deleted": False,
                "message": "You do not have right to delete this comment"}
        expected_content = JsonResponse(data, safe=False).content
        self.assertEqual(response.resolver_match.func, delete_comment)
        self.assertEqual(response.content, expected_content)
        # video owner can delete any comment
        url = reverse(
                "delete_comment",
                kwargs={
                    "video_slug": self.video.slug,
                    "comment_id": self.admin_comment.id})
        data = {
                "deleted": True,
                "comment_deleted": str(self.admin_comment.id)}
        expected_content = JsonResponse(data, safe=False).content
        self.client.logout()
        self.client.force_login(self.owner_user)
        response = self.client.post(url)
        self.assertEqual(response.content, expected_content)
        # should also remove child comment
        comment = Comment.objects.filter(
                id=self.owner_responds_admin_comment.id).first()
        self.assertIsNone(comment)
        # Admin user can delete any comment
        url = reverse(
                "delete_comment",
                kwargs={
                    "video_slug": self.video.slug,
                    "comment_id": self.simple_user_comment.id})
        data = {
                "deleted": True,
                "comment_deleted": str(self.simple_user_comment.id)}
        expected_content = JsonResponse(data, safe=False).content
        self.client.logout()
        self.client.force_login(self.admin_user)
        response = self.client.post(url)
        self.assertEqual(response.content, expected_content)
        comment = Comment.objects.filter(
                id=self.owner_responds_simple_user_comment.id).first()
        self.assertIsNone(comment)

    """
    " VOTE TEST
    """
    def test_get_votes(self):
        url = reverse(
                "get_votes",
                kwargs={"video_slug": self.video.slug})
        self.client.logout()
        self.client.force_login(self.owner_user)
        response = self.client.get(url)
        data = {"votes": []}
        expected_response = JsonResponse(data, safe=False).content
        self.assertEqual(response.content, expected_response)

        # test vote +1
        url = reverse(
                "add_vote",
                kwargs={
                    "video_slug": self.video.slug,
                    "comment_id": self.admin_comment.id})
        response = self.client.post(url)
        data = {"voted": True}
        expected_response = JsonResponse(data, safe=False).content
        self.assertEqual(response.content, expected_response)

        # test vote -1
        response = self.client.post(url)
        data['voted'] = False
        expected_response = JsonResponse(data, safe=False).content
        self.assertEqual(response.content, expected_response)

        # test method not allowed
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(
                response,
                b"<h1>Method Not Allowed</h1>",
                status_code=405)

    def tearDown(self):
        del self.video
        del self.owner_user
        del self.admin_user
        del self.simple_user
        del self.admin_comment
        del self.simple_user_comment
        del self.owner_responds_admin_comment
        del self.owner_responds_simple_user_comment
        del self.client
        del self.t1
