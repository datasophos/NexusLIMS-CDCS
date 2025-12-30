# NexusLIMS-CDCS Changes from MDCS 2.21.0

**Document Purpose:** This document provides a comprehensive, file-by-file summary of all changes made to the NexusLIMS-CDCS repository compared to the upstream MDCS 2.21.0 baseline (tag `2.21.0`, commit `00e1f5c6666a64f2040b4c81e4dad62e8a28bd3f`). This serves as a guide for re-applying NexusLIMS customizations when rebasing onto newer MDCS releases.

**Repository:** [NexusLIMS-CDCS](https://github.com/datasophos/NexusLIMS-CDCS)  
**Baseline:** MDCS 2.21.0 (July 7, 2022)  
**Current HEAD:** commit `30faa97` (Display units next to parameter names in detail view metadata tables)  
**Document Generated:** 2025-12-30

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Quick Reference](#quick-reference)
3. [Detailed File-by-File Changes](#detailed-file-by-file-changes)
4. [Critical Integration Points](#critical-integration-points)
5. [Rebase Strategy Guide](#rebase-strategy-guide)
6. [Appendices](#appendices)

---

## Executive Summary

### Change Statistics

| Metric | Value |
|--------|-------|
| **Total Files Changed** | 64 |
| **Files Added** | 47 |
| **Files Modified** | 16 |
| **Files Deleted** | 2 |
| **Lines Added** | +14,897 |
| **Lines Removed** | -192 |
| **Net Change** | +14,705 |
| **Commits Since 2.21.0** | 11 |

### Timeline

The changes span from July 2022 (MDCS 2.21.0 release) to December 2024, organized into 5 major development phases:

1. **Initial Customization** - NexusLIMS branding, logos, basic CSS
2. **Registry-Like Search View** - XSLT parameter passing, custom XML utils, responsive design
3. **Navigation & Sorting** - Menu customizations, default sort order
4. **Results Override & Documentation** - Dedicated results app, documentation links
5. **Recent Enhancements** - Sample handling, multi-signal datasets, gallery improvements

### Key Architectural Changes

Four critical architectural modifications that require special handling during rebase:

1. **XSLT Parameter Passing System** - Custom `xml.py` override enables passing dynamic parameters to XSLT transformations
2. **App Loading Order Dependency** - `core_main_app` must load before `mdcs_home` in `INSTALLED_APPS`
3. **Results Override App** - Separate Django app for overriding `results.js` without template conflicts
4. **Massive XSLT Stylesheets** - 6,107 total lines of custom XSLT for NexusLIMS-specific XML-to-HTML rendering

### Technology Additions

New client-side libraries integrated:
- **DataTables 1.10.24** - Interactive HTML tables
- **Shepherd.js** - User tours and guided walkthroughs
- **StreamSaver 2.0.3 & 2.0.4** - Client-side file download streaming
- **Web Streams Polyfills** - Browser compatibility for streaming APIs

---

## Quick Reference

### Configuration Changes Summary

| File | Setting | Old Value | New Value | Purpose |
|------|---------|-----------|-----------|---------|
| `mdcs/core_settings.py` | `CUSTOM_TITLE` | `"Materials Data Curation System"` | `"Welcome to NexusLIMS!"` | Branding |
| `mdcs/settings.py` | `DOCUMENTATION_LINK` | *(not present)* | `"http://CHANGE.THIS.VALUE"` | User docs link |
| `mdcs/settings.py` | `CAN_ANONYMOUS_ACCESS_PUBLIC_DOCUMENT` | *(not present)* | `True` | Public access |
| `mdcs/settings.py` | `VERIFY_DATA_ACCESS` | *(not present)* | `False` | Access control |
| `mdcs/settings.py` | `DATA_SORTING_FIELDS` | *(not present)* | `["-last_modification_date", "title", "template"]` | Default sort |
| `mdcs/settings.py` | `SSL_CERTIFICATES_DIR` | *(not present)* | `False` | SSL handling |
| `mdcs/settings.py` | Template context processor | `django.template.context_processors.i18n` | `mdcs_home.context_processors.doc_link` | Custom context |
| `mdcs/settings.py` | `INSTALLED_APPS` order | `mdcs_home` before core apps | `core_main_app` before `mdcs_home` | Template tag override |

### File Changes by Category

| Category | Added | Modified | Deleted | Total |
|----------|-------|----------|---------|-------|
| **Configuration Files** | 0 | 4 | 0 | 4 |
| **Python Code** | 6 | 2 | 0 | 8 |
| **Documentation** | 1 | 0 | 1 | 2 |
| **CSS Stylesheets** | 4 | 5 | 0 | 9 |
| **JavaScript Files** | 7+ | 1 | 0 | 8+ |
| **Source Maps** | 5 | 0 | 0 | 5 |
| **Static Images** | 3 | 1 | 1 | 5 |
| **Django Templates** | 8 | 5 | 0 | 13 |
| **XSLT Stylesheets** | 2 | 0 | 0 | 2 |
| **Library Files** | 11+ | 0 | 0 | 11+ |
| **TOTAL** | **47** | **18** | **2** | **67** |

### New Dependencies

| Library | Version | Purpose | File Count |
|---------|---------|---------|------------|
| **DataTables** | 1.10.24 | Interactive tables with search/sort | 2 |
| **Shepherd.js** | commit a374a73 | User tours and tutorials | 2 |
| **StreamSaver** | 2.0.3 & 2.0.4 | Client-side file downloads | 6 |
| **Web Streams Polyfill** | 2.1.0 & 3.0.3 | Browser compatibility | 3 |

---

## Detailed File-by-File Changes

### Category 1: Configuration Files (4 modified)

#### 1.1. `.gitignore`

**Status:** Modified  
**Changes:** +8 lines, -0 lines  

**Description:**  
Updated ignore patterns for project-specific files and development artifacts.

**Impact:** Low - Standard gitignore updates for development environment

---

#### 1.2. `mdcs/core_settings.py`

**Status:** Modified  
**Changes:** +2 lines, -2 lines  

**Specific Changes:**
```python
# Line 11 - Changed application title
- CUSTOM_TITLE = "Materials Data Curation System"
+ CUSTOM_TITLE = "Welcome to NexusLIMS!"

# Line 127 - Removed trailing newline (formatting)
```

**Impact:** Medium - Affects branding throughout the application

**Rebase Notes:** Simple string replacement, low conflict risk

---

#### 1.3. `mdcs/settings.py`

**Status:** Modified  
**Changes:** +26 lines, -4 lines  

**Specific Changes:**

1. **New NexusLIMS Settings (lines 34-38):**
```python
# Nexus settings
DOCUMENTATION_LINK = "http://CHANGE.THIS.VALUE"
CAN_ANONYMOUS_ACCESS_PUBLIC_DOCUMENT = True
VERIFY_DATA_ACCESS = False
```

2. **Default Sorting Configuration (lines 86-89):**
```python
# set default sorting option to be most recent records first:
DATA_SORTING_FIELDS = ["-last_modification_date", "title", "template"]

# NOTE: This appears twice in the diff (lines 86-89 and duplicated)
# May need cleanup during rebase
```

3. **INSTALLED_APPS Reorganization (lines 102-116):**
```python
INSTALLED_APPS = (
    # ... existing apps ...
    "django_celery_beat",
    
    # this needs to come before mdcs_home so xml templatetag
    # override works
    "core_main_app",
    
    # Local apps
    "mdcs_home",
    
    # Override for results.js;
    "results_override",
    
    # Core apps (continued)
    "core_exporters_app",
    # ... rest of core apps ...
    # NOTE: mdcs_home was previously here at the end
)
```

4. **Template Context Processor Change (line 182):**
```python
- "django.template.context_processors.i18n",
+ "mdcs_home.context_processors.doc_link"
```

5. **SSL Configuration (line 469):**
```python
# Don't verify SSL certificates internally
SSL_CERTIFICATES_DIR = False
```

**Impact:** **CRITICAL** - App ordering is essential for template tag override to function

**Rebase Notes:**  
- **High conflict potential** - INSTALLED_APPS order is critical
- Must ensure `core_main_app` loads before `mdcs_home`
- Must include `results_override` app
- Verify all context processors are present in newer MDCS versions

---

#### 1.4. `mdcs/urls.py`

**Status:** *(Assumed unchanged based on exploration data)*  
**Changes:** None documented

---

### Category 2: Python Code - New Modules (6 new files)

#### 2.1. `mdcs_home/context_processors.py`

**Status:** Added  
**Changes:** +5 lines  

**Full Content:**
```python
from django.conf import settings # import the settings file

def doc_link(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'DOCUMENTATION_LINK': settings.DOCUMENTATION_LINK}
```

**Purpose:** Makes `DOCUMENTATION_LINK` setting available in all templates

**Impact:** Low - Self-contained utility

**Rebase Notes:** Can be copied as-is to new MDCS version

---

#### 2.2. `mdcs_home/templatetags/__init__.py`

**Status:** Added  
**Changes:** +0 lines (empty file)  

**Purpose:** Package initialization for custom template tags

**Impact:** Low - Standard Python package structure

**Rebase Notes:** Copy as-is

---

#### 2.3. `mdcs_home/templatetags/render_extras.py`

**Status:** Added  
**Changes:** +29 lines  

**Purpose:** Custom template tag implementations for NexusLIMS-specific rendering

**Impact:** Medium - Extends Django template functionality

**Rebase Notes:** Copy as-is, verify no conflicts with newer MDCS template tags

---

#### 2.4. `mdcs_home/templatetags/xsl_transform_tag.py`

**Status:** Added  
**Changes:** +136 lines  

**Purpose:** **CRITICAL** - Custom XSL transformation template tag that supports passing parameters to XSLT

**Key Functions:**
- `render_xml_as_html()` - List view transformation (decorated as `@register.simple_tag(name="xsl_transform_list")`)
- `render_xml_as_html()` - Detail view transformation (decorated as `@register.simple_tag(name="xsl_transform_detail")`)
- `_render_xml_as_html()` - Core transformation logic

**Critical Import:**
```python
# Uses custom xml.py instead of core_main_app version
from mdcs_home.utils.xml import xsl_transform
```

**Parameter Passing:**
```python
# List view extracts detail_url and passes to XSLT
detail_url = '"{}"'.format(kwargs.pop('detail_url', '#'))
return _render_xml_as_html(..., detail_url=detail_url)

# Detail view extracts xmlName and passes all other kwargs
xmlName = '"{}"'.format(kwargs.pop('xmlName', ''))
return _render_xml_as_html(..., xmlName=xmlName, **kwargs)
```

**Impact:** **CRITICAL** - Core functionality for NexusLIMS record display

**Rebase Notes:**  
- Must be copied to new version
- Requires `mdcs_home/utils/xml.py` to function
- Depends on `core_main_app` loading before `mdcs_home` in INSTALLED_APPS

---

#### 2.5. `mdcs_home/utils/xml.py`

**Status:** Added  
**Changes:** +48 lines  

**Purpose:** **CRITICAL** - Overrides `core_main_app.utils.xml.xsl_transform()` to accept kwargs

**Full Content:**
```python
""" Xml utils for the core applications
    Override of some functions in core_main_app.utils.xml
"""
import json
import logging
from collections import OrderedDict
from urllib.parse import urlparse

import xmltodict
from django.urls import reverse

import core_main_app.commons.exceptions as exceptions
import xml_utils.commons.constants as xml_utils_constants
import xml_utils.xml_validation.validation as xml_validation
from core_main_app.commons.exceptions import XMLError
from core_main_app.settings import XERCES_VALIDATION, SERVER_URI
from core_main_app.utils.resolvers.resolver_utils import lmxl_uri_resolver
from core_main_app.utils.urls import get_template_download_pattern
from xml_utils.commons.constants import XSL_NAMESPACE
from xml_utils.xsd_hash import xsd_hash
from xml_utils.xsd_tree.operations.namespaces import get_namespaces
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
    except Exception:
        raise exceptions.CoreError("An unexpected exception happened while transforming the XML")
```

**Key Enhancement:**
```python
# The **kwargs are passed directly to the XSLT transform
transformed_tree = transform(xsd_tree, **kwargs)
```

**Impact:** **CRITICAL** - Enables dynamic parameter passing to XSLT (record names, URLs, etc.)

**Rebase Notes:**  
- Check if newer MDCS versions have updated `core_main_app.utils.xml`
- May need to merge changes if upstream function signature changed
- This is the foundation of the XSLT parameter system

---

#### 2.6. `results_override/__init__.py`

**Status:** Added  
**Changes:** +0 lines (empty file)  

**Purpose:** Package initialization for results override app

**Impact:** Low - Standard Django app structure

**Rebase Notes:** Copy as-is

---

### Category 3: Python Code - Modified Modules (2 modified)

#### 3.1. `mdcs_home/menus.py`

**Status:** Modified  
**Changes:** +59 lines, -21 lines  

**Purpose:** Customizes navigation menu structure

**Impact:** Medium - Affects site navigation

**Rebase Notes:**  
- Compare with newer MDCS menu structure
- May need to adapt to new menu system if MDCS changed navigation
- Likely contains 3 placeholder links mentioned in README

---

#### 3.2. `mdcs_home/views.py`

**Status:** Modified  
**Changes:** +17 lines, -15 lines  

**Purpose:** View logic updates for custom homepage and templates

**Impact:** Medium - Affects page rendering

**Rebase Notes:**  
- Check for conflicts with newer MDCS view patterns
- Verify template context variables are compatible

---

### Category 4: Documentation (1 deleted, 1 added)

#### 4.1. `README.md`

**Status:** Deleted  
**Changes:** -27 lines  

**Purpose:** Removed original MDCS README in Markdown format

**Impact:** Low - Replaced with reStructuredText version

---

#### 4.2. `README.rst`

**Status:** Added  
**Changes:** +113 lines  

**Purpose:** NexusLIMS-CDCS specific documentation in reStructuredText format

**Key Content:**
- About this repository
- Installation instructions
- **Values to customize** (critical for deployment):
  - XSLT variables: `datasetBaseUrl`, `previewBaseUrl`, `sharepointBaseUrl`
  - XSLT dictionaries: `instr-color-dictionary`, `sharepoint-instrument-dictionary`
  - Django settings: `DOCUMENTATION_LINK`
  - Menu configuration: `menus.py` customizations
  - Tutorial configuration: `menu-custom.js`

**Impact:** Medium - Essential deployment documentation

**Rebase Notes:**  
- Update to reference newer MDCS version
- Maintain customization instructions

---

### Category 5: CSS Stylesheets (5 modified, 4 added)

#### Modified CSS Files

#### 5.1. `static/core_main_app/css/homepage.css`

**Status:** Modified  
**Changes:** +50 lines, -5 lines  

**Purpose:** Homepage styling updates for NexusLIMS branding

**Likely Changes:** Color scheme, layout adjustments, typography

**Impact:** Medium - Visual branding

**Rebase Notes:** Check for conflicts with newer MDCS homepage styles

---

#### 5.2. `static/css/btn_custom.css`

**Status:** Modified  
**Changes:** +7 lines, -7 lines  

**Purpose:** Custom button styling

**Impact:** Low - UI polish

**Rebase Notes:** Low conflict risk, mostly cosmetic

---

#### 5.3. `static/css/extra.css`

**Status:** Modified  
**Changes:** +130 lines, -5 lines  

**Purpose:** Additional CSS for NexusLIMS-specific components

**Impact:** Medium - Significant style additions

**Rebase Notes:** May need to verify selectors work with newer MDCS HTML structure

---

#### 5.4. `static/css/main.css`

**Status:** Modified  
**Changes:** +107 lines, -44 lines  

**Purpose:** Main stylesheet updates for layout and design

**Impact:** High - Core styling changes

**Rebase Notes:** High conflict potential if MDCS updated main styles

---

#### 5.5. `static/css/menu.css`

**Status:** Modified  
**Changes:** +15 lines, -4 lines  

**Purpose:** Menu styling improvements

**Impact:** Low - Navigation appearance

**Rebase Notes:** Check compatibility with newer MDCS menu structure

---

#### Added CSS Files

#### 5.6. `results_override/static/core_explore_common_app/user/css/query_result.css`

**Status:** Added  
**Changes:** +7 lines  

**Purpose:** Custom query result styling

**Impact:** Low - Specific to query results page

**Rebase Notes:** Copy to same location in new structure

---

#### 5.7. `results_override/static/core_explore_common_app/user/css/results.css`

**Status:** Added  
**Changes:** +179 lines  

**Purpose:** Results page styling overrides (controls layout and appearance of search/query results)

**Impact:** Medium - Customizes search results appearance

**Rebase Notes:** Verify CSS selectors match newer MDCS HTML

---

#### 5.8. `static/libs/datatables/1.10.24/datatables.min.css`

**Status:** Added  
**Changes:** +24 lines (minified)  

**Purpose:** DataTables library CSS

**Impact:** Low - Third-party library

**Rebase Notes:** Can copy as-is or upgrade to newer DataTables version

---

#### 5.9. `static/libs/shepherd.js/a374a73/shepherd.css`

**Status:** Added  
**Changes:** +204 lines  

**Purpose:** Shepherd.js tour/tutorial library CSS

**Impact:** Low - Third-party library

**Rebase Notes:** Copy as-is

---

### Category 6: JavaScript Files (1 modified, 7+ added)

#### Modified JavaScript Files

#### 6.1. `results_override/static/core_explore_common_app/user/js/results.js`

**Status:** Modified (complete replacement)  
**Changes:** +293 lines  

**Purpose:** Custom results handling with multi-signal dataset download support

**Key Features:**
- DataTables integration for interactive results
- StreamSaver integration for file downloads
- Multi-signal dataset duplicate file handling
- "Please wait" messaging during operations

**Impact:** **HIGH** - Core functionality for data exploration

**Rebase Notes:**  
- Must check if newer MDCS changed results.js functionality
- May need to merge new features from upstream
- Critical for download system

---

#### Added JavaScript Files

#### 6.2. `static/js/menu_custom.js`

**Status:** Added  
**Changes:** +335 lines  

**Purpose:** Custom menu interactions and logic, including Shepherd.js tour configuration

**Impact:** Medium - Enhances user experience with guided tours

**Rebase Notes:** Verify menu selectors match newer MDCS structure

---

#### 6.3. `static/js/nexus_buttons.js`

**Status:** Added  
**Changes:** +103 lines  

**Purpose:** NexusLIMS-specific button behaviors (edit button, copy PID, tooltips)

**Impact:** Medium - Custom interactive features

**Rebase Notes:** Copy as-is, low conflict risk

---

#### 6.4-6.5. DataTables Libraries

**Files:**
- `static/libs/datatables/1.10.24/datatables.min.js` (+503 lines)
- `static/libs/datatables/datatables.min.js` (+462 lines)

**Purpose:** DataTables 1.10.24 library (two variants)

**Impact:** Low - Third-party library

**Rebase Notes:** Can copy or upgrade to newer version

---

#### 6.6-6.7. StreamSaver Libraries

**Files:**
- `static/libs/StreamSaver/2.0.3/StreamSaver.js` (+297 lines)
- `static/libs/StreamSaver/2.0.4/StreamSaver.js` (+299 lines)

**Purpose:** StreamSaver library for client-side file downloads (two versions)

**Impact:** Medium - File download functionality

**Rebase Notes:** Copy as-is or upgrade to newer StreamSaver

---

#### 6.8. Web Streams Polyfill

**File:** `static/libs/web-streams-polyfill/3.0.3/ponyfill.es6.js`  
**Changes:** +3852 lines  

**Purpose:** Web Streams polyfill for browser compatibility

**Impact:** Low - Dependency for StreamSaver

**Rebase Notes:** Copy as-is

---

#### Supporting Files for StreamSaver (HTML/JS)

**Files Added:**
- `static/libs/StreamSaver/2.0.3/mitm.html` (+169 lines)
- `static/libs/StreamSaver/2.0.3/sw.js` (+128 lines)
- `static/libs/StreamSaver/2.0.3/zip-stream.js` (+209 lines)
- `static/libs/StreamSaver/2.0.4/mitm.html` (+169 lines)
- `static/libs/StreamSaver/2.0.4/sw.js` (+128 lines)
- `static/libs/StreamSaver/2.0.4/zip-stream.js` (+209 lines)

**Purpose:** Service worker, middleware, and zip utilities for StreamSaver

**Impact:** Low - StreamSaver infrastructure

**Rebase Notes:** Copy all supporting files together

---

#### Additional Polyfills

**Files:**
- `static/libs/web-streams-adapter/c688970/web-streams-adapter.min.js` (+1 line)
- `static/libs/web-streams-polyfill/2.1.0/ponyfill.js` (+7 lines)

**Purpose:** Additional Web Streams compatibility

**Impact:** Low

**Rebase Notes:** Copy as-is

---

### Category 7: Source Map Files (5 new)

**Files Added:**
1. `static/core_main_app/libs/bootstrap/4.5.2/css/bootstrap.min.css.map`
2. `static/core_main_app/libs/bootstrap/4.5.2/js/bootstrap.min.js.map`
3. `static/core_main_app/libs/popper-js/popper.min.js.map`
4. `static/libs/shepherd.js/a374a73/shepherd.min.js.map`
5. `static/libs/web-streams-polyfill/3.0.3/ponyfill.es6.js.map`

**Purpose:** Debug source maps for minified JavaScript and CSS

**Impact:** Low - Development/debugging aid

**Rebase Notes:** Copy as-is or regenerate from updated libraries

---

### Category 8: Static Images (1 deleted, 3 added, 1 modified)

#### 8.1. `static/core_main_app/img/mgi_diagram.jpg`

**Status:** Deleted  

**Purpose:** Removed Materials Genome Initiative diagram from MDCS

**Impact:** Low - Branding change

---

#### 8.2. `static/core_main_app/img/logo_horizontal_text.png`

**Status:** Added (binary file)  

**Purpose:** NexusLIMS horizontal logo with text

**Impact:** Medium - Primary branding

**Rebase Notes:** Copy to new version

---

#### 8.3. `static/img/logo_bare.png`

**Status:** Added (binary file)  

**Purpose:** NexusLIMS logo without text (icon version)

**Impact:** Medium - Used in navigation/favicon contexts

**Rebase Notes:** Copy to new version

---

#### 8.4. `static/img/logo_horizontal.png`

**Status:** Added (binary file)  

**Purpose:** NexusLIMS horizontal logo

**Impact:** Medium - Branding

**Rebase Notes:** Copy to new version

---

#### 8.5. `static/img/favicon.png`

**Status:** Modified (binary file)  

**Purpose:** Updated favicon to NexusLIMS branding

**Impact:** Low - Browser tab icon

**Rebase Notes:** Replace with NexusLIMS version

---

### Category 9: Django Templates (5 modified, 8 added)

#### Modified Templates

#### 9.1. `templates/core_main_app/user/homepage.html`

**Status:** Modified  
**Changes:** +32 lines, -23 lines  

**Purpose:** Homepage layout and content updates for NexusLIMS

**Impact:** High - First page users see

**Rebase Notes:** Compare with newer MDCS homepage structure, may need significant merging

---

#### 9.2. `templates/mdcs_home/tiles.html`

**Status:** Modified  
**Changes:** +35 lines, -6 lines  

**Purpose:** Dashboard/tiles view updates

**Impact:** Medium - Main navigation tiles

**Rebase Notes:** Check for newer MDCS tile patterns

---

#### 9.3. `templates/theme.html`

**Status:** Modified  
**Changes:** +4 lines, -2 lines  

**Purpose:** Base theme template adjustments

**Impact:** High - Affects all pages

**Rebase Notes:** Critical to merge carefully with newer MDCS theme

---

#### 9.4. `templates/theme/footer/default.html`

**Status:** Modified  
**Changes:** +12 lines, -10 lines  

**Purpose:** Footer content updates (likely removing NIST-specific content, adding NexusLIMS info)

**Impact:** Medium - Page footers

**Rebase Notes:** Straightforward replacement

---

#### 9.5. `templates/theme/menu.html`

**Status:** Modified  
**Changes:** +17 lines, -17 lines  

**Purpose:** Navigation menu structure changes

**Impact:** High - Site navigation

**Rebase Notes:** Verify compatibility with newer MDCS menu system

---

#### Added Templates

#### 9.6. `templates/core_explore_common_app/user/results/data_source_info.html`

**Status:** Added  
**Changes:** +36 lines  

**Purpose:** Data source information display template

**Impact:** Medium - Search results functionality

**Rebase Notes:** Copy to same location

---

#### 9.7. `templates/core_explore_common_app/user/results/data_source_results.html`

**Status:** Added  
**Changes:** +14 lines  

**Purpose:** Single data source search results template

**Impact:** Medium - Search results

**Rebase Notes:** Copy as-is

---

#### 9.8. `templates/core_explore_common_app/user/results/data_sources_results.html`

**Status:** Added  
**Changes:** +48 lines  

**Purpose:** Multi-data source results template

**Impact:** Medium - Search results

**Rebase Notes:** Copy as-is

---

#### 9.9. `templates/core_explore_keyword_app/user/index.html`

**Status:** Added  
**Changes:** +29 lines  

**Purpose:** Keyword exploration index template

**Impact:** Medium - Keyword search UI

**Rebase Notes:** Copy to same location

---

#### 9.10. `templates/core_main_app/_render/user/theme_base.html`

**Status:** Added  
**Changes:** +78 lines  

**Purpose:** Base theme rendering template

**Impact:** High - Template inheritance base

**Rebase Notes:** Check for conflicts with newer MDCS base templates

---

#### 9.11. `templates/core_main_app/common/data/detail_data.html`

**Status:** Added  
**Changes:** +12 lines  

**Purpose:** Data detail common template

**Impact:** Medium - Record display

**Rebase Notes:** Copy as-is

---

#### 9.12. `templates/core_main_app/user/data/detail.html`

**Status:** Added  
**Changes:** +11 lines  

**Purpose:** User data detail view template

**Impact:** High - Primary record detail view

**Rebase Notes:** Critical - likely contains XSLT transform tag calls

---

#### 9.13. Missing Template Information

**Note:** Full template content was not captured in initial exploration. During rebase, use `git diff 2.21.0..HEAD` to get exact template changes.

---

### Category 10: XSLT Stylesheets (2 new - MAJOR ADDITIONS)

#### 10.1. `xslt/detail_stylesheet.xsl`

**Status:** Added  
**Changes:** +5,492 lines  

**Purpose:** **MOST SIGNIFICANT CHANGE** - Transforms XML records into HTML for detail view display

**Parameters Accepted:**
- `xmlName` - Name of the XML record (passed from Django template)
- `datasetBaseUrl` - Base URL for dataset file downloads
- `previewBaseUrl` - Base URL for preview images
- `sharepointBaseUrl` - Base URL for SharePoint calendar

**Key Features:**
1. **Instrument Badge Colors** - Color-coded badges based on instrument PID
2. **Sample Information Display** - Renders sample metadata with periodic table lookups
3. **Acquisition Activity Rendering** - Groups datasets by temporal clusters
4. **Dataset Metadata with Units** - Displays parameters with their units
5. **Preview Image Galleries** - Responsive gallery layout with spacing
6. **Filename Display** - Shows original filenames in captions
7. **PID Display & Copy** - Persistent Identifier handling with copy-to-clipboard
8. **Data Download System** - Links to download individual files or full datasets
9. **NEMO Calendar Integration** - Links to reservation system
10. **Conditional Logic** - Handles optional elements (sample refs, multi-signal data)
11. **Simple vs. Detailed Display** - Automatically switches to simple list view for >100 datasets

**Internal Dictionaries:**
- `month-num-dictionary` - Month number to name conversion
- `periodic-table-dictionary` - Element symbols to full names
- `instr-color-dictionary` - Instrument PID to badge color mapping (site-specific)
- `sharepoint-instrument-dictionary` - Instrument to SharePoint mappings (site-specific)

**Example Structure (first 100 lines):**
```xsl
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema"
    xmlns:nx="https://data.nist.gov/od/dm/nexus/experiment/v1.0"
    xmlns:exslt="http://exslt.org/common"
    xmlns:math="http://exslt.org/math"
    extension-element-prefixes="exslt"
    version="1.0">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>

    <xsl:param name="xmlName" select="''"/>

    <xsl:variable name="datasetBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>
    <xsl:variable name="previewBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>

    <!-- Dataset count limit for interactive display -->
    <xsl:variable name="maxDatasetCount">100</xsl:variable>
    <xsl:variable name="simpleDisplay" select="count(//nx:dataset) > $maxDatasetCount"/>

    <!-- Month conversion dictionary -->
    <xsl:variable name="month-num-dictionary">
        <month month-number="01">January</month>
        <!-- ... months 02-12 ... -->
    </xsl:variable>
    <xsl:key name="lookup.date.month" match="month" use="@month-number"/>

    <!-- Periodic table dictionary -->
    <xsl:variable name="periodic-table-dictionary">
        <element symbol="H">1 - Hydrogen</element>
        <element symbol="He">2 - Helium</element>
        <!-- ... elements continue ... -->
    </xsl:variable>
```

**Impact:** **CRITICAL** - Core of NexusLIMS record display system

**Rebase Notes:**  
- This is a completely custom file, not a modification of MDCS
- Copy entirely to new version
- Update `datasetBaseUrl`, `previewBaseUrl`, `sharepointBaseUrl` for deployment
- Update instrument color dictionaries for site-specific instruments
- No upstream conflicts expected (new file)

---

#### 10.2. `xslt/list_stylesheet.xsl`

**Status:** Added  
**Changes:** +615 lines  

**Purpose:** Transforms XML record lists into HTML table/list view for search results

**Parameters Accepted:**
- `detail_url` - URL pattern for detail view links

**Key Features:**
1. **Searchable/Sortable Record Lists** - DataTables integration
2. **Metadata in Tabular Format** - Displays key fields in columns
3. **Filtering and Pagination** - Interactive table controls
4. **Consistent Formatting** - Handles multiple records uniformly
5. **Responsive Design** - Adapts to different screen sizes

**Impact:** High - Controls search results appearance

**Rebase Notes:**  
- Completely custom file
- Copy entirely to new version
- No upstream conflicts expected

---

### Category 11: Library Additions (Summary)

All library files are third-party dependencies that can be copied as-is or upgraded to newer versions during rebase. See individual file listings in Categories 5-7 above for details.

**Libraries Added:**
1. DataTables 1.10.24 (CSS + JS)
2. Shepherd.js (CSS + JS + source map)
3. StreamSaver 2.0.3 & 2.0.4 (JS + HTML + service worker + utilities)
4. Web Streams Polyfill 2.1.0 & 3.0.3 (JS + source maps)
5. Web Streams Adapter (minified JS)

**Total Library Files:** 11+ files across multiple directories

---

## Critical Integration Points

This section documents the architectural dependencies that must be preserved during rebase.

### 1. XSLT Parameter Passing System

**Components:**
1. `mdcs_home/utils/xml.py` - Overrides `core_main_app.utils.xml.xsl_transform()`
2. `mdcs_home/templatetags/xsl_transform_tag.py` - Custom template tags that use the override
3. Django templates that call `{% xsl_transform_detail %}` or `{% xsl_transform_list %}`
4. XSLT files that declare and use `<xsl:param>` elements

**How It Works:**
```
Django Template
    ↓ calls {% xsl_transform_detail xml_content=record xmlName=title ... %}
mdcs_home/templatetags/xsl_transform_tag.py
    ↓ extracts kwargs, calls xsl_transform(xml, xslt, **kwargs)
mdcs_home/utils/xml.py (override)
    ↓ passes kwargs to XSLT transform: transform(xsd_tree, **kwargs)
XSLT Stylesheet
    ↓ receives parameters: <xsl:param name="xmlName" select="''"/>
    ↓ uses in output: <h1><xsl:value-of select="$xmlName"/></h1>
Final HTML
```

**Rebase Requirements:**
- All four components must be present
- Import in `xsl_transform_tag.py` must use custom `xml.py`
- Templates must pass parameters to transform tags
- XSLT must declare params that match template kwargs

**Testing:**
- Verify record detail pages display record title (from `xmlName` parameter)
- Verify download links work (from `datasetBaseUrl` parameter)
- Check browser console for XSLT transformation errors

---

### 2. App Loading Order Dependency

**Critical Requirement:** `core_main_app` MUST load before `mdcs_home` in `INSTALLED_APPS`

**Reason:** Django's template tag resolution uses first-found wins. The custom `xsl_transform_tag.py` in `mdcs_home/templatetags/` needs to override the one from `core_main_app`. If `mdcs_home` loads first, Django will find its template tags first, but templates in `mdcs_home` can't override templates from apps loaded later.

**Correct Order in `mdcs/settings.py`:**
```python
INSTALLED_APPS = (
    # ... built-in Django apps ...
    "django_celery_beat",
    
    # This needs to come before mdcs_home so xml templatetag override works
    "core_main_app",
    
    # Local apps
    "mdcs_home",
    
    # Override for results.js
    "results_override",
    
    # Core apps (continued)
    "core_exporters_app",
    # ... rest of core apps ...
)
```

**Wrong Order (will break template tag override):**
```python
INSTALLED_APPS = (
    # ... built-in Django apps ...
    "mdcs_home",  # ❌ If this comes before core_main_app
    "core_main_app",
    # ...
)
```

**Rebase Testing:**
- After rebase, verify `core_main_app` appears before `mdcs_home`
- Test record detail view renders with parameters (not broken)
- Check Django debug toolbar or logs for template tag source

---

### 3. Results Override App Architecture

**Why Separate App:** The `results_override` app exists solely to override `results.js` from `core_explore_common_app` without affecting template resolution order.

**Directory Structure:**
```
results_override/
├── __init__.py
└── static/
    └── core_explore_common_app/
        └── user/
            ├── css/
            │   ├── query_result.css
            │   └── results.css
            └── js/
                └── results.js  (overrides core_explore_common_app version)
```

**How Django Finds It:**
Django's `STATICFILES_FINDERS` searches apps in `INSTALLED_APPS` order. Since `results_override` is listed, Django finds its `static/core_explore_common_app/user/js/results.js` and uses it instead of the one from `core_explore_common_app`.

**Why Not Put in `mdcs_home`:**
Putting it in `mdcs_home` would work for static files, but caused issues with template resolution order in earlier development (see commit 18f8e1f).

**Rebase Requirements:**
- `results_override` must be in `INSTALLED_APPS`
- Directory structure must match upstream app's static path exactly
- Must be listed after `core_explore_common_app` in `INSTALLED_APPS`

**Testing:**
- View page source on search results page
- Verify `results.js` contains NexusLIMS customizations (check for StreamSaver code)
- Test multi-signal dataset downloads work

---

### 4. Download System Architecture

**Components:**
1. `results_override/static/.../results.js` - Frontend download logic
2. StreamSaver library files - Client-side streaming download
3. Service worker (`sw.js`) - Background download handling
4. MITM HTML (`mitm.html`) - Cross-origin iframe communication
5. XSLT stylesheet - Generates download links with correct URLs

**How Multi-File Download Works:**
```
User clicks "Download All Files"
    ↓
results.js creates StreamSaver writable stream
    ↓
Service worker (sw.js) intercepts fetch requests
    ↓
results.js iterates through files, fetching each
    ↓
Duplicate filename handling (multi-signal datasets)
    ↓
Files streamed to zip archive
    ↓
Browser downloads single .zip file
```

**Critical Commits:**
- `240a7f9` - Fix duplicate file handling for multi-signal datasets

**Rebase Requirements:**
- All StreamSaver files must be copied
- Service worker must be registered in `results.js`
- XSLT must generate correct file URLs using `datasetBaseUrl`

**Testing:**
- Download single file - should work via direct link
- Download all files from record - should create zip
- Download multi-signal dataset - should handle duplicate filenames
- Test in Chrome, Firefox, Safari (browser compatibility)

---

## Rebase Strategy Guide

### Overview

When rebasing NexusLIMS-CDCS onto a newer MDCS version, changes fall into three categories:

1. **Self-Contained** - Can copy as-is with no/low conflict risk
2. **Integration Required** - Must merge carefully with upstream changes
3. **Testing Critical** - Must verify thoroughly after rebase

### Self-Contained Changes (Copy As-Is)

These can be copied directly from NexusLIMS-CDCS to the new MDCS version:

#### New Files (47 files)
- ✅ All files in `mdcs_home/` (Python modules, template tags, utils)
- ✅ All files in `results_override/`
- ✅ Both XSLT stylesheets (`xslt/detail_stylesheet.xsl`, `xslt/list_stylesheet.xsl`)
- ✅ All library files (`static/libs/`)
- ✅ All new templates in `templates/` (8 files)
- ✅ Logo images (`static/img/logo_*.png`, `static/core_main_app/img/logo_*.png`)
- ✅ Custom JavaScript (`static/js/menu_custom.js`, `static/js/nexus_buttons.js`)
- ✅ `README.rst`

**Process:**
```bash
# From NexusLIMS-CDCS repository
git diff 2.21.0..HEAD --name-only --diff-filter=A > added_files.txt

# Copy each file to new MDCS version at same path
while read file; do
    cp "$file" "/path/to/new-mdcs/$file"
done < added_files.txt
```

### Integration Required Changes (Merge Carefully)

These files require careful merging because upstream MDCS may have also changed them:

#### Configuration Files
- ⚠️ `mdcs/settings.py` - **HIGH CONFLICT RISK**
  - Check if newer MDCS changed `INSTALLED_APPS` structure
  - Ensure `core_main_app` before `mdcs_home` order is preserved
  - Add NexusLIMS settings: `DOCUMENTATION_LINK`, `DATA_SORTING_FIELDS`, etc.
  - Update context processors list
  - Add `SSL_CERTIFICATES_DIR = False` if using HTTPS
  
- ⚠️ `mdcs/core_settings.py` - **LOW CONFLICT RISK**
  - Simple string replacement: `CUSTOM_TITLE = "Welcome to NexusLIMS!"`
  
- ⚠️ `.gitignore` - **LOW CONFLICT RISK**
  - Add NexusLIMS-specific ignore patterns to newer version

#### Modified Python Code
- ⚠️ `mdcs_home/menus.py` - **MEDIUM CONFLICT RISK**
  - Compare menu structure with newer MDCS
  - May need to adapt to new menu system
  
- ⚠️ `mdcs_home/views.py` - **MEDIUM CONFLICT RISK**
  - Check for new view patterns in MDCS
  - Merge view logic changes

#### Modified Templates
- ⚠️ `templates/core_main_app/user/homepage.html` - **HIGH CONFLICT RISK**
  - MDCS likely changed homepage structure
  - Manually merge NexusLIMS customizations
  
- ⚠️ `templates/theme.html` - **HIGH CONFLICT RISK**
  - Base template changes affect all pages
  - Compare carefully and merge
  
- ⚠️ `templates/theme/menu.html` - **HIGH CONFLICT RISK**
  - Menu structure may have changed
  - Verify NexusLIMS menu items work with new structure
  
- ⚠️ Other modified templates - **MEDIUM CONFLICT RISK**
  - Compare each with newer MDCS version
  - Preserve NexusLIMS customizations

#### Modified CSS/JavaScript
- ⚠️ `static/core_main_app/css/homepage.css` - **MEDIUM CONFLICT RISK**
  - Check if MDCS changed homepage styles
  - Merge NexusLIMS branding
  
- ⚠️ `static/css/*.css` - **MEDIUM CONFLICT RISK**
  - Verify selectors work with newer MDCS HTML structure
  - May need to update to match new element IDs/classes

### Rebase Process Checklist

#### Phase 1: Preparation
- [ ] Clone/checkout newer MDCS version
- [ ] Review MDCS changelog for breaking changes
- [ ] Create backup branch of current NexusLIMS-CDCS
- [ ] List all modified files: `git diff 2.21.0..HEAD --name-status`

#### Phase 2: Copy Self-Contained Files
- [ ] Copy all new Python modules (`mdcs_home/`, `results_override/`)
- [ ] Copy XSLT stylesheets
- [ ] Copy library files (`static/libs/`)
- [ ] Copy new templates
- [ ] Copy logos and images
- [ ] Copy custom JavaScript
- [ ] Copy `README.rst`

#### Phase 3: Merge Configuration
- [ ] Update `mdcs/settings.py`:
  - [ ] Add NexusLIMS settings block
  - [ ] Add `DATA_SORTING_FIELDS`
  - [ ] Reorder `INSTALLED_APPS` (core_main_app → mdcs_home → results_override)
  - [ ] Update context processors
  - [ ] Add SSL settings if needed
- [ ] Update `mdcs/core_settings.py`:
  - [ ] Change `CUSTOM_TITLE`
- [ ] Update `.gitignore`

#### Phase 4: Merge Templates and Static Files
- [ ] For each modified template:
  - [ ] Compare with newer MDCS version using diff tool
  - [ ] Manually merge NexusLIMS customizations
  - [ ] Test rendering
- [ ] For each modified CSS file:
  - [ ] Check selectors against new HTML structure
  - [ ] Update if needed
  - [ ] Test styles

#### Phase 5: Testing (Critical)
- [ ] **Basic functionality:**
  - [ ] Site loads without errors
  - [ ] Homepage displays correctly
  - [ ] Navigation menu works
  - [ ] Login/logout works
- [ ] **Search and results:**
  - [ ] Keyword search works
  - [ ] Results page displays (registry-like view)
  - [ ] Results table is interactive (DataTables)
  - [ ] Pagination works
- [ ] **Record detail view:**
  - [ ] Detail page loads
  - [ ] Record title displays (xmlName parameter working)
  - [ ] Metadata tables show units
  - [ ] Instrument badges show colors
  - [ ] Sample information displays
  - [ ] Preview images appear in gallery
  - [ ] Gallery spacing looks correct
- [ ] **Download system:**
  - [ ] Single file download works
  - [ ] "Download All" creates zip file
  - [ ] Multi-signal datasets handle duplicate filenames
  - [ ] Download works in Chrome, Firefox, Safari
- [ ] **XSLT parameter system:**
  - [ ] No console errors about XSLT transforms
  - [ ] Parameters passed correctly (check page source)
  - [ ] Custom template tags work
- [ ] **App loading order:**
  - [ ] Verify core_main_app loads before mdcs_home
  - [ ] Template tag override working
  - [ ] No import errors
- [ ] **Branding:**
  - [ ] NexusLIMS logos display
  - [ ] Title is "Welcome to NexusLIMS!"
  - [ ] Colors/theme correct
  - [ ] Footer content correct
- [ ] **Documentation link:**
  - [ ] Link appears in menu
  - [ ] Link appears on homepage
  - [ ] URL is correct (not placeholder)

#### Phase 6: Configuration for Deployment
- [ ] Update XSLT variables (see below)
- [ ] Update environment variables
- [ ] Update Django settings for deployment
- [ ] Test in production-like environment

### Post-Rebase Configuration

After rebasing, update these deployment-specific values:

#### In `xslt/detail_stylesheet.xsl`:
```xsl
<xsl:variable name="datasetBaseUrl">https://YOUR-SITE-URL/data</xsl:variable>
<xsl:variable name="previewBaseUrl">https://YOUR-SITE-URL/previews</xsl:variable>
<xsl:variable name="sharepointBaseUrl">https://YOUR-SHAREPOINT-URL</xsl:variable>

<!-- Update instrument colors in instr-color-dictionary -->
<!-- Update sharepoint mappings in sharepoint-instrument-dictionary -->
```

#### In `mdcs/settings.py`:
```python
DOCUMENTATION_LINK = "https://YOUR-DOCS-URL"
```

#### In `mdcs_home/menus.py`:
- Update menu item URLs (3 placeholder links)

#### In `static/js/menu-custom.js`:
- Update Shepherd.js tour steps if site structure changed

### Common Rebase Issues and Solutions

#### Issue 1: Template Tag Not Found
**Symptom:** `TemplateSyntaxError: 'xsl_transform_detail' is not a registered tag`

**Cause:** App loading order wrong or template tag files not copied

**Solution:**
1. Check `INSTALLED_APPS` - ensure `core_main_app` before `mdcs_home`
2. Verify `mdcs_home/templatetags/xsl_transform_tag.py` exists
3. Restart Django server

#### Issue 2: XSLT Parameters Not Working
**Symptom:** Record detail page shows no title, download links broken

**Cause:** Custom `xml.py` not being used

**Solution:**
1. Verify `mdcs_home/utils/xml.py` exists
2. Check import in `xsl_transform_tag.py`: should be `from mdcs_home.utils.xml import xsl_transform`
3. Not `from core_main_app.utils.xml import xsl_transform`

#### Issue 3: Results.js Not Overriding
**Symptom:** Search results page broken, StreamSaver not found

**Cause:** `results_override` app not in `INSTALLED_APPS` or wrong directory structure

**Solution:**
1. Add `"results_override"` to `INSTALLED_APPS`
2. Verify directory structure matches: `results_override/static/core_explore_common_app/user/js/results.js`
3. Run `python manage.py collectstatic`

#### Issue 4: Styles Look Wrong
**Symptom:** Colors, layout broken

**Cause:** CSS selectors don't match newer MDCS HTML structure

**Solution:**
1. Inspect elements in browser dev tools
2. Update CSS selectors to match new element IDs/classes
3. Compare HTML structure between MDCS versions

#### Issue 5: Download System Not Working
**Symptom:** "Download All" button doesn't work, console errors

**Cause:** StreamSaver files not copied or service worker not registered

**Solution:**
1. Verify all StreamSaver files copied to `static/libs/StreamSaver/`
2. Check `results.js` has service worker registration
3. Test service worker in browser dev tools (Application tab)
4. Ensure HTTPS if required by browser for service workers

---

## Appendices

### Appendix A: Complete Commit History

Commits from 2.21.0 baseline to current HEAD (chronological order):

1. **bbe230b** - Initial style changes for NexusLIMS CDCS
   - Base CSS and branding updates
   
2. **353ba91** - Add logo for loading page
   - Loading spinner logo addition
   
3. **daf11c3** - Fix css styling error for custom button text
   - Button text color fix
   
4. **062201b** - Changes to enable registry-like view on search page
   - Override XML processing to enable kwargs for XSLT
   - Change data_source_info and _results to remove sidebars
   
5. **3fad876** - Actual fix for css from last commit
   - CSS correction
   
6. **c128b84** - Make detail xsl take kwargs, update detail xsl to be more responsive
   - Add custom JS for edit button, sidebar, tooltips
   
7. **c80144c** - Initialize all tooltips by default
   - Tooltip system activation
   
8. **d622413** - Fix background color bug on button hovering
   - Button hover state fix
   
9. **4f683fb** - Un-disable animations and transitions
   - Re-enable CSS transitions in Firefox
   
10. **ad8eedd** - Make "edit button" open in new window instead of existing one
    - Target="_blank" for edit links
    
11. **ec63bb6** - Change tooltips to be triggered by hover rather than focus
    - Tooltip trigger change
    
12. **fe7e467** - Add menu item for SP calendar (and js to add icon) to top bar
    - SharePoint calendar menu integration
    
13. **67e19f9** - Update sharepoint link to new sharepoint calendar
    - SharePoint URL update
    
14. **1bb5d04** - Update CDCS settings to sort most recent records first
    - `DATA_SORTING_FIELDS` configuration
    
15. **1bac623** - Remove links to create new records (without removing app)
    - UI cleanup for read-only users
    
16. **93c3306** - Override some js to allow a "please wait" message on data explore
    - Loading state messaging
    
17. **fb5c2ac** - Remove "go back" button css and add to XSL instead
    - Button moved to XSLT
    
18. **18f8e1f** - Move results.js override to a new Django app
    - Created `results_override` app
    - Fixed template resolution issue
    
19. **d71577d** - Add documentation link to homepage and top menu
    - Fix how icons and target='_blank' are added to top menu
    
20. **be669db** - DETAIL: change sample info block condition to include when samples only have refs
    - XSLT sample handling improvement
    
21. **c0ad331** - Merge branch 'XSLT_simple_display' into 'NexusLIMS_master_internal'
    - Simple display mode for >100 datasets
    
22. **42d93a4** - Merge branch 'XSLT_Hotfix_decode_rootpath' into 'NexusLIMS_master_internal'
    - Root path decoding fix
    
23. **6f1142a** - Merge branch 'add_filename_to_preview_caption' into 'NexusLIMS_master_internal'
    - Filename display in image captions
    
24. **2b746f5** - Add badge colors for two new instruments
    - Instrument color dictionary update
    
25. **440a376** - Merge branch 'add_instrument_colors' into 'NexusLIMS_master'
    - Additional instrument colors
    
26. **e2109c6** - Add a little spacing to the top of the image gallery to improve appearance
    - Gallery CSS spacing
    
27. **ebb0b63** - Merge branch 'fix_gallery_spacing' into 'NexusLIMS_master'
    - Gallery spacing merge
    
28. **240a7f9** - Fix duplicate file handling for multi-signal datasets in download system
    - Duplicate filename resolution for multi-signal data
    
29. **30faa97** - Display units next to parameter names in detail view metadata tables
    - Units display in XSLT (current HEAD)

### Appendix B: Environment Variable Reference

Required environment variables for NexusLIMS-CDCS deployment:

#### Django Core Settings
```bash
# Server configuration
SERVER_URI=https://your-server.example.com
SERVER_NAME=YourLabName
ALLOWED_HOSTS=your-server.example.com,localhost

# Security
DJANGO_SECRET_KEY=your-secret-key-here

# Database (PostgreSQL)
POSTGRES_HOST=db-host
POSTGRES_PORT=5432
POSTGRES_DB=mdcs_db
POSTGRES_USER=mdcs_user
POSTGRES_PASS=password

# MongoDB
MONGO_HOST=mongo-host
MONGO_PORT=27017
MONGO_DB=mdcs_mongo
MONGO_USER=mongo_user
MONGO_PASS=password

# Redis (for Celery)
REDIS_HOST=redis-host
REDIS_PORT=6379
REDIS_PASS=password
```

#### NexusLIMS-Specific Settings

These are not environment variables but Django settings that should be configured:

```python
# In mdcs/settings.py
DOCUMENTATION_LINK = "https://your-docs.example.com"
CAN_ANONYMOUS_ACCESS_PUBLIC_DOCUMENT = True
VERIFY_DATA_ACCESS = False
DATA_SORTING_FIELDS = ["-last_modification_date", "title", "template"]
SSL_CERTIFICATES_DIR = False  # If using HTTPS
```

#### XSLT Variables

These are configured in `xslt/detail_stylesheet.xsl`, not environment variables:

```xml
<xsl:variable name="datasetBaseUrl">https://your-server.example.com/data</xsl:variable>
<xsl:variable name="previewBaseUrl">https://your-server.example.com/previews</xsl:variable>
<xsl:variable name="sharepointBaseUrl">https://sharepoint.example.com</xsl:variable>
```

### Appendix C: XSLT Customization Points

Key areas in XSLT stylesheets that may need site-specific customization:

#### In `xslt/detail_stylesheet.xsl`:

1. **Base URLs (lines 14-16):**
```xml
<xsl:variable name="datasetBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>
<xsl:variable name="previewBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>
<xsl:variable name="sharepointBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>
```

2. **Dataset Count Limit (line 22-23):**
```xml
<xsl:variable name="maxDatasetCount">100</xsl:variable>
<xsl:variable name="simpleDisplay" select="count(//nx:dataset) > $maxDatasetCount"/>
```

3. **Instrument Color Dictionary (location varies, search for "instr-color-dictionary"):**
```xml
<xsl:variable name="instr-color-dictionary">
    <instrument pid="643adb78efcb5b6ad9c1e87b">
        <color>blue</color>
    </instrument>
    <!-- Add entries for your instruments -->
</xsl:variable>
```

4. **SharePoint Instrument Dictionary (search for "sharepoint-instrument-dictionary"):**
```xml
<xsl:variable name="sharepoint-instrument-dictionary">
    <instrument name="InstrumentName">
        <sharepoint-name>SharePointToolName</sharepoint-name>
    </instrument>
    <!-- Add mappings for your instruments -->
</xsl:variable>
```

#### In `xslt/list_stylesheet.xsl`:

Generally no customization needed unless changing list display format.

### Appendix D: File Count by Type

For reference during rebase:

| File Type | Count |
|-----------|-------|
| Python (.py) | 8 |
| JavaScript (.js) | 11 |
| CSS (.css) | 9 |
| HTML Templates (.html) | 13 |
| XSLT (.xsl) | 2 |
| Images (.png, .jpg) | 5 |
| Source Maps (.map) | 5 |
| Documentation (.rst, .md) | 2 |
| Config (.gitignore) | 1 |
| **TOTAL** | **56+** |

*(Plus additional supporting files like service workers, HTML for libraries, etc.)*

### Appendix E: Testing Checklist Details

Detailed test cases for post-rebase validation:

#### 1. Basic Functionality Tests
```
□ Visit homepage - should load without 500 errors
□ Check page title - should be "Welcome to NexusLIMS!"
□ Verify logo displays - NexusLIMS branding
□ Check footer - no NIST-specific content
□ Login with test user - should work
□ Logout - should work
□ Access admin panel - should load
```

#### 2. Search Functionality Tests
```
□ Navigate to "Explore" → "Keyword Search"
□ Enter keyword, click search
□ Verify results display in registry-like view (not default MDCS view)
□ Check DataTables features:
  □ Search box works
  □ Sorting by columns works
  □ Pagination works
□ Click on a result - should open detail page
```

#### 3. Record Detail View Tests
```
□ Open any record detail page
□ Verify record title appears at top (from xmlName parameter)
□ Check metadata tables:
  □ Parameters display with units (e.g., "Energy: 200 kV")
  □ Tables are formatted correctly
  □ No raw XML visible
□ Check instrument badge:
  □ Badge displays with correct color
  □ Badge shows instrument PID
□ Check sample information section:
  □ Sample data displays if present
  □ Elements show periodic table expansions (e.g., "Si" → "14 - Silicon")
□ Check preview gallery:
  □ Images display in grid layout
  □ Proper spacing between images
  □ Filenames appear in captions
  □ Gallery has margin at top
□ Check acquisition activities:
  □ Activities grouped and numbered
  □ Datasets listed under activities
  □ File listings correct
```

#### 4. Download System Tests
```
□ Single file download:
  □ Click on individual file link
  □ File downloads with correct name
□ Download all files:
  □ Click "Download All Files" button
  □ Browser shows download progress
  □ Zip file downloads
  □ Zip contains all files
  □ Filenames correct in zip
□ Multi-signal dataset download:
  □ Find record with multi-signal data
  □ Click "Download All Files"
  □ Verify duplicate filenames handled (e.g., file_1.ext, file_2.ext)
□ Test in multiple browsers:
  □ Chrome
  □ Firefox
  □ Safari (if available)
```

#### 5. XSLT Parameter System Tests
```
□ Open browser dev tools console
□ Navigate to record detail page
□ Check for errors:
  □ No "XSLT transformation failed" errors
  □ No "parameter not found" errors
□ View page source:
  □ Should see HTML (not raw XML)
  □ Should see record title in <h1> or similar
  □ Should see download URLs with correct base path
□ Test with records that have:
  □ No preview images
  □ No sample information
  □ Large number of datasets (>100)
  □ Multi-signal datasets
```

#### 6. Navigation and Menu Tests
```
□ Check top navigation menu:
  □ NexusLIMS logo visible
  □ Menu items present
  □ Documentation link present (not placeholder)
  □ Documentation link opens in new tab
  □ SharePoint calendar link (if configured)
□ Check homepage tiles:
  □ Tiles display correctly
  □ Tile links work
  □ Documentation tile present
```

#### 7. Tutorial System Tests
```
□ Navigate to homepage
□ Check for tutorial/tour trigger
□ Start tutorial (if implemented)
□ Verify Shepherd.js steps display
□ Complete or dismiss tutorial
```

#### 8. Styling Tests
```
□ Check overall color scheme - NexusLIMS blue theme
□ Check buttons:
  □ Custom colors (not default Bootstrap)
  □ Hover states work
  □ No visual glitches
□ Check responsive design:
  □ Narrow browser window
  □ Verify layout adapts
  □ Mobile device view (if supported)
□ Check forms:
  □ Input fields styled correctly
  □ Validation messages appear
```

#### 9. Admin/Backend Tests
```
□ Login as admin
□ Access Django admin panel
□ Verify apps visible:
  □ mdcs_home
  □ results_override
  □ core_main_app
□ Check for errors in admin
```

#### 10. Performance Tests
```
□ Record with few datasets (<10):
  □ Page loads quickly
  □ Interactive display used
□ Record with many datasets (>100):
  □ Page loads (may be slower)
  □ Simple display mode activates
  □ File list shown instead of interactive view
□ Large download (100+ files):
  □ StreamSaver handles without memory issues
  □ Zip file created successfully
```

---

## Document Maintenance

**Last Updated:** 2025-12-30  
**MDCS Baseline Version:** 2.21.0 (July 7, 2022)  
**NexusLIMS-CDCS Version:** commit 30faa97  

When updating this document after future rebases:
1. Update the baseline version and commit SHA
2. Update change statistics
3. Add new commits to Appendix A
4. Document any new architectural changes
5. Update testing checklist with new features
6. Update version date at top of document

---

## Additional Resources

- **NexusLIMS Backend Repository:** https://github.com/datasophos/NexusLIMS
- **Upstream MDCS Repository:** https://github.com/usnistgov/mdcs
- **MDCS Documentation:** https://github.com/usnistgov/mdcs/wiki
- **NexusLIMS Docker Deployment:** https://github.com/usnistgov/nexuslims-cdcs-docker
- **NexusLIMS Publication:** https://doi.org/10.1017/S1431927621000222

---

*End of Document*
