# NexusLIMS-CDCS Upgrade Plan: v2.21.0 → v3.18.0

**Status**: 🟡 In Progress  
**Start Date**: 2025-12-30  
**Target Completion**: TBD  
**Upgrade Lead**: Claude  
**Last Updated**: 2025-12-30

## Related planning documents

CHANGES_FROM_MDCS_2.21.0.md and POTENTIAL_UPGRADE_CONFLICTS.md in the same folder as this plan document (UPGRADE_PLAN_v3.18.0.md)

---

## Quick Status Overview

| Phase | Status | Start Date | Completion Date | Blocker |
|-------|--------|------------|-----------------|---------|
| Phase 0: Pre-Upgrade Assessment | 🟢 Complete | 2025-12-30 | 2025-12-30 | - |
| Phase 1: Environment Setup | 🟢 Complete | 2025-12-30 | 2025-12-30 | - |
| Phase 2: Clean Base Creation | 🟢 Complete | 2025-12-30 | 2025-12-30 | - |
| Phase 3: Self-Contained Files | 🟢 Complete | 2025-12-30 | 2025-12-30 | - |
| Phase 4: XSLT Architecture Decision | 🟡 In Progress | 2025-12-30 | - | - |
| Phase 5: Configuration Merge | 🔴 Not Started | - | - | - |
| Phase 6: Dependencies Update | 🔴 Not Started | - | - | - |
| Phase 7: Template/Static Migrations | 🔴 Not Started | - | - | - |
| Phase 8: Database Migrations | 🔴 Not Started | - | - | - |
| Phase 9: Comprehensive Testing | 🔴 Not Started | - | - | - |
| Phase 10: Docker Dev Environment | 🔴 Not Started | - | - | - |
| Phase 11: Staging Deployment (FUTURE) | ⚪ Skipped | - | - | N/A - No production |
| Phase 12: Production Deployment (FUTURE) | ⚪ Skipped | - | - | N/A - No production |

**Legend**: 🔴 Not Started | 🟡 In Progress | 🟢 Complete | ⚠️ Blocked | ❌ Failed | ⚪ Skipped

---

## Table of Contents

