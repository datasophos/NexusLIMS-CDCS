"""Unit tests for nexuslims_gallery helper functions."""

import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from nexuslims_gallery.views import normalize_experimenter, _select_best_dataset

NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
PREVIEW_BASE = "https://files.example.com/data"


def _make_dataset_xml(name, preview=None, rating=None, featured=None, description=None):
    """Build a minimal <dataset> XML fragment string."""
    ds = ET.Element(f"{{{NS}}}dataset")
    name_el = ET.SubElement(ds, f"{{{NS}}}name")
    name_el.text = name
    loc_el = ET.SubElement(ds, f"{{{NS}}}location")
    loc_el.text = f"/data/{name}"
    if description:
        desc_el = ET.SubElement(ds, f"{{{NS}}}description")
        desc_el.text = description
    if preview:
        prev_el = ET.SubElement(ds, f"{{{NS}}}preview")
        prev_el.text = preview
    if rating is not None or featured is not None:
        cur_el = ET.SubElement(ds, f"{{{NS}}}curation")
        if rating is not None:
            r_el = ET.SubElement(cur_el, f"{{{NS}}}rating")
            r_el.text = str(rating)
        if featured:
            f_el = ET.SubElement(cur_el, f"{{{NS}}}featured")
            f_el.text = "true"
    return ET.tostring(ds, encoding="unicode")


def _make_record_xml(datasets):
    """Build a full <Experiment> XML string with the given dataset XML fragments."""
    inner = "".join(datasets)
    return (
        f'<Experiment xmlns="{NS}">'
        f"<title>Test Record</title>"
        f'<acquisitionActivity seqno="0">{inner}</acquisitionActivity>'
        f"</Experiment>"
    )


# ===========================================================================
# normalize_experimenter
# ===========================================================================


class NormalizeExperimenterTests(SimpleTestCase):
    def test_first_initial_and_last_name(self):
        self.assertEqual(
            normalize_experimenter("Joshua Taillon (jtaillon)"), "J. Taillon"
        )

    def test_strips_parenthetical_username(self):
        self.assertEqual(normalize_experimenter("Alice Smith (asmith)"), "A. Smith")

    def test_single_name_fallback(self):
        self.assertEqual(normalize_experimenter("Admin"), "Admin")

    def test_empty_string_fallback(self):
        self.assertEqual(normalize_experimenter(""), "")

    def test_no_username_portion(self):
        self.assertEqual(normalize_experimenter("John Doe"), "J. Doe")

    def test_multiple_middle_names_uses_last(self):
        self.assertEqual(normalize_experimenter("Mary Ann Jones (mj)"), "M. Jones")


# ===========================================================================
# _select_best_dataset
# ===========================================================================


class SelectBestDatasetTests(SimpleTestCase):
    def test_returns_none_for_record_with_no_preview(self):
        xml = _make_record_xml([_make_dataset_xml("no_preview.dm3")])
        self.assertIsNone(_select_best_dataset(xml, PREVIEW_BASE))

    def test_returns_dataset_with_preview(self):
        xml = _make_record_xml(
            [
                _make_dataset_xml("img.dm3", preview="/p/img.png"),
            ]
        )
        result = _select_best_dataset(xml, PREVIEW_BASE)
        self.assertIsNotNone(result)
        self.assertIn("img.png", result["preview_url"])

    def test_featured_takes_priority_over_rated(self):
        xml = _make_record_xml(
            [
                _make_dataset_xml("rated.dm3", preview="/p/rated.png", rating=5),
                _make_dataset_xml("featured.dm3", preview="/p/feat.png", featured=True),
            ]
        )
        result = _select_best_dataset(xml, PREVIEW_BASE)
        self.assertIn("feat.png", result["preview_url"])

    def test_highest_rating_wins_when_no_featured(self):
        xml = _make_record_xml(
            [
                _make_dataset_xml("low.dm3", preview="/p/low.png", rating=2),
                _make_dataset_xml("high.dm3", preview="/p/high.png", rating=5),
            ]
        )
        result = _select_best_dataset(xml, PREVIEW_BASE)
        self.assertIn("high.png", result["preview_url"])

    def test_first_preview_chosen_when_no_curation(self):
        xml = _make_record_xml(
            [
                _make_dataset_xml("a.dm3", preview="/p/a.png"),
                _make_dataset_xml("b.dm3", preview="/p/b.png"),
            ]
        )
        result = _select_best_dataset(xml, PREVIEW_BASE)
        self.assertIsNotNone(result)
        self.assertIn("a.png", result["preview_url"])

    def test_preview_url_built_from_base(self):
        xml = _make_record_xml(
            [
                _make_dataset_xml("img.dm3", preview="/previews/img.png"),
            ]
        )
        result = _select_best_dataset(xml, PREVIEW_BASE)
        self.assertEqual(result["preview_url"], f"{PREVIEW_BASE}/previews/img.png")

    def test_returns_none_for_malformed_xml(self):
        self.assertIsNone(_select_best_dataset("<not xml <<", PREVIEW_BASE))

    def test_returns_description_when_present(self):
        xml = _make_record_xml(
            [
                _make_dataset_xml(
                    "img.dm3", preview="/p/img.png", description="A nice dataset"
                ),
            ]
        )
        result = _select_best_dataset(xml, PREVIEW_BASE)
        self.assertEqual(result["description"], "A nice dataset")

    def test_returns_none_description_when_absent(self):
        xml = _make_record_xml(
            [
                _make_dataset_xml("img.dm3", preview="/p/img.png"),
            ]
        )
        result = _select_best_dataset(xml, PREVIEW_BASE)
        self.assertIsNone(result["description"])


