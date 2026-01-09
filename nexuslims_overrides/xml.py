""" Xml utils for the core applications
    Override of some functions in core_main_app.utils.xml
"""
import logging
import traceback

from django.conf import settings

import core_main_app.commons.exceptions as exceptions
from xml_utils.xsd_tree.xsd_tree import XSDTree

logger = logging.getLogger(__name__)

def xsl_transform(xml_string, xslt_string, **kwargs):
    """Apply transformation to xml, allowing for parameters to the XSLT

    Args:
        xml_string:
        xslt_string:
        kwargs : dict
            Other keyword arguments are passed as parameters to the XSLT object

    Returns:

    """
    try:
        # Build the XSD and XSLT etrees
        xslt_tree = XSDTree.build_tree(xslt_string)
        xsd_tree = XSDTree.build_tree(xml_string)

        # Get the XSLT transformation and transform the XSD
        transform = XSDTree.transform_to_xslt(xslt_tree)   # etree.XSLT object
        transformed_tree = transform(xsd_tree, **kwargs)
        return str(transformed_tree)
    except Exception as e:
        for error in transform.error_log:
            print(f"LXML ERROR: {error}")
        traceback.print_exc()
        raise exceptions.CoreError("An unexpected exception happened while transforming the XML") from e
    finally:
        # print messages from transformation, if configured
        if hasattr(settings, 'NX_XSLT_DEBUG'):
            if settings.NX_XSLT_DEBUG:
                if transform.error_log:
                    print("NX_XSLT_DEBUG output:")
                    print("-" * 21)
                for entry in transform.error_log:
                    print(entry.message)
