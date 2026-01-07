"""XSL Transformation tag with NexusLIMS parameter passing support

This module overrides core_main_app's xsl_transform_tag to enable passing
custom parameters (like detail_url, xmlName) to XSLT transformations.

Changes from core_main_app version:
1. Uses custom xsl_transform from nexuslims_overrides.xml that supports parameters
2. Extracts known parameters with .pop() to isolate extra parameters
3. Passes extra parameters through to XSLT engine via **kwargs
4. Specifically handles detail_url for list views and xmlName for detail views
"""

from django import template
from django.contrib.staticfiles import finders

from core_main_app.commons import exceptions
from core_main_app.components.template_xsl_rendering import (
    api as template_xsl_rendering_api,
)
from core_main_app.components.xsl_transformation import (
    api as xsl_transformation_api,
)
from core_main_app.settings import DEFAULT_DATA_RENDERING_XSLT
from core_main_app.utils.file import read_file_content

# Use custom xsl_transform that supports parameter passing
from nexuslims_overrides.xml import xsl_transform

register = template.Library()


class XSLType:
    """XSLType"""

    type_list = "List"
    type_detail = "Detail"


@register.simple_tag(name="xsl_transform_list")
def render_xml_as_html_list(*args, **kwargs):
    """Render an XML to HTML using the list xslt.

    Args:
        *args: Positional arguments (unused)
        **kwargs: Keyword arguments
            xml_content (str): XML content to transform
            template_id (str, optional): Template ID for XSLT lookup
            template_hash (str, optional): Template hash for XSLT lookup
            xslt_id (str, optional): Direct XSLT transformation ID
            detail_url (str, optional): URL to detail page (passed to XSLT)
            **extra: Additional parameters passed to XSLT

    Returns:
        str: Transformed HTML

    """
    # Format detail_url in-place as XSLT string parameter (wrapped in quotes)
    if 'detail_url' in kwargs:
        kwargs['detail_url'] = f"\"{kwargs['detail_url']}\""

    return _render_xml_as_html(XSLType.type_list, *args, **kwargs)


@register.simple_tag(name="xsl_transform_detail")
def render_xml_as_html_detail(*args, **kwargs):
    """Render an XML to HTML using the detail xslt.

    Args:
        *args: Positional arguments (unused)
        **kwargs: Keyword arguments
            xml_content (str): XML content to transform
            template_id (str, optional): Template ID for XSLT lookup
            template_hash (str, optional): Template hash for XSLT lookup
            xslt_id (str, optional): Direct XSLT transformation ID
            xmlName (str, optional): Name of the XML document (passed to XSLT)
            **extra: Additional parameters passed to XSLT

    Returns:
        str: Transformed HTML

    """
    # Format xmlName as XSLT string parameter (wrapped in quotes)
    if 'xmlName' in kwargs:
        kwargs['xmlName'] = f"\"{kwargs['xmlName']}\""

    # Add data ID if provided
    if 'data_id' in kwargs:
        kwargs['dataId'] = f"\"{kwargs.pop('data_id')}\""

    # Add permission URL if request is provided
    if 'request' in kwargs:
        try:
            from django.urls import reverse
            permission_url = reverse('core_main_app_rest_data_permissions')
            kwargs['permissionUrl'] = f"\"{permission_url}\""
        except Exception:
            # If URL reversal fails, don't add permission URL
            pass

    return _render_xml_as_html(XSLType.type_detail, *args, **kwargs)


def _render_xml_as_html(xslt_type, *args, **kwargs):
    """Render an XML to HTML according to an xslt type (list or detail).

    Args:
        xml_string (str): XML content to transform
        template_id (str, optional): Template ID for XSLT lookup
        template_hash (str, optional): Template hash for XSLT lookup
        xslt_type (str): Type of XSLT (list or detail)
        xsl_transform_id (str, optional): Direct XSLT transformation ID
        **kwargs: Additional keyword arguments passed to XSLT transformer
            These become XSLT parameters accessible in the stylesheet

    Returns:
        str: Transformed HTML, or original XML string on error

    """
    # NexusLIMS: pop these kwargs instead of get so they're not in kwargs
    # when we pass to xsl_transform(), which can cause exceptions when
    # the values are not strings
    xml_string = kwargs.pop("xml_content", "")
    template_id = kwargs.pop("template_id", None)
    template_hash = kwargs.pop("template_hash", None)
    xsl_transform_id = kwargs.pop("xslt_id", None)
    request = kwargs.pop("request", None)

    # Add instrument color mappings from Django settings
    from django.conf import settings
    if hasattr(settings, 'NX_INSTRUMENT_COLOR_MAPPINGS'):
        color_mappings = settings.NX_INSTRUMENT_COLOR_MAPPINGS
        # Convert the Python dict to a format that XSLT can parse
        # Create the format XSLT expects: '"pid1":"color1","pid2":"color2"'
        # Wrap the entire string in single quote to make it a valid XPath string literal
        xslt_format = ",".join([f"\"{pid}\":\"{color}\"" for pid, color in color_mappings.items()])
        kwargs['instrColorMappings'] = f"'{xslt_format}'"

    # Extract useful string values from request if provided
    # (request object itself can't be serialized for XSLT)
    if request:
        pass
        # Could add base URL or other request info as XSLT parameters if needed
        # e.g., kwargs['baseUrl'] = f'"{request.build_absolute_uri("/")}"'

    # NexusLIMS custom parameters xmlName and detail_url are
    # still in kwargs and should be passed to xsl_transform()

    try:
        try:
            if xslt_type not in (XSLType.type_list, XSLType.type_detail):
                raise Exception(
                    "XSLT Type unknown. Default xslt will be used."
                )
            if xsl_transform_id:
                xsl_transformation = xsl_transformation_api.get_by_id(
                    xsl_transform_id
                )
            elif template_id or template_hash:
                if template_id:
                    template_xsl_rendering = (
                        template_xsl_rendering_api.get_by_template_id(
                            template_id
                        )
                    )
                else:
                    template_xsl_rendering = (
                        template_xsl_rendering_api.get_by_template_hash(
                            template_hash
                        )
                    )

                if xslt_type == XSLType.type_list:
                    xsl_transformation = template_xsl_rendering.list_xslt
                else:
                    xsl_transformation = (
                        template_xsl_rendering.default_detail_xslt
                    )
            else:
                raise Exception(
                    "No template information provided. Default xslt will be used."
                )

            xslt_string = xsl_transformation.content

        except (Exception, exceptions.DoesNotExist):
            default_xslt_path = finders.find(DEFAULT_DATA_RENDERING_XSLT)
            xslt_string = read_file_content(default_xslt_path)

        # Pass kwargs through to xsl_transform to enable XSLT parameters
        return xsl_transform(xml_string, xslt_string, **kwargs)
    except Exception:
        return xml_string
