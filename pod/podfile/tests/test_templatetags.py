"""Unit tests for Podfile template filters."""

from django.test import SimpleTestCase

from ..templatetags.podfile_filters import file_basename
from ..templatetags.podfile_filters import file_extension
from ..templatetags.podfile_filters import icon_exists


class PodfileFiltersTestCase(SimpleTestCase):
    """Test file-name, extension and icon selection helpers."""

    def test_file_basename_keeps_extension(self) -> None:
        self.assertEqual(file_basename("files/user/my-caption.vtt"), "my-caption.vtt")

    def test_file_extension_is_normalized(self) -> None:
        self.assertEqual(file_extension("files/user/document.ODT"), "odt")
        self.assertEqual(file_extension("files/user/README"), "")

    def test_dedicated_open_document_and_vtt_icons_exist(self) -> None:
        for extension in ("vtt", "odt", "ods", "odp"):
            with self.subTest(extension=extension):
                self.assertEqual(icon_exists(f"file.{extension}"), extension)

    def test_unknown_extension_uses_default_icon(self) -> None:
        self.assertEqual(icon_exists("file.unknown"), "default")
