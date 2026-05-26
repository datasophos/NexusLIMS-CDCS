# Annotator Enhancements Design

**Date:** 2026-05-24
**Status:** Approved

## Overview

Extends the existing `nexuslims_annotate` full-page annotator to support:

1. Display, add, edit, and delete samples from a record
2. Assign or change the sample for each acquisition activity
3. Create and delete acquisition activities
4. All existing features (dataset descriptions, dataset moves between activities) preserved

All changes are batched and saved together through the existing "Save Annotations" flow.

## UI Layout

**Option A (chosen): Inline controls everywhere.** No tabs or accordions. All new controls live on the existing annotator page.

### Samples Section

A card panel appears at the top of the page above the activity grid. It contains:

- A section label ("Samples") and a "+ Add Sample" button
- One **vertical list card** per sample, each showing:
  - Sample name (bold, prominent)
  - Description snippet (truncated)
  - Element tags (small `<code>`-style chips, e.g. `Fe`, `Cr`, `Ni`)
  - "Edit" and "Delete" buttons at the right edge
- Clicking "Edit" or "+ Add Sample" opens the **Sample Editor Modal**
- Clicking "Delete" on a sample assigned to one or more activities shows a **warn + confirm** dialog before proceeding; otherwise deletes immediately (pending, not saved until Save is clicked)

### Activity Header Controls

Each activity header row gains three new inline controls to the right of the activity label and dataset count badge:

- **Sample dropdown** (`<select>`): "-- No sample --" plus one option per sample. Reflects the current `<sampleID>` assignment. Changing it is a pending mutation.
- **"+ below" button**: inserts a new empty activity immediately below this one (pending, not saved until Save is clicked).
- **Delete button** (trash icon): enabled only when the activity has 0 datasets; disabled with a tooltip ("Move all datasets first") when non-empty.

### Save Row

The existing Save/Cancel row gains a **"+ Add Activity"** button that appends a new empty activity at the end of the list. This is in addition to the per-activity "+ below" buttons.

### Sample Editor Modal

A Bootstrap modal with the following fields:

| Field | Control |
|---|---|
| Name | `<input type="text">` (required) |
| Description | `<textarea>` (2-3 rows) |
| Notes | `<textarea>` (2-3 rows) |
| Elements | Searchable tag input -- type a symbol or name (e.g. "Fe" or "iron"), pick from a filtered dropdown of all 118 elements, selected elements appear as removable tags |

The modal has "Save" (adds/updates the pending sample list) and "Cancel" buttons. Changes are not written to the record until the main "Save Annotations" button is clicked.

## Backend Architecture

**Approach 1 (chosen): Extend the existing single save endpoint.**

All new mutations are bundled into the existing `POST /annotate/<record_id>/save/` alongside the current `moves` and `dataset_N_description` fields. One atomic save operation applies everything.

### Extended Save Payload

New fields added to the existing form POST:

| Field | Type | Description |
|---|---|---|
| `samples` | JSON array | Full desired list of sample objects in order (replaces all existing `<sample>` elements) |
| `deleted_seqnos` | JSON array | Seqnos of activities to delete; all must have 0 datasets |
| `new_activities` | JSON array | Insertion specs: `[{temp_id, after_seqno\|at_end, sample_id}]` |
| `activity_sample_ids` | JSON object | Maps seqno or temp_id → sample_id (or null to clear) |

The existing `moves` payload is unchanged except that `targetActivitySeqno` may now reference a `temp_id` for newly created activities.

Each sample object in `samples`:

```json
{
  "id": "steel-alloy-a",
  "name": "Steel Alloy A",
  "description": "High-carbon steel reference",
  "notes": "Prepared 2024-01-10",
  "elements": ["Fe", "C", "Cr", "Ni"]
}
```

`id` is auto-generated from the name on the frontend (lowercased, spaces to hyphens, non-alphanumeric stripped). If two samples produce the same id, a numeric suffix is appended.

### Save Order in `annotate_save`

1. Validate all `deleted_seqnos` have 0 datasets -- return 400 if any are non-empty
2. Delete those activities from the XML
3. Insert new empty activities at specified positions (using `after_seqno` or `at_end`)
4. Build a seqno mapping: original seqno → final seqno, temp_id → final seqno (based on XML order after steps 2-3)
5. Apply `activity_sample_ids` using the mapping (set or clear `<sampleID>` on each activity)
6. Replace all `<sample>` elements with the new ordered list from `samples`
7. Apply descriptions (flat dataset indices are unaffected because deleted activities had 0 datasets and new activities are empty)
8. Translate `targetActivitySeqno` in moves through the seqno mapping, then apply moves via the existing `_apply_moves` helper
9. Renumber all activities to consecutive 0-based seqnos

