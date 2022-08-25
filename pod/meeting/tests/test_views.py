from django.test import TestCase
from django.contrib.auth.models import User


class meeting_TestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        User.objects.create(username="pod", password="pod1234pod")
        print(" --->  SetUp of meeting_TestView: OK!")
