# Migrating Existing Customizations to nexuslims_overrides

This guide helps migrate existing scattered template overrides into the centralized `nexuslims_overrides` app.

## Migration Strategy

### Step 1: Audit Current Overrides

List all current template overrides:

```bash
find templates/ -type f -name "*.html" | sort
```

Current overrides to migrate:
- [x] `templates/core_main_app/user/homepage.html`
- [x] `templates/theme.html`
- [x] `mdcs_home/views.py`
- [x] `templates/theme/footer/default.html`
- [x] `templates/mdcs_home/tiles.html`
- [ ] `templates/core_main_app/user/data/detail.html`
- [ ] `templates/core_main_app/common/data/detail_data.html`
- [ ] `templates/core_main_app/_render/user/theme_base.html`
- [ ] `templates/core_explore_common_app/user/results/data_source_info.html`
- [ ] `templates/core_explore_common_app/user/results/data_source_results.html`
- [ ] `templates/core_explore_common_app/user/results/data_sources_results.html`
- [ ] `templates/core_explore_keyword_app/user/index.html`
- [ ] `templates/theme/menu.html`

### Step 2: Categorize Overrides

#### Category A: Complete Replacements
Templates that completely replace the original (no inheritance possible):
- XSLT-related templates
- Heavily customized templates

**Action**: Copy to `nexuslims_overrides/templates/` with same path

#### Category B: Partial Modifications
Templates that extend or modify specific sections:
- Homepage
- Detail page
- Search results

**Action**: Use template inheritance (recommended)

#### Category C: Context/Data Only
Templates that only need different data, same structure:
- List views
- Info pages

**Action**: Use context processors or view decorators

### Step 3: Migrate Templates Using Inheritance

Example migration for `homepage.html`:

**Before** (old location: `templates/core_main_app/user/homepage.html`):
```django
{% extends 'core_main_app/user/base.html' %}
{% load static %}

{% block content %}
<div class="row" id="intro">
    <div class="col-8 offset-1">
        <h2>{{ CUSTOM_TITLE }}</h2>
        <p>{{ NX_HOMEPAGE_TEXT }}</p>
        <!-- lots of custom content -->
    </div>
</div>
{% endblock %}
```

**After** (new location: `nexuslims_overrides/templates/core_main_app/user/homepage.html`):
```django
{% extends "core_main_app/user/homepage.html" %}
{# Note: extends the ORIGINAL template from core_main_app #}

{% load static %}
{% load nexuslims_extras %}

{% block extra_head %}
    {{ block.super }}
    <link rel="stylesheet" href="{% static 'nexuslims/css/homepage.css' %}">
{% endblock %}

{% block intro_text %}
    {# Only override the intro text section #}
    <p>{{ NX_HOMEPAGE_TEXT }}</p>
{% endblock %}

{% block extra_scripts %}
    {{ block.super }}
    <script src="{% static 'nexuslims/js/main.js' %}"></script>
{% endblock %}
```

**Benefits**:
- Upstream changes to layout automatically inherited
- Only customized sections are overridden
- Clear what's different from base MDCS

### Step 4: Move Static Files

#### CSS Migration

**Before** (scattered locations):
```
static/css/main.css
static/css/extra.css
static/css/btn_custom.css
static/core_main_app/css/homepage.css
results_override/static/core_explore_common_app/user/css/results.css
```

**After** (centralized):
```
nexuslims_overrides/static/nexuslims/css/
├── main.css          # Imports all others
├── homepage.css      # Homepage specific
├── detail.css        # Detail page specific
├── search.css        # Search/results specific
├── toolbar.css       # Toolbar specific
└── buttons.css       # Button customizations
```

**Migration steps**:
1. Copy CSS content to appropriate file in `nexuslims_overrides/static/nexuslims/css/`
2. Remove duplicate rules
3. Update `main.css` to import new file
4. Test that styles still apply

#### JavaScript Migration

**Before**:
```
static/js/menu_custom.js
static/js/nexus_buttons.js
results_override/static/.../results.js
```

**After**:
```
nexuslims_overrides/static/nexuslims/js/
├── main.js           # Main initialization
├── toolbar.js        # Toolbar functionality (from nexus_buttons.js)
├── menu.js           # Menu customizations (from menu_custom.js)
├── downloads.js      # Download system (from results.js)
└── tutorial.js       # Shepherd.js tutorial
```

### Step 5: Migrate Context Processors

