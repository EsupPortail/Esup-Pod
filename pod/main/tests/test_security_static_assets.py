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

    def test_showalert_renders_messages_as_text(self):
        """Alert messages must not be reparsed as arbitrary HTML."""
        script = self._read_asset("pod/main/static/js/main.js")
        self.assertIn("document.createTextNode(line)", script)
        self.assertNotIn("new DOMParser().parseFromString(textHtml", script)
        self.assertNotIn("'<span class=\"alert-message\">' +", script)

    def test_caption_parser_does_not_use_a_filtering_regexp(self):
        """Caption markup is stripped by the browser WebVTT parser."""
        script = self._read_asset("pod/completion/static/js/caption_maker.js")
        self.assertIn("new VTTCue(0, 1, String(line))", script)
        self.assertIn("cue.getCueAsHTML().textContent", script)
        self.assertNotIn('replace(/[<>]/g, "")', script)

    def test_video_theme_data_and_labels_are_not_interpreted_as_html(self):
        """Theme JSON and DOM-derived labels must use safe browser primitives."""
        main_script = self._read_asset("pod/main/static/js/main.js")
        for template_path in (
            "pod/video/templates/videos/video_edit.html",
            "pod/video/templates/videos/dashboard.html",
        ):
            template = self._read_asset(template_path)
            self.assertIn('listTheme|json_script:"list-theme-data"', template)
            self.assertNotIn("listTheme | safe", template)

        self.assertIn("function appendThemeOptions(", main_script)
        self.assertIn("option.textContent =", main_script)
        self.assertNotIn("id_theme.innerHTML =", main_script)

    def test_github_workflows_declare_minimal_permissions(self):
        """Read-only workflows and the formatting writer declare their scopes."""
        read_only_workflows = (
            ".github/workflows/pod_dev.yml",
            ".github/workflows/pod_main.yml",
        )
        for workflow_path in read_only_workflows:
            workflow = self._read_asset(workflow_path)
            self.assertIn("\npermissions:\n  contents: read\n", workflow)

        formatting_workflow = self._read_asset(".github/workflows/code_formatting.yml")
        self.assertIn("\npermissions:\n  contents: write\n", formatting_workflow)