# ===========================================================================
# gallery_page and api_next views
# ===========================================================================


def _make_mock_record(xml_content, record_id="rec-1", title="Test Record"):
    rec = MagicMock()
    rec.content = xml_content
    rec.id = record_id
    rec.title = title
    return rec


_GALLERY_RECORD_XML = f"""\
<Experiment xmlns="{NS}">
  <title>TEM Imaging of Au Nanoparticles</title>
  <summary>
    <experimenter>Joshua Taillon (jtaillon)</experimenter>
    <instrument pid="FEI-Titan-TEM">FEI Titan TEM</instrument>
    <reservationStart>2024-03-15T09:00:00-05:00</reservationStart>
  </summary>
  <acquisitionActivity seqno="0">
    <dataset type="Image">
      <name>img001.dm3</name>
      <location>/data/img001.dm3</location>
      <description>Bright-field TEM image of gold nanoparticles on amorphous carbon.</description>
      <preview>/previews/img001.png</preview>
      <curation><rating>4</rating></curation>
    </dataset>
  </acquisitionActivity>
</Experiment>"""

_NO_PREVIEW_RECORD_XML = f"""\
<Experiment xmlns="{NS}">
  <title>No Preview Record</title>
  <acquisitionActivity seqno="0">
    <dataset type="Image">
      <name>data.dm3</name>
      <location>/data/data.dm3</location>
    </dataset>
  </acquisitionActivity>
</Experiment>"""


class GalleryPageViewTests(TestCase):
    def test_gallery_page_returns_200_without_auth(self):
        response = self.client.get("/gallery/")
        self.assertEqual(response.status_code, 200)

    def test_gallery_page_uses_correct_template(self):
        response = self.client.get("/gallery/")
        self.assertTemplateUsed(response, "nexuslims_gallery/gallery.html")


