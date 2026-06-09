# Upgrade Base CDCS Workflow

This shared workflow describes how an agent should upgrade NexusLIMS-CDCS to a new
upstream MDCS base version. Claude, Codex, and other repo agents should use this file
as the source of truth for base-version upgrades.

## Invocation Arguments

The upgrade workflow may receive a target CDCS/MDCS version, such as `3.22.0`.

## Step 0: Determine Target Version

If the user provided a version argument (e.g. `3.22.0`), use it as `TARGET_VERSION`.

If no argument was provided, fetch the latest MDCS release:
```bash
gh release list --repo usnistgov/MDCS --limit 5
```
Present the options and ask the user to confirm which version to upgrade to before proceeding.

Also determine the PREVIOUS MDCS version that is currently installed:
```bash
grep 'core_main_app' pyproject.toml | head -1
```
Extract the current `2.N.*` version to determine `PREV_MDCS_VERSION = 3.N.0` (e.g. `2.20.*` → `3.20.0`).

---

## Step 1: Gather Current State

Run these in parallel to understand the starting point:

```bash
# Current version and core package pin
grep -E "^version|core_main_app" pyproject.toml | head -5

# Current branch
git branch --show-current

# Working tree state (must be clean before starting)
git status --short
```

**Gate:** If the working tree is not clean, stop and tell the user to commit or stash changes first.

---

## Step 2: Determine New Core Package Version

MDCS version maps to core package version like this:
- MDCS `3.21.0` uses `core_*_app==2.21.*`
- MDCS `3.22.0` uses `core_*_app==2.22.*`
- General rule: MDCS `3.N.x` uses `core_*_app==2.N.*`

Derive `CORE_VERSION` from `TARGET_VERSION`:
- Extract the minor version number `N` from `3.N.x`
- Set `CORE_VERSION = 2.N.*`

Verify the packages exist by checking the MDCS `requirements.core.txt` at the target tag:
```bash
curl -s "https://raw.githubusercontent.com/usnistgov/MDCS/${TARGET_VERSION}/requirements.core.txt"
```

If this returns a 404 or empty content, the tag does not exist yet -- stop and tell the user.

---

## Step 3: Read Release Notes for ALL Skipped Versions

If we are jumping across multiple MDCS versions (e.g. 3.20.0 → 3.22.0), we must read the
release notes for every intermediate version too, not just the target. Changes accumulate.

First, list all MDCS releases between PREV and TARGET:
```bash
gh release list --repo usnistgov/MDCS --limit 20 --json tagName,publishedAt \
  --jq '.[] | select(.tagName | test("^[0-9]+\\.[0-9]+\\.[0-9]+$")) | .tagName'
```

For each version greater than PREV_MDCS_VERSION and less than or equal to TARGET_VERSION, fetch its release notes:
```bash
gh release view <VERSION> --repo usnistgov/MDCS --json body,name --jq '.body'
```

Read and summarise ALL release notes. Note any mentions of:
- New settings added
- Deprecated or removed settings
- Breaking API changes
- UI changes (new templates, changed CSS)
- New or removed dependencies

---

## Step 4: Dynamically Determine Which Files We Override

Before diffing, build the current lists of overridden files from the actual repo state.

### 4a. Files we copy from the MDCS upstream repo

Get the full file tree of the MDCS upstream repo at TARGET_VERSION:
```bash
curl -s "https://api.github.com/repos/usnistgov/MDCS/git/trees/${TARGET_VERSION}?recursive=1" \
  | python3 -c "import sys,json; [print(i['path']) for i in json.load(sys.stdin).get('tree',[]) if i['type']=='blob']" \
  | sort > /tmp/mdcs-upstream-files.txt
```

Get the list of tracked files in our local repo (excluding .venv, .superpowers, generated files):
```bash
git ls-files | grep -v "^\.venv\|^\.superpowers\|^static\.prod\|^uv\.lock\|^\.gitignore" | sort > /tmp/our-files.txt
```

The intersection is the set of files that exist in both repos -- these are the files we may have overridden and that we need to check for upstream changes:
```bash
comm -12 /tmp/mdcs-upstream-files.txt /tmp/our-files.txt
```

### 4b. Templates we override from core_*_app packages

Scan the `nexuslims_overrides/templates/` directory to find all overridden templates:
```bash
find nexuslims_overrides/templates/ -type f -name "*.html" | sort
```

For each template path like `nexuslims_overrides/templates/<app_name>/<rest>`, the upstream template lives at `<rest>` in the `<app_name>` GitHub repository. Build the list of (package, template_path) pairs dynamically from this scan.

---

## Step 5: Check Upstream Changes

### 5a. Changed files in the MDCS repo itself

For each file identified in Step 4a, diff it between PREV and TARGET:
```bash
for f in <file_list_from_4a>; do
  old=$(curl -s "https://raw.githubusercontent.com/usnistgov/MDCS/${PREV_MDCS_VERSION}/$f")
  new=$(curl -s "https://raw.githubusercontent.com/usnistgov/MDCS/${TARGET_VERSION}/$f")
  if [ "$old" != "$new" ]; then
    echo "CHANGED: $f"
    diff <(echo "$old") <(echo "$new")
  fi
done
```

For each CHANGED file:
- Determine if the change is **cosmetic** (docstring reformatting, whitespace only) or **functional** (new logic, new setting, new CSS rule, etc.)
- For **functional** changes: compare the upstream diff against our local version. If we don't already have the change, apply it -- but preserve our intentional customisations.
- For **cosmetic** changes: skip (no action needed unless we want uniform formatting).

