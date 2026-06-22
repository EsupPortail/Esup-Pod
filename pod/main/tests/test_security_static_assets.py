"""
Esup-Pod security regression tests for frontend assets.
*  run with 'python manage.py test pod.main.tests.test_security_static_assets'
"""

import unittest
from pathlib import Path


class FrontendSecurityAssetsTests(unittest.TestCase):
    """Ensure high-risk frontend security fixes remain in place."""

    def _read_asset(self, relative_path: str) -> str:
        """Read a frontend asset from the repository."""
        project_root = Path(__file__).resolve().parents[3]
        return (project_root / relative_path).read_text(encoding="utf-8")

    def test_filewidget_avoids_html_string_injection_for_preview(self):
        """Test that file preview rendering uses DOM APIs and URL sanitization."""
        script = self._read_asset("pod/podfile/static/podfile/js/filewidget.js")
        self.assertIn("function sanitizePreviewUrl(url)", script)
        self.assertIn("fileInputContainer.appendChild(buildFilePreview(file));", script)
        self.assertNotIn(
            'document.getElementById("fileinput_" + id_input).innerHTML = html;',
            script,
        )
        self.assertNotIn(".innerHTML += (", script)

    def test_aside_filters_submit_with_small_buttons_without_js_redirect(self):
        """Test that sidebar filters keep explicit submit without inline JS."""
        template = self._read_asset("pod/main/templates/aside.html")
        self.assertNotIn("onchange=", template)
        self.assertNotIn('onchange="this.form.submit();"', template)
        self.assertNotIn("window.location = this.options[this.selectedIndex]", template)
        self.assertNotIn("data-value=", template)
        self.assertIn('name="discipline"', template)
        self.assertIn('name="type"', template)
        self.assertIn('type="submit"', template)
        self.assertIn("btn btn-primary btn-sm", template)
