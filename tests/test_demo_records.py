"""Validation for committed public demo record fixtures."""

from pathlib import Path
import xml.etree.ElementTree as ET

from django.test import SimpleTestCase

from deployment.scripts.generate_demo_records import ensure_demo_curation


NS = {"nx": "https://data.nist.gov/od/dm/nexus/experiment/v1.0"}
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "deployment/fixtures/demo_records"


class DemoRecordCurationTests(SimpleTestCase):
    def test_every_record_has_representative_curation(self):
        for fixture in sorted(FIXTURE_DIR.glob("*.xml")):
            with self.subTest(fixture=fixture.name):
                root = ET.parse(fixture).getroot()
                previewable = [
                    dataset
                    for dataset in root.findall(".//nx:dataset", NS)
                    if dataset.find("nx:preview", NS) is not None
                ]
                rated = [
                    dataset
                    for dataset in previewable
                    if dataset.find("nx:curation/nx:rating", NS) is not None
                ]
                featured = [
                    dataset
                    for dataset in previewable
                    if dataset.findtext(
                        "nx:curation/nx:featured",
                        default="",
                        namespaces=NS,
                    )
                    == "true"
                ]

                self.assertGreaterEqual(len(rated), 3)
                self.assertGreaterEqual(len(featured), 2)

    def test_ensuring_curation_is_idempotent(self):
        fixture = sorted(FIXTURE_DIR.glob("*.xml"))[0]
        root = ET.parse(fixture).getroot()
        before = ET.tostring(root)

        ensure_demo_curation(root)

        self.assertEqual(ET.tostring(root), before)
