# NexusLIMS Customization Guide

This guide explains how to customize your NexusLIMS deployment to match your organization's branding and requirements.

## Table of Contents

- [Overview](#overview)
- [Configuration Settings](#configuration-settings)
  - [XSLT Configuration](#xslt-configuration)
  - [Branding & Logos](#branding--logos)
  - [Theme Colors](#theme-colors)
  - [Homepage Content](#homepage-content)
  - [Navigation Menu](#navigation-menu)
  - [Feature Flags](#feature-flags)
  - [Dataset Display Threshold](#dataset-display-threshold)
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
2. **Override settings** in your deployment's `config/settings/custom_settings.py` or environment-specific settings file
3. **Place custom assets** (logos, images) in `config/static_files/`
4. **Restart your containers** to load the new configuration (no rebuild required)

---

## Configuration Settings

### XSLT Configuration

#### XSLT Debug Mode

If you are making changes to the XSLT, or the display is not as you expect, enabling debug output from the XSLT transformation process can be helpful. This setting controls whether detailed messages and errors from the XSLT processing will be output to the Django application's console.

**Configuration:**
```python
# Enable XSLT debug output (default: False)
NX_XSLT_DEBUG = True
```

**Use Cases:**
- **Development/Debugging**: Set to `True` when working on XSLT stylesheets to see detailed transformation messages
- **Production**: Set to `False` (default) to avoid verbose debug output in logs

**Important Notes:**
- Serious errors that cause exceptions during transformation will always be printed regardless of this setting
- Debug messages can be quite verbose, so it's best left as `False` in production environments
- This setting is particularly useful for profiling and debugging XSLT transformations

**Using XSLT Message Tags:**
You can add debug statements directly in your XSLT stylesheets using `<xsl:message>` tags:

```xml
<xsl:message>DEBUG: Processing instrument <xsl:value-of select="$instrument-name"/></xsl:message>
```

**Debugging Tips:**
- Use descriptive messages that indicate where in the transformation process you are
- Include variable values to track data flow
- Add messages at key decision points in your XSLT logic
- Remember to disable `NX_XSLT_DEBUG` before production deployment

#### Instrument Badge Colors

You can easily configure the colors used for instrument badges in the detail and list views. These visual indicators help users quickly identify which instrument was used for each experiment.

**How it works:**
- The XSLT stylesheets use these mappings to assign colors to instrument badges
- If an instrument PID is not found in the mapping, a default gray color (`#505050`) is used
- Colors are applied dynamically during XML-to-HTML transformation

**Best Practices:**
- Use distinct, accessible colors that work well for colorblind users
- Choose colors that contrast well with white text (badges have white text)
- Group similar instruments by color family (e.g., all TEMs in blue/purple tones)

**Color Selection Tips:**
- Use tools like [Coolors](https://coolors.co/) or [Adobe Color](https://color.adobe.com/) to create harmonious palettes
- Ensure WCAG AA contrast ratio (minimum 4.5:1 for normal text)
- Consider your organization's branding colors

**Example: Custom Color Scheme**

```python
NX_INSTRUMENT_COLOR_MAPPINGS = {
    "FEI-Titan-TEM": "#2E86AB",  # Blue for TEMs
    "FEI-Titan-STEM": "#0645AD",  # Darker blue for STEM
    "JEOL-JEM3010-TEM": "#5DADE2", # Lighter blue for older TEM
    "FEI-Quanta200-ESEM": "#A569BD", # Purple for ESEM
    "FEI-Helios-DB": "#8E44AD",    # Darker purple for dual beam
    "Hitachi-S4700-SEM": "#E74C3C", # Red for Hitachi SEMs
    "Hitachi-S5500-SEM": "#C0392B", # Darker red for newer model
    "JEOL-JSM7100-SEM": "#F39C12",  # Orange for JEOL SEMs
    "Philips-EM400-TEM": "#27AE60", # Green for Philips TEMs
    "Philips-CM30-TEM": "#229954",  # Darker green for CM30
    "Zeiss-LEO_1525_FESEM": "#16A085", # Teal for Zeiss instruments
    "Zeiss-Gemini_300_SEM": "#1ABC9C", # Lighter teal for Gemini
}
```

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

### Theme Colors

Customize the color scheme of your NexusLIMS deployment using CSS custom properties. These colors are used throughout the interface for buttons, links, badges, and other UI elements.

```python
NX_THEME_COLORS = {
    "primary": "#11659c",           # Main brand color (buttons, links, icons)
    "primary_dark": "#0d528a",      # Darker variant for hover states
    "info_badge_dark": "#505050",   # Info badge background color
    "secondary": "#f9f9f9",         # Secondary (light) button background
    "secondary_dark": "#e2e2e2",    # Secondary button hover state
    "success": "#28a745",           # Success states
    "danger": "#dc3545",            # Error/danger states
    "warning": "#ffc107",           # Warning states and hover highlights
    "info": "#17a2b8",              # Info messages
    "light_gray": "#e3e3e3",        # Light gray accents
    "dark_gray": "#212529",         # Dark text color
}
```

**How it works:**
- Colors are injected as CSS custom properties (e.g., `--nx-primary-color`)
- Only specify colors you want to change; unspecified colors use CSS defaults
- Changes take effect after restarting the Django container

**Usage:**
- Set `NX_THEME_COLORS` in your `config/settings/custom_settings.py`
- Only include the colors you want to override

**Example: Custom Blue Theme**
```python
NX_THEME_COLORS = {
    "primary": "#1a5276",
    "primary_dark": "#154360",
    "warning": "#f4d03f",
}
```

**Example: Corporate Green Theme**
```python
NX_THEME_COLORS = {
    "primary": "#1e8449",
    "primary_dark": "#196f3d",
    "info_badge_dark": "#2c3e50",
}
```

**Color Selection Tips:**
- Choose a primary color that represents your organization's brand
- Ensure sufficient contrast between text and background colors
- The `warning` color is used for hover highlights on links and buttons
- Test your color scheme in both light conditions and on different monitors

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

```

**When to Disable:**
- **Tutorials**: If you have custom onboarding or the Shepherd.js library isn't installed

#### Dataset Display Threshold

Control when the simplified display mode is used for records with many datasets.

```python
# Change this value to customize the threshold at which the "simple"
# and less interactive display mode will be used on the detail page.
# The number of individual "datasets" in a record will be compared to this
# number. Lower numbers mean smaller records will trigger the simple display.
# Set to 0 to disable the simple display entirely.
# Default: 100
NX_MAX_DATASET_DISPLAY_COUNT = 100
```

**Usage Guidelines:**
- **Default (100)**: Records with 101+ datasets use simple display
- **Lower values (e.g., 50)**: More records will use simple display (better performance)
- **Higher values (e.g., 500)**: Fewer records will use simple display (more interactive)
- **0**: Always use full interactive display (may impact performance with large records)

**Performance Considerations:**
- Simple display mode reduces browser memory usage and rendering time
- Interactive display provides better user experience but can be resource-intensive
- Adjust based on your typical record sizes and user hardware

**Best Practices:**
- Start with default (100) and monitor user feedback
- Consider your user base: research labs may prefer interactive, while production environments may prefer performance
- Test with your largest records to find the optimal balance

---

## Customization Best Practices

### 1. Use Environment-Specific Settings

Create separate settings files for different environments:

```python
# mdcs/dev_settings.py
from mdcs.settings import *

# Use different color schemes for different environments
NX_INSTRUMENT_COLOR_MAPPINGS = {
    "FEI-Titan-TEM": "#FF0000",  # Red for dev environment
    "FEI-Titan-STEM": "#FF6600",  # Orange for dev
    # ... other instruments
}

NX_CUSTOM_MENU_LINKS = [
    {"title": "DEV Portal", "url": "https://dev.portal.com", "icon": "flask"},
]

# mdcs/prod_settings.py
from mdcs.settings import *

# Production color scheme
NX_INSTRUMENT_COLOR_MAPPINGS = {
    "FEI-Titan-TEM": "#2E86AB",  # Blue for production
    "FEI-Titan-STEM": "#0645AD",  # Darker blue
    # ... other instruments
}

NX_CUSTOM_MENU_LINKS = [
    {"title": "Production Portal", "url": "https://portal.com", "icon": "database"},
]
```

### 2. Organize Custom Assets

Place your custom assets in `config/static_files/` instead of modifying the `nexuslims_overrides` directory:

```
config/
├── static_files/
│   ├── nav_logo.png           # Your navigation bar logo
│   ├── footer_logo.png        # Your footer logo
│   ├── logo_horizontal_text.png  # Your homepage logo
│   └── custom_icon.png        # Any other custom images
└── settings/
    └── custom_settings.py
```

**Benefits:**
- Keep customizations separate from app code
- No need to modify `nexuslims_overrides/` directory
- Runtime configuration updates without rebuilding containers

### 3. Version Control Custom Assets

Add your custom assets to git but use `.gitignore` for deployment-specific files:

```gitignore
# .gitignore
config/static_files/*
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

# Theme Colors (university blue)
NX_THEME_COLORS = {
    "primary": "#2E86AB",
    "primary_dark": "#1A5276",
    "warning": "#F5B041",
}

# XSLT Configuration
NX_INSTRUMENT_COLOR_MAPPINGS = {
    "FEI-Titan-TEM": "#2E86AB",  # University blue
    "FEI-Titan-STEM": "#0645AD",  # Darker blue
    "JEOL-JEM3010-TEM": "#5DADE2", # Lighter blue
    "FEI-Quanta200-ESEM": "#A569BD", # Purple
    "FEI-Helios-DB": "#8E44AD",    # Darker purple
    "Hitachi-S4700-SEM": "#E74C3C", # Red
    "Hitachi-S5500-SEM": "#C0392B", # Darker red
    "JEOL-JSM7100-SEM": "#F39C12",  # Orange
    "Philips-EM400-TEM": "#27AE60", # Green
    "Philips-CM30-TEM": "#229954",  # Darker green
    "Zeiss-LEO_1525_FESEM": "#16A085", # Teal
    "Zeiss-Gemini_300_SEM": "#1ABC9C", # Lighter teal
}

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

# Dataset Display
# Use simple display for records with 100+ datasets (better for research environment)
NX_MAX_DATASET_DISPLAY_COUNT = 99
```

### Example 2: Corporate Lab

```python
# Acme Corp - Materials Lab LIMS Settings

# Theme Colors (corporate orange)
NX_THEME_COLORS = {
    "primary": "#E67E22",
    "primary_dark": "#D35400",
    "info_badge_dark": "#34495E",
}

# XSLT Configuration
NX_INSTRUMENT_COLOR_MAPPINGS = {
    "FEI-Titan-TEM": "#1A5276",  # Corporate blue
    "FEI-Titan-STEM": "#2874A6",  # Medium blue
    "JEOL-JEM3010-TEM": "#5DADE2", # Light blue
    "FEI-Quanta200-ESEM": "#7D3C98", # Corporate purple
    "FEI-Helios-DB": "#54278F",    # Dark purple
    "Hitachi-S4700-SEM": "#E67E22", # Corporate orange
    "Hitachi-S5500-SEM": "#D35400", # Dark orange
    "JEOL-JSM7100-SEM": "#F1C40F",  # Corporate yellow
    "Philips-EM400-TEM": "#2ECC71", # Corporate green
    "Philips-CM30-TEM": "#27AE60",  # Dark green
    "Zeiss-LEO_1525_FESEM": "#16A085", # Corporate teal
    "Zeiss-Gemini_300_SEM": "#1ABC9C", # Light teal
}

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

# Dataset Display
# Use simple display for records with 250+ datasets (optimized for large research datasets)
NX_MAX_DATASET_DISPLAY_COUNT = 249
```

### Example 3: Government Research Facility

```python
# National Lab - Electron Microscopy Nexus

# Theme Colors (government blue)
NX_THEME_COLORS = {
    "primary": "#003366",
    "primary_dark": "#002244",
    "warning": "#CC9900",
}

# XSLT Configuration
NX_INSTRUMENT_COLOR_MAPPINGS = {
    "FEI-Titan-TEM": "#003366",  # Government blue
    "FEI-Titan-STEM": "#002855",  # Darker blue
    "JEOL-JEM3010-TEM": "#0055A4", # Medium blue
    "FEI-Quanta200-ESEM": "#660033", # Government purple
    "FEI-Helios-DB": "#4D0026",    # Dark purple
    "Hitachi-S4700-SEM": "#CC0000", # Government red
    "Hitachi-S5500-SEM": "#990000", # Dark red
    "JEOL-JSM7100-SEM": "#FF9900",  # Government orange
    "Philips-EM400-TEM": "#006633", # Government green
    "Philips-CM30-TEM": "#004D26",  # Dark green
    "Zeiss-LEO_1525_FESEM": "#008080", # Government teal
    "Zeiss-Gemini_300_SEM": "#009999", # Light teal
}

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

# Dataset Display
# Use simple display for records with 500+ datasets (optimized for very large government datasets)
NX_MAX_DATASET_DISPLAY_COUNT = 499
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

### Instrument Colors Not Updating

If instrument badge colors aren't changing after updating `NX_INSTRUMENT_COLOR_MAPPINGS`:

1. **Verify the setting name**: Ensure it's exactly `NX_INSTRUMENT_COLOR_MAPPINGS`
2. **Check for typos**: Instrument PIDs must match exactly what's in your database
3. **Validate color format**: Colors must be valid hex codes (e.g., `#RRGGBB`)
4. **Restart Django**: XSLT parameters are loaded at startup
5. **Check XSLT logs**: Look for transformation errors in Django logs

**Debugging tip:** Enable XSLT debug mode to see detailed transformation messages:
```python
NX_XSLT_DEBUG = True  # Set this in your settings.py
```

**Debugging tip:** Add a unique color to test if changes are being applied:
```python
NX_INSTRUMENT_COLOR_MAPPINGS = {
    "FEI-Titan-TEM": "#FF00FF",  # Bright pink for testing
    # ... other instruments
}
```

### Logo Not Displaying

- Check file path is correct (relative to `config/static_files/`)
- Verify file exists in `config/static_files/`
- Ensure file permissions allow reading
- Run `collectstatic` to collect the files: `python manage.py collectstatic` (this is run automatically when the container is restarted)
- Check Django logs for 404 errors

### Menu Links Not Showing

- Verify `NX_CUSTOM_MENU_LINKS` is a list of dictionaries
- Each dict must have `"title"` and `"url"` keys
- Check for typos in setting name
- Restart Django after settings changes

### Theme Colors Not Applying

If your custom theme colors aren't appearing:

1. **Verify dictionary keys**: Keys must be lowercase without `nx_` prefix (e.g., `"primary"`, not `"NX_PRIMARY_COLOR"`)
2. **Check color format**: Colors must be valid CSS values (e.g., `#RRGGBB`, `rgb()`, or named colors)
3. **Restart Django**: Theme colors are loaded at startup
4. **Clear browser cache**: Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)
5. **Check for typos**: Common mistakes include `"primary-dark"` instead of `"primary_dark"`

**Valid keys:**
- `primary`, `primary_dark`, `info_badge_dark`, `secondary`, `secondary_dark`
- `success`, `danger`, `warning`, `info`, `light_gray`, `dark_gray`

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
