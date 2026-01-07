"""
NexusLIMS-specific settings

These settings configure NexusLIMS customizations and branding.
Override these in your deployment's settings.py file as needed.
"""

# ============================================================================
# XSLT CONFIGURATION
# ============================================================================

# Instrument PID to badge color mappings for XSLT transformations
# These colors are used in the detail view to visually distinguish different
# instruments. The keys of this dictionary should match the instrument identifiers
# in your NexusLIMS instrument database, and the values should be hex colors
# if not defined, a default gray color will be used
NX_INSTRUMENT_COLOR_MAPPINGS = {
    "FEI-Titan-TEM": "#117f0e",
    "FEI-Titan-STEM": "#9467bd",
    "FEI-Quanta200-ESEM": "#d62728",
    "JEOL-JEM3010-TEM": "#9467bd",
    "FEI-Helios-DB": "#8c564b",
    "Hitachi-S4700-SEM": "#e377c2",
    "Hitachi-S5500-SEM": "#17becf",
    "JEOL-JSM7100-SEM": "#bcbd22",
    "Philips-EM400-TEM": "#bebada",
    "Philips-CM30-TEM": "#b3de69",
    "Zeiss-LEO_1525_FESEM": "#1a581d",
    "Zeiss-Gemini_300_SEM": "#791212",
    "FEI-Quanta_400_SEM": "#154157",
    "JEOL-7800F_SEM": "#81538d",
    "FEI-Titan-ETEM": "#CC8B2F",
    "Thermo-Scios-DB": "#496BC4",
}

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
