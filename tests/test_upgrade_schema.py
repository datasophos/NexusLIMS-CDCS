"""Tests for deployment/scripts/upgrade_schema.py."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import django.test

# Add the scripts directory so we can import the standalone script
sys.path.insert(0, str(Path(__file__).parent.parent / "deployment" / "scripts"))
import upgrade_schema  # noqa: E402


class TestDetectSchemaChange(django.test.SimpleTestCase):
    """detect_schema_change() tests."""

    # Stable sentinel hashes for use in tests — the actual value is arbitrary,
    # what matters is that "same" and "different" are distinguishable.
    _HASH_V1 = "aabbccdd" * 5  # 40-char fake SHA-1
    _HASH_V2 = "11223344" * 5

    def _make_tvm(self, current_id, versions=None):
        tvm = MagicMock()
        tvm.current = str(current_id)
        tvm.versions = versions or [str(current_id)]
        return tvm

    def _make_template(self, fake_hash):
        tmpl = MagicMock()
        tmpl.hash = fake_hash
        return tmpl

    def _patch_xsd_hash(self, return_value):
        """Return a context manager that patches xsd_hash.get_hash inside the module."""
        return patch("xml_utils.xsd_hash.xsd_hash.get_hash", return_value=return_value)

    def test_returns_none_when_hash_matches(self):
        content = "dummy schema content v1"
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "nexus-experiment.xsd"
            schema_file.write_text(content)

            tvm = self._make_tvm(current_id=1)
            tmpl = self._make_template(self._HASH_V1)

            with (
                self._patch_xsd_hash(self._HASH_V1),
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
        new_content = "dummy schema content v2"
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "nexus-experiment.xsd"
            schema_file.write_text(new_content)

            tvm = self._make_tvm(current_id=1)
            # DB has v1's hash; on-disk file computes v2's hash
            tmpl = self._make_template(self._HASH_V1)

            with (
                self._patch_xsd_hash(self._HASH_V2),
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
            schema_file.write_text("dummy schema content")

            with (
                self._patch_xsd_hash(self._HASH_V1),
                patch(
                    "core_main_app.components.template_version_manager"
                    ".models.TemplateVersionManager"
                ) as MockTVM,
                patch("core_main_app.components.template.models.Template"),
            ):
                MockTVM.objects.filter.return_value.first.return_value = None
                with self.assertRaises(RuntimeError):
                    upgrade_schema.detect_schema_change(schema_path=schema_file)


class TestAddSchemaVersion(django.test.SimpleTestCase):
    """add_schema_version() tests."""

    def test_calls_insert_and_set_current(self):
        new_content = "<xs:schema>v2</xs:schema>"
        mock_tvm = MagicMock()
        mock_request = MagicMock()
        mock_new_template = MagicMock()

        with (
            patch(
                "core_main_app.components.template.models.Template"
            ) as MockTemplate,
            patch(
                "core_main_app.components.template_version_manager.api"
            ) as mock_tvm_api,
            patch(
                "core_main_app.components.version_manager.api"
            ) as mock_vm_api,
        ):
            MockTemplate.return_value = mock_new_template

            result = upgrade_schema.add_schema_version(
                mock_tvm, new_content, mock_request
            )

        mock_tvm_api.insert.assert_called_once_with(
            mock_tvm, mock_new_template, request=mock_request
        )
        mock_vm_api.set_current.assert_called_once_with(
            mock_new_template, request=mock_request
        )
        self.assertIs(result, mock_new_template)

    def test_sets_correct_filename_content_and_hash(self):
        import hashlib
        new_content = "<xs:schema>v2</xs:schema>"
        expected_hash = hashlib.sha1(new_content.encode()).hexdigest()
        mock_tvm = MagicMock()
        mock_request = MagicMock()

        with (
            patch(
                "core_main_app.components.template.models.Template"
            ) as MockTemplate,
            patch("core_main_app.components.template_version_manager.api"),
            patch("core_main_app.components.version_manager.api"),
        ):
            instance = MockTemplate.return_value
            upgrade_schema.add_schema_version(mock_tvm, new_content, mock_request)
            self.assertEqual(instance.filename, "nexus-experiment.xsd")
            self.assertEqual(instance.content, new_content)
            self.assertEqual(instance.hash, expected_hash)


class TestMigrateRecords(django.test.SimpleTestCase):
    """migrate_records() tests."""

    def test_updates_records_on_old_versions(self):
        old_ids = ["1", "2"]
        mock_new_template = MagicMock()
        mock_new_template.id = 3

        with patch(
            "core_main_app.components.data.models.Data"
        ) as MockData:
            MockData.objects.filter.return_value.update.return_value = 5

            count = upgrade_schema.migrate_records(old_ids, mock_new_template)

        MockData.objects.filter.assert_called_once_with(template_id__in=old_ids)
        MockData.objects.filter.return_value.update.assert_called_once_with(
            template=mock_new_template
        )
        self.assertEqual(count, 5)

    def test_returns_zero_for_empty_old_ids(self):
        mock_new_template = MagicMock()

        with patch("core_main_app.components.data.models.Data") as MockData:
            count = upgrade_schema.migrate_records([], mock_new_template)

        MockData.objects.filter.assert_not_called()
        self.assertEqual(count, 0)


class TestUpdateXslt(django.test.SimpleTestCase):
    """update_xslt() tests."""

    def _make_xslt_dir(self, tmpdir):
        xslt_dir = Path(tmpdir) / "xslt"
        xslt_dir.mkdir()

        detail = (
            '<xsl:stylesheet>\n'
            '  <xsl:variable name="datasetBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>\n'
            '  <xsl:variable name="previewBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>\n'
            '</xsl:stylesheet>'
        )
        (xslt_dir / "detail_stylesheet.xsl").write_text(detail)
        (xslt_dir / "list_stylesheet.xsl").write_text("<xsl:stylesheet/>")
        return xslt_dir

    def test_patches_urls_in_detail_stylesheet(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            xslt_dir = self._make_xslt_dir(tmpdir)
            mock_detail = MagicMock()
            mock_list = MagicMock()

            with (
                patch.dict(
                    "os.environ",
                    {
                        "XSLT_DATASET_BASE_URL": "https://files.example.com/instrument-data",
                        "XSLT_PREVIEW_BASE_URL": "https://files.example.com/data",
                    },
                ),
                patch(
                    "core_main_app.components.xsl_transformation.api"
                ) as mock_xslt_api,
            ):
                mock_xslt_api.get_by_name.side_effect = lambda name: (
                    mock_detail if "detail" in name else mock_list
                )

                upgrade_schema.update_xslt(xslt_dir=xslt_dir)

            self.assertIn("https://files.example.com/instrument-data", mock_detail.content)
            self.assertIn("https://files.example.com/data", mock_detail.content)
            self.assertNotIn("CHANGE.THIS.VALUE", mock_detail.content)
            self.assertEqual(mock_xslt_api.upsert.call_count, 2)

    def test_upsert_called_for_both_stylesheets(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            xslt_dir = self._make_xslt_dir(tmpdir)

            with (
                patch.dict("os.environ", {}, clear=False),
                patch(
                    "core_main_app.components.xsl_transformation.api"
                ) as mock_xslt_api,
            ):
                mock_xslt_api.get_by_name.return_value = MagicMock()
                upgrade_schema.update_xslt(xslt_dir=xslt_dir)

            self.assertEqual(mock_xslt_api.upsert.call_count, 2)
