# Dataset Mover Feature Plan

## Context

The annotator currently only allows editing descriptions on datasets. Datasets belong to `acquisitionActivity` elements in the XML, and errors or ambiguities sometimes place a dataset under the wrong activity. This feature adds the ability to move datasets between activities directly in the full-page annotator (`/annotate/<id>/`), with changes batched and saved together with description edits.

**User decisions:**
- UI: drag-and-drop (single cards) + checkbox multi-select + batch toolbar
- Save timing: batched with descriptions at "Save Annotations" click
- Scope: full-page annotator only (not offcanvas panel)
- Setup reconciliation: full re-derivation at save time

---

## Architecture Overview

### Data Flow

1. User drags a card to another activity section, or selects multiple cards and uses the batch toolbar
2. Moves are recorded in `window.__nxPendingMoves` (JS state only -- nothing saved yet)
3. On "Save Annotations" click, the form POST includes both description fields AND a `moves` JSON field
4. Backend applies descriptions first (using pre-move indices), then applies moves with full setup reconciliation
5. Page reloads to detail view with updated XML reflected in XSLT output

### Index handling

Descriptions use the flat global index (pre-move state). Moves are recorded as `{datasetIndex, targetActivitySeqno}`. Since descriptions are applied before moves, the indices remain valid throughout the save operation. After save/redirect, XSLT re-renders with new indices computed from the updated XML.

---

## Backend Changes

**File: `nexuslims_annotate/views.py`**

Add three new helper functions:

### `_inject_setup_into_dataset(dataset_el, activity_el, ns)`
Before a dataset is physically moved, inject its source activity's setup params into its `<meta>` elements (only where the dataset doesn't already have a value for that param). This preserves the instrument state the dataset was originally acquired under.

### `_recompute_activity_setup(activity_el, ns)`
After all moves are applied, recompute the `<setup>` block for a given activity:
1. Collect all `<meta>` elements from every dataset in the activity
2. Find the intersection: params where ALL datasets share the same name and value
3. Replace the existing `<setup>` element with the new computed one
4. Remove from each dataset's `<meta>` any params now promoted to setup

Edge cases:
- Empty activity (all datasets moved out): remove `<setup>` entirely
- Single dataset: all its meta values become setup (same intersection logic works)

### `_apply_moves(xml_content, moves)`
```
moves: list of {"datasetIndex": N, "targetActivitySeqno": M}
```

Algorithm:
1. Parse XML, build flat dataset list (same logic as `_parse_datasets`)
2. For each move, look up the dataset element and its current parent activity
3. Inject source activity setup into each moving dataset (step before any move happens)
4. Perform all moves: `activity_el.remove(dataset_el)`, `target_activity_el.append(dataset_el)`
5. Collect the set of all affected activities (sources and targets)
6. Call `_recompute_activity_setup` on each affected activity
7. Return updated XML string

### Modify `annotate_save` view
After calling `_apply_descriptions`, also call `_apply_moves` if a `moves` field is present in POST data. Parse `moves` as JSON. Order: descriptions first, moves second.

---

## Frontend Changes

### Library: SortableJS
Include via CDN in `annotate.html`. ~30KB, no additional dependencies, handles ghost element, cross-container drag, and touch. Configure with `group: 'datasets'` on each activity's card grid.

### State: `window.__nxPendingMoves`
Array of `{datasetIndex, targetActivitySeqno}` -- appended to on each drag end or batch move.

### Card visual states (extend existing color system)
| State | Background | Left border | Badge |
|---|---|---|---|
| Saved | `#f0fff4` | `#198754` (green) | -- |
| Unsaved edit | `#fff8e1` | `#e67e00` (orange) | -- |
| Empty | `#f8f9fa` | `#dee2e6` (gray) | -- |
| **Pending move** | `#f0f4ff` | `#6366f1` (indigo) | "Moved" pill |

### Checkbox multi-select
- Checkbox appears in top-left corner of each card on hover (or always visible when any card is selected)
- Selecting activates card's "selected" ring style
- Selection count drives toolbar visibility

### Batch toolbar
- Fixed/sticky at bottom of the page (above the existing save/cancel footer)
- Shows: "N datasets selected -- Move to Activity: [dropdown] -- Clear selection"
- Dropdown lists all activities by their display name (e.g., "Activity 1 -- 2018-11-13 11:01") excluding the current activity of selected datasets (or just listing all)
- Selecting an activity triggers batch move: records in `__nxPendingMoves`, updates card positions in DOM, applies pending-move styling

### Drag-and-drop (single cards)
- SortableJS initialized on each `.activity-datasets` row/grid
- `group: { name: 'datasets', pull: true, put: true }` to allow cross-activity movement
- `onEnd` callback: if `to !== from` (cross-activity), record move in `__nxPendingMoves` and apply pending-move style
- Selected cards are NOT draggable as a group (drag = single card always; use toolbar for multi)

### "Undo" pending moves
- "Cancel" button behavior: existing logic clears unsaved description edits. Extend to also clear `__nxPendingMoves` and restore DOM card positions via page reload (or a smarter DOM reset)
- Individual undo: clicking "Moved" badge on a card reverts it to its original position

### Save integration
Before submitting, the save handler serializes `__nxPendingMoves` to JSON and appends it as a hidden field or includes it in the FormData.

### Activity section changes
- Activity headers show live dataset count (updates as cards are dragged in/out)
- Drop zone: when a card is being dragged, activity sections that are valid targets show a highlighted drop indicator

---

## Templates & Static Files

**`nexuslims_annotate/templates/nexuslims_annotate/annotate.html`**
- Add SortableJS CDN script tag
- Add checkboxes to each dataset card
- Add batch toolbar HTML (hidden by default)
- Add `data-activity-seqno` attribute to each activity section and each card
- Add `data-dataset-index` attribute to each card (already needed for save-one, likely already present)
- New JavaScript sections:
  - SortableJS initialization
  - Checkbox selection management
  - Batch toolbar show/hide
  - Pending move state management
  - Save form enhancement (inject moves JSON)

**`nexuslims_annotate/static/nexuslims_annotate/annotate.css`**
- Pending-move card style (indigo border/background)
- "Moved" badge style
- Drag ghost and drop-target highlighting
- Checkbox overlay positioning on cards
- Batch toolbar styles (sticky, z-index above content)

---

## Verification

1. **Unit test the backend helpers** (if test infrastructure exists): create an XML fixture with known activities/datasets/setup params, call `_apply_moves`, verify correct element placement and setup recomputation.

2. **Manual end-to-end** with example_record.xml:
   - Load a record in the full-page annotator
   - Drag a card from Activity 1 to Activity 2
   - Verify pending-move style appears; verify `__nxPendingMoves` contains the entry
   - Edit a description on a different card
   - Hit Save; verify form POST includes both description fields and moves JSON
   - Verify redirect to detail view shows the dataset now under Activity 2 in the XSLT-rendered table
   - Verify activity setup params were recomputed (check via the "Setup Parameters" modal in the detail view)

3. **Batch move** via checkbox toolbar:
   - Select 3 cards, move to another activity
   - Save; verify all 3 appear in target activity

4. **Edge cases**:
   - Move all datasets out of an activity (empty activity remains)
   - Move back to original activity (should be a no-op or cancel the pending move)
   - Reload page without saving (pending moves lost -- expected behavior, matches descriptions behavior)

---

## Out of Scope

- Creating new activities
- Changing the offcanvas panel
- Drag-and-drop in the offcanvas panel
- Server-sent undo/redo after save