**Before** (`mdcs_home/context_processors.py`):
```python
from django.conf import settings

def doc_link(request):
    return {
        'DOCUMENTATION_LINK': getattr(settings, 'DOCUMENTATION_LINK', ''),
    }
```

**After** (`nexuslims_overrides/context_processors.py`):
```python
from django.conf import settings

def nexuslims_settings(request):
    return {
        'NX_DOCUMENTATION_LINK': getattr(settings, 'NX_DOCUMENTATION_LINK', ''),
        'NX_HOMEPAGE_TEXT': getattr(settings, 'NX_HOMEPAGE_TEXT', ''),
        # ... all NexusLIMS settings
    }
```

**Update `settings.py`**:
```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... existing ...
                # OLD: 'mdcs_home.context_processors.doc_link',
                # NEW:
                'nexuslims_overrides.context_processors.nexuslims_settings',
            ],
        },
    },
]
```

### Step 6: Migrate Template Tags

**Before** (`mdcs_home/templatetags/xsl_transform_tag.py`):
- Custom XSLT transformation tags
- Scattered across mdcs_home

**After** (`nexuslims_overrides/templatetags/nexuslims_extras.py`):
- All custom tags in one place
- Properly namespaced
- Well documented

**Keep the XSLT tags in mdcs_home** if they're tightly coupled to XSLT parameter passing system. Otherwise, move to `nexuslims_overrides`.

### Step 7: Update INSTALLED_APPS Order

**Before**:
```python
INSTALLED_APPS = [
    # ...
    'mdcs_home',
    'results_override',
    'core_main_app',
    # ...
]
```

**After**:
```python
INSTALLED_APPS = [
    # ...
    'nexuslims_overrides',  # NEW: All customizations
    'mdcs_home',            # Keep for backward compat or remove
    # 'results_override',   # Can be removed if functionality moved
    'core_main_app',
    # ...
]
```

### Step 8: Testing Checklist

After migration, test:

- [ ] Homepage displays correctly
- [ ] Homepage text uses `NX_HOMEPAGE_TEXT`
- [ ] All static files load (check browser console)
- [ ] Templates use correct inheritance
- [ ] Context processors provide expected variables
- [ ] Custom template tags work (`{% load nexuslims_extras %}`)
- [ ] Toolbar appears and functions
- [ ] Download buttons work
- [ ] Search results display correctly
- [ ] Detail pages render correctly
- [ ] XSLT transformations still work
- [ ] No 404s for static files
- [ ] No template errors in logs

### Step 9: Clean Up Old Files

Once everything works with `nexuslims_overrides`:

1. **Remove old overrides**:
```bash
# Backup first!
git checkout -b cleanup/old-overrides

# Remove old scattered templates (keep backup)
mv templates/core_main_app templates/core_main_app.backup
mv templates/core_explore_common_app templates/core_explore_common_app.backup
# etc.
```

2. **Remove old static files**:
```bash
mv static/css static/css.backup
mv results_override/static results_override/static.backup
```

3. **Update gitignore** if needed

4. **Test thoroughly** before committing

5. **Commit changes**:
```bash
git add nexuslims_overrides/
git commit -m "feat: centralize customizations in nexuslims_overrides app"
```

## Gradual Migration Approach

You don't have to migrate everything at once. Recommended order:

1. **Phase 1**: Set up app structure and context processors (easiest)
2. **Phase 2**: Migrate CSS to centralized location
3. **Phase 3**: Migrate JavaScript
4. **Phase 4**: Migrate simple templates (homepage, etc.)
5. **Phase 5**: Migrate complex templates (detail, search)
6. **Phase 6**: Clean up old files

Both systems can coexist during migration!

## Troubleshooting

### Templates not found
**Issue**: `TemplateDoesNotExist` error

**Solution**: Check `INSTALLED_APPS` order - `nexuslims_overrides` must come BEFORE core apps

### Styles not applying
**Issue**: CSS not loading

**Solution**: 
1. Run `python manage.py collectstatic`
2. Check static file paths in templates
3. Check browser console for 404s

### Context variables missing
**Issue**: `{{ NX_SOMETHING }}` is empty

**Solution**: Check context processors are registered in `settings.py`

### Template inheritance not working
**Issue**: Changes in base template not appearing

**Solution**: 
1. Check `{% extends %}` points to correct template
2. Check block names match between child and parent
3. Use `{{ block.super }}` to include parent content

## Questions?

Refer to `nexuslims_overrides/README.md` for detailed usage instructions.
