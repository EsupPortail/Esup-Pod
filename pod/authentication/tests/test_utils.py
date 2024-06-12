"""Test authentication utils."""

import json

from django.test import TestCase
from django.contrib.auth.models import User
from pod.authentication.utils import get_owners


class UserTestUtils(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        self.admin = User.objects.create(
            first_name="pod",
            last_name="Admin",
            username="admin",
            password="admin1234admin",
            is_superuser=True,
        )
        self.simple_user = User.objects.create(
            first_name="Pod", last_name="User", username="pod", password="pod1234pod"
        )
        print(" --->  SetUp of VideoTestFiltersViews: OK!")

    def test_get_owners(self) -> None:
        # Search with common word
        actual = get_owners("pod", 12, 0)
        expected = [
            {
                "id": self.admin.id,
                "first_name": self.admin.first_name,
                "last_name": self.admin.last_name,
            },
            {
                "id": self.simple_user.id,
                "first_name": self.simple_user.first_name,
                "last_name": self.simple_user.last_name,
            },
        ]
        self.assertEqual(json.loads(actual.content.decode("utf-8")), expected)

        # Search with common word and limit and offset
        actual = get_owners("pod", 1, 1)
        expected = [
            {
                "id": self.simple_user.id,
                "first_name": self.simple_user.first_name,
                "last_name": self.simple_user.last_name,
            },
        ]
        self.assertEqual(json.loads(actual.content.decode("utf-8")), expected)

        # Search spécific user
        actual = get_owners("admin pod", 1, 0)
        expected = [
            {
                "id": self.admin.id,
                "first_name": self.admin.first_name,
                "last_name": self.admin.last_name,
            },
        ]
        self.assertEqual(json.loads(actual.content.decode("utf-8")), expected)
        actual = get_owners("pod admin", 1, 0)
        self.assertEqual(json.loads(actual.content.decode("utf-8")), expected)

        # Not found
        actual = get_owners("not exists", 1, 0)
        expected = []
        self.assertEqual(json.loads(actual.content.decode("utf-8")), expected)
