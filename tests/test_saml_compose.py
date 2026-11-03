"""Regression checks for the development SAML test provider."""

from pathlib import Path

import yaml
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[1]


class SamlComposeTests(SimpleTestCase):
    def test_development_idp_is_optional_and_ci_uses_same_image(self):
        dev = yaml.safe_load((ROOT / "deployment/docker-compose.dev.yml").read_text())
        ci = yaml.safe_load((ROOT / "deployment/docker-compose.ci.yml").read_text())
        idp = dev["services"]["simplesamlphp"]
        self.assertIn("sso", idp["profiles"])
        self.assertEqual(idp["image"], ci["services"]["simplesamlphp"]["image"])
        self.assertTrue(idp["image"].startswith("cirrusid/simplesamlphp:"))