- [Phase 0: Pre-Upgrade Assessment](#phase-0-pre-upgrade-assessment)
- [Phase 1: Environment Setup](#phase-1-environment-setup)
- [Phase 2: Clean Base Creation](#phase-2-clean-base-creation)
- [Phase 3: Self-Contained Files Migration](#phase-3-self-contained-files-migration)
- [Phase 4: XSLT Architecture Decision](#phase-4-xslt-architecture-decision)
- [Phase 5: Configuration File Merge](#phase-5-configuration-file-merge)
- [Phase 6: Dependencies Update](#phase-6-dependencies-update)
- [Phase 7: Template and Static File Migrations](#phase-7-template-and-static-file-migrations)
- [Phase 8: Database Migrations](#phase-8-database-migrations)
- [Phase 9: Comprehensive Testing](#phase-9-comprehensive-testing)
- [Phase 10: Docker Development Environment Setup](#phase-10-docker-development-environment-setup) ⭐ **COMPLETION MILESTONE**
- [Phase 11: Staging Deployment (FUTURE)](#phase-11-stagingproduction-deployment-future)
- [Phase 12: Production Deployment (FUTURE)](#phase-12-production-deployment-future)
- [Rollback Procedures](#rollback-procedures)
- [Risk Register](#risk-register)
- [Decision Log](#decision-log)
- [Communication Plan](#communication-plan)

---

## Upgrade Completion Milestone

**For this upgrade**: ✅ **The upgrade is complete after Phase 10** (Docker Development Environment Setup)

Phases 11 and 12 are included for future reference when deploying to staging/production environments. Since no production instance currently exists, completion of Phase 10 means you have:

- ✅ Fully upgraded NexusLIMS-CDCS code to v3.18.0
- ✅ All customizations migrated and tested
- ✅ Docker development environment configured
- ✅ Application accessible at https://nexuslims.localhost
- ✅ Live development workflow with auto-reload
- ✅ Ready for development work or future production deployment

---

## Phase 0: Pre-Upgrade Assessment

**Estimated Duration**: 1 day  
**Status**: 🟢 Complete  
**Dependencies**: None  
**Assignee**: Claude

### Objectives
- Document current development state
- Identify all customizations from NexusLIMS fork
- Establish success criteria for upgrade
- Review reference documentation

**Note**: ⚠️ **No production instance exists yet** - this is a development upgrade. Production backup tasks (0.2) are optional and for reference only.

### Tasks

#### 0.1. Current State Documentation
- [x] **Task**: Document current NexusLIMS-CDCS version
  - **Status**: 🟢
  - **Command**: `git log --oneline -1 main`
  - **Notes**: Commit 30faa97 "Display units next to parameter names in detail view metadata tables"
  - **Verification**: Git tag created: `nexuslims-cdcs-pre-upgrade-20251230`

- [x] **Task**: Document current Python/Django versions (if environment exists)
  - **Status**: 🟢
  - **Command**: `python --version && django-admin --version` (if venv active)
  - **Current**: Python 3.14.0, Django unknown (no venv yet)
  - **Target**: Python 3.11+, Django 5.2.x
  - **Note**: Will use Python 3.11 for upgrade (3.14 not tested with Django 5.2)

- [x] **Task**: List all installed MDCS apps from current main
  - **Status**: 🟢
  - **Command**: Review `INSTALLED_APPS` in `mdcs/settings.py` on main branch
  - **Output**: Created `reference/main/INSTALLED_APPS_before.txt`

#### 0.2. Database Backup Strategy (OPTIONAL - For Reference)
**Note**: Skip this section if no production database exists. Keeping for future reference when production is deployed.

- [ ] **Task**: Create production database backup (SKIP if no production)
  - **Status**: 🔴 N/A
  - **Location**: N/A
  - **Verification**: N/A
  - **Restore Test**: N/A

- [ ] **Task**: Document database schema (SKIP if no production)
  - **Status**: 🔴 N/A
  - **Command**: `python manage.py inspectdb > schema_before_upgrade.py`
  - **Verification**: N/A

- [ ] **Task**: Export critical data (SKIP if no production)
  - **Status**: 🔴 N/A
  - **Tables**: N/A
  - **Format**: N/A

#### 0.3. Code Customization Audit
- [ ] **Task**: Verify CHANGES_FROM_MDCS_2.21.0.md is current
  - **Status**: 🔴
  - **Action**: Re-read document, note any missing customizations
  - **Updates Needed**: (list here)

- [ ] **Task**: Check for undocumented customizations
  - **Status**: 🔴
  - **Command**: `git diff upstream/v2.21.0...main --stat`
  - **Review**: Any files not in CHANGES document?

- [ ] **Task**: Document any local-only modifications
  - **Status**: 🔴
  - **Examples**: Site-specific configs, local templates
  - **List**: (add here)

#### 0.4. Success Criteria Definition
- [ ] **Task**: Define functional success criteria
  - **Status**: 🔴
  - **Criteria**:
    - [ ] Server starts without errors
    - [ ] Admin interface accessible
    - [ ] Can create test user and login
    - [ ] Can upload test template/schema
    - [ ] Can create test data record
    - [ ] Search functionality works (keyword)
    - [ ] Record detail page renders correctly
    - [ ] XSLT transformations render correctly
    - [ ] Download system functions (single file, ZIP)
    - [ ] No console errors in browser
    - [ ] All Python unit tests pass (if any exist)

- [ ] **Task**: Define performance success criteria
  - **Status**: 🔴
  - **Criteria** (for future production):
    - [ ] Search results load in <2s for 100 records
    - [ ] Detail page renders in <1s
    - [ ] Download ZIP completes for 50 files in <30s
    - [ ] Static files serve quickly (<500ms)

#### 0.5. Communication & Scheduling (OPTIONAL)
**Note**: May not be needed for development upgrade. Include if working with team/stakeholders.

- [ ] **Task**: Notify stakeholders of upgrade timeline (OPTIONAL)
  - **Status**: 🔴 N/A
  - **Stakeholders**: (list here if applicable)
  - **Notification Date**: N/A

- [ ] **Task**: Schedule maintenance window (SKIP - no production)
  - **Status**: 🔴 N/A
  - **Window**: N/A
  - **Duration**: N/A

### Phase 0 Completion Checklist
- [ ] Current state documented (commit hash, versions)
- [ ] Code customization audit complete
- [ ] CHANGES_FROM_MDCS_2.21.0.md reviewed and verified
- [ ] Success criteria defined
- [ ] Ready to proceed with upgrade
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 1: Environment Setup

**Estimated Duration**: 1-2 days  
**Status**: 🟡 In Progress  
**Dependencies**: Phase 0 complete  
**Assignee**: Claude

### Objectives
- Create isolated development environment
- Set up git branch structure
- Configure Docker-based development deployment
- Prepare reference files for comparison

### Development Deployment Strategy

**Important**: This upgrade will use the **Docker-based development environment** pattern from `/Users/josh/git_repos/datasophos/cdcs/cdcs-docker/dev`. This provides:

- **Docker Compose** multi-container setup
- **Caddy** reverse proxy with automatic HTTPS (https://nexuslims.localhost)
- **Live code mounting** for development with auto-reload
- **Django runserver** for automatic code reloading
- **Isolated databases** (MongoDB, PostgreSQL, Redis)

**Architecture**:
```
Browser (HTTPS) → Caddy:443 → Django runserver:8000 → NexusLIMS-CDCS App
                      ↓
                 Static Files (/srv/nexuslims_static)
                      ↓
                 MongoDB, PostgreSQL, Redis containers
```

**After the upgrade is complete**, you'll create a similar Docker development environment for NexusLIMS-CDCS that matches the pattern in `cdcs-docker/dev/`.

### Tasks

#### 1.1. Git Branch Structure
- [x] **Task**: Create backup tag
  - **Status**: 🟢
  - **Command**: `git tag -a nexuslims-cdcs-pre-upgrade-$(date +%Y%m%d) -m "Pre-upgrade backup"`
  - **Verification**: Created tag `nexuslims-cdcs-pre-upgrade-20251230`

- [x] **Task**: Create preparation branch from main
  - **Status**: 🟢
  - **Command**: `git checkout -b upgrade/v3.18.0-preparation NexusLIMS_master`
  - **Purpose**: Document current state, prepare comparison files

- [x] **Task**: Create working upgrade branch from v3.18.0
  - **Status**: 🟢
  - **Command**: `git checkout -b upgrade/v3.18.0-working 3.18.0`
  - **Purpose**: Primary upgrade work happens here (currently on this branch)

- [x] **Task**: Configure upstream remote (if not exists)
  - **Status**: 🟢
  - **Command**: `git remote add upstream https://github.com/usnistgov/mdcs.git`
  - **Verification**: Remote `mdcs-upstream` already exists pointing to MDCS repo

- [x] **Task**: Fetch upstream tags
  - **Status**: 🟢
  - **Command**: `git fetch upstream --tags`
  - **Verification**: Both tags 2.21.0 and 3.18.0 exist

#### 1.2. Docker Development Environment Setup

**Note**: For initial testing, you can use a Python virtual environment. However, the **final testing and deployment** (Phase 9+) will use Docker.

##### Option A: Docker Setup (Recommended for Phase 9+)
- [x] **Task**: Verify Docker and Docker Compose installed
  - **Status**: 🟢
  - **Command**: `docker --version && docker compose version`
  - **Result**: Docker 28.1.1, Docker Compose v2.36.0

- [x] **Task**: Create Docker environment structure
  - **Status**: 🟢
  - **Location**: Created `.dev-deployment/` directory in repo root
  - **Pattern**: Based on `/Users/josh/git_repos/datasophos/cdcs/cdcs-docker/dev`
  - **Features**: Live code reload, non-standard ports, helper commands

##### Option B: Python Virtual Environment (For Phases 1-8)
- [x] **Task**: Create Python virtual environment
  - **Status**: 🟢
  - **Python Version**: 3.11.14
  - **Command**: `python3.11 -m venv .venv-upgrade`
  - **Verification**: `.venv-upgrade/bin/python --version` shows Python 3.11.14

- [x] **Task**: Install development dependencies
  - **Status**: 🟢
  - **Command**: `.venv-upgrade/bin/pip install -U pip setuptools wheel`
  - **Verification**: Latest pip, setuptools, and wheel installed

#### 1.3. Reference File Creation
- [x] **Task**: Export v2.21.0 configuration files
  - **Status**: 🟢
  - **Files exported**:
    - [x] `mdcs/settings.py` → `reference/v2.21.0/settings.py`
    - [x] `mdcs/urls.py` → `reference/v2.21.0/urls.py`
    - [x] `mdcs/core_settings.py` → `reference/v2.21.0/core_settings.py`
  - **Command**: `git show 2.21.0:mdcs/settings.py > reference/v2.21.0/settings.py`

- [x] **Task**: Export current main configuration files
  - **Status**: 🟢
  - **Files exported**:
    - [x] `mdcs/settings.py` → `reference/main/settings.py`
    - [x] `mdcs/urls.py` → `reference/main/urls.py`
    - [x] `mdcs/core_settings.py` → `reference/main/core_settings.py`
  - **Command**: `git show NexusLIMS_master:mdcs/settings.py > reference/main/settings.py`

- [x] **Task**: Export v3.18.0 configuration files
  - **Status**: 🟢
  - **Files exported**:
    - [x] `mdcs/settings.py` → `reference/v3.18.0/settings.py`
    - [x] `mdcs/urls.py` → `reference/v3.18.0/urls.py`
    - [x] `mdcs/core_settings.py` → `reference/v3.18.0/core_settings.py`
  - **Command**: `git show 3.18.0:mdcs/settings.py > reference/v3.18.0/settings.py`

#### 1.4. Testing Infrastructure
- [ ] **Task**: Set up local test server configuration
  - **Status**: 🔴
  - **Port**: TBD (e.g., 8001 to avoid conflict with production)
  - **Settings**: Create `mdcs/settings_test.py` if needed

- [ ] **Task**: Configure browser testing tools
  - **Status**: 🔴
  - **Tools**: Chrome DevTools, Firefox Developer Edition
  - **Extensions**: Consider Selenium for automated testing

- [ ] **Task**: Set up static file serving for development
  - **Status**: 🔴
  - **Command**: `python manage.py collectstatic --noinput` (after dependencies installed)

### Phase 1 Completion Checklist
- [x] All git branches created and verified
- [x] Development environment functional
- [x] All reference files exported
- [x] Test server can start (even if with errors)
- [x] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 2: Clean Base Creation

**Estimated Duration**: 1 day  
**Status**: 🟢 Completed 2025-12-30  
**Dependencies**: Phase 1 complete  
**Assignee**: TBD

### Objectives
- Create clean v3.18.0 base on working branch
- Verify base is buildable
- Document baseline state

### Tasks

#### 2.1. Base Verification
- [x] **Task**: Checkout v3.18.0 on working branch
  - **Status**: 🟢
  - **Branch**: `upgrade/v3.18.0-manual`
  - **Command**: `git checkout upgrade/v3.18.0-manual`
  - **Verification**: `git log -1` shows v3.18.0 tag

- [x] **Task**: Build Docker image with v3.18.0
  - **Status**: 🟢
  - **Command**: `dev-build` (or `dev-build-clean` for no cache)
  - **Expected Issues**: May fail due to dependency conflicts
  - **Resolution**: Document all errors

- [x] **Task**: Start development environment
  - **Status**: 🟢
  - **Command**: `dev-up`
  - **Result**: Services running ✓ / Failed ✗
  - **Containers**: All 5 services should be up (caddy, postgres, mongo, redis, cdcs)

- [x] **Task**: Verify database migrations
  - **Status**: 🟢
  - **Command**: `dev-migrate` (auto-runs during startup)
  - **Result**: Success ✓ / Failed ✗
  - **Errors**: Check with `dev-logs-app`

- [x] **Task**: Verify static files are collected
  - **Status**: 🟢
  - **Command**: `dev-collectstatic`
  - **Result**: Success ✓ / Failed ✗

#### 2.2. Baseline Testing
- [x] **Task**: Access admin interface
  - **Status**: 🟢
  - **URL**: `https://nexuslims-dev.localhost/staff-core-admin/dashboard` and `https://nexuslims-dev.localhost/staff-admin/`
  - **Result**: Loads ✓ / 500 Error ✗

- [x] **Task**: Create test superuser
  - **Status**: 🟢
  - **Command**: `dev-superuser`
  - **Username**: `admin` / `admin@admin.com` / `admin` (password)

- [x] **Task**: Upload test template (if possible)
  - **Status**: 🟢
  - **Purpose**: Verify basic MDCS functionality works
  - **Template**: Use simple XSD for testing
  
- [x] **Task**: Upload test document
  - **Status**: 🟢
  - **Purpose**: Verify basic MDCS functionality works
  - **Template**: Use simple XSD for testing
  - **Issue Found**: Records created in PostgreSQL but not MongoDB
  - **Root Cause**: Celery workers not running
  - **Fix**: Added celery services to dev container

- [x] **Task**: Document baseline behavior
  - **Status**: 🟢
  - **What Works**: Basic app loading, uploading template, registering XSLT, uploading records, viewing records in list (with broken XSLT)
  - **What Doesn't Work**: No NexusLIMS customizations, detail XSLT doesn't display at all (but it is being applied/working)
  - **Expected Issues**: NexusLIMS customizations not present

#### 2.3. Component Version Documentation
- [x] **Task**: Record installed app versions
  - **Status**: 🟢
  - **Command**: `pip freeze > requirements_v3.18.0_baseline.txt`
  - **Key Versions to Note**:
    - Django: 4.2.27
    - djangorestframework: 3.16.1
    - django-allauth: (not directly installed - may be a transitive dependency)
    - core_main_app: 2.18.0
    - core_explore_common_app: 2.18.0
    - core_explore_keyword_app: 2.18.0 

### Phase 2 Completion Checklist
- [x] v3.18.0 base confirmed working
- [x] All component versions documented
- [x] Test database migrated successfully
- [x] Admin interface accessible
- [x] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 3: Self-Contained Files Migration

**Estimated Duration**: 2-3 days  
**Status**: 🔴 Not Started  
**Dependencies**: Phase 2 complete  
**Assignee**: TBD

### Objectives
- Copy all 47+ self-contained files from NexusLIMS customizations
- Organize by category for clean git history
- Verify each category independently

### Reference
See **CHANGES_FROM_MDCS_2.21.0.md § "Rebase Strategy Guide" → "Self-Contained Changes (Copy As-Is)"**

### Tasks by Category

#### 3.1. Python Modules - New Files (6 files)
**Status**: 🔴 Not Started

- [ ] **Task**: Create `mdcs_home/context_processors.py`
  - **Status**: 🔴
  - **Source Branch**: `main`
  - **Command**: `git checkout main -- mdcs_home/context_processors.py`
  - **Function**: `doc_link()` context processor
  - **Test**: Import in Python shell, verify no syntax errors

- [ ] **Task**: Create `mdcs_home/templatetags/__init__.py`
  - **Status**: 🔴
  - **Source**: `git checkout main -- mdcs_home/templatetags/__init__.py`

- [ ] **Task**: Create `mdcs_home/templatetags/render_extras.py`
  - **Status**: 🔴
  - **Source**: `git checkout main -- mdcs_home/templatetags/render_extras.py`
  - **Purpose**: Custom template tags for rendering

- [ ] **Task**: Create `mdcs_home/templatetags/xsl_transform_tag.py`
  - **Status**: 🔴
  - **Source**: `git checkout main -- mdcs_home/templatetags/xsl_transform_tag.py`
  - **Purpose**: XSLT transformation template tag
  - **⚠️ Note**: May be eliminated if choosing Option B in Phase 4

- [ ] **Task**: Create `mdcs_home/utils/xml.py`
  - **Status**: 🔴
  - **Source**: `git checkout main -- mdcs_home/utils/xml.py`
  - **Function**: `xsl_transform()` with parameter passing
  - **⚠️ Note**: CRITICAL for XSLT parameter system

- [ ] **Task**: Create `results_override/__init__.py`
  - **Status**: 🔴
  - **Source**: `git checkout main -- results_override/__init__.py`
  - **Purpose**: App initialization for results override

- [ ] **Task**: Commit Python modules
  - **Status**: 🔴
  - **Command**: `git add mdcs_home/context_processors.py mdcs_home/templatetags/ mdcs_home/utils/ results_override/__init__.py`
  - **Commit Message**: 
    ```
    feat: Add NexusLIMS Python modules
    
    - Context processor for doc_link
    - Template tags for XSLT transformation
    - XML utilities with parameter passing
    - Results override app initialization
    
    References: CHANGES_FROM_MDCS_2.21.0.md § 2.1-2.6
    Original commits: 4d61307, a8e520b, 29d848d, etc.
    ```

#### 3.2. CSS Files - New (4 files)
**Status**: 🔴 Not Started

- [ ] **Task**: Create `results_override/static/core_explore_common_app/user/css/query_result.css`
  - **Status**: 🔴
  - **Source**: `git checkout main -- results_override/static/core_explore_common_app/user/css/query_result.css`

- [ ] **Task**: Create `results_override/static/core_explore_common_app/user/css/results.css`
  - **Status**: 🔴
  - **Source**: `git checkout main -- results_override/static/core_explore_common_app/user/css/results.css`

- [ ] **Task**: Create `static/libs/datatables/1.10.24/datatables.min.css`
  - **Status**: 🔴
  - **Source**: `git checkout main -- static/libs/datatables/1.10.24/`
  - **Note**: May need to copy entire directory

- [ ] **Task**: Create `static/libs/shepherd.js/a374a73/shepherd.css`
  - **Status**: 🔴
  - **Source**: `git checkout main -- static/libs/shepherd.js/a374a73/`
  - **Purpose**: Tutorial system styles

- [ ] **Task**: Commit CSS files
  - **Status**: 🔴
  - **Commit Message**: `feat: Add NexusLIMS CSS customizations`

#### 3.3. JavaScript Files - New (7+ files)
**Status**: 🔴 Not Started

- [ ] **Task**: Create `static/js/menu_custom.js`
  - **Status**: 🔴
  - **Source**: `git checkout main -- static/js/menu_custom.js`
  - **Purpose**: Custom menu behavior

- [ ] **Task**: Create `static/js/nexus_buttons.js`
  - **Status**: 🔴
  - **Source**: `git checkout main -- static/js/nexus_buttons.js`
  - **Purpose**: Download system button handlers

- [ ] **Task**: Copy DataTables library files
  - **Status**: 🔴
  - **Files**:
    - [ ] `static/libs/datatables/1.10.24/datatables.min.js`
    - [ ] `static/libs/datatables/1.10.24/DataTables-1.10.24/**`
  - **Command**: `git checkout main -- static/libs/datatables/`

- [ ] **Task**: Copy StreamSaver library files
  - **Status**: 🔴
  - **Files**:
    - [ ] `static/libs/StreamSaver.js/2.0.5/StreamSaver.js`
    - [ ] `static/libs/StreamSaver.js/2.0.5/sw.js`
    - [ ] `static/libs/StreamSaver.js/2.0.5/mitm.html`
  - **Command**: `git checkout main -- static/libs/StreamSaver.js/`

- [ ] **Task**: Copy Web Streams Polyfill
  - **Status**: 🔴
  - **File**: `static/libs/web-streams-polyfill/3.2.1/ponyfill.min.js`
  - **Command**: `git checkout main -- static/libs/web-streams-polyfill/`

- [ ] **Task**: Copy additional polyfills (if needed)
  - **Status**: 🔴
  - **Directory**: `static/libs/`
  - **Review**: Check for any other new libraries

- [ ] **Task**: Commit JavaScript files
  - **Status**: 🔴
  - **Commit Message**: `feat: Add NexusLIMS JavaScript libraries and customizations`

#### 3.4. Source Map Files (5 files)
**Status**: 🔴 Not Started

- [ ] **Task**: Copy all .map files
  - **Status**: 🔴
  - **Command**: `git checkout main -- static/libs/**/*.map`
  - **Verification**: `find static/libs -name "*.map" | wc -l` shows 5

- [ ] **Task**: Commit source maps
  - **Status**: 🔴
  - **Commit Message**: `chore: Add source maps for JavaScript libraries`

#### 3.5. Templates - New (8 files)
**Status**: 🔴 Not Started

- [ ] **Task**: Create `templates/core_explore_common_app/user/results/data_source_info.html`
  - **Status**: 🔴
  - **Source**: `git checkout main -- templates/core_explore_common_app/user/results/data_source_info.html`

- [ ] **Task**: Create `templates/core_explore_common_app/user/results/data_source_results.html`
  - **Status**: 🔴
  - **Source**: `git checkout main -- templates/core_explore_common_app/user/results/data_source_results.html`

- [ ] **Task**: Create `templates/core_explore_common_app/user/results/data_sources_results.html`
  - **Status**: 🔴
  - **Source**: `git checkout main -- templates/core_explore_common_app/user/results/data_sources_results.html`

- [ ] **Task**: Create `templates/core_explore_keyword_app/user/index.html`
  - **Status**: 🔴
  - **Source**: `git checkout main -- templates/core_explore_keyword_app/user/index.html`

- [ ] **Task**: Create `templates/core_main_app/_render/user/theme_base.html`
  - **Status**: 🔴
  - **Source**: `git checkout main -- templates/core_main_app/_render/user/theme_base.html`

- [ ] **Task**: Create `templates/core_main_app/common/data/detail_data.html`
  - **Status**: 🔴
  - **Source**: `git checkout main -- templates/core_main_app/common/data/detail_data.html`

- [ ] **Task**: Create `templates/core_main_app/user/data/detail.html`
  - **Status**: 🔴
  - **Source**: `git checkout main -- templates/core_main_app/user/data/detail.html`

- [ ] **Task**: Verify any additional template files
  - **Status**: 🔴
  - **Command**: `diff -r templates/ ../nexuslims-cdcs-main/templates/ --brief | grep "Only in ../nexuslims-cdcs-main"`
  - **Missing Templates**: (list if found)

- [ ] **Task**: Commit template files
  - **Status**: 🔴
  - **Commit Message**: `feat: Add NexusLIMS template overrides`

#### 3.6. XSLT Stylesheets - CRITICAL (2 files)
**Status**: 🔴 Not Started

- [ ] **Task**: Create `xslt/detail_stylesheet.xsl`
  - **Status**: 🔴
  - **Source**: `git checkout main -- xslt/detail_stylesheet.xsl`
  - **Purpose**: Renders individual record detail view
  - **Size**: ~1000 lines
  - **⚠️ CRITICAL**: Core of NexusLIMS record rendering

- [ ] **Task**: Create `xslt/list_stylesheet.xsl`
  - **Status**: 🔴
  - **Source**: `git checkout main -- xslt/list_stylesheet.xsl`
  - **Purpose**: Renders search results table
  - **Size**: ~500 lines
  - **⚠️ CRITICAL**: Search results display

- [ ] **Task**: Create `xslt/` directory if needed
  - **Status**: 🔴
  - **Command**: `mkdir -p xslt`

- [ ] **Task**: Verify XSLT validation
  - **Status**: 🔴
  - **Tool**: `xmllint --xslt xslt/detail_stylesheet.xsl` (if available)
  - **Alternative**: Load in browser and check for errors

- [ ] **Task**: Commit XSLT files
  - **Status**: 🔴
  - **Commit Message**: 
    ```
    feat: Add NexusLIMS XSLT stylesheets
    
    - detail_stylesheet.xsl: Record detail view rendering
    - list_stylesheet.xsl: Search results table rendering
    
    These are the core rendering engine for NexusLIMS records.
    
    References: CHANGES_FROM_MDCS_2.21.0.md § 10.1-10.2
    ```

#### 3.7. Static Images (3 new, 1 modified)
**Status**: 🔴 Not Started

- [ ] **Task**: Add `static/core_main_app/img/logo_horizontal_text.png`
  - **Status**: 🔴
  - **Source**: `git checkout main -- static/core_main_app/img/logo_horizontal_text.png`

- [ ] **Task**: Add `static/img/logo_bare.png`
  - **Status**: 🔴
  - **Source**: `git checkout main -- static/img/logo_bare.png`

- [ ] **Task**: Add `static/img/logo_horizontal.png`
  - **Status**: 🔴
  - **Source**: `git checkout main -- static/img/logo_horizontal.png`

- [ ] **Task**: Update `static/img/favicon.png` (modified)
  - **Status**: 🔴
  - **Source**: `git checkout main -- static/img/favicon.png`

- [ ] **Task**: Remove `static/core_main_app/img/mgi_diagram.jpg` (deleted)
  - **Status**: 🔴
  - **Command**: `git rm static/core_main_app/img/mgi_diagram.jpg` (if exists)

- [ ] **Task**: Commit image files
  - **Status**: 🔴
  - **Commit Message**: `feat: Add NexusLIMS branding images`

### Phase 3 Completion Checklist
- [ ] All 47+ self-contained files copied
- [ ] Each category committed separately with clear messages
- [ ] No merge conflicts during file copy
- [ ] Git history is clean and traceable
- [ ] Files organized into logical commits (7-8 commits total)
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 4: XSLT Architecture Decision

**Estimated Duration**: 2-3 days (Option A) or 3-5 days (Option B)  
**Status**: 🔴 Not Started  
**Dependencies**: Phase 3 complete  
**Assignee**: TBD

### Objectives
- Make critical architectural decision about XSLT parameter system
- Implement chosen approach
- Verify rendering works correctly

### Decision Point

**DECISION REQUIRED**: Choose Option A or Option B

**Option A**: Preserve XSLT Parameter System (Higher ongoing maintenance)  
**Option B**: Eliminate XSLT Parameter System (One-time refactor, cleaner architecture)

**Recommendation**: Option B (see POTENTIAL_UPGRADE_CONFLICTS.md § 1.1)

---

### Option A: Preserve XSLT Parameter System

**Status**: 🔴 Not Started (if chosen)

#### A.1. Verify Required Files Present
- [ ] **Task**: Confirm `mdcs_home/utils/xml.py` exists
  - **Status**: 🔴
  - **Function**: `xsl_transform()` with `param_dict` support
  - **Location**: Should be copied in Phase 3.1

- [ ] **Task**: Confirm `mdcs_home/templatetags/xsl_transform_tag.py` exists
  - **Status**: 🔴
  - **Tag**: `{% xsl_transform %}`
  - **Location**: Should be copied in Phase 3.1

#### A.2. Configure App Loading Order
- [ ] **Task**: Add `results_override` to INSTALLED_APPS
  - **Status**: 🔴
  - **File**: `mdcs/settings.py`
  - **Position**: BEFORE `core_main_app` and `core_explore_common_app`
  - **Critical**: App order determines template/static file precedence

- [ ] **Task**: Verify `results_override/static/` directory structure
  - **Status**: 🔴
  - **Expected**:
    ```
    results_override/
    └── static/
        └── core_explore_common_app/
            └── user/
                ├── css/
                │   ├── query_result.css
                │   └── results.css
                └── js/
                    └── results.js
    ```

#### A.3. Update Configuration to Use Custom xsl_transform
- [ ] **Task**: Review templates using XSLT
  - **Status**: 🔴
  - **Files**:
    - `templates/core_main_app/user/data/detail.html`
    - `templates/core_explore_common_app/user/results/data_source_results.html`
  - **Verification**: Look for `{% load xsl_transform_tag %}` and `{% xsl_transform %}`

- [ ] **Task**: Ensure context processor is registered
  - **Status**: 🔴
  - **File**: `mdcs/settings.py`
  - **Section**: `TEMPLATES[0]['OPTIONS']['context_processors']`
  - **Add**: `'mdcs_home.context_processors.doc_link'`

#### A.4. Test XSLT Parameter Passing
- [ ] **Task**: Create test record with known parameters
  - **Status**: 🔴
  - **Test XML**: Upload sample NexusLIMS record
  - **Expected Params**: `record_url`, `cdcs_url`, `api_url`

- [ ] **Task**: Verify parameters in rendered output
  - **Status**: 🔴
  - **Method**: View page source, check for parameter values
  - **Check**: "View Raw" button has correct URL

- [ ] **Task**: Test in browser console
  - **Status**: 🔴
  - **Console Check**: No errors related to undefined variables
  - **Network Tab**: API calls use correct URLs

#### A.5. Document Maintenance Requirements
- [ ] **Task**: Document future upgrade impacts
  - **Status**: 🔴
  - **File**: Create `docs/XSLT_PARAMETER_SYSTEM.md`
  - **Content**: 
    - How system works
    - Files that must be preserved in future upgrades
    - Testing procedure
    - Known limitations

---

### Option B: Eliminate XSLT Parameter System (RECOMMENDED)

**Status**: 🔴 Not Started (if chosen)

#### B.1. Analysis and Planning
- [ ] **Task**: Identify all XSLT parameters in use
  - **Status**: 🔴
  - **Command**: `grep -r "xsl:param" xslt/`
  - **Current Parameters**:
    - [ ] `record_url`
    - [ ] `cdcs_url`
    - [ ] `api_url`
    - [ ] Others: (list if found)

- [ ] **Task**: Document current parameter usage
  - **Status**: 🔴
  - **File**: Create analysis doc
  - **For Each Param**:
    - Where it's set (Python)
    - Where it's used (XSLT)
    - What functionality depends on it

#### B.2. Modify XSLT Templates
- [ ] **Task**: Replace `<xsl:param>` declarations with placeholders
  - **Status**: 🔴
  - **File**: `xslt/detail_stylesheet.xsl`
  - **Before**:
    ```xml
    <xsl:param name="record_url" select="''" />
    <xsl:value-of select="$record_url" />
    ```
  - **After**:
    ```xml
    <!-- Parameter removed - set via JavaScript -->
    <span class="api-endpoint" data-endpoint="record"></span>
    ```

- [ ] **Task**: Add data attributes to HTML output
  - **Status**: 🔴
  - **Approach**: Modify XSLT to output data-* attributes
  - **Example**:
    ```xml
    <xsl:template name="view-raw-button">
      <a href="#" class="btn btn-primary" 
         data-record-id="{//id}"
         data-action="view-raw">View Raw</a>
    </xsl:template>
    ```

- [ ] **Task**: Test XSLT still renders without parameters
  - **Status**: 🔴
  - **Method**: Transform XML with xsltproc (no params)
  - **Verification**: Output contains data attributes

#### B.3. Create JavaScript Parameter Injection
- [ ] **Task**: Create `static/js/xslt_params.js`
  - **Status**: 🔴
  - **Purpose**: Read Django template variables, populate data attributes
  - **Example**:
    ```javascript
    document.addEventListener('DOMContentLoaded', function() {
        const recordUrl = '{{ record_url|escapejs }}';
        const cdcsUrl = '{{ cdcs_url|escapejs }}';
        
        // Populate all elements with data-endpoint attribute
        document.querySelectorAll('[data-endpoint]').forEach(el => {
            const endpoint = el.dataset.endpoint;
            if (endpoint === 'record') el.dataset.url = recordUrl;
            // ... etc
        });
    });
    ```

- [ ] **Task**: Include script in detail template
  - **Status**: 🔴
  - **File**: `templates/core_main_app/user/data/detail.html`
  - **Add**: `<script src="{% static 'js/xslt_params.js' %}"></script>`

#### B.4. Update Button Handlers
- [ ] **Task**: Modify "View Raw" button handler
  - **Status**: 🔴
  - **File**: `static/js/nexus_buttons.js` (or create new file)
  - **Before**: Assumed URL in XSLT output
  - **After**: Read from `data-url` attribute

- [ ] **Task**: Modify download system handlers
  - **Status**: 🔴
  - **Purpose**: Ensure API calls use data attributes
  - **Files**: Check for any hardcoded URLs

#### B.5. Remove Obsolete Files
- [ ] **Task**: Remove `mdcs_home/utils/xml.py`
  - **Status**: 🔴
  - **Command**: `git rm mdcs_home/utils/xml.py`
  - **Reason**: No longer needed

- [ ] **Task**: Remove `mdcs_home/templatetags/xsl_transform_tag.py`
  - **Status**: 🔴
  - **Command**: `git rm mdcs_home/templatetags/xsl_transform_tag.py`
  - **Reason**: No longer needed

- [ ] **Task**: Update templates to use default XSLT tag
  - **Status**: 🔴
  - **Files**: All templates using `{% xsl_transform %}`
  - **Change**: Use core_main_app's built-in XSLT rendering

#### B.6. Test New Architecture
- [ ] **Task**: Verify detail page renders correctly
  - **Status**: 🔴
  - **Check**: All buttons present, no layout issues
  - **Console**: No JavaScript errors

- [ ] **Task**: Test "View Raw" functionality
  - **Status**: 🔴
  - **Action**: Click "View Raw" button
  - **Expected**: Opens correct XML endpoint

- [ ] **Task**: Test download functionality
  - **Status**: 🔴
  - **Action**: Click download buttons
  - **Expected**: Files download correctly

- [ ] **Task**: Test search results rendering
  - **Status**: 🔴
  - **Check**: Results table displays correctly
  - **Links**: All links point to correct URLs

#### B.7. Documentation
- [ ] **Task**: Document new architecture
  - **Status**: 🔴
  - **File**: Create `docs/XSLT_RENDERING_ARCHITECTURE.md`
  - **Content**:
    - How rendering works without parameters
    - Data attribute convention
    - JavaScript integration points
    - Advantages over old system

- [ ] **Task**: Update upgrade documentation
  - **Status**: 🔴
  - **File**: This document (UPGRADE_PLAN)
  - **Note**: Record decision and rationale in Decision Log

---

### Phase 4 Completion Checklist
- [ ] Architecture decision made and documented in Decision Log
- [ ] Chosen approach fully implemented
- [ ] All rendering tests pass
- [ ] Documentation updated
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 5: Configuration File Merge

**Estimated Duration**: 3-4 days  
**Status**: 🔴 Not Started  
**Dependencies**: Phase 4 complete  
**Assignee**: TBD

### Objectives
- Merge NexusLIMS customizations into v3.18.0 config files
- Ensure all new Django 5.2 requirements met
- Preserve all site-specific settings

### Reference
See **POTENTIAL_UPGRADE_CONFLICTS.md § "MDCS Core Repository Changes"**

---

### 5.1. mdcs/settings.py - CRITICAL MERGE

**Status**: 🔴 Not Started

#### 5.1.1. Preparation
- [ ] **Task**: Open three-way comparison
  - **Status**: 🔴
  - **Files**:
    - Base: `reference/v2.21.0/settings.py`
    - Ours: `reference/main/settings.py`
    - Theirs: `reference/v3.18.0/settings.py`
  - **Tool**: Visual diff tool (VSCode, Beyond Compare, etc.)

- [ ] **Task**: Identify all NexusLIMS customizations
  - **Status**: 🔴
  - **Method**: Compare Base vs Ours
  - **Document**: List all custom sections below
  - **Custom Sections Found**:
    1. 
    2. 
    3. 

#### 5.1.2. INSTALLED_APPS Section
- [ ] **Task**: Start with v3.18.0 INSTALLED_APPS order
  - **Status**: 🔴
  - **Reason**: Django 5.2 may depend on new app order
  - **Source**: `reference/v3.18.0/settings.py`

- [ ] **Task**: Verify core apps present
  - **Status**: 🔴
  - **Required Apps** (from POTENTIAL_UPGRADE_CONFLICTS.md § 3.1.B):
    - [ ] `django.contrib.admin`
    - [ ] `django.contrib.auth`
    - [ ] `django.contrib.contenttypes`
    - [ ] `django.contrib.sessions`
    - [ ] `django.contrib.messages`
    - [ ] `django.contrib.staticfiles`
    - [ ] `django.contrib.sites`
    - [ ] `allauth`
    - [ ] `allauth.account`
    - [ ] `allauth.socialaccount`
    - [ ] `oauth2_provider`
    - [ ] `rest_framework`
    - [ ] `rest_framework.authtoken`
    - [ ] `django_celery_beat`
    - [ ] `menu`

- [ ] **Task**: Add `results_override` app (if Option A chosen in Phase 4)
  - **Status**: 🔴
  - **Position**: BEFORE `core_main_app`
  - **Code**:
    ```python
    INSTALLED_APPS = [
        # ... Django apps ...
        'results_override',  # MUST be before core apps for override
        'core_main_app',
        'core_explore_common_app',
        # ... rest ...
    ]
    ```

- [ ] **Task**: Verify removed apps are gone
  - **Status**: 🔴
  - **Apps Removed in v3.18.0**:
    - [ ] `core_oaipmh_harvester_app` (removed)
    - [ ] `core_oaipmh_provider_app` (removed)
    - [ ] `core_module_local_id_registry_app` (removed)
  - **Action**: Ensure not in final INSTALLED_APPS

- [ ] **Task**: Check for NexusLIMS-specific apps
  - **Status**: 🔴
  - **Custom Apps**: (list if any)
  - **Action**: Add to INSTALLED_APPS if needed

#### 5.1.3. MIDDLEWARE Configuration
- [ ] **Task**: Use v3.18.0 MIDDLEWARE order
  - **Status**: 🔴
  - **Source**: `reference/v3.18.0/settings.py`
  - **Reason**: Django 5.2 requires specific order

- [ ] **Task**: Verify security middleware present
  - **Status**: 🔴
  - **Required**:
    - [ ] `django.middleware.security.SecurityMiddleware`
    - [ ] `django.middleware.csrf.CsrfViewMiddleware`
    - [ ] `django.middleware.clickjacking.XFrameOptionsMiddleware`

- [ ] **Task**: Check for custom middleware
  - **Status**: 🔴
  - **NexusLIMS Custom**: (list if any)
  - **Action**: Add if needed, maintain proper order

#### 5.1.4. TEMPLATES Configuration
- [ ] **Task**: Merge context processors
  - **Status**: 🔴
  - **Base v3.18.0 processors**: (copy from reference file)
  - **Add NexusLIMS processor**:
    ```python
    'OPTIONS': {
        'context_processors': [
            # ... v3.18.0 processors ...
            'mdcs_home.context_processors.doc_link',  # NexusLIMS
        ],
    }
    ```

- [ ] **Task**: Verify template loaders
  - **Status**: 🔴
  - **Check**: App directories loader present
  - **Purpose**: Enables template overrides

#### 5.1.5. REST_FRAMEWORK Configuration
- [ ] **Task**: Start with v3.18.0 REST_FRAMEWORK
  - **Status**: 🔴
  - **Source**: `reference/v3.18.0/settings.py`

- [ ] **Task**: Preserve NexusLIMS pagination settings (if customized)
  - **Status**: 🔴
  - **Check**: Compare `reference/main/settings.py` for custom values
  - **Settings to Review**:
    - `DEFAULT_PAGINATION_CLASS`
    - `PAGE_SIZE`
    - Custom authentication classes

- [ ] **Task**: Verify authentication classes
  - **Status**: 🔴
  - **v3.18.0 Default**:
    ```python
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ]
    ```

#### 5.1.6. Database Configuration
- [ ] **Task**: Preserve database settings
  - **Status**: 🔴
  - **NexusLIMS DB**: (check current settings)
  - **Keep**: All custom DB configuration from `reference/main/settings.py`

#### 5.1.7. Static Files Configuration
- [ ] **Task**: Merge STATIC_URL and STATIC_ROOT
  - **Status**: 🔴
  - **Use**: v3.18.0 defaults unless customized
  - **Custom Settings**: (document if any)

- [ ] **Task**: Merge STATICFILES_DIRS
  - **Status**: 🔴
  - **Check**: Any NexusLIMS-specific static directories
  - **Current**: (list from reference/main/settings.py)

- [ ] **Task**: Verify STATICFILES_FINDERS
  - **Status**: 🔴
  - **Required**:
    - `django.contrib.staticfiles.finders.FileSystemFinder`
    - `django.contrib.staticfiles.finders.AppDirectoriesFinder`

#### 5.1.8. New Settings in v3.18.0
- [ ] **Task**: Add django-allauth settings
  - **Status**: 🔴
  - **Settings** (from POTENTIAL_UPGRADE_CONFLICTS.md § 3.1.D):
    ```python
    ACCOUNT_EMAIL_VERIFICATION = 'optional'
    ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
    SOCIALACCOUNT_AUTO_SIGNUP = True
    LOGIN_REDIRECT_URL = '/'
    ACCOUNT_LOGOUT_REDIRECT_URL = '/'
    ```

- [ ] **Task**: Add SITE_ID setting
  - **Status**: 🔴
  - **Code**: `SITE_ID = 1`
  - **Reason**: Required for django.contrib.sites

- [ ] **Task**: Review new security settings
  - **Status**: 🔴
  - **Check**: CSRF, CORS, XSS protection settings in v3.18.0

#### 5.1.9. NexusLIMS-Specific Settings
- [ ] **Task**: Preserve all environment variable references
  - **Status**: 🔴
  - **Pattern**: `os.getenv(...)` or `os.environ[...]`
  - **Check**: Documentation links, API URLs, custom paths

- [ ] **Task**: Preserve custom logging configuration
  - **Status**: 🔴
  - **Current**: (document from reference/main/settings.py)

- [ ] **Task**: Preserve any XSLT-related settings
  - **Status**: 🔴
  - **Examples**: XSLT file paths, transformation settings

#### 5.1.10. Final Review and Testing
- [ ] **Task**: Syntax check
  - **Status**: 🔴
  - **Command**: `python -m py_compile mdcs/settings.py`
  - **Result**: No syntax errors

- [ ] **Task**: Import test
  - **Status**: 🔴
  - **Command**: `python -c "from mdcs import settings"`
  - **Result**: Imports successfully

- [ ] **Task**: Run Django check
  - **Status**: 🔴
  - **Command**: `python manage.py check`
  - **Result**: (document warnings/errors)

- [ ] **Task**: Commit settings.py
  - **Status**: 🔴
  - **Commit Message**:
    ```
    config: Merge NexusLIMS settings.py to v3.18.0
    
    - Updated INSTALLED_APPS for Django 5.2
    - Merged MIDDLEWARE configuration
    - Added django-allauth settings
    - Preserved NexusLIMS custom configuration
    - [Option A: Added results_override app]
    
    References: POTENTIAL_UPGRADE_CONFLICTS.md § 3.1
    ```

---

### 5.2. mdcs/urls.py Merge

**Status**: 🔴 Not Started

#### 5.2.1. Preparation
- [ ] **Task**: Open three-way comparison
  - **Status**: 🔴
  - **Files**:
    - Base: `reference/v2.21.0/urls.py`
    - Ours: `reference/main/urls.py`
    - Theirs: `reference/v3.18.0/urls.py`

#### 5.2.2. Admin URL Changes
- [ ] **Task**: Update admin URL prefix
  - **Status**: 🔴
  - **v2.21.0**: `path('admin/', admin.site.urls)`
  - **v3.18.0**: `path('djadmin/', admin.site.urls)` (changed prefix)
  - **Action**: Use `djadmin/` to avoid conflicts

#### 5.2.3. Removed URL Patterns
- [ ] **Task**: Remove OAI-PMH routes
  - **Status**: 🔴
  - **Removed**:
    - `path('oai-pmh/server/', ...)`
    - `path('oai-pmh/harvester/', ...)`
  - **Action**: Ensure not in final urls.py

- [ ] **Task**: Remove module discovery routes
  - **Status**: 🔴
  - **Removed**: `path('modules/', ...)`
  - **Action**: Delete if present

#### 5.2.4. New URL Patterns
- [ ] **Task**: Add django-allauth URLs
  - **Status**: 🔴
  - **Code**:
    ```python
    path('accounts/', include('allauth.urls')),
    ```
  - **Verification**: Added to urlpatterns

- [ ] **Task**: Verify OAuth2 URLs
  - **Status**: 🔴
  - **Code**:
    ```python
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    ```

#### 5.2.5. NexusLIMS Custom Routes
- [ ] **Task**: Identify custom URL patterns
  - **Status**: 🔴
  - **Source**: `reference/main/urls.py`
  - **Custom Routes**: (list here)

- [ ] **Task**: Add custom routes to v3.18.0 base
  - **Status**: 🔴
  - **Location**: Appropriate position in urlpatterns

#### 5.2.6. Testing and Commit
- [ ] **Task**: Syntax check
  - **Status**: 🔴
  - **Command**: `python -m py_compile mdcs/urls.py`

- [ ] **Task**: URL reverse test
  - **Status**: 🔴
  - **Command**: `python manage.py check --deploy`
  - **Result**: (document issues)

- [ ] **Task**: Commit urls.py
  - **Status**: 🔴
  - **Commit Message**: `config: Merge NexusLIMS urls.py to v3.18.0`

---

### 5.3. mdcs/core_settings.py Merge

**Status**: 🔴 Not Started

#### 5.3.1. Preparation
- [ ] **Task**: Open three-way comparison
  - **Status**: 🔴
  - **Files**: Same pattern as above

#### 5.3.2. Merge Changes
- [ ] **Task**: Review all changes in v3.18.0
  - **Status**: 🔴
  - **Note**: Usually minimal changes in core_settings.py

- [ ] **Task**: Preserve NexusLIMS customizations
  - **Status**: 🔴
  - **Custom Settings**: (document from reference/main/core_settings.py)

- [ ] **Task**: Test and commit
  - **Status**: 🔴
  - **Commit Message**: `config: Merge NexusLIMS core_settings.py to v3.18.0`

---

### 5.4. .gitignore Update

**Status**: 🔴 Not Started

- [ ] **Task**: Merge .gitignore changes
  - **Status**: 🔴
  - **Source**: `git checkout main -- .gitignore`
  - **Review**: Any v3.18.0 additions worth keeping

- [ ] **Task**: Commit .gitignore
  - **Status**: 🔴
  - **Commit Message**: `chore: Update .gitignore for NexusLIMS`

---

### Phase 5 Completion Checklist
- [ ] All configuration files merged
- [ ] Django check passes with no errors
- [ ] All settings documented
- [ ] Clear git history with separate commits per file
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 6: Dependencies Update

**Estimated Duration**: 1-2 days  
**Status**: 🔴 Not Started  
**Dependencies**: Phase 5 complete  
**Assignee**: TBD

### Objectives
- Update requirements.txt with v3.18.0 dependencies
- Install and verify all packages
- Document version conflicts

### Reference
See **POTENTIAL_UPGRADE_CONFLICTS.md § "Critical Breaking Changes" → "Core App Dependency Versions"**

### Tasks

#### 6.1. requirements.txt / requirements.core.txt Update

- [ ] **Task**: Backup current requirements
  - **Status**: 🔴
  - **Command**: `cp requirements.txt requirements.txt.backup`

- [ ] **Task**: Start with v3.18.0 requirements
  - **Status**: 🔴
  - **Source**: `git show upstream/v3.18.0:requirements.txt`
  - **Output**: `requirements.txt`

- [ ] **Task**: Verify critical package versions
  - **Status**: 🔴
  - **From POTENTIAL_UPGRADE_CONFLICTS.md § 2**:
    - [ ] `Django>=5.2.0,<5.3.0`
    - [ ] `djangorestframework~=3.15.0`
    - [ ] `django-allauth~=65.2.0`
    - [ ] `django-oauth-toolkit~=3.0.1`
    - [ ] `celery~=5.4.0`
    - [ ] `django-celery-beat~=2.7.0`
    - [ ] `core_main_app~=2.28.0`
    - [ ] `core_explore_common_app~=2.28.0`
    - [ ] `core_explore_keyword_app~=2.28.0`

- [ ] **Task**: Add NexusLIMS-specific dependencies
  - **Status**: 🔴
  - **Source**: `reference/main/requirements.txt`
  - **Custom Packages**: (list here)

- [ ] **Task**: Document version justifications
  - **Status**: 🔴
  - **File**: `docs/DEPENDENCY_VERSIONS.md`
  - **Content**: Why specific versions chosen

#### 6.2. Installation and Testing

- [ ] **Task**: Create clean virtual environment
  - **Status**: 🔴
  - **Command**: `python3.11 -m venv .venv-final`
  - **Activation**: `source .venv-final/bin/activate`

- [ ] **Task**: Install updated requirements
  - **Status**: 🔴
  - **Command**: `pip install -r requirements.txt`
  - **Warnings**: (document any)
  - **Conflicts**: (document any)

- [ ] **Task**: Freeze installed versions
  - **Status**: 🔴
  - **Command**: `pip freeze > requirements_frozen_$(date +%Y%m%d).txt`
  - **Purpose**: Reproducible builds

- [ ] **Task**: Check for deprecated package warnings
  - **Status**: 🔴
  - **Command**: `python -Wd manage.py check`
  - **Warnings**: (list and document resolution plan)

#### 6.3. Python Version Verification

- [ ] **Task**: Test with Python 3.11
  - **Status**: 🔴
  - **Command**: `python3.11 --version && python3.11 -m venv test-3.11 && ...`
  - **Result**: Works ✓ / Errors ✗

- [ ] **Task**: Test with Python 3.12 (if available)
  - **Status**: 🔴
  - **Command**: `python3.12 --version && python3.12 -m venv test-3.12 && ...`
  - **Result**: Works ✓ / Errors ✗

- [ ] **Task**: Document minimum Python version
  - **Status**: 🔴
  - **Minimum**: 3.11 (Django 5.2 requirement)
  - **Recommended**: (specify)

#### 6.4. Commit Dependencies

- [ ] **Task**: Commit requirements.txt
  - **Status**: 🔴
  - **Commit Message**:
    ```
    deps: Update dependencies to MDCS v3.18.0
    
    - Django 2.2 → 5.2
    - Add django-allauth ~65.2.0
    - Update core MDCS apps to ~2.28.0
    - Python 3.11+ now required
    
    References: POTENTIAL_UPGRADE_CONFLICTS.md § 2
    ```

### Phase 6 Completion Checklist
- [ ] All packages install without errors
- [ ] Version conflicts resolved
- [ ] Python version requirements documented
- [ ] Dependencies frozen and committed
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 7: Template and Static File Migrations

**Estimated Duration**: 3-4 days  
**Status**: 🔴 Not Started  
**Dependencies**: Phase 6 complete  
**Assignee**: TBD

### Objectives
- Update modified templates to v3.18.0 base
- Apply Bootstrap 5 migrations
- Merge JavaScript changes
- Update CSS files

### Reference
See **POTENTIAL_UPGRADE_CONFLICTS.md § "core_main_app Conflicts"** and **"core_explore_common_app Conflicts"**

---

### 7.1. Modified Templates - Bootstrap 5 Migration

**Status**: 🔴 Not Started

#### 7.1.1. templates/theme.html
- [ ] **Task**: Compare versions
  - **Status**: 🔴
  - **Base**: `git show upstream/v2.21.0:templates/theme.html`
  - **Ours**: `git show main:templates/theme.html`
  - **Theirs**: `git show upstream/v3.18.0:templates/theme.html`

- [ ] **Task**: Identify NexusLIMS customizations
  - **Status**: 🔴
  - **Customizations**: (list here)

- [ ] **Task**: Update Bootstrap references
  - **Status**: 🔴
  - **Changes**:
    - Bootstrap 3/4 → Bootstrap 5 CDN links
    - jQuery removal (if applicable)

- [ ] **Task**: Test and commit
  - **Status**: 🔴

#### 7.1.2. templates/theme/menu.html
- [ ] **Task**: Merge menu changes
  - **Status**: 🔴
  - **NexusLIMS Custom**: Check for custom menu items

- [ ] **Task**: Update Bootstrap 5 syntax
  - **Status**: 🔴
  - **Changes**:
    - `data-toggle` → `data-bs-toggle`
    - `data-dismiss` → `data-bs-dismiss`

- [ ] **Task**: Test and commit
  - **Status**: 🔴

#### 7.1.3. templates/theme/footer/default.html
- [ ] **Task**: Merge footer customizations
  - **Status**: 🔴
  - **Check**: NexusLIMS branding, links

- [ ] **Task**: Test and commit
  - **Status**: 🔴

#### 7.1.4. templates/core_main_app/user/homepage.html
- [ ] **Task**: Merge homepage changes
  - **Status**: 🔴
  - **NexusLIMS Custom**: Check for custom tiles, layout

- [ ] **Task**: Update Bootstrap 5 grid system
  - **Status**: 🔴
  - **Check**: Column classes still valid

- [ ] **Task**: Test and commit
  - **Status**: 🔴

#### 7.1.5. templates/mdcs_home/tiles.html
- [ ] **Task**: Merge tile customizations
  - **Status**: 🔴
  - **Purpose**: Custom dashboard tiles

- [ ] **Task**: Test and commit
  - **Status**: 🔴

---

### 7.2. Modified CSS Files

**Status**: 🔴 Not Started

#### 7.2.1. static/core_main_app/css/homepage.css
- [ ] **Task**: Three-way merge
  - **Status**: 🔴
  - **NexusLIMS Custom**: (identify changes)

- [ ] **Task**: Update for Bootstrap 5
  - **Status**: 🔴
  - **Changes**: Review class name changes

- [ ] **Task**: Test and commit
  - **Status**: 🔴

#### 7.2.2. static/css/btn_custom.css
- [ ] **Task**: Merge button customizations
  - **Status**: 🔴

#### 7.2.3. static/css/extra.css
- [ ] **Task**: Merge extra styles
  - **Status**: 🔴

#### 7.2.4. static/css/main.css
- [ ] **Task**: Merge main stylesheet
  - **Status**: 🔴

#### 7.2.5. static/css/menu.css
- [ ] **Task**: Merge menu styles
  - **Status**: 🔴

---

### 7.3. Modified JavaScript - results.js

**Status**: 🔴 Not Started (CRITICAL)

#### 7.3.1. Analysis
- [ ] **Task**: Compare complete files
  - **Status**: 🔴
  - **Base**: `git show upstream/v1.21.0:core_explore_common_app/static/core_explore_common_app/user/js/results.js`
  - **Ours**: `git show main:results_override/static/core_explore_common_app/user/js/results.js`
  - **Theirs**: Check current core_explore_common_app version

- [ ] **Task**: Document upstream changes since v1.21.0
  - **Status**: 🔴
  - **File**: Create `results.js.CHANGES.md`
  - **Content**: List all upstream changes

- [ ] **Task**: Document NexusLIMS customizations
  - **Status**: 🔴
  - **Custom Features**:
    - Download system integration
    - Custom result formatting
    - (list others)

#### 7.3.2. Merge Strategy
- [ ] **Task**: Start with latest upstream results.js
  - **Status**: 🔴
  - **Source**: Current core_explore_common_app package

- [ ] **Task**: Apply NexusLIMS download system
  - **Status**: 🔴
  - **Functions**: Identify download-related functions
  - **Integration**: Ensure compatibility with new upstream code

- [ ] **Task**: Apply NexusLIMS formatting customizations
  - **Status**: 🔴
  - **Check**: Result card formatting, data display

- [ ] **Task**: Update jQuery to vanilla JavaScript (if needed)
  - **Status**: 🔴
  - **Reason**: Bootstrap 5 no longer requires jQuery
  - **Pattern**: `$(el)` → `document.querySelector(el)`

#### 7.3.3. Testing
- [ ] **Task**: Test search functionality
  - **Status**: 🔴
  - **Actions**:
    - Perform keyword search
    - Check results display
    - Verify pagination works

- [ ] **Task**: Test download system
  - **Status**: 🔴
  - **Actions**:
    - Download single file
    - Download multiple files as ZIP
    - Test "Download All" functionality

- [ ] **Task**: Browser console check
  - **Status**: 🔴
  - **Check**: No JavaScript errors
  - **Browsers**: Chrome, Firefox, Safari

- [ ] **Task**: Commit results.js
  - **Status**: 🔴
  - **Commit Message**:
    ```
    feat: Merge NexusLIMS results.js with upstream updates
    
    - Integrated latest core_explore_common_app changes
    - Preserved NexusLIMS download system
    - Updated to vanilla JavaScript (Bootstrap 5 compat)
    
    References: POTENTIAL_UPGRADE_CONFLICTS.md § core_explore_common_app
    ```

---

### 7.4. Collect and Test Static Files

- [ ] **Task**: Collect all static files
  - **Status**: 🔴
  - **Command**: `python manage.py collectstatic --noinput`
  - **Result**: Success ✓ / Errors ✗

- [ ] **Task**: Verify static files served correctly
  - **Status**: 🔴
  - **Test**: Load homepage, check browser Network tab
  - **Check**: All CSS, JS, images load (200 status)

- [ ] **Task**: Test in multiple browsers
  - **Status**: 🔴
  - **Browsers**:
    - [ ] Chrome
    - [ ] Firefox
    - [ ] Safari
    - [ ] Edge (if available)

### Phase 7 Completion Checklist
- [ ] All templates updated to Bootstrap 5
- [ ] All CSS files merged and tested
- [ ] results.js merged and functional
- [ ] Static files collected and served
- [ ] No browser console errors
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 8: Database Migrations

**Estimated Duration**: 1-2 days  
**Status**: 🔴 Not Started  
**Dependencies**: Phase 7 complete  
**Assignee**: TBD

### Objectives
- Run all Django migrations safely
- Verify data integrity
- Create rollback snapshots

### Tasks

#### 8.1. Pre-Migration Backup

- [ ] **Task**: Create database backup
  - **Status**: 🔴
  - **Command**: (depends on DB type)
    - SQLite: `cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)`
    - PostgreSQL: `pg_dump ... > backup_$(date +%Y%m%d_%H%M%S).sql`
  - **Location**: (specify backup path)
  - **Verification**: Backup file exists and is non-empty

- [ ] **Task**: Export data as JSON fixtures
  - **Status**: 🔴
  - **Command**: `python manage.py dumpdata > data_backup_$(date +%Y%m%d).json`
  - **Purpose**: Human-readable backup

- [ ] **Task**: Document current migration state
  - **Status**: 🔴
  - **Command**: `python manage.py showmigrations > migrations_before.txt`

#### 8.2. Check Migration Plan

- [ ] **Task**: Generate migration plan
  - **Status**: 🔴
  - **Command**: `python manage.py migrate --plan`
  - **Review**: (paste output, review for issues)

- [ ] **Task**: Identify potential conflicts
  - **Status**: 🔴
  - **Look for**: Unapplied migrations, missing dependencies
  - **Conflicts**: (document here)

#### 8.3. Run Migrations

- [ ] **Task**: Run fake migrations for pre-existing apps (if needed)
  - **Status**: 🔴
  - **Purpose**: Mark old migrations as applied if DB already up-to-date
  - **Command**: `python manage.py migrate --fake-initial` (use carefully!)

- [ ] **Task**: Run all migrations
  - **Status**: 🔴
  - **Command**: `python manage.py migrate`
  - **Output**: (document success/failures)

- [ ] **Task**: Handle migration errors
  - **Status**: 🔴
  - **If errors occur**:
    - Document error message
    - Identify conflicting migration
    - Resolve (may need to fake, edit, or rollback)

#### 8.4. Post-Migration Verification

- [ ] **Task**: Verify migration state
  - **Status**: 🔴
  - **Command**: `python manage.py showmigrations > migrations_after.txt`
  - **Check**: All migrations marked as `[X]`

- [ ] **Task**: Test database queries
  - **Status**: 🔴
  - **Actions**:
    - Open Django shell: `python manage.py shell`
    - Query users: `from django.contrib.auth.models import User; User.objects.all()`
    - Query templates: (import and query template models)
    - Query data: (check records)

- [ ] **Task**: Check for orphaned tables
  - **Status**: 🔴
  - **Command**: `python manage.py inspectdb` (review for unexpected tables)

- [ ] **Task**: Run data integrity checks
  - **Status**: 🔴
  - **Custom Checks**: (any NexusLIMS-specific data validation)

#### 8.5. Create Post-Migration Snapshot

- [ ] **Task**: Create clean migration snapshot
  - **Status**: 🔴
  - **Command**: `cp db.sqlite3 db.sqlite3.migrated_clean`
  - **Purpose**: Baseline for testing

- [ ] **Task**: Commit migration files (if any generated)
  - **Status**: 🔴
  - **Check**: Any new migration files in app directories?
  - **Commit**: If yes, commit with message

### Phase 8 Completion Checklist
- [ ] All migrations applied successfully
- [ ] Database backup created and verified
- [ ] Data integrity verified
- [ ] No orphaned tables or data
- [ ] Migration state documented
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 9: Comprehensive Testing

**Estimated Duration**: 5-7 days  
**Status**: 🔴 Not Started  
**Dependencies**: Phase 8 complete  
**Assignee**: TBD

### Objectives
- Execute full test suite
- Perform manual functional testing
- Load/performance testing
- Browser compatibility testing

### Reference
See **CHANGES_FROM_MDCS_2.21.0.md § "Appendix E: Testing Checklist Details"**

---

### 9.1. Basic Functionality Tests

**Status**: 🔴 Not Started

- [ ] **Test**: Server starts without errors
  - **Status**: 🔴
  - **Command**: `python manage.py runserver 8001`
  - **Result**: Starts cleanly ✓ / Errors ✗
  - **Console Output**: (note warnings)

- [ ] **Test**: Homepage loads
  - **Status**: 🔴
  - **URL**: `http://localhost:8001/`
  - **Result**: Loads ✓ / 500 Error ✗
  - **Check**: No console errors in browser

- [ ] **Test**: Admin interface accessible
  - **Status**: 🔴
  - **URL**: `http://localhost:8001/djadmin/` (note new prefix!)
  - **Login**: Test admin credentials
  - **Result**: Loads ✓ / Errors ✗

- [ ] **Test**: User login works
  - **Status**: 🔴
  - **URL**: `http://localhost:8001/login`
  - **Result**: Can log in ✓ / Errors ✗

- [ ] **Test**: User logout works
  - **Status**: 🔴
  - **Action**: Click logout
  - **Result**: Redirects correctly ✓ / Errors ✗

- [ ] **Test**: Template upload (admin)
  - **Status**: 🔴
  - **Action**: Upload XSD template via admin
  - **Template**: Use test XSD (e.g., simple schema)
  - **Result**: Upload succeeds ✓ / Errors ✗

- [ ] **Test**: Workspace creation (admin)
  - **Status**: 🔴
  - **Action**: Create test workspace
  - **Result**: Workspace created ✓ / Errors ✗

---

### 9.2. Search Functionality Tests

**Status**: 🔴 Not Started

- [ ] **Test**: Keyword search page loads
  - **Status**: 🔴
  - **URL**: `http://localhost:8001/explore/keyword`
  - **Result**: Loads ✓ / Errors ✗

- [ ] **Test**: Basic keyword search works
  - **Status**: 🔴
  - **Query**: (choose test keyword)
  - **Expected Results**: (specify)
  - **Actual Results**: 
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Search results table displays
  - **Status**: 🔴
  - **Check**: Table renders using `list_stylesheet.xsl`
  - **Columns**: Verify expected columns present
  - **Result**: Displays correctly ✓ / Errors ✗

- [ ] **Test**: Pagination works
  - **Status**: 🔴
  - **Action**: Navigate to page 2, 3, etc.
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Sorting works
  - **Status**: 🔴
  - **Action**: Click column headers to sort
  - **Result**: Sorts correctly ✓ / Errors ✗

- [ ] **Test**: Filtering works
  - **Status**: 🔴
  - **Action**: Use DataTables filter box
  - **Result**: Filters correctly ✓ / Errors ✗

- [ ] **Test**: Advanced search page loads
  - **Status**: 🔴
  - **URL**: (check for advanced search link)
  - **Result**: Loads ✓ / N/A if not implemented

- [ ] **Test**: Search with 100+ results
  - **Status**: 🔴
  - **Purpose**: Load testing
  - **Result**: Loads in <2s ✓ / Slow ✗

---

### 9.3. Record Detail View Tests

**Status**: 🔴 Not Started

- [ ] **Test**: Detail page loads
  - **Status**: 🔴
  - **Action**: Click on search result to view detail
  - **Result**: Loads ✓ / Errors ✗

- [ ] **Test**: XSLT transformation renders correctly
  - **Status**: 🔴
  - **Check**: `detail_stylesheet.xsl` applied correctly
  - **Visual**: Matches expected layout
  - **Result**: Renders correctly ✓ / Errors ✗

- [ ] **Test**: Metadata displays correctly
  - **Status**: 🔴
  - **Fields to check**:
    - [ ] Instrument name
    - [ ] Experimenter
    - [ ] Session information
    - [ ] Acquisition activities
    - [ ] File listings
  - **Result**: All present ✓ / Missing fields ✗

- [ ] **Test**: Images/previews display
  - **Status**: 🔴
  - **Check**: Thumbnail images load
  - **Result**: Display ✓ / Broken images ✗

- [ ] **Test**: "View Raw" button works
  - **Status**: 🔴
  - **Action**: Click "View Raw" button
  - **Expected**: Opens XML in new tab/window
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Download buttons present
  - **Status**: 🔴
  - **Buttons to check**:
    - [ ] Download individual files
    - [ ] Download ZIP of all files
    - [ ] (others as applicable)
  - **Result**: Present ✓ / Missing ✗

- [ ] **Test**: Links to SharePoint/NEMO work (if applicable)
  - **Status**: 🔴
  - **Check**: Links use correct URLs from XSLT params or data attributes
  - **Result**: Correct URLs ✓ / Broken ✗

- [ ] **Test**: Color coding by instrument works
  - **Status**: 🔴
  - **Check**: Instrument names have correct color highlighting
  - **Source**: XSLT `instrument-colors` variable
  - **Result**: Colors applied ✓ / Not working ✗

---

### 9.4. Download System Tests (CRITICAL)

**Status**: 🔴 Not Started

- [ ] **Test**: Single file download
  - **Status**: 🔴
  - **Action**: Click download button for single file
  - **Result**: File downloads ✓ / Errors ✗

- [ ] **Test**: Multiple file download (ZIP)
  - **Status**: 🔴
  - **Action**: Select multiple files, download as ZIP
  - **Result**: ZIP downloads ✓ / Errors ✗

- [ ] **Test**: ZIP file contents
  - **Status**: 🔴
  - **Action**: Extract downloaded ZIP
  - **Check**: All selected files present
  - **Result**: Correct ✓ / Files missing ✗

- [ ] **Test**: Large file download (>100MB)
  - **Status**: 🔴
  - **Action**: Download large file
  - **Result**: Completes ✓ / Timeout/Errors ✗

- [ ] **Test**: StreamSaver.js for large downloads
  - **Status**: 🔴
  - **Purpose**: Verify streaming download works
  - **Check**: Browser memory doesn't spike
  - **Result**: Streams ✓ / Loads to memory ✗

- [ ] **Test**: Download progress indicator
  - **Status**: 🔴
  - **Check**: Progress bar or indicator displays
  - **Result**: Shows progress ✓ / No feedback ✗

- [ ] **Test**: Download error handling
  - **Status**: 🔴
  - **Scenario**: Attempt to download non-existent file
  - **Expected**: Error message displayed
  - **Result**: Graceful error ✓ / Crash ✗

- [ ] **Test**: "Download All" functionality
  - **Status**: 🔴
  - **Action**: Click "Download All" on record detail page
  - **Expected**: ZIP with all record files
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: File download from search results
  - **Status**: 🔴
  - **Action**: Download from search results table (if feature exists)
  - **Result**: Works ✓ / N/A ✗

---

### 9.5. XSLT Parameter System Tests (if Option A chosen)

**Status**: 🔴 Not Started (skip if Option B chosen)

- [ ] **Test**: Custom `xsl_transform` function works
  - **Status**: 🔴
  - **Check**: `mdcs_home.utils.xml.xsl_transform` is called
  - **Method**: Add debug logging, check logs

- [ ] **Test**: Parameters passed to XSLT
  - **Status**: 🔴
  - **Check**: View page source, verify parameters embedded
  - **Parameters**: `record_url`, `cdcs_url`, `api_url`
  - **Result**: Present ✓ / Missing ✗

- [ ] **Test**: Template tag resolution
  - **Status**: 🔴
  - **Check**: `{% xsl_transform %}` tag resolves to custom version
  - **Method**: Template debug mode, check which tag loads
  - **Result**: Custom tag ✓ / Core tag (wrong) ✗

- [ ] **Test**: `results_override` app loaded first
  - **Status**: 🔴
  - **Check**: `INSTALLED_APPS` order in settings
  - **Verification**: `results_override` before `core_main_app`
  - **Result**: Correct order ✓ / Wrong order ✗

- [ ] **Test**: Static file override works
  - **Status**: 🔴
  - **File**: `results_override/static/core_explore_common_app/user/js/results.js`
  - **Check**: Overrides core app version
  - **Method**: Add console.log, check browser console
  - **Result**: Override works ✓ / Core version loaded ✗

---

### 9.6. Navigation and Menu Tests

**Status**: 🔴 Not Started

- [ ] **Test**: Main navigation menu displays
  - **Status**: 🔴
  - **Check**: All menu items present
  - **Result**: Displays ✓ / Errors ✗

- [ ] **Test**: Custom menu items work
  - **Status**: 🔴
  - **File**: `static/js/menu_custom.js`
  - **Check**: NexusLIMS-specific menu behavior
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Responsive menu (mobile)
  - **Status**: 🔴
  - **Action**: Resize browser to mobile width
  - **Check**: Hamburger menu appears and works
  - **Result**: Works ✓ / Broken ✗

- [ ] **Test**: Breadcrumb navigation
  - **Status**: 🔴
  - **Check**: Breadcrumbs display on detail pages
  - **Result**: Present ✓ / Missing ✗

---

### 9.7. Tutorial System Tests (if implemented)

**Status**: 🔴 Not Started

- [ ] **Test**: Shepherd.js tutorial loads
  - **Status**: 🔴
  - **Library**: `static/libs/shepherd.js/a374a73/`
  - **Check**: Tutorial overlay appears
  - **Result**: Loads ✓ / N/A ✗

- [ ] **Test**: Tutorial steps advance
  - **Status**: 🔴
  - **Action**: Click "Next" through tutorial
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Tutorial can be dismissed
  - **Status**: 🔴
  - **Action**: Click "Skip" or close button
  - **Result**: Closes ✓ / Errors ✗

---

### 9.8. Styling Tests

**Status**: 🔴 Not Started

- [ ] **Test**: Homepage styling correct
  - **Status**: 🔴
  - **File**: `static/core_main_app/css/homepage.css`
  - **Check**: Tiles, layout match expected design
  - **Result**: Correct ✓ / Layout issues ✗

- [ ] **Test**: Button styling correct
  - **Status**: 🔴
  - **File**: `static/css/btn_custom.css`
  - **Check**: Custom buttons display properly
  - **Result**: Correct ✓ / Issues ✗

- [ ] **Test**: No CSS conflicts
  - **Status**: 🔴
  - **Check**: Browser dev tools for overridden styles
  - **Result**: No conflicts ✓ / Conflicts ✗

- [ ] **Test**: Dark mode (if implemented)
  - **Status**: 🔴
  - **Check**: Dark mode toggle works
  - **Result**: Works ✓ / N/A ✗

- [ ] **Test**: Print stylesheet (if applicable)
  - **Status**: 🔴
  - **Action**: Print preview a record detail page
  - **Result**: Formats correctly ✓ / Broken ✗

---

### 9.9. Admin/Backend Tests

**Status**: 🔴 Not Started

- [ ] **Test**: Django admin dashboard loads
  - **Status**: 🔴
  - **URL**: `/djadmin/`
  - **Result**: Loads ✓ / Errors ✗

- [ ] **Test**: User management works
  - **Status**: 🔴
  - **Actions**: Create, edit, delete users
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Template management works
  - **Status**: 🔴
  - **Actions**: Upload, edit, delete templates
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Workspace management works
  - **Status**: 🔴
  - **Actions**: Create, edit, delete workspaces
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Data record management
  - **Status**: 🔴
  - **Actions**: View, edit, delete records via admin
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Celery tasks (if used)
  - **Status**: 🔴
  - **Check**: Celery beat schedule, task execution
  - **Result**: Works ✓ / N/A ✗

---

### 9.10. Performance Tests

**Status**: 🔴 Not Started

- [ ] **Test**: Homepage load time
  - **Status**: 🔴
  - **Target**: <1s
  - **Actual**: 
  - **Result**: Pass ✓ / Fail ✗

- [ ] **Test**: Search results load time (100 records)
  - **Status**: 🔴
  - **Target**: <2s
  - **Actual**: 
  - **Result**: Pass ✓ / Fail ✗

- [ ] **Test**: Detail page load time
  - **Status**: 🔴
  - **Target**: <1s
  - **Actual**: 
  - **Result**: Pass ✓ / Fail ✗

- [ ] **Test**: Static file loading
  - **Status**: 🔴
  - **Check**: Network tab, time to load all assets
  - **Target**: <3s total
  - **Actual**: 
  - **Result**: Pass ✓ / Fail ✗

- [ ] **Test**: Large ZIP download time (50 files, ~500MB)
  - **Status**: 🔴
  - **Target**: <30s
  - **Actual**: 
  - **Result**: Pass ✓ / Fail ✗

- [ ] **Test**: Concurrent users (if possible)
  - **Status**: 🔴
  - **Tool**: Apache Bench, Locust, or similar
  - **Scenario**: 10 concurrent users searching
  - **Result**: Handles load ✓ / Errors ✗

---

### 9.11. Browser Compatibility Tests

**Status**: 🔴 Not Started

#### Chrome
- [ ] **Test**: All functionality in Chrome
  - **Status**: 🔴
  - **Version**: 
  - **Result**: Works ✓ / Issues ✗
  - **Issues**: (list any)

#### Firefox
- [ ] **Test**: All functionality in Firefox
  - **Status**: 🔴
  - **Version**: 
  - **Result**: Works ✓ / Issues ✗
  - **Issues**: (list any)

#### Safari
- [ ] **Test**: All functionality in Safari
  - **Status**: 🔴
  - **Version**: 
  - **Result**: Works ✓ / Issues ✗
  - **Issues**: (list any)

#### Edge
- [ ] **Test**: All functionality in Edge (if available)
  - **Status**: 🔴
  - **Version**: 
  - **Result**: Works ✓ / Issues ✗
  - **Issues**: (list any)

---

### 9.12. Regression Tests

**Status**: 🔴 Not Started

- [ ] **Test**: All Python unit tests pass
  - **Status**: 🔴
  - **Command**: `python manage.py test`
  - **Result**: All pass ✓ / Failures ✗
  - **Failures**: (document if any)

- [ ] **Test**: Known issues from previous version resolved
  - **Status**: 🔴
  - **Issues**: (list any known bugs from v2.21.0)
  - **Result**: Resolved ✓ / Still present ✗

- [ ] **Test**: No new regressions introduced
  - **Status**: 🔴
  - **Check**: Features that worked in v2.21.0 still work
  - **Result**: No regressions ✓ / New issues ✗

---

### 9.13. Security Tests

**Status**: 🔴 Not Started

- [ ] **Test**: CSRF protection works
  - **Status**: 🔴
  - **Method**: Submit form without CSRF token
  - **Expected**: Rejected
  - **Result**: Protected ✓ / Vulnerable ✗

- [ ] **Test**: XSS protection
  - **Status**: 🔴
  - **Method**: Attempt to inject script in search
  - **Expected**: Sanitized
  - **Result**: Protected ✓ / Vulnerable ✗

- [ ] **Test**: Authentication required for protected pages
  - **Status**: 🔴
  - **Method**: Access admin pages while logged out
  - **Expected**: Redirect to login
  - **Result**: Protected ✓ / Accessible ✗

- [ ] **Test**: SQL injection protection
  - **Status**: 🔴
  - **Method**: Django ORM should prevent this by default
  - **Check**: No raw SQL queries with user input
  - **Result**: Protected ✓ / Vulnerable ✗

---

### Phase 9 Completion Checklist
- [ ] All basic functionality tests pass
- [ ] Search and display tests pass
- [ ] Download system fully functional
- [ ] Performance meets targets
- [ ] Cross-browser compatibility verified
- [ ] No security vulnerabilities introduced
- [ ] All test results documented
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 10: Docker Development Environment Setup

**Estimated Duration**: 1-2 days  
**Status**: 🔴 Not Started  
**Dependencies**: Phase 9 complete  
**Assignee**: TBD

### Objectives
- Create Docker-based development environment for NexusLIMS-CDCS
- Mirror the structure from `cdcs-docker/dev`
- Enable live code editing with auto-reload
- Document development workflow

### Reference
Pattern based on: `/Users/josh/git_repos/datasophos/cdcs/cdcs-docker/dev`

### Tasks

#### 10.1. Directory Structure Setup

- [ ] **Task**: Create Docker environment directory
  - **Status**: 🔴
  - **Command**: `mkdir -p ../nexuslims-cdcs-docker/dev`
  - **Note**: Create alongside NexusLIMS-CDCS repo, not inside it

- [ ] **Task**: Create subdirectories
  - **Status**: 🔴
  - **Directories**:
    - [ ] `caddy/` - Caddy reverse proxy config
    - [ ] `nexuslims-cdcs/` - Django settings overrides
    - [ ] `mongo/` - MongoDB configuration
    - [ ] `saml2/` - SAML configuration (if needed)
    - [ ] `handle/` - Handle server config (if needed)
    - [ ] `extra/` - Extra environment variables

#### 10.2. Docker Compose Files

- [ ] **Task**: Create `docker-compose.yml`
  - **Status**: 🔴
  - **Source**: Adapt from `cdcs-docker/dev/docker-compose.yml`
  - **Changes**:
    - Replace `PROJECT_NAME=mdcs` with `PROJECT_NAME=nexuslims_cdcs`
    - Update image name to NexusLIMS-CDCS image
    - Adjust volume paths for NexusLIMS-CDCS

- [ ] **Task**: Create `docker-compose.dev.yml`
  - **Status**: 🔴
  - **Source**: Adapt from `cdcs-docker/dev/docker-compose.dev.yml`
  - **Key Features**:
    - Mount local NexusLIMS-CDCS source code
    - Use Django runserver with auto-reload
    - Enable DEBUG mode
    - Override with dev_settings.py

- [ ] **Task**: Create MongoDB docker-compose
  - **Status**: 🔴
  - **File**: `mongo/docker-compose.yml`
  - **Source**: Copy from `cdcs-docker/dev/mongo/docker-compose.yml`

#### 10.3. Environment Configuration

- [ ] **Task**: Create `.env` file
  - **Status**: 🔴
  - **Source**: Adapt from `cdcs-docker/dev/.env`
  - **Key Settings**:
    ```bash
    COMPOSE_FILE=docker-compose.yml:mongo/docker-compose.yml
    COMPOSE_PROJECT_NAME=nexuslims-dev
    PROJECT_NAME=nexuslims_cdcs
    IMAGE_NAME=nexuslims-cdcs
    IMAGE_VERSION=3.18.0
    HOSTNAME=nexuslims.localhost
    SERVER_URI=https://nexuslims.localhost
    ALLOWED_HOSTS=nexuslims.localhost
    CSRF_TRUSTED_ORIGINS=https://nexuslims.localhost
    SERVER_NAME=NexusLIMS-CDCS
    WEB_SERVER=gunicorn
    SETTINGS=dev_settings
    # Database credentials
    MONGO_ADMIN_USER=admin
    MONGO_ADMIN_PASS=admin
    MONGO_USER=nexuslims
    MONGO_PASS=nexuslims
    MONGO_DB=nexuslims
    POSTGRES_DB=nexuslims
    POSTGRES_USER=nexuslims
    POSTGRES_PASS=nexuslims
    REDIS_PASS=nexuslims
    # Versions
    MONGO_VERSION=8.0
    REDIS_VERSION=8
    POSTGRES_VERSION=17
    CADDY_VERSION=2
    ```

- [ ] **Task**: Create `.env.dev` file (optional)
  - **Status**: 🔴
  - **Purpose**: Development-specific overrides

#### 10.4. Caddy Configuration

- [ ] **Task**: Create `caddy/Caddyfile`
  - **Status**: 🔴
  - **Source**: Adapt from `cdcs-docker/dev/caddy/Caddyfile`
  - **Content**:
    ```
    nexuslims.localhost {
        reverse_proxy cdcs:8000
        file_server /static/* {
            root /srv/nexuslims_static
        }
        encode gzip
    }
    ```

#### 10.5. Django Settings Override

- [ ] **Task**: Create `nexuslims-cdcs/dev_settings.py`
  - **Status**: 🔴
  - **Source**: Adapt from `cdcs-docker/dev/cdcs/dev_settings.py`
  - **Key Settings**:
    ```python
    from nexuslims_cdcs.settings import *
    
    DEBUG = True
    ALLOWED_HOSTS = ['nexuslims.localhost', 'localhost', '127.0.0.1']
    CSRF_TRUSTED_ORIGINS = ['https://nexuslims.localhost']
    
    # Disable template caching for development
    for template_engine in TEMPLATES:
        template_engine['OPTIONS']['debug'] = True
        if 'loaders' in template_engine['OPTIONS']:
            del template_engine['OPTIONS']['loaders']
    
    # Enable verbose logging
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }
    ```

#### 10.6. Utility Scripts

- [ ] **Task**: Create `dev-commands.sh`
  - **Status**: 🔴
  - **Source**: Adapt from `cdcs-docker/dev/dev-commands.sh`
  - **Commands**:
    - `dev-up` - Start environment
    - `dev-down` - Stop environment
    - `dev-logs` - View logs
    - `dev-logs-app` - View app logs only
    - `dev-restart` - Restart app
    - `dev-shell` - Container shell
    - `dev-manage` - Django management commands

- [ ] **Task**: Create migration scripts
  - **Status**: 🔴
  - **Scripts**:
    - [ ] `docker_migrate.sh`
    - [ ] `docker_createsuperuser.sh`
    - [ ] `docker_loadmodules.sh` (if applicable)
    - [ ] `docker_loadexporters.sh` (if applicable)

#### 10.7. Documentation

- [ ] **Task**: Create `README.md`
  - **Status**: 🔴
  - **Content**: Document NexusLIMS-CDCS dev environment
  - **Include**:
    - Prerequisites
    - Quick start
    - Architecture diagram
    - Common workflows
    - Troubleshooting

- [ ] **Task**: Create `QUICKSTART.md`
  - **Status**: 🔴
  - **Content**: Quick reference for common tasks

- [ ] **Task**: Create `LIVE-RELOAD.md` (optional)
  - **Status**: 🔴
  - **Content**: Document live reload development workflow

#### 10.8. Initial Testing

- [ ] **Task**: Build or pull NexusLIMS-CDCS Docker image
  - **Status**: 🔴
  - **Command**: `docker build -t nexuslims-cdcs:3.18.0 ../NexusLIMS-CDCS/`
  - **Or**: Use pre-built image if available

- [ ] **Task**: Start development environment
  - **Status**: 🔴
  - **Command**: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
  - **Result**: All containers start ✓ / Errors ✗

- [ ] **Test**: Access https://nexuslims.localhost
  - **Status**: 🔴
  - **Action**: Open browser, accept self-signed cert
  - **Result**: Site loads ✓ / Errors ✗

- [ ] **Test**: Verify code mounting works
  - **Status**: 🔴
  - **Action**: Edit a file in NexusLIMS-CDCS repo
  - **Expected**: Django runserver detects change and reloads
  - **Check**: `docker logs -f nexuslims-dev_cdcs` shows reload message

- [ ] **Test**: Run migrations
  - **Status**: 🔴
  - **Command**: `source dev-commands.sh && dev-manage migrate`
  - **Result**: Migrations apply ✓ / Errors ✗

- [ ] **Test**: Create superuser
  - **Status**: 🔴
  - **Command**: `dev-manage createsuperuser`
  - **Result**: User created ✓ / Errors ✗

- [ ] **Test**: Login and basic functionality
  - **Status**: 🔴
  - **Actions**:
    - [ ] Login to admin
    - [ ] Upload test template
    - [ ] Create test record
    - [ ] View record detail
  - **Result**: All work ✓ / Issues ✗

#### 10.9. Performance Verification

- [ ] **Test**: Auto-reload speed
  - **Status**: 🔴
  - **Action**: Make code change, measure reload time
  - **Target**: <3 seconds
  - **Actual**: _____ seconds

- [ ] **Test**: Page load times
  - **Status**: 🔴
  - **Check**: Homepage, search, detail pages load quickly
  - **Note**: May be slower than production due to DEBUG mode

#### 10.10. Developer Workflow Documentation

- [ ] **Task**: Document complete development workflow
  - **Status**: 🔴
  - **File**: `nexuslims-cdcs-docker/dev/WORKFLOW.md`
  - **Content**:
    - Starting the environment
    - Making code changes
    - Running tests
    - Viewing logs
    - Database management
    - Troubleshooting

### Phase 10 Completion Checklist
- [ ] Docker environment fully configured
- [ ] All containers start successfully
- [ ] Application accessible at https://nexuslims.localhost
- [ ] Live code editing works with auto-reload
- [ ] All utility scripts functional
- [ ] Documentation complete
- [ ] Developer workflow tested and documented
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 11: Staging/Production Deployment (FUTURE)

**Estimated Duration**: 2-3 days  
**Status**: ⚪ Skipped  
**Dependencies**: Phase 10 complete  
**Assignee**: TBD

**Note**: ⚠️ **This phase is for future reference** when you're ready to deploy to staging/production. Since no production instance exists yet, this entire phase can be skipped for now. The upgrade is complete after Phase 10 (Docker dev environment).

### Objectives
- Deploy to staging/production environment
- Perform final validation in production-like environment
- Document deployment process

### Tasks

#### 10.1. Staging Environment Preparation

- [ ] **Task**: Provision staging server (if not exists)
  - **Status**: 🔴
  - **Server**: (specify host/IP)
  - **OS**: (specify)
  - **Python Version**: 3.11+

- [ ] **Task**: Clone production database to staging
  - **Status**: 🔴
  - **Method**: (specify backup/restore process)
  - **Verification**: Row counts match production

- [ ] **Task**: Set up environment variables
  - **Status**: 🔴
  - **File**: `.env` or system environment
  - **Variables**: (reference Appendix B in POTENTIAL_UPGRADE_CONFLICTS.md)

- [ ] **Task**: Configure web server
  - **Status**: 🔴
  - **Server**: Nginx / Apache / (specify)
  - **Config**: Update for Django 5.2, new static file paths

- [ ] **Task**: Configure WSGI/ASGI server
  - **Status**: 🔴
  - **Server**: Gunicorn / uWSGI / (specify)
  - **Workers**: (specify count)

#### 10.2. Deployment

- [ ] **Task**: Push code to staging server
  - **Status**: 🔴
  - **Method**: Git pull, rsync, etc.
  - **Branch**: `upgrade/v3.18.0-working`

- [ ] **Task**: Install dependencies
  - **Status**: 🔴
  - **Command**: `pip install -r requirements.txt`
  - **Virtual Env**: (specify path)

- [ ] **Task**: Collect static files
  - **Status**: 🔴
  - **Command**: `python manage.py collectstatic --noinput`
  - **Path**: (specify STATIC_ROOT)

- [ ] **Task**: Run database migrations
  - **Status**: 🔴
  - **Command**: `python manage.py migrate`
  - **Backup**: Ensure DB backup taken first

- [ ] **Task**: Restart web services
  - **Status**: 🔴
  - **Commands**: 
    - Restart WSGI server
    - Restart web server
    - Restart Celery (if used)

#### 10.3. Staging Validation

- [ ] **Test**: Staging site loads
  - **Status**: 🔴
  - **URL**: (specify staging URL)
  - **Result**: Loads ✓ / Errors ✗

- [ ] **Test**: Login with production credentials
  - **Status**: 🔴
  - **Result**: Works ✓ / Errors ✗

- [ ] **Test**: Production data visible
  - **Status**: 🔴
  - **Check**: Known records display correctly
  - **Result**: Displays ✓ / Missing ✗

- [ ] **Test**: HTTPS/SSL working (if applicable)
  - **Status**: 🔴
  - **Result**: Valid cert ✓ / Errors ✗

- [ ] **Test**: Repeat critical Phase 9 tests
  - **Status**: 🔴
  - **Tests**: Search, detail view, downloads
  - **Result**: All pass ✓ / Failures ✗

#### 10.4. Stakeholder Review

- [ ] **Task**: Invite stakeholders to test staging
  - **Status**: 🔴
  - **Stakeholders**: (list)
  - **Invitation Sent**: Date: _______

- [ ] **Task**: Collect feedback
  - **Status**: 🔴
  - **Method**: Survey, email, meetings
  - **Feedback**: (document here)

- [ ] **Task**: Address critical feedback
  - **Status**: 🔴
  - **Issues**: (list)
  - **Resolutions**: (document)

#### 10.5. Performance Monitoring

- [ ] **Task**: Set up performance monitoring (if not exists)
  - **Status**: 🔴
  - **Tool**: New Relic, Datadog, Sentry, etc.
  - **Metrics**: Response time, error rate, DB queries

- [ ] **Task**: Establish baseline metrics
  - **Status**: 🔴
  - **Avg Response Time**: 
  - **Error Rate**: 
  - **DB Query Time**: 

- [ ] **Task**: Compare to production metrics
  - **Status**: 🔴
  - **Result**: Comparable ✓ / Degradation ✗

### Phase 10 Completion Checklist
- [ ] Staging deployment successful
- [ ] All critical tests pass in staging
- [ ] Stakeholder approval received
- [ ] Performance acceptable
- [ ] Deployment process documented
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Phase 12: Production Deployment (FUTURE)

**Estimated Duration**: 1 day (actual deployment) + monitoring period  
**Status**: ⚪ Skipped  
**Dependencies**: Phase 11 complete, stakeholder approval  
**Assignee**: TBD

**Note**: ⚠️ **This phase is for future reference** when you have a production instance to deploy to. Skip for now.

### Objectives
- Deploy to production with minimal downtime
- Monitor for issues
- Execute rollback if needed

### Tasks

#### 11.1. Pre-Deployment

- [ ] **Task**: Schedule maintenance window
  - **Status**: 🔴
  - **Date/Time**: 
  - **Duration**: 
  - **Communicated**: ✓ / ✗

- [ ] **Task**: Create production database backup
  - **Status**: 🔴
  - **Backup Path**: 
  - **Verification**: Backup complete and verified
  - **Offsite Copy**: ✓ / ✗

- [ ] **Task**: Create code backup
  - **Status**: 🔴
  - **Method**: Git tag, tar.gz, etc.
  - **Tag**: `nexuslims-cdcs-v2.21.0-final`

- [ ] **Task**: Prepare rollback scripts
  - **Status**: 🔴
  - **Scripts**: (document commands for rollback)

- [ ] **Task**: Final review of deployment checklist
  - **Status**: 🔴
  - **Reviewers**: (list)
  - **Approved**: ✓ / ✗

#### 11.2. Deployment Execution

- [ ] **Task**: Put site in maintenance mode
  - **Status**: 🔴
  - **Method**: (maintenance page, HTTP 503, etc.)
  - **Time**: _______

- [ ] **Task**: Backup current production database (final)
  - **Status**: 🔴
  - **Time**: _______
  - **Backup**: (path)

- [ ] **Task**: Pull new code to production server
  - **Status**: 🔴
  - **Branch**: `upgrade/v3.18.0-working` or merge to `main` first
  - **Commit**: (SHA)
  - **Time**: _______

- [ ] **Task**: Install dependencies
  - **Status**: 🔴
  - **Command**: `pip install -r requirements.txt`
  - **Time**: _______

- [ ] **Task**: Collect static files
  - **Status**: 🔴
  - **Command**: `python manage.py collectstatic --noinput`
  - **Time**: _______

- [ ] **Task**: Run database migrations
  - **Status**: 🔴
  - **Command**: `python manage.py migrate`
  - **Time**: _______
  - **Result**: Success ✓ / Errors ✗

- [ ] **Task**: Restart services
  - **Status**: 🔴
  - **Services**:
    - [ ] WSGI server
    - [ ] Web server
    - [ ] Celery (if used)
  - **Time**: _______

- [ ] **Task**: Remove maintenance mode
  - **Status**: 🔴
  - **Time**: _______

- [ ] **Task**: Verify site is up
  - **Status**: 🔴
  - **URL**: (production URL)
  - **Result**: Loads ✓ / Down ✗
  - **Time**: _______

#### 11.3. Post-Deployment Validation

- [ ] **Test**: Homepage loads
  - **Status**: 🔴
  - **Result**: ✓ / ✗
  - **Time**: _______

- [ ] **Test**: User login works
  - **Status**: 🔴
  - **Result**: ✓ / ✗

- [ ] **Test**: Search functionality
  - **Status**: 🔴
  - **Result**: ✓ / ✗

- [ ] **Test**: Record detail view
  - **Status**: 🔴
  - **Result**: ✓ / ✗

- [ ] **Test**: Download system
  - **Status**: 🔴
  - **Result**: ✓ / ✗

- [ ] **Test**: Admin interface
  - **Status**: 🔴
  - **URL**: `/djadmin/`
  - **Result**: ✓ / ✗

#### 11.4. Monitoring

- [ ] **Task**: Monitor error logs
  - **Status**: 🔴
  - **Period**: First 24 hours
  - **Errors**: (document any)

- [ ] **Task**: Monitor performance metrics
  - **Status**: 🔴
  - **Metrics**:
    - Response time: 
    - Error rate: 
    - Resource usage: 

- [ ] **Task**: Monitor user feedback
  - **Status**: 🔴
  - **Channels**: Email, support tickets, etc.
  - **Issues**: (document)

- [ ] **Task**: Check for failed background jobs
  - **Status**: 🔴
  - **Celery Tasks**: (check if applicable)

#### 11.5. Communication

- [ ] **Task**: Announce deployment complete
  - **Status**: 🔴
  - **Channels**: (email, Slack, etc.)
  - **Time**: _______

- [ ] **Task**: Provide user documentation updates
  - **Status**: 🔴
  - **Changes**: (any UI changes users need to know)

- [ ] **Task**: Update internal documentation
  - **Status**: 🔴
  - **Docs**: Deployment procedures, architecture diagrams

#### 11.6. Post-Deployment Cleanup

- [ ] **Task**: Merge upgrade branch to main
  - **Status**: 🔴
  - **Command**: `git checkout main && git merge upgrade/v3.18.0-working`
  - **Push**: `git push origin main`

- [ ] **Task**: Tag production release
  - **Status**: 🔴
  - **Tag**: `nexuslims-cdcs-v3.18.0-production`
  - **Command**: `git tag -a nexuslims-cdcs-v3.18.0-production -m "Production deployment v3.18.0"`

- [ ] **Task**: Clean up old backups (after retention period)
  - **Status**: 🔴
  - **Retention**: (specify policy)

- [ ] **Task**: Document lessons learned
  - **Status**: 🔴
  - **File**: `docs/UPGRADE_RETROSPECTIVE.md`
  - **Content**: What went well, what to improve

### Phase 11 Completion Checklist
- [ ] Production deployment successful
- [ ] All post-deployment tests pass
- [ ] No critical errors in first 24 hours
- [ ] Users notified
- [ ] Code merged and tagged
- [ ] **Phase Lead Sign-off**: _______________ Date: ___________

---

## Rollback Procedures

**Execute if critical issues found in production**

### Immediate Rollback (Emergency)

**Trigger**: Site down, data loss, critical security issue

1. **Put site in maintenance mode**
   ```bash
   # Enable maintenance page
   ```

2. **Restore database backup**
   ```bash
   # Stop services
   sudo systemctl stop gunicorn
   
   # Restore DB (command depends on DB type)
   # SQLite: cp db.sqlite3.backup_YYYYMMDD db.sqlite3
   # PostgreSQL: psql < backup_YYYYMMDD.sql
   ```

3. **Restore previous code**
   ```bash
   git checkout nexuslims-cdcs-v2.21.0-final
   pip install -r requirements.txt
   python manage.py collectstatic --noinput
   ```

4. **Restart services**
   ```bash
   sudo systemctl start gunicorn
   sudo systemctl restart nginx
   ```

5. **Remove maintenance mode**

6. **Verify site operational**

7. **Notify stakeholders**

### Partial Rollback (Non-Critical Issues)

**Trigger**: Minor bugs, performance issues, non-critical features broken

1. **Document issues**
   - Create GitHub issues
   - Prioritize fixes

2. **Hot-fix on upgrade branch**
   ```bash
   git checkout upgrade/v3.18.0-working
   # Make fixes
   git commit -m "hotfix: [description]"
   ```

3. **Deploy hot-fix to staging**
   - Test fixes

4. **Deploy hot-fix to production**

5. **Monitor**

### Rollback Decision Tree

```
Is site completely down?
├─ Yes → IMMEDIATE ROLLBACK
└─ No
    ├─ Is there data loss/corruption?
    │   ├─ Yes → IMMEDIATE ROLLBACK
    │   └─ No
    │       ├─ Is there a security vulnerability?
    │       │   ├─ Yes → IMMEDIATE ROLLBACK
    │       │   └─ No
    │       │       ├─ Are core features broken (search, login, display)?
    │       │       │   ├─ Yes → Evaluate: Can hot-fix in <2 hours?
    │       │       │   │   ├─ Yes → HOT-FIX
    │       │       │   │   └─ No → ROLLBACK
    │       │       │   └─ No → HOT-FIX or defer to next maintenance window
```

---

## Risk Register

| Risk ID | Description | Probability | Impact | Mitigation | Owner | Status |
|---------|-------------|-------------|--------|------------|-------|--------|
| R-001 | XSLT parameter system breaks | Medium | High | Thorough testing in Phase 4, consider Option B | TBD | 🔴 Open |
| R-002 | Bootstrap 5 migration breaks layout | Medium | Medium | Manual testing all pages, cross-browser | TBD | 🔴 Open |
| R-003 | results.js merge introduces bugs | High | High | Careful merge, extensive download testing | TBD | 🔴 Open |
| R-004 | Database migration fails | Low | Critical | Multiple backups, test migrations on copy | TBD | 🔴 Open |
| R-005 | Performance degradation | Medium | Medium | Load testing, performance monitoring | TBD | 🔴 Open |
| R-006 | Authentication issues (django-allauth) | Medium | High | Test all auth flows, SSO if applicable | TBD | 🔴 Open |
| R-007 | Static files not serving | Low | High | Test collectstatic, web server config | TBD | 🔴 Open |
| R-008 | Download system breaks | Medium | High | Extensive testing Phase 9.4 | TBD | 🔴 Open |
| R-009 | Incompatible Python version | Low | High | Test on Python 3.11 and 3.12 | TBD | 🔴 Open |
| R-010 | Third-party package conflicts | Medium | Medium | Lock dependency versions, test | TBD | 🔴 Open |

**Probability**: Low / Medium / High  
**Impact**: Low / Medium / High / Critical  
**Status**: 🔴 Open | 🟡 Monitoring | 🟢 Closed

---

## Decision Log

| Date | Decision | Rationale | Impact | Decider |
|------|----------|-----------|--------|---------|
| YYYY-MM-DD | (Phase 4) XSLT Architecture: Option A / Option B | (Document reasoning) | (Document affected components) | TBD |
| | | | | |
| | | | | |

---

## Communication Plan

### Stakeholders

| Stakeholder | Role | Contact | Notification Timing |
|-------------|------|---------|---------------------|
| | | | Pre-upgrade, weekly updates, deployment |
| | | | |

### Communication Templates

#### Pre-Upgrade Announcement
```
Subject: NexusLIMS-CDCS Upgrade to v3.18.0 - Planned

Dear [Stakeholder],

We are planning an upgrade of NexusLIMS-CDCS from version 2.21.0 to 3.18.0.

Key Changes:
- Django framework upgrade (2.2 → 5.2) for improved security and performance
- Updated UI components (Bootstrap 5)
- Enhanced download system
- [Other user-facing changes]

Timeline:
- Upgrade Start: [Date]
- Staging Testing: [Date Range]
- Production Deployment: [Date]

Expected Downtime: [Duration] during production deployment

We will provide weekly updates as we progress through testing phases.

Questions? Contact: [Contact Info]

Best regards,
[Name]
```

#### Weekly Update Template
```
Subject: NexusLIMS-CDCS Upgrade - Week [N] Update

Current Phase: [Phase Name]
Status: On Track / Delayed / Ahead

Completed This Week:
- [Item 1]
- [Item 2]

Next Week:
- [Item 1]
- [Item 2]

Issues/Risks:
- [Any concerns]

No action required from you at this time.
```

#### Deployment Notification
```
Subject: NexusLIMS-CDCS Upgrade - Deployment Scheduled

The NexusLIMS-CDCS upgrade to v3.18.0 is scheduled for:

Date: [Date]
Time: [Time]
Expected Downtime: [Duration]

During this time, the system will be unavailable.

After deployment, you may notice:
- [User-visible change 1]
- [User-visible change 2]

Updated documentation will be available at: [URL]

If you experience any issues after the upgrade, please contact: [Contact]
```

#### Post-Deployment Announcement
```
Subject: NexusLIMS-CDCS Upgrade Complete - v3.18.0 Now Live

The NexusLIMS-CDCS upgrade to v3.18.0 has been successfully deployed.

The system is now available at: [URL]

What's New:
- [User benefit 1]
- [User benefit 2]

Known Issues:
- [Any known minor issues]

Please report any issues to: [Contact]

Thank you for your patience during this upgrade.
```

---

## Appendices

### Appendix A: Key Files Reference

**Configuration Files**:
- `mdcs/settings.py` - Main Django settings
- `mdcs/urls.py` - URL routing
- `mdcs/core_settings.py` - MDCS core settings
- `requirements.txt` - Python dependencies

**Custom Python Code**:
- `mdcs_home/context_processors.py` - Template context
- `mdcs_home/templatetags/xsl_transform_tag.py` - XSLT template tag
- `mdcs_home/utils/xml.py` - XSLT transformation with parameters
- `mdcs_home/views.py` - Custom views
- `mdcs_home/menus.py` - Menu configuration

**Templates**:
- `templates/theme.html` - Base theme
- `templates/theme/menu.html` - Navigation menu
- `templates/core_main_app/user/data/detail.html` - Record detail view
- `templates/core_explore_common_app/user/results/*.html` - Search results

**XSLT**:
- `xslt/detail_stylesheet.xsl` - Record detail rendering
- `xslt/list_stylesheet.xsl` - Search results table

**JavaScript**:
- `static/js/menu_custom.js` - Custom menu behavior
- `static/js/nexus_buttons.js` - Download system buttons
- `results_override/static/core_explore_common_app/user/js/results.js` - Search results logic

**CSS**:
- `static/css/*.css` - Custom styles
- `results_override/static/core_explore_common_app/user/css/*.css` - Results styling

### Appendix B: Environment Variables

See **POTENTIAL_UPGRADE_CONFLICTS.md § Appendix B** for complete list.

Key variables:
- `DJANGO_SECRET_KEY`
- `DJANGO_SETTINGS_MODULE`
- `DATABASE_URL`
- `STATIC_ROOT`
- `STATIC_URL`
- (NexusLIMS-specific variables)

### Appendix C: Useful Commands

**Git**:
```bash
# Three-way diff
git diff upstream/v2.21.0...main -- [file]

# Show file at specific commit
git show upstream/v3.18.0:mdcs/settings.py

# Create backup tag
git tag -a backup-YYYYMMDD -m "Backup before upgrade"
```

**Django**:
```bash
# Check for issues
python manage.py check
python manage.py check --deploy

# Show migrations
python manage.py showmigrations

# Migration plan
python manage.py migrate --plan

# Collect static
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

**Testing**:
```bash
# Run tests
python manage.py test

# Run specific test
python manage.py test app.tests.TestClass.test_method

# Coverage
coverage run --source='.' manage.py test
coverage report
```

**Database**:
```bash
# SQLite backup
cp db.sqlite3 db.sqlite3.backup

# SQLite restore
cp db.sqlite3.backup db.sqlite3

# Export fixtures
python manage.py dumpdata > backup.json

# Import fixtures
python manage.py loaddata backup.json
```

### Appendix D: Contact Information

| Role | Name | Email | Phone |
|------|------|-------|-------|
| Upgrade Lead | | | |
| Technical Lead | | | |
| Stakeholder 1 | | | |
| Stakeholder 2 | | | |

---

## Document Maintenance

**Version**: 1.0  
**Created**: 2025-12-30  
**Last Updated**: 2025-12-30  
**Next Review**: (after Phase 0 completion)

**Change Log**:
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-12-30 | 1.0 | Initial creation | Claude |
| | | | |

**How to Use This Document**:
1. Update task statuses as you complete items (🔴 → 🟡 → 🟢)
2. Fill in "Notes" fields with relevant details, errors, solutions
3. Update "Last Updated" date at top when making changes
4. Use checkboxes to track individual tasks
5. Document all decisions in Decision Log
6. Update Risk Register as risks are identified/mitigated
7. Keep Communication Plan current with actual dates

**Location**: `/Users/josh/git_repos/datasophos/NexusLIMS-CDCS/UPGRADE_PLAN_v3.18.0.md`

---

**END OF UPGRADE PLAN**
