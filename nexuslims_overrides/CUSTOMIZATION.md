# NexusLIMS Customization Guide

This guide explains how to customize your NexusLIMS deployment to match your organization's branding and requirements.

## Table of Contents

- [Overview](#overview)
- [Configuration Settings](#configuration-settings)
  - [Branding & Logos](#branding--logos)
  - [Homepage Content](#homepage-content)
  - [Navigation Menu](#navigation-menu)
  - [Feature Flags](#feature-flags)
- [Customization Best Practices](#customization-best-practices)
- [Advanced Customization](#advanced-customization)
- [Examples](#examples)

---

## Overview

NexusLIMS uses a centralized settings approach where all customization options are defined in:

**`nexuslims_overrides/settings.py`**

This file contains default values for all NexusLIMS-specific settings. To customize your deployment, override these settings in your project's `settings.py` file.

### Customization Workflow

1. **Never modify `nexuslims_overrides/settings.py` directly**
2. **Override settings** in your deployment's `mdcs/settings.py` or environment-specific settings file
3. **Place custom assets** (logos, images) in `nexuslims_overrides/static/nexuslims/img/`
4. **Run `collectstatic`** after making changes to static files

---

## Configuration Settings

### Branding & Logos

#### Navigation Bar Logo

The logo displayed in the top-left corner of the navigation bar.

```python
# Default: "nexuslims/img/nav_logo.png"
NX_NAV_LOGO = "path/to/your/nav_logo.png"
```

**Recommendations:**
- **Format**: PNG with transparent background
- **Size**: Max height 1.5em (~24px at default font size)
- **Aspect ratio**: Horizontal logos work best (2:1 to 4:1)

#### Footer Logo

The logo displayed in the footer (left side).

```python
# Default: "nexuslims/img/datasophos_logo.png"
NX_FOOTER_LOGO = "path/to/your/footer_logo.png"

# Default: "https://datasophos.co"
NX_FOOTER_LINK = "https://your-organization.com"
```

**Recommendations:**
- **Format**: PNG or SVG
- **Size**: Height ~2.5em (~40px)
- **Color**: Should contrast well with footer background (#f8f8f8)

#### Homepage Logo

The logo displayed on the homepage alongside the welcome text.

```python
# Default: "nexuslims/img/logo_horizontal_text.png"
NX_HOMEPAGE_LOGO = "path/to/your/homepage_logo.png"
```

**Recommendations:**
- **Format**: PNG or SVG
- **Size**: Max width 400px
- **Style**: Can include text/wordmark

---

### Homepage Content

#### Welcome Title

```python
# Default: "Welcome to NexusLIMS!"
CUSTOM_TITLE = "Welcome to Your LIMS!"
```

#### Homepage Text

```python
NX_HOMEPAGE_TEXT = """
Your custom introductory text here. This appears on the homepage
and explains what your LIMS does and how to use it.
"""
```

**Best Practice:** Keep this concise (2-3 sentences) and action-oriented.

#### Documentation Link

```python
# Default: "https://datasophos.github.io/NexusLIMS/"
NX_DOCUMENTATION_LINK = "https://docs.your-organization.com"
```

Set to empty string `""` to hide the documentation link entirely.

---

### Navigation Menu

#### Custom Menu Links

Add custom links to the top navigation bar.

```python
NX_CUSTOM_MENU_LINKS = [
    {
        "title": "Data Portal",
        "url": "https://portal.your-org.com",
        "icon": "database",           # Font Awesome icon name (optional)
        "iconClass": "fas"             # Font Awesome class (optional, default: "fas")
    },
    {
        "title": "Help Desk",
        "url": "https://help.your-org.com",
        "icon": "question-circle"
    },
    {
        "title": "Team Directory",
        "url": "/team",
        "icon": "users"
    },
]
```

**Icon Options:**
- Use any [Font Awesome 5](https://fontawesome.com/v5/search) icon name
- `iconClass` can be `"fas"` (solid), `"far"` (regular), or `"fab"` (brands)
- Omit `icon` to display text only

**Best Practices:**
- Limit to 3-5 custom links to avoid cluttering the navigation
- Use descriptive titles (2-3 words max)
- External links should open in new tab (handled automatically for `https://` URLs)

---

### Feature Flags

#### Enable/Disable Features

```python
# Enable the interactive tutorial
# Default: True
NX_ENABLE_TUTORIALS = True

# Enable download buttons on data records
# Default: True
NX_ENABLE_DOWNLOADS = True
```

**When to Disable:**
- **Tutorials**: If you have custom onboarding or the Shepherd.js library isn't installed
- **Downloads**: If data export is restricted by policy

---

## Customization Best Practices

### 1. Use Environment-Specific Settings

Create separate settings files for different environments:

```python
# mdcs/dev_settings.py
from mdcs.settings import *

NX_CUSTOM_MENU_LINKS = [
    {"title": "DEV Portal", "url": "https://dev.portal.com", "icon": "flask"},
]

# mdcs/prod_settings.py
from mdcs.settings import *

NX_CUSTOM_MENU_LINKS = [
    {"title": "Production Portal", "url": "https://portal.com", "icon": "database"},
]
```

### 2. Organize Custom Assets

```
nexuslims_overrides/static/nexuslims/img/
├── nav_logo.png           # Your navigation bar logo
├── footer_logo.png        # Your footer logo
├── logo_horizontal_text.png  # Your homepage logo
└── custom_icon.png        # Any other custom images
```

### 3. Version Control Custom Assets

Add your custom logos to git but use `.gitignore` for deployment-specific files:

```gitignore
# .gitignore
nexuslims_overrides/static/nexuslims/img/local_*
```

### 4. Document Your Customizations

Keep a `DEPLOYMENT.md` in your project documenting:
- Custom settings and their purposes
- Asset locations and specifications
- Contact information for branding questions

---

## Advanced Customization

### Custom CSS

Add deployment-specific CSS:

```python
# In your settings.py
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "custom_static"),
]
```

Create `custom_static/css/custom.css` and include in your template:

```django
{% load static %}
<link rel="stylesheet" href="{% static 'css/custom.css' %}">
```

### Custom Templates

Override any NexusLIMS template by creating a file with the same path in your project's `templates/` directory. Django will use your template instead of the default.

**Example:** Override the homepage further

```
your_project/templates/core_main_app/user/homepage.html
```

The template loader searches in this order:
1. Your project's `templates/` directory
2. `nexuslims_overrides/templates/`
3. Core app templates

### Custom Context Processors

Add your own context processor to make custom variables available in all templates:

```python
# your_app/context_processors.py
def custom_settings(request):
    return {
        'COMPANY_NAME': 'Your Organization',
        'SUPPORT_EMAIL': 'support@example.com',
    }

# settings.py
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... existing processors ...
                'your_app.context_processors.custom_settings',
            ],
        },
    },
]
```

---

## Examples

### Example 1: University Deployment

```python
# University of Example - NexusLIMS Settings

# Branding
CUSTOM_TITLE = "Welcome to UEx Microscopy LIMS"
NX_NAV_LOGO = "nexuslims/img/uex_nav_logo.png"
NX_FOOTER_LOGO = "nexuslims/img/uex_footer_logo.png"
NX_FOOTER_LINK = "https://microscopy.uex.edu"

# Content
NX_HOMEPAGE_TEXT = (
    "Access and manage microscopy data from the University of Example "
    "Microscopy Core Facility. All data is automatically harvested from "
    "our instruments and made searchable through this portal."
)

NX_DOCUMENTATION_LINK = "https://microscopy.uex.edu/docs"

# Navigation
NX_CUSTOM_MENU_LINKS = [
    {"title": "Core Facility", "url": "https://microscopy.uex.edu", "icon": "microscope"},
    {"title": "Book Time", "url": "https://booking.uex.edu", "icon": "calendar"},
    {"title": "Training", "url": "https://training.uex.edu", "icon": "graduation-cap"},
]

# Features
NX_ENABLE_TUTORIALS = True
NX_ENABLE_DOWNLOADS = True
```

### Example 2: Corporate Lab

```python
# Acme Corp - Materials Lab LIMS Settings

# Branding
CUSTOM_TITLE = "Acme Materials Lab"
NX_NAV_LOGO = "nexuslims/img/acme_logo_white.png"
NX_FOOTER_LOGO = "nexuslims/img/acme_logo_color.png"
NX_FOOTER_LINK = "https://acme.com/materials-lab"

# Content
NX_HOMEPAGE_TEXT = (
    "Materials characterization data management system for Acme Corp R&D. "
    "Search and browse experimental records from our analytical instruments."
)

NX_DOCUMENTATION_LINK = ""  # Internal documentation not public

# Navigation
NX_CUSTOM_MENU_LINKS = [
    {"title": "Sample Request", "url": "https://samples.acme.internal", "icon": "flask"},
    {"title": "Lab Wiki", "url": "https://wiki.acme.internal/materials", "icon": "book"},
    {"title": "Support", "url": "mailto:lab-support@acme.com", "icon": "envelope"},
]

# Features
NX_ENABLE_TUTORIALS = False  # Custom onboarding process
NX_ENABLE_DOWNLOADS = True
```

### Example 3: Government Research Facility

```python
# National Lab - Electron Microscopy Nexus

# Branding
CUSTOM_TITLE = "National Lab EM Nexus"
NX_NAV_LOGO = "nexuslims/img/natlab_seal.png"
NX_FOOTER_LOGO = "nexuslims/img/doe_logo.png"
NX_FOOTER_LINK = "https://www.natlab.gov"

# Content
NX_HOMEPAGE_TEXT = (
    "The National Lab Electron Microscopy Nexus Facility provides access to "
    "state-of-the-art characterization capabilities. This system tracks and "
    "curates all experimental data for facility users."
)

NX_DOCUMENTATION_LINK = "https://www.natlab.gov/em-nexus/docs"

# Navigation
NX_CUSTOM_MENU_LINKS = [
    {"title": "Facility Home", "url": "https://www.natlab.gov/em-nexus", "icon": "home"},
    {"title": "User Portal", "url": "https://users.natlab.gov", "icon": "user"},
    {"title": "Publications", "url": "https://www.natlab.gov/publications", "icon": "book"},
]

# Features
NX_ENABLE_TUTORIALS = True
NX_ENABLE_DOWNLOADS = True
```

---

## Troubleshooting

### Changes Not Appearing

1. **Restart Django**: Settings changes require a server restart
   ```bash
   docker-compose restart cdcs
   ```

2. **Run collectstatic**: Static file changes require collection
   ```bash
   docker-compose exec cdcs python manage.py collectstatic --noinput
   ```

3. **Clear browser cache**: Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)

### Logo Not Displaying

- Check file path is correct (relative to `static/`)
- Verify file exists in `nexuslims_overrides/static/nexuslims/img/`
- Ensure file permissions allow reading
- Check Django logs for 404 errors

### Menu Links Not Showing

- Verify `NX_CUSTOM_MENU_LINKS` is a list of dictionaries
- Each dict must have `"title"` and `"url"` keys
- Check for typos in setting name
- Restart Django after settings changes

---

## Getting Help

- **Documentation**: [NexusLIMS GitHub](https://github.com/datasophos/NexusLIMS-CDCS)
- **Migration Guide**: See `nexuslims_overrides/MIGRATION_GUIDE.md` for upgrading
- **Issues**: Report bugs or request features on GitHub

---

## Summary

NexusLIMS customization is designed to be:
- **Centralized**: All settings in one place (`nexuslims_overrides/settings.py`)
- **Safe**: Override in your settings, never modify defaults
- **Flexible**: From simple logo swaps to complete rebranding
- **Maintainable**: Clearly separated from core CDCS code

Start with basic branding (logos and text), then progressively customize navigation, features, and styling as needed.
