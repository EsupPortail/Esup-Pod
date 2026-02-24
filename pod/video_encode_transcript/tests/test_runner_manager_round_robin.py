"""
Runner manager round-robin ordering tests for Esup-Pod.

Run with `python manage.py test pod.video_encode_transcript.tests.test_runner_manager_round_robin`
"""

from django.contrib.sites.models import Site
from django.test import TestCase

from pod.video_encode_transcript.models import RunnerManager, Task
from pod.video_encode_transcript.runner_manager import _get_runner_managers


class RunnerManagerRoundRobinTests(TestCase):
    """Validate runner manager ordering and per-priority group rotation."""

    def setUp(self) -> None:
        """Ensure a site exists for runner manager associations."""
        self.site = Site.objects.filter(pk=1).first()
        if self.site is None:
            self.site = Site.objects.create(domain="example.com", name="example.com")

    def test_get_runner_managers_initial_order_when_no_history(self):
        """Keep creation order inside each priority level when no history exists."""
        rm1 = RunnerManager.objects.create(
            name="rm-1",
            priority=1,
            url="https://rr-initial-1.example.com/",
            token="token-1",
            site=self.site,
        )
        rm2 = RunnerManager.objects.create(
            name="rm-2",
            priority=1,
            url="https://rr-initial-2.example.com/",
            token="token-2",
            site=self.site,
        )
        rm3 = RunnerManager.objects.create(
            name="rm-3",
            priority=2,
            url="https://rr-initial-3.example.com/",
            token="token-3",
            site=self.site,
        )

        ordered_ids = [rm.id for rm in _get_runner_managers(self.site)]

        self.assertEqual(ordered_ids, [rm1.id, rm2.id, rm3.id])

    def test_get_runner_managers_rotates_same_priority_group(self):
        """Rotate only managers of the same priority after each running task."""
        rm1 = RunnerManager.objects.create(
            name="rm-a",
            priority=1,
            url="https://rr-rotate-a.example.com/",
            token="token-a",
            site=self.site,
        )
        rm2 = RunnerManager.objects.create(
            name="rm-b",
            priority=1,
            url="https://rr-rotate-b.example.com/",
            token="token-b",
            site=self.site,
        )

        Task.objects.create(type="encoding", status="running", runner_manager=rm1)
        ordered_after_rm1 = [rm.id for rm in _get_runner_managers(self.site)]
        self.assertEqual(ordered_after_rm1, [rm2.id, rm1.id])

        Task.objects.create(type="encoding", status="running", runner_manager=rm2)
        ordered_after_rm2 = [rm.id for rm in _get_runner_managers(self.site)]
        self.assertEqual(ordered_after_rm2, [rm1.id, rm2.id])

    def test_get_runner_managers_rotates_each_priority_group_independently(self):
        """Rotate each priority group independently based on its own task history."""
        rm1 = RunnerManager.objects.create(
            name="rm-p1-a",
            priority=1,
            url="https://rr-group-p1-a.example.com/",
            token="token-p1-a",
            site=self.site,
        )
        rm2 = RunnerManager.objects.create(
            name="rm-p1-b",
            priority=1,
            url="https://rr-group-p1-b.example.com/",
            token="token-p1-b",
            site=self.site,
        )
        rm3 = RunnerManager.objects.create(
            name="rm-p2-a",
            priority=2,
            url="https://rr-group-p2-a.example.com/",
            token="token-p2-a",
            site=self.site,
        )
        rm4 = RunnerManager.objects.create(
            name="rm-p2-b",
            priority=2,
            url="https://rr-group-p2-b.example.com/",
            token="token-p2-b",
            site=self.site,
        )

        Task.objects.create(type="encoding", status="running", runner_manager=rm1)
        Task.objects.create(type="encoding", status="running", runner_manager=rm3)

        ordered_ids = [rm.id for rm in _get_runner_managers(self.site)]

        self.assertEqual(ordered_ids, [rm2.id, rm1.id, rm4.id, rm3.id])
