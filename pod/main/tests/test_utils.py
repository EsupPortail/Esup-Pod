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
        attended = (
            "<img id=\"qrcode\" src=\"data:image/png;base64, "
            "iVBORw0KGgoAAAANSUhEUgAAAXIAAAFyAQAAAADAX2ykAAACdUlEQVR4nO2bTWrkMBBGX40NvVTDHK"
            "CPYt9gjhTmSLlB60AN1jJg881CkvsHQghxO9FQtVBj+y0Kiip9qlKb+IzFX5/CwXnnnXfeeeedf4+3"
            "Yj1EM7ORxYDFINVv447+OL8V3+ef4QyQfmPDo+DqZgBsH3+cfw6fSobqr5lB6gE62QjkxN7XH+efxA"
            "8TEE8z5Pr83f44/yW+f3g26GaDHuKfCyLt64/zz+GDpDOQF02UTAaQNO/tj/Ob8tHMzI5gLxPYSCcb"
            "00E2smT5vK8/zm/E5/p81cyCN4MwQzy9GYR7Pf3T/Hf+A5MkMUxdXiTNa0HuVL7md5LOP81/5z8wFZ"
            "vJYTzTSedQ3kJ9ZPD4NsjXvAyrggozOZ0JKsswgce3Sf7mfCQAG14PIh47IBnA0iue5l77+OP8tvzt"
            "/gtlkaZOpVIDObs9f1vkV/38ZlUoL8bwSu5EW+4/p4O8/9wkn+NrhEnEESBcesXTjOJxghxuLX7+bZ"
            "O/18+1iaWspGv1Jvj5qGne7AiQeuyl9iJtDDM2pj63K23c0R/nt+LvzkehZG05Gt3JLddXTfKP+rnE"
            "cm1nrYH3+DbJ1/ylNDTqEKnLu25Gzr7/tsrX/FXtWg1TnQ+u8c2p6/Ftl69d5zJVsJHupit5vb3zU/"
            "13/l2rYwSA2rAqlfqmE+37b6P8Wp9VupLX4zAU1ez1uX2+VuByEl7LdcxXNxavz/8Hr3Mqd3FshDwT"
            "/k5/nN+WL/evUg/DtFjejqMd9A7/bH+c/xpf579BQAKRujnff47HC0a4IFjM579N8o/6ub67XudYlb"
            "TrqwZ508fMjfn/u5133nnnnXd+A/4f0cHNpt8hpEYAAAAASUVORK5CYII=\" "
            "width=\"200px\" height=\"200px\" alt=\"test QR code\">")
        print(attended)
        got = utils.generate_qrcode(url, alt, None)
        print(got)
        self.assertEqual(attended, got)
        print(" --->  test_generate_qrcode OK.")
