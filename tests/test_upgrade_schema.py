"""Tests for deployment/scripts/upgrade_schema.py."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import django.test

# Add the scripts directory so we can import the standalone script
sys.path.insert(0, str(Path(__file__).parent.parent / "deployment" / "scripts"))
import upgrade_schema  # noqa: E402


class TestDetectSchemaChange(django.test.SimpleTestCase):
    """detect_schema_change() tests."""

    def _make_tvm(self, current_id, versions=None):
        tvm = MagicMock()
        tvm.current = str(current_id)
        tvm.versions = versions or [str(current_id)]
        return tvm

    def _make_template(self, content):
        tmpl = MagicMock()
        tmpl.hash = hashlib.sha1(content.encode()).hexdigest()
        return tmpl

    def test_returns_none_when_hash_matches(self):
        content = "<xs:schema>v1</xs:schema>"
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "nexus-experiment.xsd"
            schema_file.write_text(content)

            tvm = self._make_tvm(current_id=1)
            tmpl = self._make_template(content)

            with (
                patch(
                    "core_main_app.components.template_version_manager"
                    ".models.TemplateVersionManager"
                ) as MockTVM,
                patch(
                    "core_main_app.components.template.models.Template"
                ) as MockTemplate,
            ):
                MockTVM.objects.filter.return_value.first.return_value = tvm
                MockTemplate.objects.get.return_value = tmpl

                result = upgrade_schema.detect_schema_change(schema_path=schema_file)

        self.assertIsNone(result)

    def test_returns_tuple_when_hash_differs(self):
        old_content = "<xs:schema>v1</xs:schema>"
        new_content = "<xs:schema>v2</xs:schema>"
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "nexus-experiment.xsd"
            schema_file.write_text(new_content)

            tvm = self._make_tvm(current_id=1)
            tmpl = self._make_template(old_content)

            with (
                patch(
                    "core_main_app.components.template_version_manager"
                    ".models.TemplateVersionManager"
                ) as MockTVM,
                patch(
                    "core_main_app.components.template.models.Template"
                ) as MockTemplate,
            ):
                MockTVM.objects.filter.return_value.first.return_value = tvm
                MockTemplate.objects.get.return_value = tmpl

                result = upgrade_schema.detect_schema_change(schema_path=schema_file)

        self.assertIsNotNone(result)
        result_tvm, result_content = result
        self.assertIs(result_tvm, tvm)
        self.assertEqual(result_content, new_content)

    def test_raises_if_schema_file_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "does-not-exist.xsd"
            with (
                patch(
                    "core_main_app.components.template_version_manager"
                    ".models.TemplateVersionManager"
                ),
                patch("core_main_app.components.template.models.Template"),
            ):
                with self.assertRaises(FileNotFoundError):
                    upgrade_schema.detect_schema_change(schema_path=missing)

    def test_raises_if_tvm_not_in_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "nexus-experiment.xsd"
            schema_file.write_text("<xs:schema/>")

            with (
                patch(
                    "core_main_app.components.template_version_manager"
                    ".models.TemplateVersionManager"
                ) as MockTVM,
                patch("core_main_app.components.template.models.Template"),
            ):
                MockTVM.objects.filter.return_value.first.return_value = None
                with self.assertRaises(RuntimeError):
                    upgrade_schema.detect_schema_change(schema_path=schema_file)