class ApiNextViewTests(TestCase):
    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_returns_json_with_expected_fields(self, mock_data_api, mock_ws_api):
        mock_ws_api.get_global_workspace.return_value = MagicMock()
        mock_data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_GALLERY_RECORD_XML)
        ]
        response = self.client.get("/gallery/api/next/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("title", body)
        self.assertIn("preview_url", body)
        self.assertIn("record_url", body)
        self.assertFalse(body["featured"])

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_featured_dataset_identified_in_response(
        self,
        mock_data_api,
        mock_ws_api,
    ):
        mock_ws_api.get_global_workspace.return_value = MagicMock()
        featured_xml = _GALLERY_RECORD_XML.replace(
            "<curation><rating>4</rating></curation>",
            "<curation><rating>4</rating><featured>true</featured></curation>",
        )
        mock_data_api.get_all_by_workspace.return_value = [
            _make_mock_record(featured_xml)
        ]

        body = self.client.get("/gallery/api/next/").json()

        self.assertTrue(body["featured"])

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_long_title_is_returned_in_full(self, mock_data_api, mock_ws_api):
        mock_ws_api.get_global_workspace.return_value = MagicMock()
        long_title = (
            "Structure of metal-organic framework nanocrystals obtained from "
            "electron diffraction data by iterative phase retrieval"
        )
        xml = _GALLERY_RECORD_XML.replace(
            "TEM Imaging of Au Nanoparticles",
            long_title,
        )
        mock_data_api.get_all_by_workspace.return_value = [_make_mock_record(xml)]

        body = self.client.get("/gallery/api/next/").json()

        self.assertEqual(body["title"], long_title)

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_experimenter_normalised(self, mock_data_api, mock_ws_api):
        mock_ws_api.get_global_workspace.return_value = MagicMock()
        mock_data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_GALLERY_RECORD_XML)
        ]
        body = self.client.get("/gallery/api/next/").json()
        self.assertEqual(body.get("experimenter"), "J. Taillon")

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_records_without_preview_excluded(self, mock_data_api, mock_ws_api):
        mock_ws_api.get_global_workspace.return_value = MagicMock()
        mock_data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_NO_PREVIEW_RECORD_XML)
        ]
        response = self.client.get("/gallery/api/next/")
        self.assertEqual(response.status_code, 404)

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_month_year_in_response(self, mock_data_api, mock_ws_api):
        mock_ws_api.get_global_workspace.return_value = MagicMock()
        mock_data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_GALLERY_RECORD_XML)
        ]
        body = self.client.get("/gallery/api/next/").json()
        self.assertEqual(body.get("month_year"), "March 2024")

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_instrument_in_response(self, mock_data_api, mock_ws_api):
        mock_ws_api.get_global_workspace.return_value = MagicMock()
        mock_data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_GALLERY_RECORD_XML)
        ]
        body = self.client.get("/gallery/api/next/").json()
        self.assertEqual(body.get("instrument"), "FEI Titan TEM")

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_description_included_when_present(self, mock_data_api, mock_ws_api):
        mock_ws_api.get_global_workspace.return_value = MagicMock()
        mock_data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_GALLERY_RECORD_XML)
        ]
        body = self.client.get("/gallery/api/next/").json()
        self.assertEqual(
            body.get("description"),
            "Bright-field TEM image of gold nanoparticles on amorphous carbon.",
        )

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_uses_anonymous_user_for_workspace_query(self, mock_data_api, mock_ws_api):
        from django.contrib.auth.models import AnonymousUser

        mock_ws_api.get_global_workspace.return_value = MagicMock()
        mock_data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_GALLERY_RECORD_XML)
        ]
        self.client.get("/gallery/api/next/")
        call_args = mock_data_api.get_all_by_workspace.call_args
        user_arg = call_args[0][1]  # second positional argument
        self.assertIsInstance(user_arg, AnonymousUser)

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_description_omitted_when_absent(self, mock_data_api, mock_ws_api):
        mock_ws_api.get_global_workspace.return_value = MagicMock()
        xml_no_desc = f"""\
<Experiment xmlns="{NS}">
  <title>No Description</title>
  <acquisitionActivity seqno="0">
    <dataset type="Image">
      <name>img.dm3</name>
      <location>/data/img.dm3</location>
      <preview>/previews/img.png</preview>
    </dataset>
  </acquisitionActivity>
</Experiment>"""
        mock_data_api.get_all_by_workspace.return_value = [
            _make_mock_record(xml_no_desc)
        ]
        body = self.client.get("/gallery/api/next/").json()
        self.assertNotIn("description", body)


