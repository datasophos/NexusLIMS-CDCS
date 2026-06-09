"""
Context processors for NexusLIMS customizations.

These functions add variables to the template context for all templates.
Register in settings.py under TEMPLATES['OPTIONS']['context_processors'].
"""

from importlib.metadata import PackageNotFoundError, version

from django.conf import settings
from packaging.version import InvalidVersion, Version


def _nexuslims_version():
    """Return the full project version declared in package metadata."""
    try:
        return version("nexuslims-cdcs")
    except PackageNotFoundError:
        return getattr(settings, "PROJECT_VERSION", "")


def _nexuslims_version_parts():
    """Return the CDCS base version and optional NexusLIMS sub-version."""
    raw_version = _nexuslims_version()
    try:
        parsed = Version(raw_version)
    except InvalidVersion:
        return raw_version, ""
    return parsed.public, parsed.local or ""


def nexuslims_settings(request):
    """
    Make NexusLIMS settings available in all templates.

    Usage in templates:
        {{ NX_DOCUMENTATION_LINK }}
        {{ NX_HOMEPAGE_TEXT }}
        {{ NX_CUSTOM_TITLE }}
        {{ NX_HOMEPAGE_LOGO }}
        {{ NX_NAV_LOGO }}
        {{ NX_FOOTER_LOGO }}
        {{ NX_FOOTER_LINK }}
        {{ NX_VERSION }}
    """
    nx_version, nx_subversion = _nexuslims_version_parts()
    return {
        "NX_DOCUMENTATION_LINK": getattr(settings, "NX_DOCUMENTATION_LINK", ""),
        "NX_HOMEPAGE_TEXT": getattr(settings, "NX_HOMEPAGE_TEXT", ""),
        "NX_CUSTOM_TITLE": getattr(settings, "CUSTOM_TITLE", "Welcome to NexusLIMS!"),
        "NX_HOMEPAGE_LOGO": getattr(
            settings, "NX_HOMEPAGE_LOGO", "nexuslims/img/logo_stacked_modern.png"
        ),
        "NX_NAV_LOGO": getattr(
            settings, "NX_NAV_LOGO", "nexuslims/img/logo_horizontal_light.png"
        ),
        "NX_FOOTER_LOGO": getattr(
            settings, "NX_FOOTER_LOGO", "nexuslims/img/datasophos_logo.png"
        ),
        "NX_FOOTER_LINK": getattr(settings, "NX_FOOTER_LINK", "https://datasophos.co"),
        "NX_VERSION": _nexuslims_version(),
        "NX_BASE_VERSION": nx_version,
        "NX_SUBVERSION": nx_subversion,
    }


def nexuslims_features(request):
    """
    Add NexusLIMS feature flags and configuration to templates.

    Usage in templates:
        {% if NX_ENABLE_TUTORIALS %}
            <!-- Setup template -->
        {% endif %}
    """
    return {
        "NX_ENABLE_TUTORIALS": getattr(settings, "NX_ENABLE_TUTORIALS", True),
        "NX_ENABLE_ANNOTATOR": getattr(settings, "NX_ENABLE_ANNOTATOR", True),
        "NX_ENABLE_GALLERY": (
            "nexuslims_gallery" in settings.INSTALLED_APPS
            and getattr(settings, "NX_ENABLE_GALLERY", True)
        ),
        "IS_PUBLIC_DEMO": getattr(settings, "IS_PUBLIC_DEMO", False),
    }


def nexuslims_colors(request):
    """
    Make NexusLIMS theme colors available for CSS custom property overrides.
    """
    return {
        "NX_THEME_COLORS": getattr(settings, "NX_THEME_COLORS", {}),
    }
