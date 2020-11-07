from django.http import JsonResponse
from django.test import TestCase, Client
from django.urls import reverse
from pod.authentication.models import User
from pod.video.models import Category, Video, Type
from django.contrib.sites.models import Site
from pod.video.views import get_categories, add_category
from pod.video.views import edit_category, delete_category
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
                title="Test category video",
                is_draft=False,
                encoding_in_progress=False,
                owner=self.owner_user,
                video="testvideocategory.mp4",
                type=self.t1)

    def tearDown(self):
        del self.video
        del self.owner_user
        del self.admin_user
        del self.simple_user
        del self.client
        del self.t1