class GalleryCurationModeTests(TestCase):
    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_curated_mode_excludes_uncurated_records(self, data_api, workspace_api):
        from nexuslims_gallery.models import GallerySettings

        GallerySettings.objects.create(pk=1, selection_mode="curated")
        data_api.get_all_by_workspace.return_value = [
            _make_mock_record(
                _make_record_xml([_make_dataset_xml("plain", preview="plain.png")])
            ),
            _make_mock_record(_GALLERY_RECORD_XML, record_id="curated"),
        ]
        response = self.client.get("/gallery/api/next/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["record_url"], "/data?id=curated")

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_featured_mode_excludes_rated_only_records(self, data_api, workspace_api):
        from nexuslims_gallery.models import GallerySettings

        GallerySettings.objects.create(pk=1, selection_mode="featured")
        data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_GALLERY_RECORD_XML)
        ]
        self.assertEqual(self.client.get("/gallery/api/next/").status_code, 404)

    def test_admin_page_requires_staff(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(username="ordinary", password="pw")
        self.client.force_login(user)
        self.assertNotEqual(self.client.get("/admin/gallery/").status_code, 200)

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_staff_can_save_mode_and_see_selectable_images(
        self, data_api, workspace_api
    ):
        from django.contrib.auth import get_user_model
        from nexuslims_gallery.models import GallerySettings

        user = get_user_model().objects.create_user(
            username="staff", password="pw", is_staff=True
        )
        self.client.force_login(user)
        data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_GALLERY_RECORD_XML)
        ]
        response = self.client.post(
            "/admin/gallery/", {"selection_mode": "curated", "minimum_rating": "1"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GallerySettings.objects.get(pk=1).selection_mode, "curated")
        from django.shortcuts import render

        with patch(
            "nexuslims_gallery.views.admin_render",
            side_effect=lambda request, template, context: render(
                request, template, {"data": context}
            ),
        ):
            response = self.client.get("/admin/gallery/")
        self.assertContains(response, "img001.dm3")
        self.assertContains(response, "Joshua Taillon")
        self.assertContains(response, "/data?id=rec-1")

    def test_tied_winners_are_all_in_inventory(self):
        from nexuslims_gallery.views import _selectable_datasets

        xml = _make_record_xml(
            [
                _make_dataset_xml("one", preview="one.png", rating=5),
                _make_dataset_xml("two", preview="two.png", rating=5),
                _make_dataset_xml("three", preview="three.png", rating=3),
            ]
        )
        self.assertEqual(
            {
                item["name"]
                for item in _selectable_datasets(xml, PREVIEW_BASE, "curated")
            },
            {"one", "two"},
        )

    def test_empty_preview_is_not_selectable(self):
        from nexuslims_gallery.views import _selectable_datasets

        xml = _make_record_xml([f'<dataset xmlns="{NS}"><preview></preview></dataset>'])
        self.assertEqual(_selectable_datasets(xml, PREVIEW_BASE), [])

    def test_nonstaff_cannot_change_settings(self):
        from django.contrib.auth import get_user_model
        from nexuslims_gallery.models import GallerySettings

        user = get_user_model().objects.create_user(username="ordinary", password="pw")
        self.client.force_login(user)
        self.client.post("/admin/gallery/", {"selection_mode": "featured"})
        self.assertFalse(GallerySettings.objects.exists())

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_minimum_rating_filters_curated_records_but_not_featured(
        self, data_api, workspace_api
    ):
        from nexuslims_gallery.models import GallerySettings

        GallerySettings.objects.create(pk=1, selection_mode="curated", minimum_rating=5)
        data_api.get_all_by_workspace.return_value = [
            _make_mock_record(_GALLERY_RECORD_XML)
        ]
        self.assertEqual(self.client.get("/gallery/api/next/").status_code, 404)
        from django.contrib.auth import get_user_model
        from django.shortcuts import render

        self.client.force_login(
            get_user_model().objects.create_user(username="staff", is_staff=True)
        )
        with patch(
            "nexuslims_gallery.views.admin_render",
            side_effect=lambda request, template, context: render(
                request, template, {"data": context}
            ),
        ):
            self.assertNotContains(self.client.get("/admin/gallery/"), "img001.dm3")
        featured = _GALLERY_RECORD_XML.replace(
            "<rating>4</rating>", "<rating>4</rating><featured>true</featured>"
        )
        data_api.get_all_by_workspace.return_value = [_make_mock_record(featured)]
        self.assertEqual(self.client.get("/gallery/api/next/").status_code, 200)

    def test_threshold_does_not_change_all_records_mode(self):
        from nexuslims_gallery.views import _selectable_datasets

        xml = _make_record_xml([_make_dataset_xml("low", preview="low.png", rating=2)])
        self.assertEqual(len(_selectable_datasets(xml, PREVIEW_BASE, "all", 5)), 1)
        self.assertEqual(_selectable_datasets(xml, PREVIEW_BASE, "curated", 5), [])

    @patch("nexuslims_gallery.views.workspace_api")
    @patch("nexuslims_gallery.views.data_api")
    def test_admin_can_save_threshold_and_rejects_invalid_value(
        self, data_api, workspace_api
    ):
        from django.contrib.auth import get_user_model
        from django.shortcuts import render
        from nexuslims_gallery.models import GallerySettings

        self.client.force_login(
            get_user_model().objects.create_user(username="staff", is_staff=True)
        )
        response = self.client.post(
            "/admin/gallery/", {"selection_mode": "curated", "minimum_rating": "4"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GallerySettings.objects.get(pk=1).minimum_rating, 4)
        with patch(
            "nexuslims_gallery.views.admin_render",
            side_effect=lambda request, template, context: render(
                request, template, {"data": context}
            ),
        ):
            response = self.client.post(
                "/admin/gallery/", {"selection_mode": "curated", "minimum_rating": "6"}
            )
        self.assertContains(response, "Ensure this value is less than or equal to 5")
        self.assertEqual(GallerySettings.objects.get(pk=1).minimum_rating, 4)
