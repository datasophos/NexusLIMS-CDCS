# Plan: NexusLIMS Record Annotator App

## Context

Users want to add textual descriptions to individual datasets within a NexusLIMS experiment record. The XSD schema already has an unused `<description>` field on `<dataset>` elements (optional, xs:string, 0+ occurrences). The XSLT detail stylesheet already renders these descriptions in the dataset metadata modal (lines 1228-1236) when present — so annotations will appear automatically once saved. This feature adds a Bootstrap offcanvas panel accessible from the record detail page, keeping the user in context while annotating.

## Architecture

New Django app `nexuslims_annotate` with two endpoints:
1. Full HTML view (for fallback/direct access) — `GET /annotate/<record_id>/`
2. AJAX fragment endpoint — `GET /annotate/<record_id>/panel/` (returns offcanvas body HTML)
3. AJAX save endpoint — `POST /annotate/<record_id>/save/` (returns JSON)

A feature flag `NX_ENABLE_ANNOTATOR` (default `False`) controls visibility of the "Annotate" button.

## Files to Create

```
nexuslims_annotate/
├── __init__.py
├── apps.py
├── views.py
├── urls.py
└── templates/
    └── nexuslims_annotate/
        ├── annotate.html          # Full-page fallback
        └── _panel.html            # Offcanvas body fragment (AJAX response)
```

No separate static files needed — Bootstrap 5 offcanvas, FontAwesome icons, and `fetch` API are all available globally in CDCS.

## Files to Modify

| File | Change |
|---|---|
| `mdcs/settings.py` | Add `nexuslims_annotate` to INSTALLED_APPS (after `nexuslims_overrides`) |
| `mdcs/urls.py` | Add `re_path(r'^annotate/', include('nexuslims_annotate.urls'))` |
| `nexuslims_overrides/settings.py` | Add `NX_ENABLE_ANNOTATOR = False` default |
| `nexuslims_overrides/context_processors.py` | Expose `NX_ENABLE_ANNOTATOR` in the `nexuslims_features` processor |
| `nexuslims_overrides/templates/core_main_app/user/data/detail.html` | Add "Annotate Record" button + offcanvas container when `NX_ENABLE_ANNOTATOR` is true |

## Implementation Details

### 1. URL patterns (`nexuslims_annotate/urls.py`)

```python
urlpatterns = [
    path('<str:record_id>/panel/', views.annotate_panel, name='nexuslims_annotate_panel'),
    path('<str:record_id>/save/', views.annotate_save, name='nexuslims_annotate_save'),
    path('<str:record_id>/', views.annotate_record, name='nexuslims_annotate_record'),
]
```

### 2. Views (`nexuslims_annotate/views.py`)

```python
@login_required
def annotate_record(request, record_id):
    """Full-page fallback (direct navigation or no-JS)."""
    data = data_api.get_by_id(record_id, request)
    datasets = _parse_datasets(data.content)
    return render(request, 'nexuslims_annotate/annotate.html', {
        'data': data, 'datasets': datasets, 'record_id': record_id,
    })

@login_required
def annotate_panel(request, record_id):
    """AJAX: return HTML fragment for offcanvas body."""
    data = data_api.get_by_id(record_id, request)
    datasets = _parse_datasets(data.content)
    return render(request, 'nexuslims_annotate/_panel.html', {
        'data': data, 'datasets': datasets, 'record_id': record_id,
    })

@login_required
def annotate_save(request, record_id):
    """AJAX POST: update <description> elements in XML, save record."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = data_api.get_by_id(record_id, request)
    updated_xml = _apply_descriptions(data.content, request.POST)
    data.content = updated_xml
    data_api.upsert(data, request)
    return JsonResponse({'success': True})
```

### 3. XML Parsing Strategy

Namespace: `https://data.nist.gov/od/dm/nexus/experiment/v1.0`
Parse with `xml.etree.ElementTree`.

`_parse_datasets(xml_content)` returns a list of dicts:
```python
{
    'index': int,                    # position for form field names
    'name': str,                     # <name> text
    'description': str,              # first <description> text, or ''
    'preview_url': str | None,       # previewBaseUrl + first <preview> path
    'activity_seqno': str,           # parent acquisitionActivity @seqno
}
```

`_apply_descriptions(xml_content, post_data)` — for each dataset at index `i`:
1. Remove all existing `<description>` child elements
2. If `post_data.get(f'dataset_{i}_description', '').strip()` is non-empty:
   - Insert a `<description>` element after `<format>` (or `<location>` if no `<format>`), before `<preview>`
