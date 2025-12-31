"""
Context processors for NexusLIMS customizations.

These functions add variables to the template context for all templates.
Register in settings.py under TEMPLATES['OPTIONS']['context_processors'].
"""
from django.conf import settings


def nexuslims_settings(request):
    """
    Make NexusLIMS settings available in all templates.

    Usage in templates:
        {{ NX_DOCUMENTATION_LINK }}
        {{ NX_HOMEPAGE_TEXT }}
        {{ NX_CUSTOM_TITLE }}
        {{ NX_HOMEPAGE_LOGO }}
        {{ NX_FOOTER_LOGO }}
        {{ NX_FOOTER_LINK }}
    """
    return {
        'NX_DOCUMENTATION_LINK': getattr(settings, 'NX_DOCUMENTATION_LINK', ''),
        'NX_HOMEPAGE_TEXT': getattr(settings, 'NX_HOMEPAGE_TEXT', ''),
        'NX_CUSTOM_TITLE': getattr(settings, 'CUSTOM_TITLE', 'Welcome to NexusLIMS!'),
        'NX_HOMEPAGE_LOGO': getattr(settings, 'NX_HOMEPAGE_LOGO', 'nexuslims/img/logo_horizontal_text.png'),
        'NX_FOOTER_LOGO': getattr(settings, 'NX_FOOTER_LOGO', 'nexuslims/img/datasophos_logo.png'),
        'NX_FOOTER_LINK': getattr(settings, 'NX_FOOTER_LINK', 'https://datasophos.co'),
    }


def nexuslims_features(request):
    """
    Add NexusLIMS feature flags and configuration to templates.

    Usage in templates:
        {% if NX_ENABLE_DOWNLOADS %}
            <!-- Download buttons -->
        {% endif %}
    """
    return {
        'NX_ENABLE_DOWNLOADS': getattr(settings, 'NX_ENABLE_DOWNLOADS', True),
        'NX_ENABLE_TUTORIALS': getattr(settings, 'NX_ENABLE_TUTORIALS', True),
        'NX_VERSION': getattr(settings, 'NX_VERSION', 'dev'),
    }
