"""Esup-Pod security tests for path handling in Encoding_video_model."""

import os
import tempfile

from django.test import SimpleTestCase

from pod.video_encode_transcript.Encoding_video_model import Encoding_video_model


class EncodingVideoModelPathSecurityTests(SimpleTestCase):
    """Ensure file paths used by the encoder stay inside the output directory."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.video_file = os.path.join(self.temp_dir.name, "video.mp4")
        self.encoder = Encoding_video_model(id=7, video_file=self.video_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_safe_output_path_accepts_path_inside_output_dir(self):
        path = os.path.join(self.temp_dir.name, "0007", "info_video.json")
        self.assertEqual(self.encoder._safe_output_path(path), os.path.realpath(path))

    def test_safe_output_path_rejects_path_outside_output_dir(self):
        path = os.path.join(self.temp_dir.name, "..", "escape.json")
        with self.assertRaises(ValueError):
            self.encoder._safe_output_path(path)
