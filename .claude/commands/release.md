---
allowed-tools: Bash(git:*), Bash(grep:*), Bash(cat:*), Read, Glob
argument-hint: [version] [--dry-run] [--no-push]
description: Prepare a NexusLIMS-CDCS release with intelligent changelog and upgrade instructions for deployment admins
---

# NexusLIMS-CDCS Release Preparation

## Current State

Gather the following before proceeding:

1. **Current version:** Read `pyproject.toml` and extract the `version = "..."` line.
2. **Current branch:** Run `git branch --show-current`.
3. **Last tag:** Run `git describe --tags --abbrev=0`.
4. **Commits since last tag:** Run `git log <last-tag>..HEAD --oneline`.
5. **Files changed since last tag:** Run `git diff <last-tag>..HEAD --name-only | sort`.

Gather all five before proceeding.

---

## Instructions

### Step 1: Analyse Changed Files for Upgrade Impact

Scan the changed file list and categorise each into the buckets below. For any bucket
that has matches, read the actual diff (`git diff <last-tag>..HEAD -- <file>`) to
understand *what* changed so you can write concrete upgrade instructions.

| Bucket | Patterns | Deployment impact |
|---|---|---|
| **XSLT** | `xslt/*.xsl` | Must re-upload stylesheets to database |
| **Schema** | `deployment/schemas/*.xsd` | Must re-upload schema to database |
| **Migrations** | `*/migrations/*.py` | Must run `migrate` (auto on restart, but note it) |
| **Docker image** | `deployment/Dockerfile`, `pyproject.toml`, `uv.lock` | Must rebuild image |
| **Compose config** | `deployment/docker-compose*.yml` | Must restart stack |
| **Env variables** | `deployment/.env.demo.example`, any `settings.py` | Check `.env` for new required variables |
| **Init/seed scripts** | `deployment/scripts/init_environment.py`, `deployment/scripts/seed_demo_records.py` | Note behaviour changes |
| **Caddy / TLS** | `deployment/caddy/Caddyfile*`, `deployment/caddy/docker-entrypoint.sh` | Restart Caddy; TLS config may have changed |
| **Static assets** | `nexuslims_overrides/static/**`, `nexuslims_annotate/static/**` | Run `collectstatic` (auto on restart) |
| **Templates** | `nexuslims_overrides/templates/**`, `nexuslims_annotate/templates/**` | Restart app; no manual step |
| **App code** | `nexuslims_overrides/**`, `nexuslims_annotate/**`, `mdcs/**` | Restart app |
| **Test / CI** | `tests/**`, `.github/**` | No deployment action needed |

For the **XSLT**, **Schema**, and **Env variables** buckets, always read the diff and
describe *exactly* what changed (e.g. new variable names, renamed fields, added
`xsl:variable` blocks).

### Step 2: Draft Upgrade Instructions

Write an **Upgrade Instructions** section for every release, regardless of what
changed. The section always begins with a backup step, followed by any
change-specific steps.

All upgrade instructions must use `admin-commands.sh` aliases where they exist
(source it first: `source deployment/admin-commands.sh`). Fall back to raw Docker
Compose commands only for operations that `admin-commands.sh` does not cover.
Never reference `dev-commands.sh` or `demo-commands.sh` in upgrade instructions.

Available `admin-commands.sh` aliases relevant to upgrades:
- `dc-prod` -- shorthand for `docker compose -f docker-compose.base.yml -f docker-compose.prod.yml`
- `admin-init` -- re-runs `init_environment.py` (re-uploads schema and XSLT to database)
- `admin-backup` -- backs up all CDCS data (templates, records, blobs, users)

**Template for the Upgrade Instructions section:**

```markdown
### Upgrade Instructions

#### 1. Back up your data
Always back up before upgrading:
```bash
cd deployment
source admin-commands.sh
admin-backup
```

#### 2. Pull the new code
```bash
cd /opt/nexuslims-cdcs
git pull
```

#### 3. [Change-specific steps — include only the subsections that apply]

##### Rebuild Required
(Include if Dockerfile / pyproject.toml / uv.lock changed)
Python dependencies or the container definition changed. Rebuild before restarting:
```bash
cd deployment
source admin-commands.sh
dc-prod build cdcs
```

##### New / Changed Environment Variables
(Include if .env.demo.example or settings.py changed; list each variable explicitly)
Add or update the following in your `.env`:
```
NEW_VARIABLE=value
```

##### XSLT Stylesheets Updated
(Include if xslt/*.xsl changed; describe what changed)
Re-upload the updated stylesheets to the database after restarting:
```bash
cd deployment
source admin-commands.sh
admin-init
```
Or to update only XSLT without a full re-init:
```bash
docker exec ${COMPOSE_PROJECT_NAME}_cdcs bash /srv/scripts/update-xslt.sh
```

##### Schema Updated
(Include if deployment/schemas/*.xsd changed; describe what changed)
Re-upload the updated schema to the database:
```bash
cd deployment
source admin-commands.sh
admin-init
```

#### 4. Restart the stack
```bash
cd deployment
source admin-commands.sh
dc-prod down && dc-prod up -d
```
```

