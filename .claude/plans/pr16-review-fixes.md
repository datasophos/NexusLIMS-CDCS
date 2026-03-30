# Plan: Fix Issues from PR #16 Review

Issues identified in the code review of `feat(annotator): add nexuslims_annotate app`.

---

## Critical Fixes

### Fix 1: Add permission check to `annotate_descriptions`

**File:** `nexuslims_annotate/views.py`

The `annotate_descriptions` view is `@login_required` but never calls `check_can_write` (or
`check_can_read`). Any authenticated user can probe dataset names/descriptions for any record.

**Changes:**
- Wrap the body of `annotate_descriptions` in a `try/except` that calls `check_can_write` (or
  `check_can_read` if read-only access is acceptable), returning a 403 JSON response on failure --
  matching the pattern used in `annotate_panel` and other protected views.

---

### Fix 2: Fix `TypeError` in `_sort_datasets_by_creation_time`

**File:** `nexuslims_annotate/views.py` (~line 186)

When two datasets both have no creation timestamp, Python attempts to compare `None < None` as a
tiebreaker, raising `TypeError`. The lambda also calls `_dataset_creation_time` twice per element.

**Changes:**
- Rewrite the sort key to compute the timestamp once per element and use a sentinel (e.g.,
  `datetime.min`) in place of `None` so all elements are always comparable:
  ```python
  _EPOCH = datetime.min
  sorted_datasets = sorted(
      datasets,
      key=lambda ds: (False, _EPOCH) if (t := _dataset_creation_time(ds)) is None else (False, t),
  )
  # or more concisely:
  sorted_datasets = sorted(
      datasets,
      key=lambda ds: (t := _dataset_creation_time(ds)) and (False, t) or (True, _EPOCH),
  )
  ```
  Simplest correct form:
  ```python
  _EPOCH = datetime.min
  def _sort_key(ds):
      t = _dataset_creation_time(ds)
      return (t is None, t if t is not None else _EPOCH)
  sorted_datasets = sorted(datasets, key=_sort_key)
  ```
- Add a test case in `tests/test_annotator.py` covering the scenario where multiple datasets all
  lack creation timestamps (ensuring no `TypeError` is raised).

---

### Fix 3: Remove duplicate `{% csrf_token %}` in `_panel.html`

**File:** `nexuslims_annotate/templates/nexuslims_annotate/_panel.html`

The CSRF token is rendered twice: once outside the `<form>` element (line 2) and once inside
(line 12). The stray outer token is dead HTML.

**Changes:**
- Remove the `{% csrf_token %}` at line 2 (the one outside the `<form>`).

---

## Important Fixes

### Fix 4: Align `NX_ENABLE_ANNOTATOR` defaults across all three locations

**Files:**
- `nexuslims_overrides/settings.py`
- `nexuslims_overrides/context_processors.py`
- `mdcs/urls.py`

The context processor falls back to `False` while the settings and URL config default to `True`,
causing inconsistent behavior in non-standard deployments.

**Changes:**
- Change the `NX_ENABLE_ANNOTATOR` fallback in `context_processors.py` from `False` to `True`.

---

### Fix 5: Initialize `idx` before `try` block in `annotate_save_one`

**File:** `nexuslims_annotate/views.py` (~lines 362-375)

If `dataset_index` POST value is a non-integer string, `int(...)` raises before `idx` is assigned.
The `except` handler then references `idx`, itself raising `UnboundLocalError` and swallowing the
original exception.

**Changes:**
- Add `idx = None` immediately before the `try` block so the logger call is always safe.

---

### Fix 6: Replace hard-coded URL paths in JavaScript with data attributes

**Files:**
- `nexuslims_overrides/templates/core_main_app/user/data/detail.html` (multiple lines)
- `nexuslims_annotate/templates/nexuslims_annotate/annotate.html` (lines ~34 and ~108)

Hard-coded paths like `'/annotate/' + recordId + '/save/'` break when the app is deployed at a
non-root URL prefix.