3. Return serialized XML string

Preview URL construction: `os.getenv('XSLT_PREVIEW_BASE_URL', '') + preview_path`

### 4. `_panel.html` template

Vertical scrollable list (not grid — easier to scan in a narrow panel):

```
┌──────────────────────────────────┐
│ ✏ Annotate Record           [×] │
│ ─────────────────────────────── │
│ Activity 1                       │
│ ┌──────────────────────────────┐ │
│ │ 🖼 [preview] | file001.dm3   │ │
│ │              | ┌──────────┐  │ │
│ │              | │ descrip  │  │ │
│ │              | └──────────┘  │ │
│ └──────────────────────────────┘ │
│ ┌──────────────────────────────┐ │
│ │ 🖼 [preview] | file002.tif   │ │
│ │              | ┌──────────┐  │ │
│ │              | │          │  │ │
│ │              | └──────────┘  │ │
│ └──────────────────────────────┘ │
│ Activity 2                       │
│ ...                              │
│                                  │
│ [Save Annotations]  [Cancel]     │
└──────────────────────────────────┘
```

Datasets grouped by acquisition activity (section header per activity).

### 5. Detail template integration

In `nexuslims_overrides/templates/core_main_app/user/data/detail.html`, add before the `{% include %}`:

```html
{% if NX_ENABLE_ANNOTATOR and request.user.is_authenticated %}
<div class="row mb-2">
  <div class="col text-end">
    <button class="btn btn-outline-secondary btn-sm"
            id="annotate-record-btn"
            data-record-id="{{ data.data.id }}"
            data-bs-toggle="offcanvas"
            data-bs-target="#annotate-offcanvas">
      <i class="fa fa-pencil"></i> Annotate Record
    </button>
  </div>
</div>

<div class="offcanvas offcanvas-end" tabindex="-1" id="annotate-offcanvas"
     style="width: min(600px, 50vw);">
  <div class="offcanvas-header">
    <h5 class="offcanvas-title"><i class="fa fa-pencil"></i> Annotate Record</h5>
    <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
  </div>
  <div class="offcanvas-body" id="annotate-offcanvas-body">
    <div class="text-center text-muted py-4">
      <i class="fa fa-spinner fa-spin"></i> Loading...
    </div>
  </div>
</div>

<script>
document.getElementById('annotate-offcanvas').addEventListener('show.bs.offcanvas', function() {
  const recordId = document.getElementById('annotate-record-btn').dataset.recordId;
  fetch(`/annotate/${recordId}/panel/`, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
    .then(r => r.text())
    .then(html => document.getElementById('annotate-offcanvas-body').innerHTML = html);
});
</script>
{% endif %}
```

### 6. Save via AJAX (in `_panel.html`)

The panel form submits via `fetch`:

```javascript
document.getElementById('annotate-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const formData = new FormData(this);
  fetch(`/annotate/${recordId}/save/`, {
    method: 'POST',
    body: formData,
    headers: {'X-CSRFToken': formData.get('csrfmiddlewaretoken')},
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      bootstrap.Offcanvas.getInstance(document.getElementById('annotate-offcanvas')).hide();
      // Show Bootstrap toast: "Annotations saved"
    }
  });
});
```

### 7. Versioning

CDCS does **not** have built-in data record versioning — `data_api.upsert()` overwrites in-place. The `Data.last_modification_date` is auto-updated on save. This is acceptable for an MVP. A future enhancement could add an `AnnotationHistory` model to track per-user, per-record description history.

## Enabling the Feature

In `config/settings/custom_settings.py` (or per-deployment settings):

```python
NX_ENABLE_ANNOTATOR = True
```

No Docker rebuild needed if you're only changing settings. First deployment requires a rebuild to include the new app code.

## Verification

1. Set `NX_ENABLE_ANNOTATOR = True` in dev settings
2. Navigate to any record detail page — "Annotate Record" button should appear (top-right)
3. Click button → offcanvas slides in, datasets load with previews and existing descriptions
4. Edit some descriptions, click "Save Annotations" → offcanvas closes, toast appears
5. Re-open the offcanvas — edited descriptions should be pre-populated
6. Open the dataset metadata modal (⊞ icon in the dataset table) → description should appear in the modal
7. Check `Data.last_modification_date` was updated for the record
