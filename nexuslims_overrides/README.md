# NexusLIMS Overrides App

This Django app contains all NexusLIMS-specific customizations to the base MDCS system.

## Purpose

Instead of scattering template overrides across multiple locations, this app centralizes all customizations in one place, making maintenance and upgrades easier.

## Structure

```
nexuslims_overrides/
├── __init__.py
├── apps.py                          # App configuration
├── context_processors.py            # Global template variables
├── README.md                        # This file
│
├── templatetags/                    # Custom template tags
│   ├── __init__.py
│   └── nexuslims_templatetags.py   # Custom tags and filters
│
├── templates/                       # Template overrides
│   └── nexuslims_overrides/
│       └── fragments/               # Reusable template fragments
│           ├── custom_toolbar.html
│           └── download_buttons.html
│
└── static/                          # Static files
    └── nexuslims/
        ├── css/
        │   ├── main.css            # Main stylesheet (imports others)
        │   ├── homepage.css
        │   ├── detail.css
        │   ├── search.css
        │   └── toolbar.css
        ├── js/
        │   └── main.js             # Main JavaScript
        └── img/                    # Images (logos, etc.)
```

## Installation

### 1. Add to INSTALLED_APPS

In `mdcs/settings.py`, add the app **before** core MDCS apps:

```python
INSTALLED_APPS = [
    # ... Django apps ...
    'django_celery_beat',
    
    # NexusLIMS customizations (must come before core apps)
    'nexuslims_overrides',
    
    # Core MDCS apps
    'core_main_app',
    'core_explore_common_app',
    # ...
]
```

### 2. Register context processors

In `mdcs/settings.py` under `TEMPLATES`:

```python
TEMPLATES = [
    {
        # ...
        'OPTIONS': {
            'context_processors': [
                # ... existing processors ...
                'nexuslims_overrides.context_processors.nexuslims_settings',
                'nexuslims_overrides.context_processors.nexuslims_features',
            ],
        },
    },
]
```

### 3. Include static files in base template

In your base template (e.g., `templates/theme.html`):

```django
{% load static %}

<head>
    <!-- ... existing head content ... -->
    <link rel="stylesheet" href="{% static 'nexuslims/css/main.css' %}">
</head>

<body>
    <!-- ... existing body content ... -->
    <script src="{% static 'nexuslims/js/main.js' %}"></script>
</body>
```

## Usage

### Context Processors

Available in all templates:

```django
{{ NX_DOCUMENTATION_LINK }}
{{ NX_HOMEPAGE_TEXT }}
{{ NX_CUSTOM_TITLE }}
{{ NX_ENABLE_DOWNLOADS }}
{{ NX_ENABLE_TUTORIALS }}
{{ NX_VERSION }}
```

### Template Tags

Load the custom tags in any template:

```django
{% load nexuslims_templatetags %}

{# Display version #}
{% nexuslims_version %}

{# Custom toolbar #}
{% nexuslims_custom_toolbar data %}

{# Download buttons #}
{% nexuslims_download_buttons data %}

{# Instrument color #}
{{ instrument_pid|nexuslims_instrument_color }}

{# Format with units #}
{{ value|nexuslims_format_units:"nm" }}
```

### Template Inheritance

To override a template from a core app, create a file with the same path structure:

```
nexuslims_overrides/
└── templates/
    └── core_main_app/
        └── user/
            └── data/
                └── detail.html  # Overrides core_main_app's detail.html
```

Then use template inheritance to minimize duplication:

```django
{# nexuslims_overrides/templates/core_main_app/user/data/detail.html #}
{% extends "core_main_app/user/data/detail.html" %}

{% load static %}
{% load nexuslims_templatetags %}

{% block extra_head %}
    {{ block.super }}
    <link rel="stylesheet" href="{% static 'nexuslims/css/detail.css' %}">
{% endblock %}

{% block content %}
    <div class="nexuslims-wrapper">
        {% nexuslims_custom_toolbar data %}
        {{ block.super }}
    </div>
{% endblock %}
```

## Customization

### Using a Custom Logo

The homepage logo is configurable via settings. To change it:

1. **Add your logo file** to `nexuslims_overrides/static/nexuslims/img/`:
   ```bash
   cp /path/to/your/logo.png nexuslims_overrides/static/nexuslims/img/my_logo.png
   ```

2. **Update the setting** in `mdcs/core_settings.py`:
   ```python
   # Path relative to static/ directory
   NX_HOMEPAGE_LOGO = "nexuslims/img/my_logo.png"
   ```

3. **Collect static files** (if in production):
   ```bash
   python manage.py collectstatic
   ```

**Using an environment variable:**
```python
# In mdcs/core_settings.py
NX_HOMEPAGE_LOGO = os.getenv("NX_HOMEPAGE_LOGO", "nexuslims/img/logo_horizontal_text.png")
```

**Recommended logo dimensions:**
- Width: 200-400px
- Height: 60-100px
- Format: PNG with transparency

### Adding New Styles

Add new CSS files in `static/nexuslims/css/` and import them in `main.css`:

```css
/* static/nexuslims/css/main.css */
@import url('new-component.css');
```

### Adding New JavaScript

Add functionality to `static/nexuslims/js/main.js` or create new files and include them in templates.

### Adding New Template Tags

Add new tags to `templatetags/nexuslims_templatetags.py`:

```python
@register.simple_tag
def my_custom_tag(arg):
    return f"Custom: {arg}"
```

### Adding New Settings

Add settings to `mdcs/core_settings.py` with the `NX_` prefix:

```python
NX_MY_CUSTOM_SETTING = "value"
```

Then expose in `context_processors.py`:

```python
def nexuslims_settings(request):
    return {
        # ... existing ...
        'NX_MY_CUSTOM_SETTING': getattr(settings, 'NX_MY_CUSTOM_SETTING', 'default'),
    }
```

## Maintenance

### Upgrading MDCS

When upgrading to a new MDCS version:

1. Template overrides that use inheritance will automatically get most upstream changes
2. Review this app's overrides for conflicts with new MDCS features
3. Update only the specific blocks that need customization
4. Test all functionality after upgrade

### Debugging

If customizations aren't appearing:

1. Check that app is in `INSTALLED_APPS` **before** core apps
2. Check that context processors are registered
3. Run `python manage.py collectstatic` to update static files
4. Clear browser cache
5. Check Django debug toolbar for template inheritance chain

## Best Practices

1. **Prefix everything with `NX_` or `nexuslims_`** - Avoid naming conflicts
2. **Use template inheritance** - Minimize code duplication
3. **Document customizations** - Add comments explaining why changes were made
4. **Test across browsers** - Ensure compatibility
5. **Keep it simple** - Only override what's necessary

## Support

For questions or issues related to NexusLIMS customizations, see the main project documentation.
