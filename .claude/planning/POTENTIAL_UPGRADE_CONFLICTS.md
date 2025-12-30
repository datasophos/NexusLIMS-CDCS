# NexusLIMS-CDCS: Potential Upgrade Conflicts (v2.21.0 → v3.18.0)

**Document Purpose:** This document analyzes changes in MDCS and its component repositories between v2.21.0 (July 2022) and v3.18.0 (current) to identify potential conflicts with NexusLIMS-CDCS customizations during the upgrade process.

**Analysis Date:** 2025-12-30  
**Baseline Version:** MDCS 2.21.0 (July 7, 2022)  
**Target Version:** MDCS 3.18.0  
**Related Documentation:** See `CHANGES_FROM_MDCS_2.21.0.md` for complete customization inventory

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Critical Breaking Changes](#critical-breaking-changes)
3. [MDCS Core Repository Changes](#mdcs-core-repository-changes)
4. [core_main_app Conflicts](#core_main_app-conflicts)
5. [core_explore_common_app Conflicts](#core_explore_common_app-conflicts)
6. [core_explore_keyword_app Conflicts](#core_explore_keyword_app-conflicts)
7. [Upgrade Risk Matrix](#upgrade-risk-matrix)
8. [Recommended Upgrade Strategy](#recommended-upgrade-strategy)
9. [Testing Requirements](#testing-requirements)
10. [Appendices](#appendices)

---

## Executive Summary

### Upgrade Scope

This is a **MAJOR VERSION UPGRADE** spanning:
- **87 commits** in MDCS core repository
- **48 files changed** in core configuration
- **Multiple component app upgrades** (core_main_app, core_explore_common_app, etc.)
- **Django 2.2 → 4.2 → 5.2** framework upgrades
- **Bootstrap 4 → 5** UI framework upgrade
- **MongoDB/MongoEngine → SQLModel** ORM migration

### Risk Level: **CRITICAL**

This upgrade requires substantial refactoring and testing. A recent merge attempt (commit cf1dc6d) in the NexusLIMS-CDCS repository appears to have **incorrect conflict resolution** (kept 1.21.* dependencies instead of upgrading to 2.18.*).

### Top 5 Critical Conflicts

| Priority | Area | Impact | Affected Files |
|----------|------|--------|----------------|
| 🔴 **CRITICAL** | Django 2.2 → 5.2 upgrade | Breaking changes, deprecated features | All Python code |
| 🔴 **CRITICAL** | Core app versions (1.21.* → 2.18.*) | Incompatible dependencies | requirements.core.txt, settings.py |
| 🔴 **CRITICAL** ⚠️ *Can be eliminated* | XSLT parameter system | Custom override may break | mdcs_home/utils/xml.py, template tags |
| 🔴 **CRITICAL** | results.js complete rewrite | JSON support, new selectors | results_override/static/.../results.js |
| 🟡 **HIGH** | Bootstrap 4 → 5 migration | CSS classes, template syntax | 40+ template files |

**Note:** The XSLT parameter system conflict can be **completely eliminated** with a ~4 hour refactor to use HTML5 data attributes instead. See Section "ALTERNATIVE: Eliminate XSLT Parameter System" in the core_main_app conflicts section.

### Component Repository Versions

| Repository | v2.21.0 Version | v3.18.0 Version | Breaking Changes |
|------------|-----------------|-----------------|------------------|
| core_main_app | 1.21.* | 2.18.* | Yes - Django 5, allauth |
| core_explore_common_app | 1.21.* | 2.18.* | Yes - JSON support |
| core_explore_keyword_app | 1.21.* | 2.18.* | Moderate |
| core_composer_app | 1.21.* | 2.18.* | Unknown |
| core_curate_app | 1.21.* | 2.18.* | Unknown |
| core_dashboard_app | 1.21.* | 2.18.* | Unknown |

---

## Critical Breaking Changes

### 1. Django Framework Upgrade (2.2 → 5.2)

**Commits:**
- Django 2.2 → 4.2: June 2023 (commit 1e509ce in core_main_app)
- Django 4.2 → 5.2: November 2025 (commit c81067e in core_main_app)

**Breaking Changes:**

#### Python Version Requirements
```python
# v2.21.0 (Django 2.2)
Python 3.6, 3.7, 3.8, 3.9

# v3.18.0 (Django 5.2)
Python 3.11, 3.12 ONLY
```

**Impact:** NexusLIMS-CDCS must migrate to Python 3.11+

#### Deprecated Features Removed
- `django.utils.encoding.force_text` → `force_str`
- `django.conf.urls.url()` → `django.urls.re_path()`
- `django.utils.translation.ugettext*` → `gettext*`
- Template context processors signature changes
- Middleware ordering requirements changed

**NexusLIMS Files at Risk:**
- ✅ All Python files using deprecated imports
- ✅ `mdcs_home/context_processors.py` - May need signature updates
- ✅ URL patterns if using old `url()` syntax

---

### 2. Core App Dependency Versions (CRITICAL)

**Required Changes in `requirements.core.txt`:**

```diff
# OLD (v2.21.0)
- core_main_app==1.21.0
- core_explore_common_app==1.21.0
- core_explore_keyword_app==1.21.0
# ... all other core apps at 1.21.*

# NEW (v3.18.0)
+ core_main_app[mongodb,auth]==2.18.0
+ core_explore_common_app==2.18.0
+ core_explore_keyword_app==2.18.0
# ... all other core apps at 2.18.*
```

**Critical Note:** The recent merge commit cf1dc6d states "Resolved conflicts by keeping current dependency versions (1.21.*)" - **This is incorrect and will cause failures.**

**Impact:**
- 🔴 1.21.* versions are **incompatible** with Django 4.2+
- 🔴 Missing features: JSON schema support, django-allauth, Bootstrap 5
- 🔴 Database migrations may fail

**Action Required:** All core_*_app dependencies MUST be upgraded to 2.18.* versions.

---

### 3. INSTALLED_APPS Restructuring

**Major Changes:**

#### Apps Removed
```python
# These apps are REMOVED in v3.18.0:
- "drf_yasg"                      # Replaced with drf_spectacular
- "rest_framework_mongoengine"    # MongoDB ORM removed
- "tz_detect"                     # Replaced with core_main_app middleware
- "core_oaipmh_common_app"        # OAI-PMH support removed
- "core_oaipmh_harvester_app"
- "core_oaipmh_provider_app"
- "core_explore_oaipmh_app"
```

#### Apps Added
```python
# New apps in v3.18.0:
+ "rest_framework.authtoken"
+ "drf_spectacular"
+ "fontawesomefree"
+ "defender"  # Now conditionally added
```

#### Critical Ordering Change

**v2.21.0 (ORIGINAL MDCS):**
```python
INSTALLED_APPS = (
    # ... Django apps ...
    "core_main_app",
    # ... other core apps ...
    "mdcs_home",  # At the end
)
```

**NexusLIMS-CDCS Customization:**
```python
INSTALLED_APPS = (
    # ... Django apps ...
    # THIS COMMENT IS CRITICAL:
    # "this needs to come before mdcs_home so xml templatetag override works"
    "core_main_app",
    
    # Local apps
    "mdcs_home",
    
    # Override for results.js
    "results_override",
    
    # ... rest of core apps ...
)
```

**Conflict Risk:** 🔴 **CRITICAL** - If app order changes, template tag override silently fails

**Testing Required:**
- Verify `core_main_app` loads before `mdcs_home`
- Verify `xsl_transform_detail` template tag resolves to NexusLIMS version
- Check import path: `from mdcs_home.utils.xml import xsl_transform`

---

### 4. Middleware Changes

**Removed Middleware:**
```python
- "defender.middleware.FailedLoginMiddleware"  # Now conditional
- "tz_detect.middleware.TimezoneMiddleware"    # Package removed
```

**Added Middleware:**
```python
+ "core_main_app.middleware.timezone.TimezoneMiddleware"
```

**New Conditional Logic:**
```python
# Defender now added conditionally
if "defender" not in INSTALLED_APPS:
    INSTALLED_APPS = INSTALLED_APPS + ("defender",)

if "defender.middleware.FailedLoginMiddleware" not in MIDDLEWARE:
    MIDDLEWARE = MIDDLEWARE + ("defender.middleware.FailedLoginMiddleware",)
```

**Impact:** NexusLIMS settings.py must adopt this conditional logic or explicitly include/exclude defender.

---

### 5. Authentication System Overhaul

**Commit:** 99660e3 (October 2024) - "feat: django-allauth"

**Changes:**
- **django-allauth** replaces Django's built-in authentication
- 30 new files, 1,023 insertions
- Login page completely redesigned (commit e26ef94)
- OIDC and SAML2 support added
- New URL patterns for auth

**New Settings:**
```python
ENABLE_ALLAUTH = os.getenv("ENABLE_ALLAUTH", "False").lower() == "true"

if ENABLE_ALLAUTH:
    INSTALLED_APPS += (
        "allauth",
        "allauth.account",
        "allauth.socialaccount",
        # ... social providers ...
    )
```

**NexusLIMS Impact:**

**Current Status:** ✅ **No login template customizations exist**

Investigation shows:
- Commit 564b2ed (Oct 2024) added django-allauth templates on branch `merge_attempt`
- Commit cf1dc6d attempted to merge these changes
- Current HEAD (30faa97) on `NexusLIMS_master` does NOT include allauth templates
- Templates were deleted or never merged to main branch

**Verified:** No customized templates in current working tree:
```bash
# No login/auth templates found:
templates/account/          # Does not exist
templates/allauth/          # Does not exist  
templates/socialaccount/    # Does not exist
```

**Impact Assessment:**
- ✅ No login template merge conflicts expected
- ✅ User registration flow - using vanilla MDCS
- ⚠️ URL patterns for `/accounts/` - verify no hardcoded references
- ⚠️ May affect SAML/Handle PID integration if NexusLIMS uses it (check settings)

**Action Required:** 
1. ✅ No template merging needed (no custom login templates)
2. Verify `ENABLE_SAML2_SSO_AUTH` setting if SAML is used
3. Verify `ENABLE_HANDLE_PID` setting if Handle PIDs are used
4. Test authentication flows after upgrade
5. If django-allauth is enabled, may need to add templates for branding

---

## MDCS Core Repository Changes

### Change Statistics

| Metric | Value |
|--------|-------|
| Total Commits (2.21.0 → 3.18.0) | 87 |
| Files Changed | 48 |
| Python Version | 3.6-3.9 → 3.11-3.12 |
| Django Version | 2.2.28 → 5.2 |
| Bootstrap | 4.x → 5.1.3 |

### Configuration File Changes

#### 1. `mdcs/settings.py` (CRITICAL CONFLICTS EXPECTED)

**Lines Changed:** 257+ modifications

**Key Conflicts:**

##### A. INSTALLED_APPS Section
```python
# NEW structure includes:
- Removed OAI-PMH apps
- Added drf_spectacular (OpenAPI 3.0)
- Added rest_framework.authtoken
- Conditional defender
```

**NexusLIMS Customization:**
```python
# Custom order for template tag override:
"core_main_app",      # MUST be first
"mdcs_home",          # Overrides second
"results_override",   # Static file override
```

**Merge Strategy:** Keep NexusLIMS ordering; remove OAI-PMH apps; add new apps at appropriate positions.

##### B. REST_FRAMEWORK Configuration
```python
# OLD (2.21.0)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
}

# NEW (3.18.0)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",  # NEW
}
```

**Impact:** 🟡 BasicAuthentication removed; OAuth2 and Token auth added. Check if NexusLIMS has API integrations.

##### C. Context Processors
```python
# NexusLIMS Customization (MUST PRESERVE):
"mdcs_home.context_processors.doc_link"  # Instead of i18n

# NEW in v3.18.0 may have other changes to verify compatibility
```

##### D. New Settings Added
```python
# Environment-based feature flags
ENABLE_ALLAUTH = os.getenv("ENABLE_ALLAUTH", "False").lower() == "true"
BOOTSTRAP_VERSION = os.getenv("BOOTSTRAP_VERSION", "5.1.3")
TEXT_EDITOR_LIBRARY = os.getenv("TEXT_EDITOR_LIBRARY", "Monaco")
ADMIN_URLS_PREFIX = os.getenv("ADMIN_URLS_PREFIX", "staff-")
TIME_ZONE = os.getenv("TZ", "UTC")  # Was hard-coded
```

**Action Required:** Add these to NexusLIMS settings.py with appropriate defaults.

---

#### 2. `mdcs/urls.py` (HIGH CONFLICTS)

**Changes:**

##### A. Admin URL Prefix
```python
# OLD (2.21.0)
re_path(r"^admin/", admin.site.urls)

# NEW (3.18.0)
from mdcs.core_settings import ADMIN_URLS_PREFIX
from core_main_app.admin import core_admin_site

re_path(rf"^{ADMIN_URLS_PREFIX}admin/", admin.site.urls)
re_path(rf"^{ADMIN_URLS_PREFIX}core-admin/", core_admin_site.urls)
```

**Impact:** 🟡 Any hardcoded `/admin/` links in templates or JavaScript will break.

**Files to Update:**
- All templates with admin links
- JavaScript files with admin URL references
- Documentation

##### B. OAI-PMH Routes Removed
```python
# REMOVED in v3.18.0:
- re_path(r"^oaipmh_search/", include("core_explore_oaipmh_app.urls"))
- re_path(r"^oai_pmh/", include("core_oaipmh_harvester_app.urls"))
- re_path(r"^oai_pmh/server/", include("core_oaipmh_provider_app.urls"))
```

**Impact:** 🟡 If NexusLIMS users access OAI-PMH endpoints, they will 404.

**Action Required:** Decide if OAI-PMH is needed; if yes, maintain fork of those apps.

##### C. Module Discovery Removed
```python
# REMOVED at end of urls.py:
- discover_modules(urlpatterns)
```

**Impact:** Unknown - check if NexusLIMS relies on module discovery for custom apps.

---

#### 3. `mdcs/core_settings.py` (MEDIUM CONFLICTS)

**New Settings:**

```python
# BigAutoField for primary keys (migration required)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# MongoDB configuration moved from settings.py
MONGODB_INDEXING = os.getenv("MONGODB_INDEXING", "False").lower() == "true"
MONGODB_ASYNC = os.getenv("MONGODB_ASYNC", "True").lower() == "true"

# New feature flags
ENABLE_SAML2_SSO_AUTH = os.getenv("ENABLE_SAML2_SSO_AUTH", "False").lower() == "true"
ENABLE_HANDLE_PID = os.getenv("ENABLE_HANDLE_PID", "False").lower() == "true"
```

**NexusLIMS Existing Customization:**
```python
CUSTOM_TITLE = "Welcome to NexusLIMS!"  # Changed from MDCS default
```

**Action Required:** Preserve NexusLIMS title; adopt new env-based settings.

---

### Static Files Changes

**Removed (IE Support):**
- `static/ie/` directory - IE 8/9 polyfills
- `static/libs/jquery.dropotron/` - Menu widget
- `static/libs/skel/` - Responsive framework
- `static/js/dropdown.js`

**Impact:** 🟢 Low - NexusLIMS doesn't rely on these (uses custom menu system).

**Added:**
- Bootstrap 5 support
- Font Awesome Free integration
- Updated main.css and menu.css

**Impact:** 🟡 Medium - CSS selectors may conflict with NexusLIMS custom styles.

---

## core_main_app Conflicts

### Repository Analysis

**Component:** core_main_app  
**Location:** `/Users/josh/git_repos/datasophos/cdcs/core_main_app`  
**Version Jump:** 1.21.* → 2.18.*

### Critical Changes Affecting NexusLIMS

#### 1. XSLT Transform Function (CRITICAL)

**File:** `core_main_app/utils/xml.py`  
**Function:** `xsl_transform(xml_string, xslt_string)`  
**Line:** 508 (current)

**Status:** Function signature **has not changed** but NexusLIMS has a critical override.

**NexusLIMS Override:** `mdcs_home/utils/xml.py`
```python
def xsl_transform(xml_string, xslt_string, **kwargs):
    """Apply transformation to xml, allowing for parameters to the XSLT
    
    Args:
        xml_string:
        xslt_string:
        kwargs : dict
            Other keyword arguments are passed as parameters to the XSLT object
    """
    try:
        xslt_tree = XSDTree.build_tree(xslt_string)
        xsd_tree = XSDTree.build_tree(xml_string)
        transform = XSDTree.transform_to_xslt(xslt_tree)
        transformed_tree = transform(xsd_tree, **kwargs)  # ← kwargs passed here
        return str(transformed_tree)
    except Exception:
        raise exceptions.CoreError("An unexpected exception happened while transforming the XML")
```

**Upstream Version (core_main_app):**
```python
def xsl_transform(xml_string, xslt_string):
    """Apply transformation to xml
    
    Args:
        xml_string:
        xslt_string:
    
    Returns:
    """
    # No **kwargs support
```

**Conflict Risk:** 🔴 **CRITICAL**

**Why This Matters:**
- NexusLIMS XSLT stylesheets (`detail_stylesheet.xsl`, `list_stylesheet.xsl`) **require** parameters like `xmlName`, `datasetBaseUrl`, `previewBaseUrl`
- Without this override, XSLT parameters won't be passed, and record detail pages will display incorrectly
- The override is imported in `mdcs_home/templatetags/xsl_transform_tag.py`: `from mdcs_home.utils.xml import xsl_transform`

**Recent Changes:**
- Commit e770e2f (2024): "refactor XML dependency update" - touched xml.py but didn't change signature
- Commit 15c5bbd (2024): "feat: template rest queries" - modified xml.py (+6 lines)
- No breaking changes detected, but future changes could break compatibility

**Testing Required:**
1. Verify `from mdcs_home.utils.xml import xsl_transform` resolves correctly
2. Test XSLT parameter passing: `{% xsl_transform_detail xml_content=record xmlName=title %}`
3. Confirm record detail pages display title and download links

---

#### 1.1 ALTERNATIVE: Eliminate XSLT Parameter System (RECOMMENDED)

**Status:** 🟢 **OPTIONAL REFACTOR** - This would eliminate the entire XSLT parameter customization

**Current Problem:**
The XSLT parameter system exists solely to pass `xmlName` (the record title) from Django to embedded JavaScript in the XSLT for download filenames. This creates:
- Complex custom override of `core_main_app/utils/xml.py`
- Custom template tag in `mdcs_home/templatetags/xsl_transform_tag.py`
- Dependency on specific app loading order
- High conflict risk with upstream MDCS

**Analysis of Current Usage:**

The `xmlName` parameter is used in only 2 places in `xslt/detail_stylesheet.xsl`:

1. **Line 1339:** Creates a hidden span
```xml
<span id='xmlName' style='display: none;'><xsl:value-of select="$xmlName"/></span>
```

2. **Lines 4348 & 4612:** JavaScript reads from hidden span for download filenames
```javascript
// For zip file download naming
var record_title = $('span#xmlName').text();
var zip_title = record_title.endsWith('.xml') 
    ? record_title.replace('.xml', '.zip') 
    : record_title + '.zip';

// For individual XML download naming  
a.download = $('#xmlName').text();
```

**Proposed Solution: HTML5 Data Attributes**

Replace the XSLT parameter system with standard HTML5 data attributes in the Django template.

**Implementation:**

**Step 1:** Modify Django template to add data attributes
```django
{# File: templates/core_main_app/common/data/detail_data.html #}

{# OLD (current): #}
{% xsl_transform_detail 
   xmlName=data.data.title 
   xml_content=data.data.xml_content 
   template_id=data.data.template.id 
%}

{# NEW (proposed): #}
<div class="record-detail-container" 
     data-record-id="{{ data.data.id }}"
     data-record-title="{{ data.data.title }}"
     data-template-id="{{ data.data.template.id }}">
    
    {% xsl_transform_detail 
       xml_content=data.data.xml_content 
       template_id=data.data.template.id 
    %}
    {# Note: No xmlName parameter! #}
</div>
```

**Step 2:** Update XSLT JavaScript to read from data attributes
```xml
<!-- File: xslt/detail_stylesheet.xsl -->

<!-- OLD (current) - Line 1339: -->
<span id='xmlName' style='display: none;'><xsl:value-of select="$xmlName"/></span>

<!-- NEW (proposed): -->
<!-- Remove hidden span entirely -->

<!-- OLD (current) - Lines 4348, 4612: -->
<script>
var record_title = $('span#xmlName').text();
</script>

<!-- NEW (proposed): -->
<script>
// Get from data attribute on container div
var record_title = $('.record-detail-container').data('record-title') || 
                   $('h1.record-title').text().trim() ||  // Fallback
                   'record';  // Default
</script>
```

**Step 3:** Remove custom Python code
```bash
# These files can be deleted:
rm mdcs_home/utils/xml.py
rm mdcs_home/templatetags/xsl_transform_tag.py
rm mdcs_home/templatetags/__init__.py  # If no other tags

# Update settings.py INSTALLED_APPS:
# Can now use vanilla core_main_app template tags
# No special app ordering required (though can keep for other reasons)
```

**Step 4:** Update XSLT parameter declaration
```xml
<!-- File: xslt/detail_stylesheet.xsl -->

<!-- OLD (current) - Line 11: -->
<xsl:param name="xmlName" select="''"/>

<!-- NEW (proposed): -->
<!-- Remove parameter declaration entirely -->
```

**Benefits:**

| Aspect | Current (XSLT Params) | Proposed (Data Attributes) |
|--------|----------------------|---------------------------|
| **Upstream Compatibility** | ❌ Requires custom override | ✅ Compatible with vanilla MDCS |
| **Upgrade Conflicts** | 🔴 CRITICAL conflict | 🟢 No conflicts |
| **Code Complexity** | 3 custom Python files | 0 custom Python files |
| **Maintainability** | ❌ Complex override chain | ✅ Standard HTML5 pattern |
| **Performance** | Same | Same |
| **App Loading Order** | ⚠️ Must be specific | ✅ No dependency |
| **Lines of Code** | ~200 custom Python + XSLT | ~10 lines HTML changes |

**Migration Effort:**

| Task | Estimated Time | Complexity |
|------|---------------|------------|
| Modify Django template | 30 minutes | Low |
| Update XSLT JavaScript | 1 hour | Low |
| Remove Python overrides | 15 minutes | Low |
| Test functionality | 2 hours | Medium |
| **Total** | **~4 hours** | **Low-Medium** |

**Testing Checklist:**
```
□ Record detail page loads
□ Record title displays correctly
□ Download single XML file - filename is correct
□ Download all files as zip - filename is correct
□ Multi-signal datasets download with correct zip name
□ No JavaScript console errors
□ Works in Chrome, Firefox, Safari
```

**Risk Assessment:**

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Data attribute missing | Low | High | Add fallback to page title |
| JavaScript selector breaks | Low | Medium | Test thoroughly before deploy |
| Browser compatibility | Very Low | Low | Data attributes are HTML5 standard |

**Recommendation:**

🟢 **STRONGLY RECOMMENDED** - Implement this refactor before attempting the 3.18.0 upgrade.

**Why:**
1. **Eliminates CRITICAL upgrade conflict** - Removes dependency on custom xml.py
2. **Future-proof** - Won't break with future MDCS updates
3. **Industry standard** - HTML5 data attributes are the proper pattern
4. **Low effort** - Can be completed in ~4 hours
5. **Reduces complexity** - Removes ~200 lines of custom code
6. **Better architecture** - Separates concerns properly (Django templates handle data, JavaScript reads it)

**Implementation Order:**

If implementing this refactor:
1. Do it **BEFORE** the 3.18.0 upgrade (on current 2.21.0 base)
2. Test thoroughly on current version
3. Then proceed with upgrade - one less critical conflict to manage

If skipping this refactor:
1. Must preserve all custom Python files during upgrade
2. Must verify app loading order
3. Must test XSLT parameter system after upgrade
4. Higher risk of conflicts with future updates

---

#### 2. Template Tag System (HIGH RISK) ⚠️ *Can be eliminated with data attributes*

**File:** `core_main_app/templatetags/xsl_transform_tag.py` (upstream)

**NexusLIMS Override:** `mdcs_home/templatetags/xsl_transform_tag.py` (136 lines)

**Purpose of Override:**  
This override exists solely to enable passing **kwargs** to XSLT transformations. It works in conjunction with the custom `mdcs_home/utils/xml.py` to forward parameters from Django templates to XSLT stylesheets.

**Key Difference from Upstream:**

```python
# UPSTREAM (core_main_app) - Does NOT pass kwargs:
def _render_xml_as_html(xslt_type, *args, **kwargs):
    xml_string = kwargs["xml_content"]
    template_id = kwargs.get("template_id", None)
    # ... process ...
    return xsl_transform(xml_string, xslt_string)  # ← No kwargs!

# NEXUSLIMS OVERRIDE (mdcs_home) - Passes kwargs:
def _render_xml_as_html(xml_string, template_id=None, ..., **kwargs):
    # ... process ...
    return xsl_transform(xml_string, xslt_string, **kwargs)  # ← Forwards kwargs!
```

**Parameters Currently Used:**

1. **Detail View:** `xmlName` - Record title for download filenames
   ```python
   xmlName = '"{}"'.format(kwargs.pop('xmlName', ''))
   # String wrapped in quotes for XSLT string literal
   ```

2. **List View:** `detail_url` - URL pattern for detail page links
   ```python
   detail_url = '"{}"'.format(kwargs.pop('detail_url', '#'))
   ```

**Complete Dependency Chain:**
```
Django Template
  ↓ {% xsl_transform_detail xmlName=data.title xml_content=xml ... %}
mdcs_home/templatetags/xsl_transform_tag.py
  ↓ Extracts xmlName from kwargs
  ↓ from mdcs_home.utils.xml import xsl_transform
mdcs_home/utils/xml.py
  ↓ def xsl_transform(xml_string, xslt_string, **kwargs)
  ↓ transform(xsd_tree, **kwargs)  # Passes to XSLT processor
XSLT Stylesheet (detail_stylesheet.xsl)
  ↓ <xsl:param name="xmlName" select="''"/>
  ↓ <span id='xmlName'><xsl:value-of select="$xmlName"/></span>
JavaScript (embedded in XSLT)
  ↓ var title = $('span#xmlName').text();
  ↓ Uses for download filenames
```

**Critical Requirement:** `core_main_app` MUST load before `mdcs_home` in `INSTALLED_APPS`.

**Why:** Django's template tag discovery uses first-found. The override must be found second so it can replace the standard implementation. Additionally, the override imports from `mdcs_home.utils.xml`, creating a dependency on app load order.

**Correct Order:**
```python
INSTALLED_APPS = (
    # ...
    "core_main_app",      # ← MUST load first
    "mdcs_home",          # ← Template tag override found second
    "results_override",   # Static file overrides
    # ...
)
```

**Recent Upstream Changes:**
- Commit 80c1420 (2024): "fix: refactor render_xml_as_html method"
- Commit e648df5 (2024): "refactor template tag code"

**Conflict Risk:** 🔴 **HIGH** - If core_main_app's template tag structure changed significantly, the override may break.

**Files Affected:**
- `mdcs_home/templatetags/xsl_transform_tag.py` (136 lines)
- `mdcs_home/templatetags/__init__.py` (package init)
- Depends on: `mdcs_home/utils/xml.py`

**Testing Required:**
1. Check app loading order in final settings.py
2. Verify template tag registration: `python manage.py shell` → `from django import template` → `template.libraries['xsl_transform_tag']`
3. Test detail view rendering with correct download filenames

---

**⚠️ ELIMINATION PATH:**

This **entire override can be removed** by implementing the data attributes approach described in Section 1.1.

**If data attributes are implemented:**
- ✅ Delete `mdcs_home/templatetags/xsl_transform_tag.py`
- ✅ Delete `mdcs_home/templatetags/__init__.py`
- ✅ Delete `mdcs_home/utils/xml.py`
- ✅ Use vanilla `core_main_app` template tags
- ✅ No app loading order dependency
- ✅ No upgrade conflicts

**Migration removes:**
- 136 lines from xsl_transform_tag.py
- 48 lines from xml.py
- 2 files total
- Complex override chain
- Critical upgrade conflict

**Recommended:** Implement data attributes refactor **before** upgrading to eliminate this conflict entirely.

---

#### 3. Django-Allauth Integration (LOW RISK) ✅ *No conflicts expected*

**Commit:** 99660e3 (October 2024) - "feat: django-allauth" in `core_main_app`

**Files Changed in Upstream:**
- `core_main_app/settings.py` (+30 lines)
- `core_main_app/utils/urls.py` (+124 lines changed)
- 30 new template files for account management
- Login page redesign (commit e26ef94)

**New Dependencies:**
```python
# Added to requirements:
django-allauth>=0.57.0
```

**Settings Changes in Upstream:**
```python
ENABLE_ALLAUTH = os.getenv("ENABLE_ALLAUTH", "False").lower() == "true"

if ENABLE_ALLAUTH:
    INSTALLED_APPS += (
        "allauth",
        "allauth.account",
        "allauth.socialaccount",
        "allauth.socialaccount.providers.google",
        "allauth.socialaccount.providers.github",
        # ... other providers ...
    )
    
    AUTHENTICATION_BACKENDS = (
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
    )
```

**URL Changes in Upstream:**
```python
# New URL pattern in core_main_app/utils/urls.py
if settings.ENABLE_ALLAUTH:
    urlpatterns += [
        path("accounts/", include("allauth.urls")),
    ]
```

**Upstream Template Changes:**
- New `templates/account/` directory with 20+ templates
- Login page completely redesigned
- Registration flow changed
- Password reset flow changed

---

**NexusLIMS-CDCS Status:**

**✅ VERIFIED: No custom authentication templates**

Investigation of NexusLIMS-CDCS repository shows:
- Current HEAD (30faa97): **No allauth or login templates exist**
- The `merge_attempt` branch (cf1dc6d) added allauth templates but was never merged to main
- Current `templates/` directory contains only:
  - `core_explore_common_app/` - Results display overrides
  - `core_explore_keyword_app/` - Keyword search overrides  
  - `core_main_app/` - Homepage, data detail overrides
  - `mdcs_home/` - Template list, tiles
  - `theme/` - Banner, footer, menu

**Missing (confirmed):**
```bash
templates/account/          # Does not exist
templates/allauth/          # Does not exist
templates/socialaccount/    # Does not exist
```

**Conflict Risk:** 🟢 **LOW** - No template conflicts

**NexusLIMS Impact Assessment:**
- ✅ **No login template conflicts** - NexusLIMS has no custom login templates
- ✅ **No registration customizations** - Using vanilla MDCS authentication
- ⚠️ **URL patterns** - Verify no hardcoded `/accounts/login/` references exist in:
  - JavaScript files (check menu navigation, redirects)
  - Templates (check login/logout links)
  - Python code (check authentication redirects)
- ⚠️ **SAML Integration** - May be affected if `ENABLE_SAML2_SSO_AUTH` is used
- ⚠️ **Handle PID** - May be affected if `ENABLE_HANDLE_PID` is used

**Action Required:**

**Minimal (Low Risk):**
1. ✅ **No template merging needed** - NexusLIMS has no custom auth templates
2. Search for hardcoded login URLs:
   ```bash
   grep -r "/accounts/login" templates/ static/
   grep -r "core_main_app_login" templates/ static/
   ```
3. Check settings for SAML/Handle PID usage:
   ```python
   # In mdcs/settings.py or environment:
   ENABLE_SAML2_SSO_AUTH = ?
   ENABLE_HANDLE_PID = ?
   ```
4. Test authentication after upgrade:
   - Login works
   - Logout works
   - Password reset (if needed)
5. Optional: Add custom branding templates if django-allauth is enabled

**Decision: Enable django-allauth?**

By default, `ENABLE_ALLAUTH=False`, so vanilla Django authentication will be used. If you want SSO (Google, GitHub, etc.), set `ENABLE_ALLAUTH=True` and add provider configuration.

**Recommendation:** Keep `ENABLE_ALLAUTH=False` for simplicity unless SSO is needed.

---

#### 4. Bootstrap 5 Migration (HIGH RISK)

**Commit:** e23522a (July 2023) - Bootstrap 5.x support

**Files Changed:** 40+ template files

**CSS Class Changes:**
```python
# Bootstrap 4 → Bootstrap 5 mapping
"badge-secondary" → "bg-secondary"
"float-right" → "float-end"
"float-left" → "float-start"
"data-toggle" → "data-bs-toggle"
"data-target" → "data-bs-target"
"ml-*" / "mr-*" → "ms-*" / "me-*"
"pl-*" / "pr-*" → "ps-*" / "pe-*"
```

**Template Conditional Logic:**
```django
{% if BOOTSTRAP_VERSION|first == "5" %}
  <button data-bs-toggle="modal">...</button>
{% else %}
  <button data-toggle="modal">...</button>
{% endif %}
```

**NexusLIMS Files at Risk:**
- `static/css/*.css` - Custom CSS with Bootstrap classes
- `templates/**/*.html` - 13 overridden templates
- Custom JavaScript that manipulates Bootstrap components
- **⚠️ `xslt/detail_stylesheet.xsl`** - **CRITICAL: 5,492 lines with extensive Bootstrap usage**
- `xslt/list_stylesheet.xsl` - 615 lines with minimal Bootstrap usage

**XSLT Files Bootstrap Analysis:**

**detail_stylesheet.xsl (CRITICAL):**
- **~117 Bootstrap CSS classes** used (buttons, badges, grid, layout)
- **~75 Bootstrap 4 data attributes** (`data-toggle`, `data-placement`, `data-target`)
- **~199 Bootstrap JavaScript component references** (tooltips, popovers, modals, collapse)
- **Bootstrap 4-specific issues found:**

```xml
<!-- Line ~1300s: Bootstrap 4 data attributes -->
<button data-toggle="tooltip" data-placement="top">...</button>
<!-- Bootstrap 5 requires: data-bs-toggle="tooltip" data-bs-placement="top" -->

<!-- Line ~2900s: Tooltip JavaScript API calls -->
$('[data-toggle="tooltip"]').tooltip({trigger: 'hover'});
$('#btn-copy-pid').tooltip('update');
<!-- Bootstrap 5 API is similar but may have changes -->

<!-- Line ~1300s: Badge classes -->
<span class="badge list-record-badge">...</span>
<!-- May need Bootstrap 5 badge updates (e.g., badge-secondary → bg-secondary) -->

<!-- Line ~2900s: Float utilities (if any float-right/float-left) -->
class="float-right"  <!-- Bootstrap 5: class="float-end" -->
```

**Key Bootstrap Components in XSLT:**
1. **Tooltips** - Used extensively (~199 references)
   - On buttons (edit, download, copy PID, file listing)
   - On metadata table elements
   - Initialization and update calls in JavaScript
2. **Buttons** - Multiple button groups and styles
3. **Badges** - For instrument identifiers and status
4. **Grid System** - col-md-12 and other responsive classes
5. **Utility Classes** - pr-4 (padding), float-right (if present)

**list_stylesheet.xsl (LOW RISK):**
- ~16 Bootstrap class references
- Minimal JavaScript interactions
- Primarily uses basic grid and button classes

**Conflict Risk:** 🟡 **HIGH** - XSLT files have extensive Bootstrap 4 dependencies

**Critical Migration Required:**

**XSLT detail_stylesheet.xsl updates needed:**

1. **Update data attributes** (~75 instances):
   ```bash
   # In xslt/detail_stylesheet.xsl:
   sed -i 's/data-toggle="/data-bs-toggle="/g' xslt/detail_stylesheet.xsl
   sed -i 's/data-placement="/data-bs-placement="/g' xslt/detail_stylesheet.xsl
   sed -i 's/data-target="/data-bs-target="/g' xslt/detail_stylesheet.xsl
   ```

2. **Update JavaScript selectors** (~199 instances):
   ```javascript
   // OLD (Bootstrap 4):
   $('[data-toggle="tooltip"]').tooltip({trigger: 'hover'});
   
   // NEW (Bootstrap 5):
   $('[data-bs-toggle="tooltip"]').each(function() {
       new bootstrap.Tooltip(this, {trigger: 'hover'});
   });
   ```

3. **Update tooltip API calls**:
   ```javascript
   // OLD:
   $('#btn-copy-pid').tooltip('update');
   $('#btn-copy-pid').tooltip('show');
   
   // NEW:
   const tooltip = bootstrap.Tooltip.getInstance('#btn-copy-pid');
   tooltip.update();
   tooltip.show();
   ```

4. **Check for deprecated classes**:
   - `badge-*` → `bg-*` (if used)
   - `float-right` → `float-end` (found at least 1 instance)
   - `float-left` → `float-start`
   - `ml-*` / `mr-*` → `ms-*` / `me-*`
   - `pl-*` / `pr-*` → `ps-*` / `pe-*` (found pr-4)

**Testing Required:**
1. Set `BOOTSTRAP_VERSION` environment variable to "5.1.3"
2. Test all buttons with tooltips (edit, download, copy PID, file listing)
3. Verify tooltip initialization on page load
4. Test tooltip show/hide/update functionality
5. Check badge display (instrument identifiers)
6. Verify responsive grid layout
7. Test in Chrome, Firefox, Safari

**Migration Effort:**
- **XSLT updates:** 6-8 hours (detailed file, many changes)
- **Testing:** 4-6 hours (extensive Bootstrap component usage)
- **Total:** 10-14 hours for XSLT Bootstrap 5 migration

**Migration Path:**
1. Create backup: `cp xslt/detail_stylesheet.xsl xslt/detail_stylesheet.xsl.bootstrap4.backup`
2. Update data attributes with sed commands (or manually)
3. Update JavaScript tooltip initialization (lines ~2900s)
4. Update tooltip API calls (lines ~1300s, ~2600s)
5. Search and replace deprecated utility classes
6. Test thoroughly with Bootstrap 5
7. Keep backup until migration is verified

**Recommended Approach:**
- Do XSLT Bootstrap migration as a **separate, focused task**
- Test extensively before deploying
- Consider this when planning overall upgrade timeline (adds 10-14 hours)

---

#### 5. Static File Changes

**Library Removals:**
- Commit d72f086: "remove datatables.js" from core_main_app
- Commit 3c858b7: "remove FSelect.js"

**Impact on NexusLIMS:**

**Current DataTables Version:** 1.10.24 (released March 2021, now ~4 years old)

**DataTables Usage in NexusLIMS:**
- **Bundled location:** `static/libs/datatables/1.10.24/`
- **Loaded in:** `templates/core_main_app/_render/user/theme_base.html`
- **Used in XSLT:** 4 DataTable initializations in `detail_stylesheet.xsl`:
  - Line 3390: Navigation table
  - Line 3443: Metadata tables
  - Line 3472: Additional tables
  - Line 4371: File listing table (primary use case)
- **CSS styling:** ~40+ custom DataTable class selectors in XSLT CSS

**Why Upgrade DataTables:**

1. **Bootstrap 5 Compatibility** - DataTables 1.10.24 was built for Bootstrap 4
   - Latest DataTables 2.x has native Bootstrap 5 styling
   - Better integration with Bootstrap 5 components

2. **Bug Fixes & Security** - 1.10.24 is 4 years old
   - Multiple bug fixes and improvements in newer versions
   - Security patches for potential XSS vulnerabilities

3. **Performance Improvements** - Newer versions have better rendering

4. **API Changes** - Some deprecated methods removed in 2.x

**Recommended Upgrade:**

**Target Version:** DataTables **2.1.8** (latest stable as of Dec 2024, Bootstrap 5 compatible)

**Migration Steps:**

1. **Download new version:**
   ```bash
   cd static/libs/datatables/
   mkdir 2.1.8
   # Download from https://datatables.net/download/
   # Or use CDN for testing
   ```

2. **Update template reference:**
   ```html
   <!-- templates/core_main_app/_render/user/theme_base.html -->
   <!-- OLD: -->
   <link rel="stylesheet" href="{% static 'libs/datatables/1.10.24/datatables.min.css' %}">
   <script src="{% static 'libs/datatables/1.10.24/datatables.min.js' %}"></script>
   
   <!-- NEW: -->
   <link rel="stylesheet" href="{% static 'libs/datatables/2.1.8/datatables.min.css' %}">
   <script src="{% static 'libs/datatables/2.1.8/datatables.min.js' %}"></script>
   ```

3. **Check for API changes in XSLT:**
   ```javascript
   // In detail_stylesheet.xsl, verify these still work:
   var filelist_dt = $('table#filelist-table').DataTable({
       // Check configuration options for deprecations
   });
   ```

4. **Update CSS selectors if needed:**
   - DataTables 2.x may use different class names
   - Check the ~40 `.dataTable` CSS rules in XSLT
   - May need updates for Bootstrap 5 styling

5. **Test extensively:**
   - Navigation table rendering
   - Metadata tables display
   - File listing table (primary feature)
   - Sorting, filtering, pagination
   - Selection functionality
   - Custom styling preserved

**Migration Effort:**
- Library download/setup: 30 minutes
- Template updates: 15 minutes
- XSLT CSS verification: 2-3 hours
- Testing: 2-3 hours
- **Total: ~5-7 hours**

**Conflict Risk:** 🟡 **MEDIUM** - DataTables upgrade needed for Bootstrap 5 compatibility

**CSS Changes (Upstream):**
- Commit e321d5e: "replace notify.js library"
- Commit d72f086: "remove datatables.js" from core_main_app (doesn't affect NexusLIMS)
- Multiple CSS refactoring commits

**Overall CSS Conflict Risk:** 🟡 **MEDIUM** - CSS selectors may have changed, affecting custom styles

**Recommendation:**
- Upgrade DataTables to 2.1.8 as part of Bootstrap 5 migration
- Do this upgrade **together with Bootstrap 5** since they're tightly coupled
- Test file listing table thoroughly (most complex DataTable usage)
- Keep 1.10.24 as backup during migration

---

## core_explore_common_app Conflicts

### Repository Analysis

**Component:** core_explore_common_app  
**Location:** `/Users/josh/git_repos/datasophos/cdcs/core_explore_common_app`  
**Version Jump:** 1.21.* → 2.18.*

**NexusLIMS Overrides:**
- `results_override/static/core_explore_common_app/user/js/results.js` (complete override)
- `results_override/static/core_explore_common_app/user/css/results.css`
- `results_override/static/core_explore_common_app/user/css/query_result.css`
- `templates/core_explore_common_app/user/results/data_source_info.html`
- `templates/core_explore_common_app/user/results/data_source_results.html`
- `templates/core_explore_common_app/user/results/data_sources_results.html`

### Critical Changes

#### 1. results.js - Upstream Changes Since 1.21.0 (MEDIUM RISK)

**NexusLIMS Baseline:** core_explore_common_app **1.21.0** (271 lines, July 2022)  
**NexusLIMS Current:** results_override/results.js (292 lines)  
**Upstream Current:** core_explore_common_app 2.18.0 (292 lines)

---

**NexusLIMS Changes from Baseline 1.21.0:**

**Summary:** NexusLIMS made **minimal, conservative changes** (+21 lines, ~31 lines modified)

**A. Enhanced Loading UX** (+21 lines)
```javascript
// ADDED in get_data_source_results() success handler:
result_page.hide();  // Hide before updating
$("#loading-placeholder").fadeOut("normal", function() {
    $(this).hide();  // Remove "please wait" message
});
result_page.html(data.results);  // Update content while hidden
result_page.fadeIn("normal", function() {
    $(this).show();  // Fade in with results
})

// Same pattern added to error handler
```

**B. Disabled Leave Notice Warnings** (1 line commented)
```javascript
// COMMENTED OUT:
//leaveNotice($("#results_" + nb_results_id.match(/(\d+)/)[0] + " a"));
```

**C. Minor formatting** (2 whitespace changes - cosmetic)

**Total NexusLIMS modifications:** ~22 functional lines

---

**Upstream Changes Since 1.21.0 (2022-07 → 2024-10):**

**Major features added in upstream:**

1. **61fe22e** (2022-06-14): Added loading spinner
2. **28224e1** (2023-03-29): Added "Open in Text Editor" button
   ```javascript
   // NEW: Open button for editing records
   var openLinkElement = inputElement.siblings(".permissions-link-open");
   if(dataFormat == "XSD") openLinkElement.attr("href", openXMLRecordUrl + '?id=' + id);
   else if (dataFormat == "JSON") openLinkElement.attr("href", openJSONRecordUrl + '?id=' + id);
   ```

3. **d4c2d2f** (2023-10-18): Highlight data content feature
4. **ab50e5d** (2023-11-16): Format and highlight JSON content
   ```javascript
   // NEW: JSON syntax highlighting
   $('.highlight-content code').each(function(i, block) {
       if ($(".data-template-format").val() == "JSON"){
           var jsonContent = JSON.parse($(block).text());
           var highlighted = hljs.highlight('json', JSON.stringify(jsonContent, null, 8)).value;
           $(block).html(highlighted.value);
       }
   });
   ```

5. **22c33d3** (2024-02-23): Enable JSON editing
6. **5ed1ec1** (2024-10-31): Fix issues with JSON list display

---

**Conflict Analysis:**

**What NexusLIMS HAS:**
- ✅ Custom loading placeholder animations (fade in/out)
- ✅ Cleaner UX (no leave warnings)
- ✅ Based on stable 1.21.0

**What NexusLIMS LACKS (added in upstream after 1.21.0):**
- ❌ JSON syntax highlighting (commits ab50e5d, d4c2d2f)
- ❌ "Open in Text Editor" button (commit 28224e1)
- ❌ Enhanced error handling with notifications
- ❌ Bug fixes from 1.21.0 → 2.18.0

**Conflict Risk:** 🟡 **MEDIUM** (was CRITICAL, revised down)

**Why MEDIUM not CRITICAL:**
- NexusLIMS made minimal changes to baseline
- Only +22 functional lines modified
- No feature removals, only additions
- Changes are isolated (loading UX only)
- Low risk of merge conflicts

---

**Merge Strategy:**

**Option 1: Conservative (Recommended)**
- Keep NexusLIMS version as baseline
- Cherry-pick bug fixes from upstream 2.18.0
- Add JSON features only if needed
- Preserve loading placeholder animations

**Option 2: Adopt Upstream**
- Start with upstream 2.18.0
- Re-apply NexusLIMS loading UX enhancements (+22 lines)
- Re-apply leave notice disabling (1 line)
- Test thoroughly

**Migration Steps:**

1. **Identify bug fixes** in upstream 1.21.0 → 2.18.0 commits
2. **Decision point:** Does NexusLIMS need JSON support?
   - If NO: Keep current version, cherry-pick bug fixes only
   - If YES: Adopt upstream, re-apply UX enhancements
3. **Preserve NexusLIMS features:**
   - Loading placeholder fade animations
   - StreamSaver download system (if in this file)
   - Multi-signal dataset handling (if in this file)
4. **Test all functionality:**
   - Search results display
   - Loading states and animations
   - Downloads (single and multi-file)
   - Error handling

**Estimated Effort:**
- Review upstream changes: 2 hours
- Merge strategy decision: 1 hour
- Implementation: 3-4 hours
- Testing: 3-4 hours
- **Total: 9-11 hours**

**Recommendation:** Use **Option 1 (Conservative)** unless JSON support is specifically needed. NexusLIMS changes are minimal and isolated, making this a low-risk upgrade path.

---

#### 2. data_source_info.html Template (HIGH RISK)

**Commits:**
- **f2e55e0** (2023-08-28): JSON Schema support
- **8703d16** (2023-07-24): Bootstrap 5.x support
- **22c33d3** (2024-02-23): Removed disabled attribute for JSON editing
- **5ed1ec1** (2024-10-31): JSON list display fixes

**Current Upstream Template Structure:**
```django
{% load result_to_html %}  {# NEW template tag #}

<div class="result-line-main-container" name="result">
  <div class="result-line-title-container">
    <div class="data-info-left-container">
      <!-- Checkboxes, expand button, title -->
      
      {# CRITICAL: Hidden field for JavaScript #}
      <input class="data-template-format" type="hidden" 
             value="{{result.template_info.format}}">
      
      {# Bootstrap version conditional #}
      {% if BOOTSTRAP_VERSION|first == "5" %}
        <button data-bs-toggle="collapse">...</button>
      {% else %}
        <button data-toggle="collapse">...</button>
      {% endif %}
      
      {# Edit button only for XSD #}
      {% if result.template_info.format == 'XSD' %}
        <button class="edit-result">Edit</button>
      {% endif %}
    </div>
  </div>
  
  {# Conditional rendering by format #}
  <div class="content-result highlight-content">
    {% if result.template_info.format == 'XSD' %}
      {{ html_string }}  {# Pre-rendered HTML #}
    {% else %}
      <pre><code>{{html_string}}</code></pre>  {# JSON/other #}
    {% endif %}
  </div>
</div>
```

**NexusLIMS Override:** Verified actual structure (based on 1.21.0, with modifications)

**Current NexusLIMS Template (36 lines):**
```django
{% load json_date %}
{% load render_extras %}  {# NexusLIMS custom tag #}

<div class="result-line-main-container" name="result">
    <div class="result-line-title-container">
        <div class="data-info-left-container">
            <input data-template-id="{{result.template_info.id}}" ... />
            
            {# NexusLIMS: xmlResult div MOVED inside container #}
            <div class='xmlResult' readonly='true'>
                {{ xml_representation }}
            </div>
            
            {# NexusLIMS: Commented out expand/title/template info #}
            {% comment %}
            <span class="expand" onclick="showhideResult(event);"></span>
            <span class="result-title">...</span>
            <span class="template-info-name">...</span>
            {% endcomment %}
            
            {# Edit button (same as upstream 1.21.0) #}
            {% if result.permission_url and display_edit_button %}
                <input class="input-permission-url" type="hidden" ...>
                <a class="permissions-link" href="#"><i class="fa fa-pencil-alt ..."></i></a>
            {% endif %}
        </div>
    </div>
</div>
```

**NexusLIMS Changes from 1.21.0:**
1. ✅ Added `{% load render_extras %}` (custom template tag)
2. ✅ **Moved** `.xmlResult` div inside `.data-info-left-container` (structural change)
3. ❌ **Commented out** expand button, result title, template info (hidden from display)
4. ✅ Uses `{{ xml_representation }}` variable (consistent with 1.21.0)

**What NexusLIMS HAS:**
- ✅ `.xmlResult` class (from 1.21.0)
- ✅ Edit button with permissions check
- ✅ Data template ID/hash in checkbox
- ✅ Last modification date

**What NexusLIMS LACKS (added in upstream 2.18.0):**
- ❌ `data-template-format` hidden field → JavaScript will error
- ❌ `.content-result .highlight-content` classes → CSS won't apply
- ❌ Format conditional rendering (XSD vs JSON)
- ❌ "Open in text editor" button
- ❌ Bootstrap version conditional attributes
- ❌ Blob/file badge
- ❌ Timezone-aware date formatting

**Conflict Risk:** 🟡 **MEDIUM** (revised from HIGH)

**Why MEDIUM:**
- NexusLIMS made structural change (moved div) but kept same classes
- Only commented out elements, didn't delete
- Based on stable 1.21.0
- Missing features are mostly new additions, not breaking changes

**Critical Issue:**
The JavaScript in results.js expects `.content-result .highlight-content` but NexusLIMS template has `.xmlResult`. However, since NexusLIMS also uses its own results.js, this is internally consistent.

**Action Required for Upgrade:**

**If adopting upstream 2.18.0 template:**
1. Add `{% load render_extras %}` (preserve NexusLIMS tag)
2. Decide: Keep expand/title hidden or show them?
3. Add `<input class="data-template-format" type="hidden" value="XSD">` (NexusLIMS only uses XML)
4. Update CSS classes: `.xmlResult` → `.content-result .highlight-content`
5. Add Bootstrap version conditionals if using Bootstrap 5
6. Keep structural layout from NexusLIMS (div inside container)

**If keeping NexusLIMS template:**
1. Ensure results.js stays compatible with `.xmlResult` class
2. No template changes needed
3. JSON support not available (acceptable if only using XML)

**Recommended Approach:**
Keep NexusLIMS template if results.js stays NexusLIMS version. They're designed to work together.

---

#### 3. results.css & query_result.css (MEDIUM RISK)

**Changes:**

**Commit d4c2d2f** (2023-10-18): Added `.highlight-content` styles
```css
.highlight-content {
    max-height: 160px !important;
    overflow: auto;
    font-size: 18px;
}

.content-result {
    width: 100%;
    overflow: auto;
}
```

**Commit 28224e1** (2023-03-29): Open button styles
```css
.permissions-link,
.permissions-link-open {
    float: right;
    display: none;  /* Shown by JavaScript */
}
```

**NexusLIMS Overrides:**
- `results_override/static/.../results.css` (+179 lines)
- `results_override/static/.../query_result.css` (+7 lines)

**Conflict Risk:** 🟡 **MEDIUM**

**Action Required:**
1. Compare NexusLIMS overrides with upstream versions
2. Add new `.highlight-content` and `.content-result` styles if missing
3. Verify scrollable areas work correctly
4. Test result display height limits

---

#### 4. JSON Schema Support Architecture (HIGH RISK)

**Commit:** f2e55e0 (2023-08-28)

**Backend Changes:**
- **Result model:** Field renamed from `xml_content` to generic `content`
- **Template info:** Added `format` field (values: 'XSD' or 'JSON')
- **Query model:** Added `symmetrical=False` to template relationships

**Frontend Impact:**
- Templates conditionally render based on `result.template_info.format`
- JSON wrapped in `<pre><code>` tags for syntax highlighting
- XSD rendered as HTML via template tag

**NexusLIMS Impact:** 🔴 **HIGH**

**NexusLIMS Current Usage - VERIFIED:**

1. **Template Format:** NexusLIMS uses **XSD (XML) only** - no JSON schema support
2. **Attribute Usage:** NexusLIMS templates use `xml_content` attribute:
   - `templates/core_main_app/common/data/detail_data.html:6` → `data.data.xml_content`
   - `templates/core_explore_common_app/user/results/data_source_results.html:5` → `result.xml_content`

**Compatibility Status:**

✅ **Good News:** The `xml_content` attribute still exists in MDCS 2.18.0 as a **backward compatibility alias**.

The Data model has:
- `content` property (primary, reads from file)
- `xml_content` property (alias for backward compatibility)

Both attributes work identically - `xml_content` is not deprecated and won't break during upgrade.

**Action Required:**

✅ **No code changes needed** - `xml_content` is still supported
- NexusLIMS templates will work as-is with MDCS 3.18.0
- Both `result.xml_content` and `result.content` are valid
- Optionally update to `content` for consistency, but not required

**Testing Required:**
1. ✅ Verify `xml_content` attribute still works in MDCS 3.18.0
2. ✅ Test detail view rendering
3. ✅ Test results list rendering
4. ✅ Confirm XML records display correctly

---

## core_explore_keyword_app Conflicts

### Repository Analysis

**Component:** core_explore_keyword_app  
**Location:** `/Users/josh/git_repos/datasophos/cdcs/core_explore_keyword_app`  
**Version Jump:** 1.21.* → 2.18.*

**NexusLIMS Overrides:**
- `templates/core_explore_keyword_app/user/index.html`

### Changes

**Commit:** 87f41f0 (2023-07-11) - Added padding

**Template Changes:**
```django
<div class="d-inline-flex col-sm-12 extra-padding">
  <div class="col-sm-3 extra-padding">
    <!-- Data sources and template filter -->
  </div>
  <div class="col-sm-9 extra-padding">
    <!-- Results display -->
    {% include "core_explore_common_app/user/results/results.html" %}
  </div>
</div>
```

**CSS Added:**
```css
.extra-padding {
    padding: 10px;
}
```

**Conflict Risk:** 🟢 **LOW**

**Impact:** Minimal - just CSS spacing changes. NexusLIMS override should merge easily.

**Action Required:**
1. Add `.extra-padding` class to elements in override template
2. Test keyword search page layout

---

## Upgrade Risk Matrix

### By Component

| Component | Risk Level | Complexity | Breaking Changes | Estimated Effort |
|-----------|------------|------------|------------------|------------------|
| **MDCS Core** | 🔴 CRITICAL | Very High | Yes - Django 5, dependencies | 40 hours |
| **core_main_app** | 🔴 CRITICAL | Very High | Yes - allauth, Bootstrap 5 | 32 hours |
| **core_explore_common_app** | 🔴 CRITICAL | High | Yes - JSON support, selectors | 24 hours |
| **core_explore_keyword_app** | 🟢 LOW | Low | No | 2 hours |
| **Python/Django** | 🔴 CRITICAL | Medium | Yes - 2.2 → 5.2 | 16 hours |
| **Templates** | 🟡 HIGH | High | Yes - Bootstrap 5, allauth | 20 hours |
| **Static Files** | 🟡 MEDIUM | Medium | Moderate - CSS classes | 12 hours |
| **Testing** | 🔴 CRITICAL | Very High | N/A | 40 hours |

**Total Estimated Effort:** ~186 hours (4-5 weeks for 1 developer)

### By Risk Area

| Risk Area | Files Affected | Testing Priority | Migration Strategy |
|-----------|----------------|------------------|---------------------|
| **XSLT Parameter System** | xml.py, xsl_transform_tag.py, 2 XSLT files | 🔴 CRITICAL | Preserve override, verify imports |
| **App Loading Order** | settings.py | 🔴 CRITICAL | Enforce order, add validation |
| **results.js Override** | results.js, 3 templates, 2 CSS files | 🔴 CRITICAL | Line-by-line merge |
| **Authentication** | Login templates, URLs, settings | 🟡 HIGH | Test flows, merge templates |
| **Bootstrap 5** | 40+ templates, all CSS | 🟡 HIGH | Update classes, test UI |
| **JSON Support** | Templates, results.js, models | 🟡 HIGH | Add conditionals, test formats |
| **Admin URLs** | Templates, JavaScript | 🟡 MEDIUM | Update hardcoded paths |
| **Dependencies** | requirements.txt | 🔴 CRITICAL | Update all core_* to 2.18.* |

---

## Recommended Upgrade Strategy

### Phase 1: Preparation & Assessment (Week 1)

#### 1.1. Environment Setup
```bash
# Create new Python 3.12 environment
python3.12 -m venv venv-mdcs-3.18
source venv-mdcs-3.18/bin/activate

# Clone MDCS 3.18.0
git clone https://github.com/usnistgov/mdcs.git mdcs-3.18
cd mdcs-3.18
git checkout 3.18.0
```

#### 1.2. Dependency Analysis
```bash
# Compare requirements
diff /path/to/NexusLIMS-CDCS/requirements.core.txt mdcs-3.18/requirements.core.txt > deps.diff

# Identify version conflicts
grep "core_" deps.diff
```

#### 1.3. Create Backup Branch
```bash
cd /path/to/NexusLIMS-CDCS
git checkout -b upgrade-3.18.0-attempt2
git branch backup-pre-upgrade  # Safety backup
```

#### 1.4. Audit Recent Merge
```bash
# Review commit cf1dc6d - check if it has errors
git show cf1dc6d:requirements.core.txt | grep "core_main_app"
# If shows 1.21.*, the merge was incorrect
```

---

### Phase 2: Core Dependencies (Week 1-2)

#### 2.1. Update requirements.core.txt
```bash
# Apply all version updates:
sed -i 's/==1.21./==2.18./g' requirements.core.txt

# Add new extras:
sed -i 's/core_main_app==2.18.0/core_main_app[mongodb,auth]==2.18.0/' requirements.core.txt

# Remove obsolete packages:
# - rest_framework_mongoengine
# - tz_detect (if present)
```

#### 2.2. Install and Test
```bash
pip install -r requirements.core.txt
pip install -r requirements.txt

# Check for conflicts
pip check
```

---

### Phase 3: Configuration Files (Week 2)

#### 3.1. Merge settings.py (CRITICAL)

**Strategy:** Three-way merge
```bash
# Get baseline (MDCS 2.21.0)
git show 2.21.0:mdcs/settings.py > settings-2.21.py

# Get upstream target (MDCS 3.18.0)
cp /path/to/mdcs-3.18/mdcs/settings.py settings-3.18.py

# Get NexusLIMS current
cp mdcs/settings.py settings-nexus.py

# Use merge tool
meld settings-2.21.py settings-3.18.py settings-nexus.py
```

**Critical Checklist:**
- [ ] Update all `core_*_app` versions to 2.18.*
- [ ] Remove OAI-PMH apps from INSTALLED_APPS
- [ ] Add `rest_framework.authtoken`, `drf_spectacular`, `fontawesomefree`
- [ ] **PRESERVE** app order: `core_main_app` → `mdcs_home` → `results_override`
- [ ] **PRESERVE** context processor: `mdcs_home.context_processors.doc_link`
- [ ] Add new settings:
  ```python
  ENABLE_ALLAUTH = os.getenv("ENABLE_ALLAUTH", "False").lower() == "true"
  BOOTSTRAP_VERSION = os.getenv("BOOTSTRAP_VERSION", "5.1.3")
  ADMIN_URLS_PREFIX = os.getenv("ADMIN_URLS_PREFIX", "staff-")
  ```
- [ ] Update REST_FRAMEWORK authentication classes
- [ ] Update DEFAULT_AUTO_FIELD to BigAutoField
- [ ] Update middleware (remove tz_detect, add core_main_app.middleware.timezone)

#### 3.2. Merge urls.py
```bash
# Similar three-way merge
# Remove OAI-PMH routes
# Update admin URL with prefix
# Preserve custom routes
```

**Checklist:**
- [ ] Update admin URL pattern: `rf"^{ADMIN_URLS_PREFIX}admin/"`
- [ ] Add core-admin URL: `rf"^{ADMIN_URLS_PREFIX}core-admin/", core_admin_site.urls`
- [ ] Remove OAI-PMH routes (or preserve if needed)
- [ ] Preserve NexusLIMS custom routes

#### 3.3. Update core_settings.py
```bash
# Preserve NexusLIMS customization
CUSTOM_TITLE = "Welcome to NexusLIMS!"

# Add new settings from upstream
```

---

### Phase 4: XSLT Parameter System Preservation (Week 2)

#### 4.1. Verify Override Files

**Files to verify:**
1. `mdcs_home/utils/xml.py` - Check still has `**kwargs` support
2. `mdcs_home/templatetags/xsl_transform_tag.py` - Check import path
3. `xslt/detail_stylesheet.xsl` - Check parameter declarations
4. `xslt/list_stylesheet.xsl` - Check parameter declarations

**Verification:**
```python
# Test import resolution
python manage.py shell
>>> from mdcs_home.utils.xml import xsl_transform
>>> import inspect
>>> print(inspect.signature(xsl_transform))
# Should show: (xml_string, xslt_string, **kwargs)
```

#### 4.2. Test App Loading Order
```python
# In Django shell
from django.conf import settings
apps = [app for app in settings.INSTALLED_APPS if 'core_main_app' in app or 'mdcs_home' in app]
print(apps)
# Should show: ['core_main_app', 'mdcs_home', ...]
```

#### 4.3. Test Template Tag Resolution
```python
from django import template
register = template.Library()
# Try to load xsl_transform_detail tag
# Should resolve from mdcs_home, not core_main_app
```

---

### Phase 5: Template Migrations (Week 2-3)

#### 5.1. Bootstrap 5 Updates

**Strategy:** Update all custom CSS and templates

**Files to update:**
- `static/css/*.css` - All custom CSS
- `templates/**/*.html` - 13 overridden templates
- `static/js/*.js` - Check for Bootstrap JS calls

**Class Mapping:**
```bash
# Use sed for bulk replacements
find templates/ static/ -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" \) -exec sed -i.bak '
  s/badge-secondary/bg-secondary/g
  s/float-right/float-end/g
  s/float-left/float-start/g
  s/ml-/ms-/g
  s/mr-/me-/g
  s/pl-/ps-/g
  s/pr-/pe-/g
  s/data-toggle=/data-bs-toggle=/g
  s/data-target=/data-bs-target=/g
' {} \;
```

**Manual Review Required:**
- Modal JavaScript calls
- Dropdown initialization
- Tooltip/popover initialization

#### 5.2. Authentication Templates

**If using django-allauth:**
```bash
# Copy allauth templates to customize
cp -r /path/to/mdcs-3.18/templates/account/ templates/
# Merge with NexusLIMS branding
```

**Test:**
- Login page
- Logout
- Password reset
- Registration (if enabled)

---

### Phase 6: results.js Override Merge (Week 3)

**This is the most complex merge.**

#### 6.1. Compare Complete Files
```bash
# Get upstream version
cp /path/to/cdcs/core_explore_common_app/static/core_explore_common_app/user/js/results.js results-upstream.js

# Get NexusLIMS version
cp results_override/static/core_explore_common_app/user/js/results.js results-nexus.js

# Use diff tool
diff -u results-upstream.js results-nexus.js > results.diff
```

#### 6.2. Merge Strategy

**Sections to merge:**

1. **Initialization** (lines 1-50)
   - Preserve both upstream and NexusLIMS initialization

2. **get_data_source_results()** (lines 73-90)
   - **ADD** JSON formatting from upstream
   - **PRESERVE** NexusLIMS download system setup
   - **UPDATE** CSS selectors: `.xmlResult` → `.content-result .highlight-content`

3. **Event Handlers** (lines 100-200)
   - **ADD** data format routing logic
   - **PRESERVE** download button handlers
   - **PRESERVE** multi-signal dataset logic

4. **Download System** (lines 200+)
   - **PRESERVE** all NexusLIMS StreamSaver code
   - **PRESERVE** duplicate filename handling
   - **PRESERVE** multi-file zip creation

#### 6.3. Testing Checklist
```
□ Search results display correctly
□ Expand/collapse result works
□ JSON results render with syntax highlighting (if applicable)
□ XML results render as before
□ Single file download works
□ Multi-file download creates zip
□ Multi-signal datasets handle duplicate filenames
□ "Please wait" message shows during operations
□ No JavaScript console errors
```

---

### Phase 7: Database Migrations (Week 3)

#### 7.1. Backup Database
```bash
# PostgreSQL
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB > backup-pre-upgrade.sql

# MongoDB
mongodump --host $MONGO_HOST --port $MONGO_PORT --db $MONGO_DB --out backup-mongo/
```

#### 7.2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate

# Watch for BigAutoField warnings
# May require custom migration for primary key changes
```

#### 7.3. Test Data Integrity
```bash
# Check record counts
python manage.py shell
>>> from core_main_app.components.data.models import Data
>>> Data.objects.count()

# Verify MongoDB connectivity
>>> from core_main_app.utils.databases.pymongo_database import get_full_text_query
```

---

### Phase 8: Static Files & Assets (Week 3-4)

#### 8.1. Collect Static Files
```bash
python manage.py collectstatic --noinput

# Verify NexusLIMS overrides take precedence
# Check that results.js is from results_override, not core_explore_common_app
```

#### 8.2. CSS Testing
```
□ Homepage displays correctly
□ Menu styles correct
□ Buttons have NexusLIMS colors
□ Record detail page styling correct
□ Image gallery spacing correct
□ Results table styling correct
```

---

### Phase 9: Comprehensive Testing (Week 4)

#### 9.1. Functional Testing

**Authentication:**
```
□ Login works
□ Logout works
□ Password reset works
□ User registration (if enabled)
□ SAML/Handle PID (if used)
```

**Search & Explore:**
```
□ Keyword search works
□ Results display in registry-like view
□ DataTables sorting/filtering works
□ Pagination works
□ Expand/collapse results
```

**Record Detail View:**
```
□ Record title displays (xmlName parameter)
□ Metadata tables show units
□ Instrument badges show colors
□ Sample information displays correctly
□ Preview image gallery displays
□ Gallery spacing correct
□ File listings correct
```

**Download System:**
```
□ Single file download works
□ "Download All" creates zip
□ Multi-signal datasets handle duplicates
□ Download works in Chrome
□ Download works in Firefox
□ Download works in Safari
```

**Admin:**
```
□ Admin panel accessible at /staff-admin/ (or configured prefix)
□ Core admin accessible
□ Defender working (if enabled)
```

#### 9.2. Performance Testing
```
□ Record with <10 datasets loads quickly
□ Record with >100 datasets uses simple display
□ Large file downloads don't crash browser
□ Search results load in reasonable time
```

#### 9.3. Browser Compatibility
```
□ Chrome latest
□ Firefox latest
□ Safari latest (if available)
□ Edge latest
```

---

### Phase 10: Deployment & Rollback Plan (Week 4-5)

#### 10.1. Staging Deployment
```bash
# Deploy to staging environment
# Run full test suite
# Get user feedback
```

#### 10.2. Rollback Plan
```bash
# If issues found, rollback:
git checkout backup-pre-upgrade
git reset --hard

# Restore database
psql -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB < backup-pre-upgrade.sql
mongorestore --host $MONGO_HOST --port $MONGO_PORT backup-mongo/
```

#### 10.3. Production Deployment
```bash
# Schedule maintenance window
# Backup production database
# Deploy upgrade
# Verify functionality
# Monitor logs
```

---

## Testing Requirements

### Unit Tests

**Python Code:**
```bash
# Test custom utilities
python -m pytest tests/unit/test_xml_utils.py
python -m pytest tests/unit/test_template_tags.py
```

**JavaScript:**
```bash
# If you have JS tests
npm test
```

### Integration Tests

**XSLT Parameter System:**
```python
# Test in Django shell
from django.template import Template, Context
from core_main_app.components.data.models import Data

# Get a test record
data = Data.objects.first()

# Render with parameters
template = Template("""
{% load xsl_transform_tag %}
{% xsl_transform_detail 
   xml_content=xml 
   template_id=template_id 
   xmlName=title 
   datasetBaseUrl=base_url 
%}
""")

context = Context({
    'xml': data.content,
    'template_id': data.template.id,
    'title': data.title,
    'base_url': 'https://example.com/data',
})

html = template.render(context)

# Verify title appears in HTML
assert data.title in html
assert 'https://example.com/data' in html
```

**App Loading Order:**
```python
# Verify in Django shell
from django.conf import settings

apps_list = list(settings.INSTALLED_APPS)
core_main_idx = apps_list.index('core_main_app')
mdcs_home_idx = apps_list.index('mdcs_home')

assert core_main_idx < mdcs_home_idx, "core_main_app must load before mdcs_home"
```

**results.js Override:**
```python
# Check static file resolution
from django.contrib.staticfiles import finders

results_js = finders.find('core_explore_common_app/user/js/results.js')

# Should resolve to results_override app
assert 'results_override' in results_js
```

### End-to-End Tests

**Selenium Test Example:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_record_detail_display():
    driver = webdriver.Chrome()
    driver.get('http://localhost:8000/data/detail/1/')
    
    # Check title displays
    title = driver.find_element(By.TAG_NAME, 'h1')
    assert title.text != ""
    
    # Check download button exists
    download_btn = driver.find_element(By.CLASS_NAME, 'download-all-files')
    assert download_btn.is_displayed()
    
    # Check image gallery
    gallery = driver.find_element(By.CLASS_NAME, 'preview-gallery')
    assert gallery.is_displayed()
    
    driver.quit()
```

---

## Appendices

### Appendix A: File Change Summary

**MDCS Core (48 files changed):**
- settings.py
- urls.py
- core_settings.py
- requirements.core.txt
- requirements.txt
- 40+ static/template files

**core_main_app:**
- utils/xml.py
- settings.py
- utils/urls.py
- templatetags/
- 30 new auth templates
- 40+ Bootstrap 5 template updates

**core_explore_common_app:**
- static/.../results.js (major rewrite)
- static/.../results.css (new styles)
- templates/.../data_source_info.html (format conditionals)
- templates/.../data_source_results.html (template tag)

**core_explore_keyword_app:**
- templates/.../index.html (padding)

### Appendix B: Environment Variables Reference

**New in v3.18.0:**
```bash
# Feature flags
ENABLE_ALLAUTH=False              # Enable django-allauth
ENABLE_SAML2_SSO_AUTH=False       # Enable SAML authentication
ENABLE_HANDLE_PID=False           # Enable Handle PID support

# UI Configuration
BOOTSTRAP_VERSION=5.1.3           # Bootstrap version
TEXT_EDITOR_LIBRARY=Monaco        # Text editor choice

# Admin Configuration
ADMIN_URLS_PREFIX=staff-          # Admin URL prefix

# Timezone
TZ=UTC                            # Timezone (was hard-coded)

# MongoDB
MONGODB_INDEXING=False            # Enable MongoDB indexing
MONGODB_ASYNC=True                # Async MongoDB operations
```

**Preserve from NexusLIMS:**
```bash
# NexusLIMS-specific (from settings.py)
DOCUMENTATION_LINK=http://CHANGE.THIS.VALUE
CAN_ANONYMOUS_ACCESS_PUBLIC_DOCUMENT=True
VERIFY_DATA_ACCESS=False
```

### Appendix C: Conflict Resolution Decision Tree

```
Question 1: Does the file exist in both MDCS 3.18 and NexusLIMS?
├─ YES → Question 2
└─ NO → Is it a new MDCS file or NexusLIMS-only?
   ├─ New MDCS → Copy to NexusLIMS
   └─ NexusLIMS-only → Keep as-is

Question 2: Is this a configuration file (settings, urls, requirements)?
├─ YES → Question 3
└─ NO → Question 4

Question 3: Is the NexusLIMS change critical (XSLT override, app order)?
├─ YES → Merge carefully, preserve NexusLIMS functionality
└─ NO → Adopt MDCS changes, verify compatibility

Question 4: Is this a template or static file?
├─ Template → Check if it overrides core app template
│  ├─ YES → Three-way merge (2.21.0, 3.18.0, NexusLIMS)
│  └─ NO → Adopt MDCS version
└─ Static → Check if it's a library or custom
   ├─ Library → Adopt MDCS version
   └─ Custom → Keep NexusLIMS version
```

### Appendix D: Rollback Checklist

If upgrade fails:

```
□ Stop application server
□ Checkout backup branch: git checkout backup-pre-upgrade
□ Restore database:
  □ PostgreSQL: psql < backup-pre-upgrade.sql
  □ MongoDB: mongorestore backup-mongo/
□ Clear Python cache: find . -name "*.pyc" -delete
□ Reinstall old dependencies: pip install -r requirements.txt
□ Collect static files: python manage.py collectstatic
□ Start application server
□ Verify functionality
□ Document what failed for next attempt
```

### Appendix E: Communication Plan

**Before Upgrade:**
```
□ Notify users of planned maintenance window
□ Provide estimated downtime (recommend 4-8 hours)
□ Explain new features (if any user-visible)
□ Provide rollback communication plan
```

**During Upgrade:**
```
□ Post status updates every 30-60 minutes
□ Communicate any delays immediately
□ Keep stakeholders informed of progress
```

**After Upgrade:**
```
□ Confirm system is operational
□ Notify users upgrade is complete
□ Provide link to new features documentation
□ Monitor for bug reports
□ Schedule post-upgrade review meeting
```

---

## Document Maintenance

**Last Updated:** 2025-12-30  
**Analysis Based On:**
- MDCS repository: commits between 2.21.0 and 3.18.0
- core_main_app repository: commits since July 2022
- core_explore_common_app repository: commits since July 2022
- core_explore_keyword_app repository: commits since July 2022

**Next Review:** After attempting upgrade, update this document with:
- Actual conflicts encountered
- Resolution strategies used
- Estimated vs. actual effort
- Lessons learned

---

*End of Document*
