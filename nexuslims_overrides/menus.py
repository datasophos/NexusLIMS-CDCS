"""
NexusLIMS Menu Configuration

Customizes the CDCS menu structure for NexusLIMS.
This file overrides the default menu items from core apps and mdcs_home.

Menu Categories:
  * nodropdown - Top-level menu items (no dropdown)
  * explorer - Data Exploration dropdown items
  * composer - Composer dropdown items
  * dashboard - User dashboard dropdown items
  * help - Help dropdown items
"""

from django.urls import reverse
from menu import Menu, MenuItem

from core_main_app.utils.labels import get_form_label, get_data_label

# Ensure all menu categories exist (even if empty)
# Must initialize both Menu.items and Menu.sorted for each category
for category in ["nodropdown", "explorer", "composer", "dashboard", "help", "user"]:
    if category not in Menu.items:
        Menu.items[category] = []
        Menu.sorted[category] = False

# ============================================================================
# NO DROPDOWN MENU - Top-level navigation items
# ============================================================================

Menu.add_item(
    "nodropdown",
    MenuItem(
        "Browse and Search Records",
        reverse("core_explore_keyword_app_search"),
        icon="search",
        iconClass="fas"
    )
)

# Custom menu links - configurable via settings
# Set NX_CUSTOM_MENU_LINKS in settings.py as a list of dicts:
# NX_CUSTOM_MENU_LINKS = [
#     {"title": "Link 1", "url": "https://example.com", "icon": "fish"},
#     {"title": "Link 2", "url": "https://example.com", "icon": "fish"},
#     {"title": "Link 3", "url": "https://example.com", "icon": "users"},
# ]
from django.conf import settings

custom_links = getattr(settings, 'NX_CUSTOM_MENU_LINKS', [
    {"title": "LINK 1", "url": "https://example.com", "icon": "fish"},
    {"title": "LINK 2", "url": "https://example.com", "icon": "fish"},
    {"title": "LINK 3", "url": "https://example.com", "icon": "users"},
])

for link in custom_links:
    Menu.add_item(
        "nodropdown",
        MenuItem(
            link.get("title", "Link"),
            link.get("url", "#"),
            icon=link.get("icon", "link"),
            iconClass=link.get("iconClass", "fas")
        )
    )

# Tutorial menu item - conditional on NX_ENABLE_TUTORIALS setting
if getattr(settings, 'NX_ENABLE_TUTORIALS', True):
    Menu.add_item(
        "nodropdown",
        MenuItem(
            "Tutorial",
            "#",
            icon="question-circle",
            iconClass="fas"
        )
    )

# ============================================================================
# DASHBOARD MENU - User-specific items (shown when authenticated)
# ============================================================================

Menu.add_item(
    "dashboard",
    MenuItem(
        "My Workspaces",
        reverse("core_dashboard_workspaces"),
        icon="folder-open",
        iconClass="fas"
    ),
)

Menu.add_item(
    "dashboard",
    MenuItem(
        "My {0}s".format(get_data_label().title()),
        reverse("core_dashboard_records"),
        icon="file-alt",
        iconClass="fas"
    ),
)

Menu.add_item(
    "dashboard",
    MenuItem(
        "My {0}s".format(get_form_label().title()),
        reverse("core_dashboard_forms"),
        icon="file-alt",
        iconClass="fas"
    ),
)

Menu.add_item(
    "dashboard",
    MenuItem(
        "My Files",
        reverse("core_dashboard_files"),
        icon="file-alt",
        iconClass="fas"
    )
)

Menu.add_item(
    "dashboard",
    MenuItem(
        "My Queries",
        reverse("core_dashboard_queries"),
        icon="search",
        iconClass="fas"
    ),
)

# ============================================================================
# HELP MENU
# ============================================================================

# Get documentation link from settings
from django.conf import settings
DOCUMENTATION_LINK = getattr(settings, 'NX_DOCUMENTATION_LINK', 'https://example.com')

Menu.add_item(
    "help",
    MenuItem(
        "NexusLIMS Documentation",
        DOCUMENTATION_LINK,
        icon="book",
        iconClass="fas"
    )
)

Menu.add_item(
    "help",
    MenuItem(
        "API Documentation",
        reverse("swagger_view"),
        icon="cogs",
        iconClass="fas"
    )
)

# ============================================================================
# EXPLORER MENU - Commented out in 2.21.0, keeping empty
# ============================================================================
# Menu.add_item(
#     "explorer",
#     MenuItem("Search by Keyword", reverse("core_explore_keyword_app_search")),
# )

# ============================================================================
# COMPOSER MENU - Commented out in 2.21.0, keeping empty
# ============================================================================
# Menu.add_item(
#     "composer",
#     MenuItem("Create New Template", reverse("core_composer_index"))
# )
