"""Unit tests for Esup-Pod dressing utilities."""

import os
import unittest
from unittest.mock import patch
from django.contrib.auth.models import User
from pod.authentication.models import AccessGroup
from pod.dressing.utils import get_dressings, get_position_value, get_dressing_input
from pod.dressing.models import Dressing


class DressingUtilitiesTests(unittest.TestCase):
    """TestCase for Esup-Pod dressing utilities."""

    def test_get_position_value(self):
        """Test for the get_position_value function."""
        result = get_position_value("top_right", "720")
        self.assertEqual(result, "overlay=main_w-overlay_w-36.0:36.0")

        result = get_position_value("top_left", "720")
        self.assertEqual(result, "overlay=36.0:36.0")

        result = get_position_value("bottom_right", "720")
        self.assertEqual(result, "overlay=main_w-overlay_w-36.0:main_h-overlay_h-36.0")

        result = get_position_value("bottom_left", "720")
        self.assertEqual(result, "overlay=36.0:main_h-overlay_h-36.0")

        print(" ---> test_get_position_value: OK! --- DressingUtilsTest")

    def test_get_dressing_input(self):
        """Test for the get_dressing_input function"""

        dressing = Dressing(watermark=None, opening_credits=None, ending_credits=None)

        FFMPEG_DRESSING_INPUT = "input=%s"

        with patch("os.path.join", side_effect=os.path.join):
            result = get_dressing_input(dressing, FFMPEG_DRESSING_INPUT)

        self.assertIn("", result)

        print(" ---> test_get_dressing_input: OK! --- DressingUtilsTest")

    def test_get_dressings(self):
        """Test for the get_dressings function."""
        user = User.objects.create_user(username="user", password="password", is_staff=1)
        access_group = AccessGroup.objects.create(
            code_name="group1", display_name="Group 1"
        )

        dressing1 = Dressing.objects.create(title="Dressing 1")
        dressing1.owners.add(user.id)

        dressing2 = Dressing.objects.create(title="Dressing 2")
        dressing2.users.add(user.id)

        dressing3 = Dressing.objects.create(title="Dressing 3")
        dressing3.allow_to_groups.add(access_group)

        dressings = get_dressings(user.id, [access_group])

        self.assertIn(dressing1, dressings)
        self.assertIn(dressing2, dressings)
        self.assertIn(dressing3, dressings)

        self.assertEqual(len(dressings), 3)

        print(" ---> test_get_dressings: OK! --- DressingUtilsTest")

    def test_get_dressings_empty(self):
        """Test for the get_dressings_empty function."""
        new_user = User.objects.create_user(username="newuser", password="newpassword")

        dressings = get_dressings(new_user, [])

        self.assertEqual(len(dressings), 0)

        print(" ---> test_get_dressings_empty: OK! --- DressingUtilsTest")
