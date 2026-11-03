"""Routing coverage for the production gallery administration URL."""

import runpy
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import resolve

from nexuslims_gallery.views import gallery_admin


class GalleryAdminUrlTests(SimpleTestCase):
    def test_gallery_admin_resolves_with_empty_admin_prefix(self):
        with (
            patch("mdcs.core_settings.ADMIN_URLS_PREFIX", ""),
            patch("django.conf.urls.include", return_value=([], None, None)),
        ):
            urls = runpy.run_module("mdcs.urls")["urlpatterns"]

        self.assertIs(resolve("/admin/gallery/", urlconf=tuple(urls)).func, gallery_admin)