**Why flat dataset indices survive structural changes:** Step 1 guarantees deleted activities are empty, and new activities (step 3) are also empty, so no dataset shifts position in the flat 0-based order.

### New Helper Functions in `views.py`

| Function | Purpose |
|---|---|
| `_parse_samples(xml)` | Returns list of sample dicts (id, name, description, notes, elements list) |
| `_apply_samples(xml, samples_data)` | Replaces all `<sample>` elements in the XML with the new list |
| `_apply_activity_mutations(xml, deleted_seqnos, new_activities, sample_ids)` | Deletes activities, inserts new ones, sets sampleID; returns updated XML + seqno mapping dict |
| `_renumber_activities(xml)` | Rewrites all `seqno` attributes to consecutive 0-based integers in XML order |

`annotate_record` view is extended to pass `samples` to the template context alongside existing `activities` and `datasets`.

### Error Handling

| Condition | Response |
|---|---|
| `deleted_seqnos` contains a non-empty activity | 400 JSON error |
| `deleted_seqnos` references a seqno that does not exist | Silently skipped (idempotent) |
| `new_activities` references an `after_seqno` that does not exist | 400 JSON error |
| Sample `id` collision in the submitted list | 400 JSON error |
| Malformed JSON in any of the new fields | 400 JSON error |
| Existing error conditions (record not found, no write permission) | Unchanged (404, 403) |

## Frontend State Management

The annotator page JS is extended with:

- `__nxPendingSamples`: array of sample objects in current desired order (initialized from server-rendered data)
- `__nxDeletedSeqnos`: array of seqnos pending deletion
- `__nxNewActivities`: array of insertion specs `{temp_id, after_seqno|at_end, sample_id}`
- `__nxActivitySampleIds`: object mapping seqno/temp_id → sample_id

On form submit, these are serialized to the four new hidden inputs alongside the existing `moves` input.

The existing `hasDirtyState()` function is extended to return true when any of the new state arrays/objects are non-empty or differ from initial state.

New activities rendered in the DOM use `data-seqno="new-<uuid>"` so the existing SortableJS drag logic treats them like any other activity. The move dropdown is rebuilt to include new activities by name (e.g. "New Activity").

## XML Data Model

### Sample elements (at Experiment level, before `<acquisitionActivity>`)

```xml
<sample id="steel-alloy-a">
  <name>Steel Alloy A</name>
  <description>High-carbon steel reference</description>
  <notes>
    <entry>Prepared 2024-01-10. Cross-section mounted on copper grid.</entry>
  </notes>
  <elements><Fe/><C/><Cr/><Ni/></elements>
</sample>
```

`<notes>` is written as a single `<notes>` element with one `<entry>` child containing the full text of the notes textarea. On read, all `<entry>` text content is joined with newlines. The schema's `Entry`/`TextEntry` hierarchy is intentionally simplified here -- `<entry>` is written as a plain text node rather than a structured `<p>` subtree, which is valid for the annotation use case.

### Activity sampleID

```xml
<acquisitionActivity seqno="0">
  <startTime>...</startTime>
  <sampleID>steel-alloy-a</sampleID>
  <setup>...</setup>
  ...
</acquisitionActivity>
```

`<sampleID>` is inserted after `<startTime>` (or as the first child if no `<startTime>`), before `<setup>`.

## Testing

New unit tests in `tests/test_annotator.py`:

- `_parse_samples`: returns correct count, name, description, notes, elements; empty when no samples present
- `_apply_samples`: replaces existing samples; creates new ones; handles empty list (removes all)
- `_apply_activity_mutations`: delete empty activity; reject non-empty delete; insert at end; insert after seqno; seqno mapping correctness; sampleID set and cleared
- `_renumber_activities`: consecutive numbering after gaps; no-op when already consecutive
- Extended `annotate_save` view tests: structural mutations round-trip; combined moves + structural changes; 400 on non-empty delete

Existing tests are unaffected (save endpoint falls back gracefully when new fields are absent).