### 5b. Changed templates in core_*_app packages

For each (package, template_path) pair from Step 4b:

```bash
OLD_CORE="${PREV_MDCS_VERSION/#3./2.}.0"   # e.g. 3.20.0 -> 2.20.0
NEW_CORE="${TARGET_VERSION/#3./2.}.0"       # e.g. 3.21.0 -> 2.21.0

old=$(curl -s "https://raw.githubusercontent.com/usnistgov/<PACKAGE>/${OLD_CORE}/<TEMPLATE_PATH>")
new=$(curl -s "https://raw.githubusercontent.com/usnistgov/<PACKAGE>/${NEW_CORE}/<TEMPLATE_PATH>")
diff <(echo "$old") <(echo "$new")
```

For each CHANGED template, compare the upstream diff against our local override in
`nexuslims_overrides/templates/`. Determine whether:
- Our override already incorporates the upstream change (no action needed)
- Our override needs to be updated to stay compatible
- The upstream change conflicts with our customisation (flag for user review)

### 5c. New settings in core_main_app

Diff `core_main_app/settings.md` between old and new versions:
```bash
OLD_CORE="${PREV_MDCS_VERSION/#3./2.}.0"
NEW_CORE="${TARGET_VERSION/#3./2.}.0"
diff \
  <(curl -s "https://raw.githubusercontent.com/usnistgov/core_main_app/${OLD_CORE}/settings.md") \
  <(curl -s "https://raw.githubusercontent.com/usnistgov/core_main_app/${NEW_CORE}/settings.md")
```

For each new setting found:
- Add it to `mdcs/core_settings.py` using the `os.getenv("SETTING_NAME", default)` pattern
- Use the same default value as upstream
- Include a one-line docstring from the upstream `settings.md`

---

## Step 6: Create Feature Branch

```bash
git checkout -b issue-{ISSUE_NUMBER}-upgrade-base-cdcs-${TARGET_VERSION}
```

If there is no issue number, use:
```bash
git checkout -b upgrade-base-cdcs-${TARGET_VERSION}
```

---

## Step 7: Apply Changes

### 7a. Update `pyproject.toml`

1. Bump the `version` field to `${TARGET_VERSION}+nx0`
2. Update the comment line: `# CDCS/MDCS core packages - all pinned to ${CORE_VERSION} for compatibility`
3. Update all `core_*_app` pins from old version to `${CORE_VERSION}` (use the list from `requirements.core.txt` as the authoritative list -- it may add or remove packages between versions)

### 7b. Update `mdcs/core_settings.py`

1. Update `PROJECT_VERSION` default from old version to `${TARGET_VERSION}`
2. Apply any new or removed settings identified in Steps 3 and 5c

### 7c. Apply upstream file changes (from Step 5)

For each functional change found in Step 5a or 5b, apply the equivalent change to our local file.
Do NOT blindly apply all upstream changes -- our files intentionally diverge from upstream in places.
Apply only the lines that add new behavior or fix bugs, while preserving our customisations.

### 7d. Regenerate the lockfile

```bash
uv lock --upgrade
```

Review the output and note which packages were updated (for the commit message and changelog).

---

## Step 8: Create Changelog Fragment

Create `docs/changes/{ISSUE_NUMBER}.misc.md`:

```
Upgraded the underlying CDCS/MDCS base from version PREV_MDCS_VERSION to TARGET_VERSION, bringing in the latest upstream improvements including [brief summary from all release notes].
```

If there is no issue number, skip this step.

---

## Step 9: Run Tests

```bash
uv run python runtests.py
```

Fix any failures before proceeding. Common upgrade issues:
- New required settings missing from `core_settings.py`
- Deprecated API usage removed upstream
- Migration conflicts

---

## Step 10: Lint

```bash
uv tool run ruff format .
uv tool run ruff check .
```

Fix any violations introduced by your changes. Do not add `# noqa` suppressions without user
confirmation. Pre-existing violations (present on `main`) that are not introduced by this upgrade
do not need to be fixed; they may be cleaned up in a separate commit if desired.

---

## Step 11: Commit

Stage and commit the upgrade-specific files first:
```bash
git add pyproject.toml uv.lock mdcs/core_settings.py docs/changes/
# plus any other files specifically changed by the upgrade (e.g. static/css/main.css)
git commit -m "feat: upgrade base CDCS to MDCS ${TARGET_VERSION} (core packages ${CORE_VERSION})

- Update all core_*_app packages from OLD_CORE_VERSION to ${CORE_VERSION} in pyproject.toml
- Bump project version to ${TARGET_VERSION}+nx0
- Update PROJECT_VERSION default to ${TARGET_VERSION}
- [List any new settings added]
- [List any upstream file changes applied]
- [Note any other significant changes from the lockfile upgrade]

Closes #{ISSUE_NUMBER}"
```

If ruff format changed additional files, commit those separately:
```bash
git add -A
git commit -m "style: apply ruff format to all Python source files"
```

---

## Step 12: Summary

Report:
- Branch name created
- All intermediate versions whose release notes were reviewed
- All packages updated (old → new versions from `uv lock` output)
- Any upstream file changes applied (and whether they were functional or cosmetic)
- Any template override changes needed
- New settings added to `core_settings.py` (if any)
- Test results
- Next step: open a pull request using the repository's pull-request workflow
