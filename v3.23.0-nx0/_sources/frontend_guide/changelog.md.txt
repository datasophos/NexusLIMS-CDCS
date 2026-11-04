(cdcs-changelog)=
# Frontend Changelog

This [changelog](https://keepachangelog.com/) tracks NexusLIMS-specific changes to the CDCS frontend.
It documents only the customizations made on top of the upstream CDCS/MDCS base.
Upstream CDCS release notes are available from the
[MDCS project](https://github.com/usnistgov/MDCS).

Version numbers for NexusLIMS CDCS use the format `{CDCS base version}-nx{N}`
(e.g., `3.18.0-nx1`), where the base version reflects the upstream CDCS release
and `nx{N}` is an incrementing counter for NexusLIMS-specific releases on that base.

---

## 3.23.0-nx0 -- 2026-11-03

### Highlights

This release upgrades the underlying CDCS platform to 3.23.0 and adds administration controls for selecting images in the public gallery. It also fixes dataset moves that could produce invalid XML and moves the frontend guide to a dedicated documentation site.

This release is intended for compatibility NexusLIMS backend version 2.9.0.

As always, if you need assistance with configuration or deployment of NexusLIMS-CDCS, contact [Datasophos](https://datasophos.co/#contact).

### Upgrade Instructions

These instructions assume you have installed following the instructions in the NexusLIMS docs. If you have customized your
installation, you may need to modify the following commands.

#### 1. Back up your data

```bash
cd /opt/nexuslims-cdcs/deployment
source admin-commands.sh
admin-backup
```

#### 2. Pull the new code

```bash
cd /opt/nexuslims-cdcs
git pull
```

#### 3. Rebuild the application image

```bash
cd /opt/nexuslims-cdcs/deployment
source admin-commands.sh
dc-prod build cdcs
```

> The included Caddy configuration has been updated and the file server and application file routes have been moved to a shared file. If you maintain a custom Caddyfile or Compose configuration, review the changes when updating it, as the example `Caddyfile.prod` has been changed to use the shared routes.

#### 4. Restart the stack

```bash
cd /opt/nexuslims-cdcs/deployment
source admin-commands.sh
dc-prod down && dc-prod up -d
```

No schema or XSLT update is required for this release.

### New Features

- Added a gallery administration page with selection modes, a minimum rating, and a searchable view of eligible images. [#42](https://github.com/datasophos/NexusLIMS-CDCS/pull/42)
- Added a dedicated, versioned CDCS documentation site containing the frontend guide. [#49](https://github.com/datasophos/NexusLIMS-CDCS/pull/49)
- Upgraded the CDCS/MDCS base to 3.23.0, including upstream PID improvements and a health endpoint. [#43](https://github.com/datasophos/NexusLIMS-CDCS/pull/43)

### Bug Fixes

- Preserve valid XML element order when moving curated datasets between activities. [#38](https://github.com/datasophos/NexusLIMS-CDCS/pull/38)
- Allow token-authenticated API requests to bypass demo auto-login and authenticate correctly. [#39](https://github.com/datasophos/NexusLIMS-CDCS/pull/39)
- Include upstream fixes for data-processing recursion. [#43](https://github.com/datasophos/NexusLIMS-CDCS/pull/43)

### Internal / Maintenance

- Updated core application packages to the 2.23 series and refreshed the dependency lockfile. [#43](https://github.com/datasophos/NexusLIMS-CDCS/pull/43)
- Added crawler protections and rate limits to the public demo’s administrative routes. [#36](https://github.com/datasophos/NexusLIMS-CDCS/pull/36)
- Restore the development and CI SAML test provider and allow local development without starting it. [#41](https://github.com/datasophos/NexusLIMS-CDCS/pull/41)
- Updated release and changelog workflows. [#47](https://github.com/datasophos/NexusLIMS-CDCS/pull/47)
- Added a documentation root redirect to the stable release. [#50](https://github.com/datasophos/NexusLIMS-CDCS/pull/50)

### Full Changelog

https://github.com/datasophos/NexusLIMS-CDCS/compare/v3.21.0-nx1...v3.23.0-nx0

---

## 3.21.0-nx1 -- 2026-06-08

This version is intended to be used with NexusLIMS backend versions 2.7.3+.

### Added

- **Public dataset gallery**: Added an unauthenticated, presentation-ready gallery at
  `/gallery/` with automatic rotation, previous/next controls, keyboard navigation,
  full-screen mode, configurable facility branding, and links to source records
- **Dataset curation controls**: Users with write access can assign 1-to-5 ratings and
  featured status from record dataset tables or the annotation panel
- Gallery slide selection prioritizes featured datasets, then the highest-rated
  previewable dataset within each selected record

### Upgrade Notes

Upgrade the Nexus Experiment schema and migrate existing records by running
`admin-upgrade-schema` after deploying this release. Follow the
{ref}`production upgrade procedure <cdcs-production-upgrading>` for the complete
sequence.

---

## 3.21.0-nx0 -- 2026-05-30

This version is intended to be used with NexusLIMS backend versions 2.7.1+.

### Added

- **Full sample and activity management in the record editor**: Users can now add,
  edit, reorder, and delete samples and activities directly in the annotator without
  manually editing raw XML
- **Inline title editing**: Record titles can be edited inline in the annotator
- **Pending-changes modal**: Navigating away with unsaved changes now triggers a
  confirmation modal that summarises all pending edits (title, descriptions, samples,
  dataset moves, and activity changes)
- **Playwright E2E test suite**: Covers auth, record list/detail, annotator, and SSO

### Changed

- **Improved multi-sample display on record detail**: Multiple samples are now
  rendered as Bootstrap cards (name, PID, expandable description, and element chips)
  instead of a flat table; each activity header now displays a linked badge identifying
  its associated sample
- CDCS base upgraded to **MDCS 3.21.0** (core packages `2.21.*`)
- "Edit Record" button label and tooltip refined

### Bug Fixes

- Fixed SSO login button styling -- the "Sign in with SSO" button now matches the
  primary button style with correct contrast

### Upgrade Notes

Rebuilding the Docker image is required (Python dependencies changed). Re-upload
the XSLT stylesheet after restarting (`admin-update-xslt`).

---

## 3.20.0-nx0 -- 2026-03-29

This version is intended to be used with NexusLIMS backend versions 2.6.1+.

### Added

- **Annotator app** (`nexuslims_annotate`): Added a new Django app for reviewing and
  annotating NexusLIMS experiment records directly in the browser
  - Annotation panel accessible from any detail-view record page allows users
    (with edit rights) to add plain-text descriptions to any dataset
  - Dedicated full-width annotator page for a focused editing experience that
    also allows moving/reassigning datasets between acquisition activities
  - Help text and tutorials for all the new annotator features
- **GitHub Actions CI**: unit test workflow that runs the Django test suite on
  every push and pull request (also added basic Django tests for certain functions)

### Changed

- XSLT translator received some updates to better display dataset descriptions
  in the record view
- CDCS base upgraded to **MDCS 3.20.0** (core packages `2.20.*`, Django 5.2)

---

## 3.18.0-nx1 -- 2026-01-31

### Added

- Automatic local TLS certificate provisioning via Caddy, eliminating manual
  certificate setup for development deployments
- Improved documentation for local HTTPS deployment workflow

### Changed

- Simplified `docker-compose` configuration for local development with HTTPS

---

## 3.18.0-nx0 -- 2026-01-19

Initial tagged release of NexusLIMS customizations on the CDCS 3.18.0 base,
incorporating a major refactor and a large set of frontend improvements.
This version is intended to be used with NexusLIMS backend versions 2.0 through
2.6.0.

### Added

- **Guided tour system**: Shepherd.js-based tours for the home, explore, and
  detail pages; tours can be enabled/disabled per user; mobile-responsive
- **Token authentication**: API token support in deployment configurations,
  enabling programmatic record submission from the NexusLIMS harvester
- **JSON/XML export**: one-click export of experiment records from the detail
  view in both formats
- **XSLT debug mode**: configurable flag to expose raw XSLT transformation
  errors in the browser for easier troubleshooting
- **Configurable instrument badge colors**: map instrument names to Bootstrap
  color classes via `INSTRUMENT_BADGE_COLORS` setting
- **Configurable dataset display threshold**: hide the dataset file list for
  records with more than `DATASET_DISPLAY_THRESHOLD` files
- Bandwidth limit on the Caddy file server image

### Changed

- Migrated Python dependency management from pip/requirements files to
  [uv](https://github.com/astral-sh/uv) with a committed lockfile
  (`uv.lock`) for reproducible builds
- Modernized detail page styling with Bootstrap 5 throughout
- Upgraded DataTables to 2.3.6 with Bootstrap 5 integration; DataTables
  initialization extracted into a dedicated JS module
- Detail view navigation and layout consistency improvements
- File list modal rebuilt with Bootstrap 5 and improved tooltip styling;
  fixed header for large file lists
- Improved responsive layout on the home page
- Replaced browser-detection guards with feature detection
- Modernized NexusLIMS logos throughout the UI