**Changes:**
- In `detail.html`: add `data-url-*` attributes to the relevant elements (e.g., the "Annotate
  Record" button or a surrounding container) rendered via `{% url ... %}`, and update the
  JavaScript to read URLs from those attributes instead of constructing them manually.
- In `annotate.html`: replace hard-coded `/data?id=...` hrefs with `{% url 'data_detail' %}?id=...`
  (or equivalent named URL) for both anchor tags (~lines 34 and 108).

---

### Fix 7: Add view-level integration tests

**File:** `tests/test_annotator.py`

The test suite covers only pure XML helpers. No view is tested, meaning permission bugs and
`UnboundLocalError` cases are invisible to CI.

**Changes:**
- Add integration tests using Django's `TestClient` (or `RequestFactory`) for at minimum:
  - `annotate_descriptions`: verify unauthenticated returns 302/403; authenticated-without-access
    returns 403; authenticated-with-access returns 200 with correct JSON.
  - `annotate_save_one`: verify invalid `dataset_index` value returns a graceful error (not 500).
  - Feature flag: verify that when `NX_ENABLE_ANNOTATOR=False`, the panel URL returns 404 or
    appropriate response.

---

## Minor Fixes

### Fix 8: Remove unused `{% load i18n %}` from `_panel.html`

**File:** `nexuslims_annotate/templates/nexuslims_annotate/_panel.html`

`{% load i18n %}` is loaded but no translation tags are used.

**Changes:**
- Remove the `{% load i18n %}` tag.

---

### Fix 9: Vendor SortableJS locally

**File:** `nexuslims_annotate/templates/nexuslims_annotate/annotate.html` (~line 137)

SortableJS is loaded from `cdn.jsdelivr.net` while all other third-party libraries are vendored
under `static/libs/`. This breaks air-gapped deployments and is inconsistent with project
convention.

**Changes:**
- Download SortableJS (the version currently referenced in the CDN link) to
  `nexuslims_annotate/static/nexuslims_annotate/libs/sortable/Sortable.min.js` (or the equivalent
  path under the app's static directory).
- Update the `<script>` tag in `annotate.html` to use `{% static '...' %}`.

---

### Fix 10: Handle missing record gracefully in `annotate_record` and `annotate_panel`

**File:** `nexuslims_annotate/views.py`

`data_api.get_by_id` is called without a try/except. An invalid `record_id` raises an unhandled
exception, returning a 500 instead of a 404.

**Changes:**
- Wrap `data_api.get_by_id(record_id)` calls in a try/except that catches the appropriate
  exception (e.g., `DoesNotExist` or the equivalent from the CDCS data API) and returns
  `Http404` or a 404 `JsonResponse`.

---

### Fix 11: Document `seqno` assumption in templates

**Files:**
- `nexuslims_annotate/templates/nexuslims_annotate/annotate.html`
- `nexuslims_annotate/templates/nexuslims_annotate/_panel.html`

`{{ group.grouper|add:1 }}` and `parseInt(act.seqno) + 1` silently misbehave if `seqno` is
non-numeric (Django's `add` filter string-concatenates instead of adding).

**Changes:**
- Add an HTML comment near each usage noting that `seqno` is assumed to be a zero-based integer
  string, as defined by the NexusLIMS schema.

---

## Implementation Order

1. Fix 3 (csrf_token) -- trivial, no risk
2. Fix 8 (unused i18n) -- trivial, no risk
3. Fix 4 (feature flag default) -- one-line change, low risk
4. Fix 5 (UnboundLocalError) -- one-line change, low risk
5. Fix 1 (permission check) -- moderate, needs care to match existing pattern
6. Fix 2 (sort TypeError) + test coverage -- moderate, needs a new test case
7. Fix 10 (404 on missing record) -- moderate, need to identify correct exception class
8. Fix 6 (hard-coded URLs) -- moderate, touches multiple templates and JS
9. Fix 7 (view-level tests) -- larger effort, best done last so the views are stable
10. Fix 9 (vendor SortableJS) -- low priority, can be a follow-up PR
11. Fix 11 (seqno comments) -- cosmetic, can be bundled with any of the above
