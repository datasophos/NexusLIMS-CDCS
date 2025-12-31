"""
NexusLIMS-specific settings

These settings configure NexusLIMS customizations and branding.
Override these in your deployment's settings.py file as needed.
"""

# ============================================================================
# HOMEPAGE CONFIGURATION
# ============================================================================

NX_HOMEPAGE_TEXT = (
    "This laboratory information management system (LIMS) allows for the "
    "automated creation and curation of microscopy experimental records using "
    "the schema co-developed by ODI and the MML Electron Microscopy Nexus Facility. "
    "Experimental records are automatically harvested from multiple data sources to "
    "facilitate browsing and searching of data collected from the varied instruments "
    "in the Nexus Facility."
)

NX_HOMEPAGE_LOGO = "nexuslims/img/logo_horizontal_text.png"  # Path relative to static/

# ============================================================================
# BRANDING & LINKS
# ============================================================================

NX_DOCUMENTATION_LINK = "https://datasophos.github.io/NexusLIMS/"

# Navigation bar branding
NX_NAV_LOGO = "nexuslims/img/nav_logo.png"  # Path relative to static/

# Footer branding
NX_FOOTER_LOGO = "nexuslims/img/datasophos_logo.png"  # Path relative to static/
NX_FOOTER_LINK = "https://datasophos.co"

# ============================================================================
# NAVIGATION MENU
# ============================================================================

# Custom menu links in navigation bar
# Each link should be a dict with: title, url, icon (optional), iconClass (optional)
NX_CUSTOM_MENU_LINKS = [
    {"title": "LINK 1", "url": "https://example.com", "icon": "fish"},
    {"title": "LINK 2", "url": "https://example.com", "icon": "fish"},
    {"title": "LINK 3", "url": "https://example.com", "icon": "users"},
]

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Enable/disable features
NX_ENABLE_TUTORIALS = True

# ============================================================================
# VERSION
# ============================================================================

NX_VERSION = "dev"
