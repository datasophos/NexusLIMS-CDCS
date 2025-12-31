"""
NexusLIMS custom views.

These views override or extend the default MDCS views.

File overrides:
- tiles() -> overrides mdcs_home/views.py::tiles()
"""
import logging

from django.conf import settings
from django.shortcuts import render
from django.urls import reverse

logger = logging.getLogger(__name__)


def tiles(request):
    """
    NexusLIMS customized tiles for homepage.

    Customizations from base mdcs_home.views.tiles():
    - Reordered: Search first, then Curate
    - Disabled: "Build your own queries", "Compose a template"
    - Custom text: "Browse and Search Records" instead of "Search by keyword"
    - Added IDs: "app_search" and "curator" for JavaScript targeting
    - NexusLIMS-specific descriptions

    :param request:
    :return:
    """
    installed_apps = settings.INSTALLED_APPS
    context = {"tiles": []}

    # First tile: Browse and Search (keyword search)
    if "core_explore_keyword_app" in installed_apps:
        explore_keywords_tile = {
            "logo": "fa-search",
            "link": reverse("core_explore_keyword_app_search"),
            "title": "Browse and Search Records",
            "text": "Click here to explore the NexusLIMS record repository",
            "id": "app_search"
        }
        context["tiles"].append(explore_keywords_tile)

    # Second tile: Create a new record (curate) - currently disabled
    if "core_curate_app" in installed_apps:
        curate_tile = {
            "logo": "fa-edit",
            "link": reverse("core_curate_index"),
            "title": "Create a new record",
            "text": "Click here to upload a record manually or build a record from scratch",
            "id": "curator"
        }
        # Disabled for NexusLIMS - records are auto-generated
        # Uncomment to enable manual record creation:
        # context["tiles"].append(curate_tile)

    # Third tile: Build your own queries - disabled for NexusLIMS
    if "core_explore_example_app" in installed_apps:
        explore_example_tile = {
            "logo": "fa-flask",
            "link": reverse("core_explore_example_index"),
            "title": "Build your own queries",
            "text": "Click here to search for Materials Data in the repository using flexible queries.",
        }
        # Disabled for NexusLIMS
        # Uncomment to enable:
        # context["tiles"].append(explore_example_tile)

    # Fourth tile: Compose a template - disabled for NexusLIMS
    if "core_composer_app" in installed_apps:
        compose_tile = {
            "logo": "fa-file-code",
            "link": reverse("core_composer_index"),
            "title": "Compose a template",
            "text": "Click here to compose your own template.",
        }
        # Disabled for NexusLIMS - template is pre-defined
        # Uncomment to enable:
        # context["tiles"].append(compose_tile)

    return render(request, "mdcs_home/tiles.html", context)
