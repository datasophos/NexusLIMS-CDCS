# Plan: Upgrade NexusLIMS-CDCS to MDCS 3.20.0

> Note: Per CLAUDE.md, this plan should be saved to the project's `.claude/plans/` folder after plan mode exits.

## Context

The upstream NIST MDCS project released version 3.20.0 (March 5, 2026). This project (NexusLIMS-CDCS) is currently at MDCS 3.18.0 using CDCS core packages pinned to `2.18.*` and Django 4.2. The target state is:

- **MDCS application version**: 3.18.0 → 3.20.0
- **CDCS core packages**: `2.18.*` → `2.20.*` (21 packages)
- **Django**: 4.2 LTS → 5.2 LTS (introduced in MDCS 3.19.0)

The Django 4.2 → 5.2 jump is the highest-risk change and requires careful compatibility review of our custom code.

**Version scheme note**: The MDCS application version (e.g. 3.20.0) is separate from the CDCS core package versions (e.g. 2.20.*). Each MDCS release pins a corresponding set of core package versions -- check the upstream `requirements.txt` at the target tag to find the correct core package pin.

---

## Scope of Changes

### 1. `pyproject.toml`

- Update `version` from `"3.18.0"` to `"3.20.0"`
- Update all 21 core packages from `2.18.*` to `2.20.*`:
  ```toml
  # CDCS/MDCS core packages - all pinned to 2.20.* for compatibility
  core = [
      "core_main_app[auth]==2.20.*",
      "core_composer_app==2.20.*",
      "core_curate_app==2.20.*",
      "core_dashboard_common_app==2.20.*",
      "core_dashboard_app==2.20.*",
      "core_explore_example_app==2.20.*",
      "core_explore_keyword_app==2.20.*",
      "core_explore_federated_search_app==2.20.*",
      "core_exporters_app==2.20.*",
      "core_federated_search_app==2.20.*",
      "core_website_app==2.20.*",
      "core_module_blob_host_app==2.20.*",
      "core_module_remote_blob_host_app==2.20.*",
      "core_module_advanced_blob_host_app==2.20.*",
      "core_module_excel_uploader_app==2.20.*",
      "core_module_periodic_table_app==2.20.*",
      "core_module_chemical_composition_app==2.20.*",
      "core_module_chemical_composition_simple_app==2.20.*",
      "core_module_text_area_app==2.20.*",
      "core_file_preview_app==2.20.*",
      "core_linked_records_app==2.20.*",
  ]
  ```

### 2. `mdcs/core_settings.py`

- Update `PROJECT_VERSION` default: `"3.18.0"` → `"3.20.0"`
- Rename `PID_XPATH` → `PID_PATH` with backward-compat env var fallback:
  ```python
  PID_PATH = os.getenv("PID_PATH", os.getenv("PID_XPATH", "root.pid"))
  ```
- Add two new workspace/data visibility settings (upstream 3.20.0 defaults):
  ```python
  CAN_SET_PUBLIC_DATA_TO_PRIVATE = True
  CAN_SET_WORKSPACE_PUBLIC = True
  ```

### 3. `mdcs/settings.py`

- Update docstring Django version references from `4.2` to `5.2`
- Update database engine string (deprecated in Django 4.0, potentially removed in 5.x):
  ```python
  # Old (deprecated):
  "ENGINE": "django.db.backends.postgresql_psycopg2",
  # New:
  "ENGINE": "django.db.backends.postgresql",
  ```

### 4. Dependency lockfile regeneration

After updating `pyproject.toml`, regenerate `uv.lock`:
```bash
uv lock --upgrade
```
Commit both `pyproject.toml` and `uv.lock`.

### 5. Docker rebuild and database migrations

After committing dependency changes:
```bash
cd deployment
source dev-commands.sh
dev-build-clean  # Rebuild Docker image with new dependencies
dev-up           # Start services - Django will apply migrations automatically
```

---

## Files to Modify

| File | Change |
|------|--------|
| `pyproject.toml` | Version bump + 21 package version pins |
| `mdcs/core_settings.py` | PID_PATH rename, new settings, version default |
| `mdcs/settings.py` | Docstring + DB engine string |
| `uv.lock` | Regenerated (not manually edited) |

## Files That Stay Unchanged

- `mdcs/urls.py` - federated search stays disabled (intentional NexusLIMS divergence)
- `nexuslims_overrides/` - all custom overrides remain as-is
- `nexuslims_annotate/` - custom annotation app
- `config/settings/` - deployment-specific configs
- `deployment/` - Docker and scripts

---

## Risk Areas

