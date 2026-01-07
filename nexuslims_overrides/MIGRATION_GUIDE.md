# Migrating Existing Customizations to nexuslims_overrides

This guide helps migrate existing scattered template overrides into the centralized `nexuslims_overrides` app.

## Migration Strategy


### Current status:
- [x] Homepage
- [x] Explore page
  - [x] Download/export button not working
- [ ] Record page
  - [x] wonky styling
    - [x] paginate on left side bar
    - [x] paginate on file list tables
    - [x] badge font is too large
    - [x] datatable search and paginate on metadata display modal
    - [x] preview gallery caption styling is super wide; it should only be as wide as the preview gallery itself
    - [x] "X" button is not clickable on activity metadata modal
    - [x] Buttons and header styling on download file modal
  - [x] Tooltips stay visible when clicking a link with one
  - [x] `xmlName` parameter should get passed into
    - `<span id="xmlName" style="display: none;"></span>`
  - [x] top toolbar
  - [x] page jumps when closing modal
  - [x] "InstallTrigger is deprecated and will be removed in the future."
  - [x] how to include instrument data (maybe init_dev_environment expands a .tar.gz?)
  - [x] ZIP downloads
  - [x] Edit button doesn't work, 
    - [x] should only show when the user is logged in and has permissions
  - [x] feat: easily configurable badge colors?
- [ ] Simple display should be checked
  - [ ] fix sidebar on wide display and never show "scroll to top" button
  - [ ] we should add search filtering to the datatable on this display
- [ ] Homepage responsive spacing

### Other TODOs:
- [ ] Tutorials
- [x] Javascript libraries for detail XSLT (maybe better in an app, or override?)
- [x] overall spacing on explore page
- [x] search bar overlaps search button on explore
- [x] color of search button on explore page



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
- [x] `templates/theme/menu.html`
- [x] `templates/core_explore_keyword_app/user/index.html`
- [x] `templates/core_explore_common_app/user/results/data_sources_results.html`
  - [x] Replace Bootstrap nav-tabs structure with custom flex-based tab layout
  - [x] Move toolbar from inside tab panels to main navigation bar (`explore-bar`)
  - [x] Change results counter from Bootstrap badges to plain `<span>` elements
  - [x] Simplify data source labels from "From {{ data_source.name }}" to "Found X Results:" format
  - [x] Remove Bootstrap version conditional checks (BOOTSTRAP_VERSION)
  - [x] Add `flex-grow: 1` and `text-align: left` styling to tab list items
  - [x] Update tab navigation to use `explore-bar` class instead of `nav nav-tabs`
  - [x] Move sorting menu include to main toolbar section
  - [x] Move persistent query button to main toolbar
  - [x] Move linked records button to main toolbar
  - [x] Move export button to main toolbar
  - [x] Move date toggle to main toolbar
  - [x] Add "Please wait while records are loading..." loading placeholder message
  - [x] Remove individual `result-toolbar` divs from each tab panel
  - [x] Consolidate toolbar controls into single unified bar
  - [x] Update tab panel structure to reference new toolbar location
  - [x] Test tab switching functionality with unified toolbar
  - [x] Verify loading placeholder displays correctly during data loading
  - [ ] Ensure all toolbar buttons function correctly with new layout
- [x] `results_override` application
  - [x] **Major Functional Changes in `get_data_source_results`:**
    - [x] Added result page hiding/showing with fade effects for better UX
    - [x] Added loading placeholder removal logic
    - [x] Commented out the `leaveNotice` functionality
    - [x] Added proper fade-in/fade-out animations for result loading
  - [x] **Specific Changes in Success Callback:**
    - [x] Added `result_page.hide()` to hide the result page initially
    - [x] Added fade-out animation for loading placeholder
    - [x] Commented out the `leaveNotice` call
    - [x] Added fade-in animation for showing results
  - [x] **Changes in Error Callback:**
    - [x] Added `result_page.hide()` to hide the result page initially
    - [x] Added fade-out animation for loading placeholder
    - [x] Added fade-in animation for showing error results
  - [x] **`query_result.css` Changes:** 
    - **`.xmlResult`:** (changed to `.content-result` to follow new class name)
      - [x] Removed `background-color: #F8F8F8;`
      - [x] Removed `display:none;
  - [x] **`results.css` Changes:**
    - [x] **`.data-info-right-container`:**
      - [x] Commented out `float: right;`
      - [x] Added `flex-grow: 1;`
      - [x] Changed `width: auto;` to `width: auto !important;`
    - [x] **`.data-info-left-container`:**
      - [x] Commented out `float: left;`
      - [x] Added `display: flex;`
      - [x] Added `align-items: center;`
      - [x] Added `justify-content: space-between;`
    - [x] **`.xmlResult`:** (changed to `.content-result` to follow new class name)
      - [x] Added `flex-grow: 1;`
      - [x] Added `margin-left: 1em;`
      - [x] Added `margin-right: 1em;`
      - [x] Added comment "jat additions"
    - [x] **New CSS classes added:**
      - [x] `.exporter-checkbox` with fixed height and width (24px)
      - [x] `.explore-bar` with flex display and styling
      - [x] `.toggle-container label` with display and vertical-align overrides
      - [x] `#loading-placeholder` with flex-grow and text alignment
- [x] `templates/core_explore_common_app/user/results/data_source_info.html`
- [x] `mdcs_home/templatetags/xsl_transform_tag.py` - copied as `nexuslims_overrides/templatetags/nexuslims_xsl_transform.py`
- [x] `mdcs_home/utils/xml.py` - copied as is to nexuslims_overrides.xml
- [x] `templates/core_explore_common_app/user/results/data_source_results.html`
- [x] `templates/core_main_app/user/data/detail.html`
  - [x] Comment out title section (h2 with data.data.title and template.display_name)
  - [x] Comment out tools_data.html include (removes XSLT selector toolbar)
  - [x] Keep only the detail_data.html include for clean content-only view
- [x] `templates/core_main_app/common/data/detail_data.html`
  - [x] Wrap content in Bootstrap container-fluid/row structure instead of plain div
  - [x] Pass xmlName=data.data.title parameter to xsl_transform_detail tag
  - [x] Preserve new 2.18.0 features (data_detail_html tag, JSON/XSD format handling)
  - [x] Keep request parameter for XSLT context (unlike 2.21.0 version which removed it)
- [x] `templates/core_main_app/_render/user/theme_base.html`

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
{% load nexuslims_templatetags %}

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

**After** (`nexuslims_overrides/templatetags/nexuslims_templatetags.py`):
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
- [ ] Custom template tags work (`{% load nexuslims_templatetags %}`)
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
