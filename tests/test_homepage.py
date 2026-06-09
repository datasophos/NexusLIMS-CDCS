"""Tests for NexusLIMS homepage tiles."""

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from nexuslims_overrides.views import tiles


class HomepageTileTests(SimpleTestCase):
    @patch("nexuslims_overrides.views.render")
    def test_gallery_tile_is_included_when_enabled(self, mock_render):
        tiles(request=None)

        context = mock_render.call_args.args[2]
        gallery_tile = context["tiles"][0]
        self.assertEqual(gallery_tile["title"], "Visual Gallery")
        self.assertEqual(gallery_tile["link"], "/gallery/")

    @override_settings(NX_ENABLE_GALLERY=False)
    @patch("nexuslims_overrides.views.render")
    def test_gallery_tile_is_omitted_when_disabled(self, mock_render):
        tiles(request=None)

        context = mock_render.call_args.args[2]
        self.assertEqual(context["tiles"], [])
