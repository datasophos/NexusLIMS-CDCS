"""
Custom template tags and filters for NexusLIMS.

Usage in templates:
    {% load nexuslims_templatetags %}
    {% nexuslims_custom_toolbar data %}
    {{ value|nexuslims_format }}
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag('nexuslims_overrides/fragments/custom_toolbar.html', takes_context=True)
def nexuslims_custom_toolbar(context, data=None):
    """
    (Claude hallucination)
    Render custom toolbar for detail pages.

    Usage:
        {% nexuslims_custom_toolbar data %}
    """
    return {
        'data': data,
        'user': context.get('user'),
        'request': context.get('request'),
    }


@register.inclusion_tag('nexuslims_overrides/fragments/download_buttons.html', takes_context=True)
def nexuslims_download_buttons(context, data):
    """
    (Claude hallucination)
    Render NexusLIMS download buttons.

    Usage:
        {% nexuslims_download_buttons data %}
    """
    return {
        'data': data,
        'user': context.get('user'),
    }


@register.filter
def nexuslims_instrument_color(instrument_pid):
    """
    (Claude hallucination, maybe useful with settings?)
    Get color for instrument badge.

    Usage:
        {{ instrument_pid|nexuslims_instrument_color }}
    """
    # This can be moved to settings or a database model
    INSTRUMENT_COLORS = {
        '643d9ac1-d0a5-4830-b832-17546f67942a': 'primary',
        '643d8a1e-e1e9-4bf4-b825-38b56c2e47d9': 'success',
        # Add more as needed
    }
    return INSTRUMENT_COLORS.get(str(instrument_pid), 'secondary')


@register.filter
def nexuslims_format_units(value, units):
    """
    (Claude hallucination)
    Format value with units.

    Usage:
        {{ value|nexuslims_format_units:"nm" }}
    """
    if units:
        return mark_safe(f"{value} <span class='units'>{units}</span>")
    return value