If the only changes are in Test / CI / app code / templates (no rebuild, no env
changes, no schema/XSLT changes), the Upgrade Instructions section still includes
steps 1, 2, and 4 -- just omit step 3.

### Step 3: Draft Release Notes

Write complete release notes using this structure. Do not hard-wrap long lines.

````markdown
## NexusLIMS-CDCS vX.Y.Z

### Highlights
(2–4 sentence plain-English summary of the most important changes, written for
deployment admins, not developers)

As always, if you need assistance with configuration or deployment of NexusLIMS-CDCS,
contact [Datasophos](https://datasophos.co/#contact).

### Upgrade Instructions
(Always include -- see Step 2 template above)

### New Features
(User- or admin-facing features; reference PR numbers where available)

### Bug Fixes
(Bug fixes; reference PR numbers where available)

### Internal / Maintenance
(Dependency bumps, CI changes, refactors -- one line each)

### Full Changelog
https://github.com/datasophos/NexusLIMS-CDCS/compare/vPREV...vNEXT
````

Base the content strictly on the commits and diffs gathered -- do not invent changes.

### Step 4: Determine the Version Number

**Version scheme for this project:**

- The version tracks the upstream CDCS/MDCS base: `3.20.0` means CDCS 3.20.0.
- NexusLIMS-specific changes on top of a CDCS release use a `-nx` suffix:
  `3.20.0-nx1`, `3.20.0-nx2`, etc.
- `pyproject.toml` stores the version in PEP 440 local form (e.g. `3.20.0+nx1`);
  git tags use the hyphen form (e.g. `v3.20.0-nx1`).

**Version bumping rules** (apply in order):

1. If the user supplied a version argument (e.g. `/release 3.21.0-nx1`), use it
   exactly and skip the rules below.

2. Check whether the CDCS/MDCS base packages changed since the last tag (look for
   bumped `core_*_app` versions in the `pyproject.toml` diff):
   - **Yes** → new version is `{NEW_CDCS_VERSION}-nx0` (e.g. `3.21.0-nx0`).
   - **No** → increment the `-nx` counter. If the current version has no `-nx` suffix
     (e.g. `3.20.0`), the new version is `3.20.0-nx1`. If it already has one (e.g.
     `3.20.0-nx1`), increment to `3.20.0-nx2`.

3. If the current `pyproject.toml` version contains `.devN` or `+devN`, strip the dev
   suffix before applying rule 2.

Present the suggested version and ask the user to confirm or change it.

### Step 5: User Review

Present the full release notes and proposed version. Ask the user to:
1. Review and approve the release notes
2. Confirm the version number

Do not proceed to Step 6 until the user explicitly approves.

### Step 6: Apply the Release

Once approved, and unless `--dry-run` was passed:

1. **Update `pyproject.toml`**: Set `version = "<VERSION>"` using the PEP 440 local
   form (e.g. `3.20.0+nx1` for tag `v3.20.0-nx1`).

2. **Write `RELEASE_NOTES.md`** to the project root with the approved release notes.

3. **Commit both files:**
   ```bash
   git add pyproject.toml RELEASE_NOTES.md
   git commit -m "chore: release vVERSION"
   ```

4. **Tag the release** (hyphen form):
   ```bash
   git tag -a vVERSION -m "Release vVERSION"
   ```

5. **Push** (unless `--no-push` was passed):
   ```bash
   git push origin main
   git push origin vVERSION
   ```

### Step 7: Post-Release Checklist

After completing Step 6:

- Check GitHub Actions: https://github.com/datasophos/NexusLIMS-CDCS/actions
- The demo server will auto-deploy via the self-hosted runner on push to `main`
- Verify the GitHub Release was created at: https://github.com/datasophos/NexusLIMS-CDCS/releases
- If XSLT or schema changed, verify the update applied on the demo server:
  ```bash
  docker logs nexuslims_demo_cdcs | grep -E "(stylesheet|schema|XSLT|Schema)"
  ```

---

## Quick Reference: Version Scheme

| Scenario | `pyproject.toml` | git tag |
|---|---|---|
| First NexusLIMS changes on CDCS 3.20.0 | `3.20.0+nx1` | `v3.20.0-nx1` |
| Second patch on 3.20.0 | `3.20.0+nx2` | `v3.20.0-nx2` |
| Upgrade to CDCS 3.21.0 | `3.21.0+nx0` | `v3.21.0-nx0` |
