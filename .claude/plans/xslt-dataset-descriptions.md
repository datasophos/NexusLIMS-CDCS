# Plan: Display Dataset Descriptions in XSLT Detail View

## Context

The `nexuslims_annotate` app now allows users to write free-text descriptions for each
dataset in a record. These descriptions are stored as `nx:description` elements in the
XML. However, the detail stylesheet (`xslt/detail_stylesheet.xsl`) currently only
surfaces `nx:description` inside the per-dataset metadata modal (lines 1228-1236) —
invisible unless the user clicks the "Meta" button for each dataset. Annotators (and
readers) need to see descriptions prominently without hunting through modals.

The tables in the interactive view are already narrow (8 columns), so adding a
description column is not viable. The proposed approach uses two display surfaces that
require no additional user interaction.

---

## Recommended Approach

### Surface 1 — Main gallery slide captions (lines 938-1013)

Each slide already has a `<figure>` caption showing the dataset name and activity
number. Add the description directly below the dataset name when it exists.

```xml
<xsl:if test="nx:description/text()">
  <p class="nx-dataset-description">
    <xsl:value-of select="nx:description"/>
  </p>
</xsl:if>
```

This puts descriptions front-and-center in the scrollable gallery that most users look
at first. Because the gallery shows one dataset at a time, a short paragraph fits
naturally.

### Surface 2 — Per-activity "Dataset Notes" block (after each activity's table)

In the interactive view each activity has a left column (per-activity gallery) and a
right column (dataset table, lines 1105-1337). After the closing `</table>` of the
dataset table, emit a collapsible "Dataset notes" block **if at least one dataset in
the activity has a description**:

```
┌─────────────────────────────────────────────┐
│  Dataset Notes  ▾                           │
├─────────────────────────────────────────────┤
│  filename_001.tif  │ Lorem ipsum …          │
│  filename_002.dm3  │ Another note …         │
└─────────────────────────────────────────────┘
```

Implementation:
- Use `<xsl:if test="nx:dataset/nx:description/text()">` to guard the block.
- Render as a Bootstrap `collapse` panel with a small toggle button (already used
  elsewhere in the stylesheet for activity setup modals).
- Inside: a two-column `<dl>` (dataset name → description) or a simple `<ul>`.
- Show/hide via a `data-bs-toggle="collapse"` button — no custom JS needed.

This keeps descriptions **in the context of the activity** they belong to, directly
under (or beside) the table that lists the datasets, making the relationship clear.

### Surface 3 — Simple filelist table sub-row (lines 2213-2465)

The simple display (>100 datasets) is a flat `<table>`. For any dataset that has a
description, emit a second `<tr>` with a single `<td colspan="8">` containing the
description in muted italic text, indented slightly. This is the only viable way to
show descriptions in-context within that table without adding a column.

```xml
<xsl:if test="nx:description/text()">
  <tr class="nx-description-row">
    <td colspan="8" style="padding-left:2rem;font-style:italic;color:#555;
                           border-top:none;padding-top:0;font-size:0.875rem;">
      <xsl:value-of select="nx:description"/>
    </td>
  </tr>
</xsl:if>
```

---

## Files to Modify

| File | Change |
|------|--------|
| `xslt/detail_stylesheet.xsl` | Three targeted insertions (Surfaces 1, 2, 3 above) |

No Python, CSS, or template changes required. After editing, run
`dev-update-xslt-detail` to push the new stylesheet to the database.

---

## Verification

1. Open any record that has at least one annotated dataset.
2. **Main gallery**: description text should appear below the filename badge in the
   figure caption for each annotated dataset's slide.
3. **Activity table**: a "Dataset Notes" section should appear below the dataset table
   for any activity that has at least one description; toggling it shows/hides the list.
4. **Simple display** (manually lower `$maxDatasetCount` below the dataset count, or
   use a record with >100 datasets): description sub-rows appear under annotated
   dataset rows.
5. Datasets with no description should show no empty placeholder in any surface.
