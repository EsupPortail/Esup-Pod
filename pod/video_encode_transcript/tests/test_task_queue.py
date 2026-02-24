"""
Task queue ranking and lookup tests for Esup-Pod.

Run with `python manage.py test pod.video_encode_transcript.tests.test_task_queue`
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.utils import timezone

from pod.video.models import Type, Video
from pod.video_encode_transcript.models import Task
from pod.video_encode_transcript.task_queue import (
    get_video_pending_encoding_queue_info,
    refresh_pending_task_ranks,
)

# ggignore-start
# gitguardian:ignore
PWD = "azerty1234"  # nosec
# ggignore-end


class TaskQueueTests(TestCase):
    """Validate queue rank computation and pending-queue lookup behavior."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Create users/videos with different affiliations used by ranking tests."""
        self.site = Site.objects.get(id=1)
        self.teacher = User.objects.create(username="teacher", password=PWD)  # nosem
        self.student = User.objects.create(username="student", password=PWD)  # nosem

        self.teacher.owner.affiliation = "faculty"
        self.teacher.owner.sites.add(Site.objects.get_current())
        self.teacher.owner.save()

        self.student.owner.affiliation = "student"
        self.student.owner.sites.add(Site.objects.get_current())
        self.student.owner.save()

        video_type = Type.objects.get(id=1)
        self.teacher_video = Video.objects.create(
            title="Teacher video",
            owner=self.teacher,
            video="teacher.mp4",
            type=video_type,
        )
        self.teacher_video.sites.add(self.site)

        self.student_video = Video.objects.create(
            title="Student video",
            owner=self.student,
            video="student.mp4",
            type=video_type,
        )
        self.student_video.sites.add(self.site)

    def test_refresh_pending_task_ranks_applies_priority(self):
        """Order pending tasks using affiliation priority and creation time."""
        base_time = timezone.now() - timedelta(hours=1)
        student_task = Task.objects.create(
            video=self.student_video,
            type="encoding",
            status="pending",
            date_added=base_time,
        )
        teacher_task = Task.objects.create(
            video=self.teacher_video,
            type="encoding",
            status="pending",
            date_added=base_time + timedelta(minutes=5),
        )
        studio_task = Task.objects.create(
            type="studio",
            status="pending",
            date_added=base_time + timedelta(minutes=10),
        )

        refresh_pending_task_ranks()

        teacher_task.refresh_from_db()
        studio_task.refresh_from_db()
        student_task.refresh_from_db()

        self.assertEqual(teacher_task.rank, 1)
        self.assertEqual(studio_task.rank, 2)
        self.assertEqual(student_task.rank, 3)

    def test_refresh_pending_task_ranks_clears_non_pending_rank(self):
        """Clear rank values on tasks that are no longer pending."""
        running_task = Task.objects.create(
            video=self.teacher_video,
            type="encoding",
            status="running",
            rank=9,
        )
        Task.objects.create(
            video=self.student_video,
            type="encoding",
            status="pending",
        )

        refresh_pending_task_ranks()
        running_task.refresh_from_db()

        self.assertIsNone(running_task.rank)

    def test_get_video_pending_encoding_queue_info_returns_rank_and_total(self):
        """Return the expected rank and pending total for a given video."""
        teacher_task = Task.objects.create(
            video=self.teacher_video,
            type="encoding",
            status="pending",
        )
        student_task = Task.objects.create(
            video=self.student_video,
            type="encoding",
            status="pending",
        )
        Task.objects.create(
            video=self.teacher_video,
            type="encoding",
            status="running",
        )

        refresh_pending_task_ranks()
        rank, total = get_video_pending_encoding_queue_info(self.student_video)

        teacher_task.refresh_from_db()
        student_task.refresh_from_db()

        self.assertEqual(teacher_task.rank, 1)
        self.assertEqual(student_task.rank, 2)
        self.assertEqual(rank, 2)
        self.assertEqual(total, 2)
