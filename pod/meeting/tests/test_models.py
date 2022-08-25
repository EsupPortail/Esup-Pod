from django.test import TestCase
from django.contrib.auth.models import User

from ..models import Meeting


class MeetingTestCase(TestCase):

    def setUp(self):
        user = User.objects.create(username="pod")
        Meeting.objects.create(name='test', owner=user)

    def test_attributs(self):
        meeting1 = Meeting.objects.get(id=1)
        self.assertEqual(meeting1.name, "test")
        print("   --->  test_attributs of RecorderTestCase: OK !")
