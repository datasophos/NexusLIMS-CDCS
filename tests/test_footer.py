"""Tests for the NexusLIMS footer override."""

from importlib.metadata import version
from pathlib import Path

from django.template import Context, Engine
from django.test import SimpleTestCase

from nexuslims_overrides.context_processors import nexuslims_settings


class FooterTemplateTests(SimpleTestCase):
    def test_context_contains_full_project_version(self):
        context = nexuslims_settings(request=None)

        self.assertEqual(context["NX_VERSION"], version("nexuslims-cdcs"))
        self.assertEqual(context["NX_BASE_VERSION"], "3.21.0")
        self.assertEqual(context["NX_SUBVERSION"], "nx1")

    def test_version_links_to_frontend_changelog(self):
        template_dir = (
            Path(__file__).resolve().parents[1]
            / "nexuslims_overrides"
            / "templates"
        )
        engine = Engine(
            dirs=[template_dir, Path(__file__).resolve().parents[1] / "templates"],
            libraries={"static": "django.templatetags.static"},
        )
        template = engine.get_template("theme/footer/default.html")
        html = template.render(
            Context({"NX_BASE_VERSION": "3.21.0", "NX_SUBVERSION": "nx1"})
        )

        self.assertIn("NexusLIMS Frontend v. 3.21.0", html)
        self.assertIn('class="nexuslims-subversion">(nx1)</code>', html)
        self.assertIn("/static/nexuslims/img/icon.svg", html)
        self.assertIn(
            "https://datasophos.github.io/NexusLIMS/stable/"
            "frontend_guide/changelog.html",
            html,
        )
        self.assertIn("fa-external-link-alt", html)
        self.assertIn('class="footer-separator"', html)
        self.assertNotIn("Powered by", html)
        self.assertNotIn("cdcs_logo.png", html)
