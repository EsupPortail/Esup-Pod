"""Unit tests for speaker views."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from pod.speaker.models import Speaker, Job

# ggignore-start
# gitguardian:ignore
PWD = "thisisnotpassword"
# ggignore-end


class SpeakerViewsTest(TestCase):
    """Test case for speaker views."""

    def setUp(self):
        """Set up the test environment."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="admin", password=PWD, email="admin@example.com"
        )
        self.user = User.objects.create_user(username="user", password=PWD)
        self.speaker = Speaker.objects.create(firstname="John", lastname="Doe")
        self.job = Job.objects.create(title="Engineer", speaker=self.speaker)

    def test_speaker_management_superuser_get(self):
        """Test GET request to speaker management by a superuser."""
        self.client.login(username="admin", password=PWD)
        response = self.client.get(reverse("speaker:speaker_management"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "speaker/speakers_management.html")

    def test_speaker_management_non_superuser_get(self):
        """Test GET request to speaker management by a non-superuser."""
        self.client.login(username="user", password=PWD)
        response = self.client.get(reverse("speaker:speaker_management"))
        self.assertEqual(response.status_code, 403)

    def test_add_speaker(self):
        """Test adding a new speaker."""
        self.client.login(username="admin", password=PWD)
        data = {
            "action": "add",
            "firstname": "Jane",
            "lastname": "Smith",
            "jobs[]": ["Teacher", "Researcher"],
        }
        url = reverse("speaker:speaker_management")
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("speaker:speaker_management"))
        self.assertTrue(
            Speaker.objects.filter(firstname="Jane", lastname="Smith").exists()
        )
        speaker = Speaker.objects.get(firstname="Jane", lastname="Smith")
        self.assertEqual(speaker.job_set.count(), 2)

    def test_delete_speaker(self):
        """Test deleting a speaker."""
        self.client.login(username="admin", password=PWD)
        data = {
            "action": "delete",
            "speakerid": self.speaker.id,
        }
        response = self.client.post(reverse("speaker:speaker_management"), data)
        self.assertRedirects(response, reverse("speaker:speaker_management"))
        self.assertFalse(Speaker.objects.filter(id=self.speaker.id).exists())

    def test_edit_speaker(self):
        """Test editing a speaker."""
        self.client.login(username="admin", password=PWD)
        data = {
            "action": "edit",
            "speakerid": self.speaker.id,
            "firstname": "Johnny",
            "lastname": "Doe",
            "jobIds[]": [self.job.id],
            "jobs[]": ["Senior Engineer"],
        }
        response = self.client.post(reverse("speaker:speaker_management"), data)
        self.assertRedirects(response, reverse("speaker:speaker_management"))
        speaker = Speaker.objects.get(id=self.speaker.id)
        self.assertEqual(speaker.firstname, "Johnny")
        self.assertEqual(speaker.job_set.count(), 1)
        self.assertEqual(speaker.job_set.first().title, "Senior Engineer")

    def test_get_speaker(self):
        """Test retrieving a speaker's details."""
        self.client.login(username="admin", password=PWD)
        response = self.client.get(reverse("speaker:get_speaker", args=[self.speaker.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "speaker": {
                    "id": self.speaker.id,
                    "firstname": self.speaker.firstname,
                    "lastname": self.speaker.lastname,
                    "jobs": [{"id": self.job.id, "title": self.job.title}],
                }
            },
        )

    def test_get_jobs(self):
        """Test retrieving jobs for a speaker."""
        self.client.login(username="admin", password=PWD)
        response = self.client.get(reverse("speaker:get_jobs", args=[self.speaker.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"jobs": [{"id": self.job.id, "title": self.job.title}]}
        )
