"""Esup-Pod security regression tests for frontend assets."""

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

    def test_completion_overlay_validation_uses_dom_parser(self):
        """Test that overlay validation checks forbidden tags via parsed DOM."""
        script = self._read_asset("pod/completion/static/js/completion.js")
        self.assertIn('parsed.querySelector("script, iframe")', script)
        self.assertNotIn("var tags = /<script.+?>|<iframe.+?>/;", script)

    def test_caption_maker_strips_html_with_dom_parser(self):
        """Test that caption sanitization no longer relies on a brittle regex."""
        script = self._read_asset("pod/completion/static/js/caption_maker.js")
        self.assertIn("var stripHtmlTags = function (line) {", script)
        self.assertIn('new DOMParser().parseFromString(line, "text/html")', script)
        self.assertNotIn("rxMarkup", script)

    def test_comment_script_sets_reply_content_as_text(self):
        """Test that comment/reply content is inserted as text content."""
        script = self._read_asset("pod/video/static/js/comment-script.js")
        self.assertIn("contentBody.textContent = content;", script)
        self.assertIn("author.textContent = `@${reply_to}`;", script)
        self.assertIn("content.textContent = reply_content;", script)
        self.assertNotIn('.querySelector(".comment_content_body").innerHTML =', script)