1. **Django version jumps**: The upstream core packages (2.20.*) handle Django 5.2 compatibility themselves, but our custom code in `nexuslims_overrides/` and `nexuslims_annotate/` needs review. Specifically:
   - `nexuslims_overrides/templates/core_main_app/user/data/detail.html` - review template for deprecated tags
   - `nexuslims_overrides/context_processors.py` - likely unaffected (simple dict returns)
   - `nexuslims_annotate/` - check views, models, forms for Django deprecations

2. **Database migrations**: The core package upgrades will include new migrations. These run automatically on `dev-up` but should be verified there are no conflicts.

3. **`postgresql_psycopg2` backend alias**: Django 5.x may have fully removed this alias. Safe to update to `postgresql` which has been the canonical name since Django 4.0.

---

## Verification Steps

1. Run `dev-build-clean && dev-up` and confirm all services start without errors
2. Check Django startup logs for deprecation warnings
3. Log into the admin UI and verify data records display correctly via XSLT
4. Run `dev-update-xslt` to confirm XSLT stylesheets still work
5. Verify the NexusLIMS schema upload works via the init script
6. Test record creation/editing via the curator interface
7. Confirm annotation functionality in `nexuslims_annotate` still works
8. Check API endpoints (Swagger UI at `/api/docs/`) are accessible

---

## Commit Strategy

1. Single commit for all `pyproject.toml` + `mdcs/core_settings.py` + `mdcs/settings.py` changes
2. Second commit for the regenerated `uv.lock`
3. Use `datasophos:pr` skill to create the PR referencing issue #13

---

## Future MDCS Version Upgrade Guide

When the upstream NIST MDCS project releases a new version, follow this process:

### Step 1: Research the release

1. Check the release notes at `https://github.com/usnistgov/MDCS/releases/tag/<version>`
2. Read the upstream `requirements.txt` to find the new core package pin version:
   ```
   https://raw.githubusercontent.com/usnistgov/MDCS/<version>/requirements.txt
   ```
3. Compare the upstream `mdcs/settings.py` and `mdcs/core_settings.py` against our local versions to identify new/changed/removed settings:
   ```
   https://raw.githubusercontent.com/usnistgov/MDCS/<version>/mdcs/settings.py
   https://raw.githubusercontent.com/usnistgov/MDCS/<version>/mdcs/core_settings.py
   ```
4. Note any Django version bumps -- these require additional review of custom code

### Step 2: Update `pyproject.toml`

- Bump the project `version` to match the new MDCS version
- Update all core package pins to the new version (e.g. `2.20.*` → `2.21.*`)
- Update the comment on the `core` optional-dependency group

### Step 3: Update `mdcs/core_settings.py`

- Change the `PROJECT_VERSION` default value
- Apply any new/renamed settings found in the upstream diff
- Keep NexusLIMS-specific settings (MongoDB disabled, GridFS disabled, etc.)

### Step 4: Update `mdcs/settings.py` (if needed)

- Update docstring Django version references if Django version changed
- Apply any structural changes from the upstream diff
- Keep NexusLIMS customizations intact:
  - Federated search apps remain disabled
  - NexusLIMS context processors remain
  - `SPECTACULAR_SETTINGS` description and `AllowAny` permission stay

### Step 5: Regenerate the lockfile

```bash
uv lock --upgrade
git add pyproject.toml uv.lock
```

### Step 6: Test in development

```bash
cd deployment
source dev-commands.sh
dev-build-clean
dev-up
```

Check:
- Django starts without errors or deprecation warnings
- All pages render correctly
- XSLT still works (`dev-update-xslt`)
- Annotation app works
- API docs accessible

### Step 7: Commit and PR

Commit with a message like:
```
chore: upgrade base CDCS to MDCS X.Y.Z (core packages A.B.*)
```

Reference the relevant GitHub issue. Use the `datasophos:pr` skill to create the PR.

### Version Mapping Reference

| MDCS App Version | Core Package Version | Django Version |
|-----------------|---------------------|----------------|
| 3.18.0          | 2.18.*              | 4.2 LTS        |
| 3.19.0          | 2.19.*              | 5.2 LTS        |
| 3.20.0          | 2.20.*              | 5.2 LTS        |

### What to Watch For

- **New settings in `core_settings.py`**: The upstream adds settings in each release; missing ones usually get sensible defaults but may expose unintended behavior
- **Renamed settings**: Check release notes for deprecation notices (e.g. `PID_XPATH` → `PID_PATH`)
- **New INSTALLED_APPS**: Upstream may add new optional apps; evaluate whether NexusLIMS needs them
- **Django deprecation warnings**: Run `dev-up` and watch logs; Django warns about deprecated APIs one version before removing them
- **Template compatibility**: Our overridden templates (`nexuslims_overrides/templates/`) may use tags/filters removed in newer Django versions
- **Custom app compatibility**: `nexuslims_annotate/` views, models, and forms should be reviewed against Django release notes when Django version changes
