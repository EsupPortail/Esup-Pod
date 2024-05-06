"""Esup-Pod unit tests for utility functions.

*  run with 'python manage.py test pod.main.tests.test_utils'
"""

from django.test import TestCase
from pod.main import utils


class MainUtilsTestCase(TestCase):
    """Main utilities test cases."""

    def setUp(self) -> None:
        """Set up main utils test case."""
        print(" --->  SetUp of MainUtilsTestCase: OK!")

    def test_sizeof_fmt(self) -> None:
        """Test the return of sizeof_fmt."""
        size = 4000
        attended = "3.9KiB"
        got = utils.sizeof_fmt(size)
        self.assertEqual(attended, got)
        print(" --->  test_sizeof_fmt OK.")

    def test_generate_qrcode(self) -> None:
        """Test the return of generate_qrcode."""
        alt = "test QR code"
        url = "https://pod.univ.fr"
        start_attended = '<img id="qrcode" src="data:image/png;base64, '
        end_attended = 'width="200px" height="200px" alt="test QR code">'
        got = utils.generate_qrcode(url, alt, None)
        self.assertEqual(start_attended, got[: len(start_attended)])
        self.assertEqual(end_attended, got[-len(end_attended) :])
        print(" --->  test_generate_qrcode OK.")
