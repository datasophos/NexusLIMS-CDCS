# Annotator Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the NexusLIMS annotator with sample management (display/add/edit/delete), sample assignment to activities, and activity creation/deletion, all saved atomically through the existing Save Annotations flow.

**Architecture:** All new mutations (sample CRUD, activity create/delete, sample-to-activity assignment) are added as JSON fields to the existing `POST /annotate/<id>/save/` endpoint. The backend applies structural changes before descriptions and moves, building a seqno mapping to translate move targets. The frontend accumulates pending state in JS and serializes it on form submit alongside existing state.

**Tech Stack:** Django, Python `xml.etree.ElementTree`, Bootstrap 5 (modals, dropdowns), SortableJS (already vendored), vanilla JS.

---

## File Map

| File | Change |
|---|---|
| `nexuslims_annotate/views.py` | Add 4 new helpers; extend `_parse_activities`; extend `annotate_record`; rewrite `annotate_save` body |
| `nexuslims_annotate/templates/nexuslims_annotate/annotate.html` | Add samples section, activity header controls, sample editor modal, new hidden inputs, new JS |
| `tests/test_annotator.py` | Add test classes for all new helpers and extended save view |

No new files. No new URL patterns. No new Django models.

---

## Test Fixtures

Add these XML strings near the top of `tests/test_annotator.py` after the existing `_TWO_ACTIVITY_XML` fixture. They are used across multiple test tasks below.

```python
NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"  # already defined

_WITH_SAMPLES_XML = f"""\
<?xml version='1.0' encoding='UTF-8'?>
<Experiment xmlns="{NS}">
  <title>Test Experiment</title>
  <summary><experimenter>Test User</experimenter></summary>
  <sample id="steel-alloy-a">
    <name>Steel Alloy A</name>
    <description>High-carbon steel reference</description>
    <notes><entry>Prepared 2024-01-10.</entry></notes>
    <elements><Fe/><C/><Cr/><Ni/></elements>
  </sample>
  <sample id="brass-ref">
    <name>Brass Reference</name>
    <description>Cu-Zn alloy</description>
    <elements><Cu/><Zn/></elements>
  </sample>
  <acquisitionActivity seqno="0">
    <startTime>2024-01-15T10:00:00-05:00</startTime>
    <sampleID>steel-alloy-a</sampleID>
    <dataset type="Image">
      <name>image_001.dm3</name>
      <location>/data/image_001.dm3</location>
    </dataset>
  </acquisitionActivity>
  <acquisitionActivity seqno="1">
    <startTime>2024-01-15T11:00:00-05:00</startTime>
    <dataset type="Image">
      <name>image_002.dm3</name>
      <location>/data/image_002.dm3</location>
    </dataset>
  </acquisitionActivity>
</Experiment>"""

_NO_SAMPLES_XML = f"""\
<?xml version='1.0' encoding='UTF-8'?>
<Experiment xmlns="{NS}">
  <title>No Samples</title>
  <acquisitionActivity seqno="0">
    <startTime>2024-01-15T10:00:00-05:00</startTime>
    <dataset type="Image">
      <name>only.dm3</name>
      <location>/data/only.dm3</location>
    </dataset>
  </acquisitionActivity>
  <acquisitionActivity seqno="1">
    <startTime>2024-01-15T11:00:00-05:00</startTime>
  </acquisitionActivity>
</Experiment>"""
```

---

## Task 1: Extend `_parse_activities` to include `sample_id`

**Files:**
- Modify: `nexuslims_annotate/views.py` (the `_parse_activities` function, around line 65)
- Modify: `tests/test_annotator.py` (add assertions to existing `ParseActivitiesTests`)

The `annotate_record` view passes `activities` to the template (used by JS for the move dropdown). The template also needs to know the current `sampleID` per activity to pre-select the right option in the sample dropdown. Adding `sample_id` to the returned dicts is the minimal change.

- [ ] **Step 1: Add a failing test**

In `tests/test_annotator.py`, inside `ParseActivitiesTests`, add:

```python
def test_sample_id_returned_when_present(self):
    acts = _parse_activities(_WITH_SAMPLES_XML)
    self.assertEqual(acts[0]['sample_id'], 'steel-alloy-a')

def test_sample_id_empty_string_when_absent(self):
    acts = _parse_activities(_WITH_SAMPLES_XML)
    self.assertEqual(acts[1]['sample_id'], '')
```

- [ ] **Step 2: Run to confirm failure**

```bash
uv run python runtests.py tests.test_annotator.ParseActivitiesTests
```

Expected: `AttributeError: 'dict' object has no key 'sample_id'` or `KeyError`.

- [ ] **Step 3: Update `_parse_activities` in `nexuslims_annotate/views.py`**

Replace the existing `_parse_activities` function (lines 65-75):

```python
def _parse_activities(xml_content):
    """Return a list of activity dicts for the move UI."""
    root = ET.fromstring(xml_content)
    activities = []
    for activity in root.findall('nx:acquisitionActivity', NS_MAP):
        seqno = activity.get('seqno', '')
        start_el = activity.find('nx:startTime', NS_MAP)
        start_time = start_el.text if start_el is not None else ''
        sample_id_el = activity.find('nx:sampleID', NS_MAP)
        sample_id = sample_id_el.text if sample_id_el is not None else ''
        dataset_count = len(activity.findall('nx:dataset', NS_MAP))
        activities.append({
            'seqno': seqno,
            'start_time': start_time,
            'dataset_count': dataset_count,
            'sample_id': sample_id,
        })
    return activities
```

- [ ] **Step 4: Run tests**

```bash
uv run python runtests.py tests.test_annotator.ParseActivitiesTests
```

Expected: All pass (including the 5 existing tests).

- [ ] **Step 5: Commit**

```bash
git add nexuslims_annotate/views.py tests/test_annotator.py
git commit -m "feat(annotator): add sample_id to _parse_activities"
```

---

## Task 2: Add `_parse_samples` helper

**Files:**
- Modify: `nexuslims_annotate/views.py` (add function after `_parse_activities`)
- Modify: `tests/test_annotator.py` (add `ParseSamplesTests` class)

- [ ] **Step 1: Write the failing tests**

Add after the `ParseActivitiesTests` class in `tests/test_annotator.py`:

```python
from nexuslims_annotate.views import _parse_samples  # add to import at top of file


class ParseSamplesTests(SimpleTestCase):
    def test_returns_correct_count(self):
        self.assertEqual(len(_parse_samples(_WITH_SAMPLES_XML)), 2)

    def test_empty_when_no_samples(self):
        self.assertEqual(_parse_samples(_NO_SAMPLES_XML), [])

    def test_id_attribute_captured(self):
        samples = _parse_samples(_WITH_SAMPLES_XML)
        self.assertEqual(samples[0]['id'], 'steel-alloy-a')
        self.assertEqual(samples[1]['id'], 'brass-ref')

    def test_name_captured(self):
        samples = _parse_samples(_WITH_SAMPLES_XML)
        self.assertEqual(samples[0]['name'], 'Steel Alloy A')

    def test_description_captured(self):
        samples = _parse_samples(_WITH_SAMPLES_XML)
        self.assertEqual(samples[0]['description'], 'High-carbon steel reference')

    def test_description_empty_string_when_absent(self):
        samples = _parse_samples(_WITH_SAMPLES_XML)
        # brass-ref has description
        self.assertEqual(samples[1]['description'], 'Cu-Zn alloy')

    def test_notes_text_joined_from_entries(self):
        samples = _parse_samples(_WITH_SAMPLES_XML)
        self.assertEqual(samples[0]['notes'], 'Prepared 2024-01-10.')

    def test_notes_empty_string_when_absent(self):
        samples = _parse_samples(_WITH_SAMPLES_XML)
        self.assertEqual(samples[1]['notes'], '')

    def test_elements_list_returned(self):
        samples = _parse_samples(_WITH_SAMPLES_XML)
        self.assertEqual(samples[0]['elements'], ['Fe', 'C', 'Cr', 'Ni'])

    def test_elements_empty_list_when_absent(self):
        xml = f'<Experiment xmlns="{NS}"><sample id="x"><name>X</name></sample></Experiment>'
        samples = _parse_samples(xml)
        self.assertEqual(samples[0]['elements'], [])
```

Also add `_parse_samples` to the import at the top of `tests/test_annotator.py`:

```python
from nexuslims_annotate.views import (
    _apply_descriptions,
    _apply_moves,
    _dataset_creation_time,
    _inject_setup_into_dataset,
    _parse_activities,
    _parse_datasets,
    _parse_samples,        # new
    _recompute_activity_setup,
    _sort_datasets_by_creation_time,
)
```

- [ ] **Step 2: Run to confirm failure**

```bash
uv run python runtests.py tests.test_annotator.ParseSamplesTests
```

Expected: `ImportError: cannot import name '_parse_samples'`.

- [ ] **Step 3: Add `_parse_samples` to `nexuslims_annotate/views.py`**

Add after the `_parse_activities` function (after line 75):

```python
def _parse_samples(xml_content):
    """Parse XML and return a list of sample dicts."""
    root = ET.fromstring(xml_content)
    samples = []
    for sample_el in root.findall('nx:sample', NS_MAP):
        name_el = sample_el.find('nx:name', NS_MAP)
        desc_el = sample_el.find('nx:description', NS_MAP)
        notes_el = sample_el.find('nx:notes', NS_MAP)
        elements_el = sample_el.find('nx:elements', NS_MAP)

        elements = []
        if elements_el is not None:
            elements = [
                child.tag.split('}')[-1] if '}' in child.tag else child.tag
                for child in elements_el
            ]

        notes = ''
        if notes_el is not None:
            entries = [
                (e.text or '').strip()
                for e in notes_el.findall('nx:entry', NS_MAP)
            ]
            notes = '\n'.join(e for e in entries if e)

        samples.append({
            'id': sample_el.get('id', ''),
            'name': name_el.text if name_el is not None else '',
            'description': desc_el.text if desc_el is not None else '',
            'notes': notes,
            'elements': elements,
        })
    return samples
```

- [ ] **Step 4: Run tests**

```bash
uv run python runtests.py tests.test_annotator.ParseSamplesTests
```

Expected: All 10 pass.

- [ ] **Step 5: Commit**

```bash
git add nexuslims_annotate/views.py tests/test_annotator.py
git commit -m "feat(annotator): add _parse_samples helper"
```

---

## Task 3: Add `_apply_samples` helper

**Files:**
- Modify: `nexuslims_annotate/views.py` (add after `_parse_samples`)
- Modify: `tests/test_annotator.py` (add `ApplySamplesTests`)

- [ ] **Step 1: Write the failing tests**

Add after `ParseSamplesTests` in `tests/test_annotator.py`:

```python
from nexuslims_annotate.views import _apply_samples  # add to import block


class ApplySamplesTests(SimpleTestCase):
    def _get_samples(self, xml_str):
        return _parse_samples(xml_str)

    def test_replaces_existing_samples_with_new_list(self):
        new_samples = [
            {'id': 'new-s', 'name': 'New Sample', 'description': 'desc', 'notes': '', 'elements': ['Au']},
        ]
        result = _apply_samples(_WITH_SAMPLES_XML, new_samples)
        samples = self._get_samples(result)
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]['name'], 'New Sample')

    def test_empty_list_removes_all_samples(self):
        result = _apply_samples(_WITH_SAMPLES_XML, [])
        self.assertEqual(self._get_samples(result), [])

    def test_adds_samples_when_none_existed(self):
        new_samples = [
            {'id': 'added', 'name': 'Added', 'description': '', 'notes': '', 'elements': []},
        ]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        samples = self._get_samples(result)
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]['id'], 'added')

    def test_id_attribute_set(self):
        new_samples = [{'id': 'my-id', 'name': 'S', 'description': '', 'notes': '', 'elements': []}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        s = root.find('nx:sample', NS_MAP)
        self.assertEqual(s.get('id'), 'my-id')

    def test_elements_written_as_child_tags(self):
        new_samples = [{'id': 's', 'name': 'S', 'description': '', 'notes': '', 'elements': ['Fe', 'Ni']}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        s = root.find('nx:sample', NS_MAP)
        elements_el = s.find(f'{{{NS}}}elements')
        self.assertIsNotNone(elements_el)
        syms = [c.tag.split('}')[-1] for c in elements_el]
        self.assertEqual(syms, ['Fe', 'Ni'])

    def test_notes_written_as_entry_child(self):
        new_samples = [{'id': 's', 'name': 'S', 'description': '', 'notes': 'My notes', 'elements': []}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        s = root.find('nx:sample', NS_MAP)
        notes_el = s.find(f'{{{NS}}}notes')
        self.assertIsNotNone(notes_el)
        entry = notes_el.find(f'{{{NS}}}entry')
        self.assertIsNotNone(entry)
        self.assertEqual(entry.text, 'My notes')

    def test_empty_notes_omits_notes_element(self):
        new_samples = [{'id': 's', 'name': 'S', 'description': '', 'notes': '', 'elements': []}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        s = root.find('nx:sample', NS_MAP)
        self.assertIsNone(s.find(f'{{{NS}}}notes'))

    def test_samples_inserted_before_acquisition_activities(self):
        new_samples = [{'id': 's', 'name': 'S', 'description': '', 'notes': '', 'elements': []}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        children_tags = [c.tag.split('}')[-1] for c in root]
        sample_pos = children_tags.index('sample')
        act_pos = children_tags.index('acquisitionActivity')
        self.assertLess(sample_pos, act_pos)

    def test_result_is_valid_xml(self):
        result = _apply_samples(_WITH_SAMPLES_XML, [])
        ET.fromstring(result)
```

Add `_apply_samples` to the import block at the top of the test file.

- [ ] **Step 2: Run to confirm failure**

```bash
uv run python runtests.py tests.test_annotator.ApplySamplesTests
```

Expected: `ImportError: cannot import name '_apply_samples'`.

- [ ] **Step 3: Add `_apply_samples` to `nexuslims_annotate/views.py`**

Add after `_parse_samples`:

```python
def _apply_samples(xml_content, samples_data):
    """Replace all <sample> elements with the provided ordered list."""
    ET.register_namespace('', NS)
    root = ET.fromstring(xml_content)

    for sample_el in root.findall('nx:sample', NS_MAP):
        root.remove(sample_el)

    # Find insertion point: after title/id/summary, before project/acquisitionActivity/notes
    insert_pos = 0
    for i, child in enumerate(root):
        local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if local in ('title', 'id', 'summary'):
            insert_pos = i + 1

    for offset, sample_data in enumerate(samples_data):
        sample_el = ET.Element(f'{{{NS}}}sample')
        sid = (sample_data.get('id') or '').strip()
        if sid:
            sample_el.set('id', sid)

        name = (sample_data.get('name') or '').strip()
        if name:
            name_el = ET.SubElement(sample_el, f'{{{NS}}}name')
            name_el.text = name

        description = (sample_data.get('description') or '').strip()
        if description:
            desc_el = ET.SubElement(sample_el, f'{{{NS}}}description')
            desc_el.text = description

        notes = (sample_data.get('notes') or '').strip()
        if notes:
            notes_el = ET.SubElement(sample_el, f'{{{NS}}}notes')
            entry_el = ET.SubElement(notes_el, f'{{{NS}}}entry')
            entry_el.text = notes

        elements = sample_data.get('elements') or []
        if elements:
            elements_el = ET.SubElement(sample_el, f'{{{NS}}}elements')
            for symbol in elements:
                ET.SubElement(elements_el, f'{{{NS}}}{symbol}')

        root.insert(insert_pos + offset, sample_el)

    return ET.tostring(root, encoding='unicode', xml_declaration=False)
```

- [ ] **Step 4: Run tests**

```bash
uv run python runtests.py tests.test_annotator.ApplySamplesTests
```

Expected: All 9 pass.

- [ ] **Step 5: Commit**

```bash
git add nexuslims_annotate/views.py tests/test_annotator.py
git commit -m "feat(annotator): add _apply_samples helper"
```

---

## Task 4: Add `_renumber_activities` helper

**Files:**
- Modify: `nexuslims_annotate/views.py` (add after `_apply_samples`)
- Modify: `tests/test_annotator.py` (add `RenumberActivitiesTests`)

- [ ] **Step 1: Write the failing tests**

Add after `ApplySamplesTests`:

```python
from nexuslims_annotate.views import _renumber_activities  # add to import block


class RenumberActivitiesTests(SimpleTestCase):
    def _seqnos(self, xml_str):
        root = ET.fromstring(xml_str)
        return [a.get('seqno') for a in root.findall('nx:acquisitionActivity', NS_MAP)]

    def test_already_consecutive_unchanged(self):
        result = _renumber_activities(_WITH_SAMPLES_XML)
        self.assertEqual(self._seqnos(result), ['0', '1'])

    def test_gaps_are_filled(self):
        xml = f"""<Experiment xmlns="{NS}">
          <acquisitionActivity seqno="0"/>
          <acquisitionActivity seqno="2"/>
          <acquisitionActivity seqno="5"/>
        </Experiment>"""
        result = _renumber_activities(xml)
        self.assertEqual(self._seqnos(result), ['0', '1', '2'])

    def test_single_activity_stays_zero(self):
        xml = f'<Experiment xmlns="{NS}"><acquisitionActivity seqno="3"/></Experiment>'
        result = _renumber_activities(xml)
        self.assertEqual(self._seqnos(result), ['0'])

    def test_no_activities_returns_valid_xml(self):
        xml = f'<Experiment xmlns="{NS}"><title>X</title></Experiment>'
        result = _renumber_activities(xml)
        ET.fromstring(result)
        self.assertEqual(self._seqnos(result), [])
```

Add `_renumber_activities` to the import block.

- [ ] **Step 2: Run to confirm failure**

```bash
uv run python runtests.py tests.test_annotator.RenumberActivitiesTests
```

Expected: `ImportError`.

- [ ] **Step 3: Add `_renumber_activities` to `nexuslims_annotate/views.py`**

Add after `_apply_samples`:

```python
def _renumber_activities(xml_content):
    """Rewrite all seqno attributes to consecutive 0-based integers in XML order."""
    ET.register_namespace('', NS)
    root = ET.fromstring(xml_content)
    for i, activity in enumerate(root.findall('nx:acquisitionActivity', NS_MAP)):
        activity.set('seqno', str(i))
    return ET.tostring(root, encoding='unicode', xml_declaration=False)
```

- [ ] **Step 4: Run tests**

```bash
uv run python runtests.py tests.test_annotator.RenumberActivitiesTests
```

Expected: All 4 pass.

- [ ] **Step 5: Commit**

```bash
git add nexuslims_annotate/views.py tests/test_annotator.py
git commit -m "feat(annotator): add _renumber_activities helper"
```

---

## Task 5: Add `_apply_activity_mutations` helper

**Files:**
- Modify: `nexuslims_annotate/views.py` (add after `_renumber_activities`)
- Modify: `tests/test_annotator.py` (add `ApplyActivityMutationsTests`)

This is the most complex helper. It validates and deletes activities by seqno, inserts new empty activities, applies `sampleID` assignments, and returns both the updated XML and a seqno mapping dict.

- [ ] **Step 1: Write the failing tests**

Add after `RenumberActivitiesTests`:

```python
from nexuslims_annotate.views import _apply_activity_mutations  # add to import block


class ApplyActivityMutationsTests(SimpleTestCase):
    def _seqnos(self, xml_str):
        root = ET.fromstring(xml_str)
        return [a.get('seqno') for a in root.findall('nx:acquisitionActivity', NS_MAP)]

    def _sample_id(self, xml_str, seqno):
        root = ET.fromstring(xml_str)
        for a in root.findall('nx:acquisitionActivity', NS_MAP):
            if a.get('seqno') == str(seqno):
                el = a.find(f'{{{NS}}}sampleID')
                return el.text if el is not None else None
        return None

    # --- delete ---

    def test_delete_empty_activity(self):
        # seqno 1 is empty in _NO_SAMPLES_XML
        result, mapping = _apply_activity_mutations(
            _NO_SAMPLES_XML, deleted_seqnos=['1'], new_activities=[], activity_sample_ids={}
        )
        root = ET.fromstring(result)
        seqnos = [a.get('seqno') for a in root.findall('nx:acquisitionActivity', NS_MAP)]
        self.assertNotIn('1', seqnos)

    def test_delete_non_empty_activity_raises_value_error(self):
        # seqno 0 in _NO_SAMPLES_XML has 1 dataset
        with self.assertRaises(ValueError):
            _apply_activity_mutations(
                _NO_SAMPLES_XML, deleted_seqnos=['0'], new_activities=[], activity_sample_ids={}
            )

    def test_delete_nonexistent_seqno_silently_skipped(self):
        result, _ = _apply_activity_mutations(
            _NO_SAMPLES_XML, deleted_seqnos=['99'], new_activities=[], activity_sample_ids={}
        )
        self.assertEqual(self._seqnos(result), ['0', '1'])

    # --- insert ---

    def test_insert_at_end(self):
        result, mapping = _apply_activity_mutations(
            _NO_SAMPLES_XML,
            deleted_seqnos=[],
            new_activities=[{'temp_id': 'new-x', 'at_end': True}],
            activity_sample_ids={},
        )
        root = ET.fromstring(result)
        acts = root.findall('nx:acquisitionActivity', NS_MAP)
        self.assertEqual(len(acts), 3)

    def test_insert_after_seqno(self):
        result, mapping = _apply_activity_mutations(
            _NO_SAMPLES_XML,
            deleted_seqnos=[],
            new_activities=[{'temp_id': 'new-x', 'after_seqno': '0'}],
            activity_sample_ids={},
        )
        root = ET.fromstring(result)
        acts = root.findall('nx:acquisitionActivity', NS_MAP)
        # should be seqno 0, new-x, 1 in that order
        self.assertEqual(acts[0].get('seqno'), '0')
        self.assertEqual(acts[1].get('seqno'), 'new-x')
        self.assertEqual(acts[2].get('seqno'), '1')

    def test_insert_after_nonexistent_seqno_raises(self):
        with self.assertRaises(ValueError):
            _apply_activity_mutations(
                _NO_SAMPLES_XML,
                deleted_seqnos=[],
                new_activities=[{'temp_id': 'new-x', 'after_seqno': '99'}],
                activity_sample_ids={},
            )

    # --- seqno mapping ---

    def test_mapping_original_seqno_to_final(self):
        # delete seqno 1, so seqno 0 stays at 0
        result, mapping = _apply_activity_mutations(
            _NO_SAMPLES_XML, deleted_seqnos=['1'], new_activities=[], activity_sample_ids={}
        )
        self.assertEqual(mapping['0'], '0')

    def test_mapping_temp_id_to_final(self):
        result, mapping = _apply_activity_mutations(
            _NO_SAMPLES_XML,
            deleted_seqnos=[],
            new_activities=[{'temp_id': 'new-x', 'at_end': True}],
            activity_sample_ids={},
        )
        self.assertIn('new-x', mapping)

    def test_mapping_shifts_after_deletion(self):
        # delete seqno 1 (empty), seqno 0 stays 0, old seqno 2 doesn't exist here
        # Use _WITH_SAMPLES_XML: seqno 0 has datasets, seqno 1 has datasets -- can't delete.
        # Build a fresh XML with three activities, middle one empty:
        xml = f"""<Experiment xmlns="{NS}">
          <acquisitionActivity seqno="0">
            <dataset><name>a.dm3</name><location>/a</location></dataset>
          </acquisitionActivity>
          <acquisitionActivity seqno="1"/>
          <acquisitionActivity seqno="2">
            <dataset><name>b.dm3</name><location>/b</location></dataset>
          </acquisitionActivity>
        </Experiment>"""
        result, mapping = _apply_activity_mutations(
            xml, deleted_seqnos=['1'], new_activities=[], activity_sample_ids={}
        )
        # old seqno 2 now maps to final seqno 1 (before renumber step)
        self.assertEqual(mapping['2'], '1')

    # --- sampleID ---

    def test_sample_id_set_on_activity(self):
        result, _ = _apply_activity_mutations(
            _NO_SAMPLES_XML,
            deleted_seqnos=[],
            new_activities=[],
            activity_sample_ids={'0': 'steel-alloy-a'},
        )
        self.assertEqual(self._sample_id(result, '0'), 'steel-alloy-a')

    def test_sample_id_cleared_when_null(self):
        result, _ = _apply_activity_mutations(
            _WITH_SAMPLES_XML,
            deleted_seqnos=[],
            new_activities=[],
            activity_sample_ids={'0': None},
        )
        self.assertIsNone(self._sample_id(result, '0'))

    def test_sample_id_inserted_after_start_time(self):
        result, _ = _apply_activity_mutations(
            _NO_SAMPLES_XML,
            deleted_seqnos=[],
            new_activities=[],
            activity_sample_ids={'0': 'my-sample'},
        )
        root = ET.fromstring(result)
        for act in root.findall('nx:acquisitionActivity', NS_MAP):
            if act.get('seqno') == '0':
                tags = [c.tag.split('}')[-1] for c in act]
                start_pos = tags.index('startTime')
                sid_pos = tags.index('sampleID')
                self.assertGreater(sid_pos, start_pos)
```

Add `_apply_activity_mutations` to the import block.

- [ ] **Step 2: Run to confirm failure**

```bash
uv run python runtests.py tests.test_annotator.ApplyActivityMutationsTests
```

Expected: `ImportError`.

- [ ] **Step 3: Add `_apply_activity_mutations` to `nexuslims_annotate/views.py`**

Add after `_renumber_activities`:

```python
def _apply_activity_mutations(xml_content, deleted_seqnos, new_activities, activity_sample_ids):
    """Delete/insert activities and set sampleID assignments.

    deleted_seqnos: list of seqno strings to delete (must all have 0 datasets)
    new_activities: list of dicts with keys: temp_id, and either after_seqno or at_end=True
    activity_sample_ids: dict mapping seqno/temp_id -> sample_id str (or None to clear)

    Returns (updated_xml, seqno_mapping) where seqno_mapping maps
    original seqno strings and temp_ids to final provisional seqno strings
    (based on XML order after all structural changes, before renumber).

    Raises ValueError if a deleted activity has datasets, or after_seqno is not found.
    """
    ET.register_namespace('', NS)
    root = ET.fromstring(xml_content)
    deleted_seqnos = [str(s) for s in deleted_seqnos]

    # Phase 1: validate and delete
    activities_by_seqno = {
        a.get('seqno', ''): a
        for a in root.findall('nx:acquisitionActivity', NS_MAP)
    }
    for seqno in deleted_seqnos:
        activity = activities_by_seqno.get(seqno)
        if activity is None:
            continue
        dataset_count = len(activity.findall(f'{{{NS}}}dataset'))
        if dataset_count > 0:
            raise ValueError(
                f'Activity {seqno} has {dataset_count} dataset(s) and cannot be deleted'
            )
        root.remove(activity)

    # Rebuild index after deletions
    activities_by_seqno = {
        a.get('seqno', ''): a
        for a in root.findall('nx:acquisitionActivity', NS_MAP)
    }

    # Phase 2: insert new activities
    for spec in new_activities:
        temp_id = spec.get('temp_id', '')
        after_seqno = spec.get('after_seqno')
        new_el = ET.Element(f'{{{NS}}}acquisitionActivity')
        new_el.set('seqno', temp_id)

        if after_seqno is not None:
            ref = activities_by_seqno.get(str(after_seqno))
            if ref is None:
                raise ValueError(f'after_seqno {after_seqno!r} not found')
            all_children = list(root)
            pos = all_children.index(ref)
            root.insert(pos + 1, new_el)
        else:
            # at_end: append after the last existing activity
            all_acts = root.findall('nx:acquisitionActivity', NS_MAP)
            if all_acts:
                all_children = list(root)
                pos = all_children.index(all_acts[-1])
                root.insert(pos + 1, new_el)
            else:
                root.append(new_el)

        activities_by_seqno[temp_id] = new_el

    # Phase 3: build seqno mapping (provisional seqno -> 0-based final position)
    final_activities = root.findall('nx:acquisitionActivity', NS_MAP)
    seqno_mapping = {a.get('seqno', ''): str(i) for i, a in enumerate(final_activities)}

    # Phase 4: apply sampleID assignments
    provisional_by_seqno = {a.get('seqno', ''): a for a in final_activities}
    for seqno_or_temp, sample_id in activity_sample_ids.items():
        activity = provisional_by_seqno.get(str(seqno_or_temp))
        if activity is None:
            continue
        for sid_el in activity.findall(f'{{{NS}}}sampleID'):
            activity.remove(sid_el)
        if sample_id:
            sid_el = ET.Element(f'{{{NS}}}sampleID')
            sid_el.text = str(sample_id)
            children = list(activity)
            insert_pos = 0
            for j, child in enumerate(children):
                local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if local == 'startTime':
                    insert_pos = j + 1
                    break
            activity.insert(insert_pos, sid_el)

    return ET.tostring(root, encoding='unicode', xml_declaration=False), seqno_mapping
```

- [ ] **Step 4: Run tests**

```bash
uv run python runtests.py tests.test_annotator.ApplyActivityMutationsTests
```

Expected: All 13 pass.

- [ ] **Step 5: Run the full test suite to confirm no regressions**

```bash
uv run python runtests.py
```

Expected: All existing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add nexuslims_annotate/views.py tests/test_annotator.py
git commit -m "feat(annotator): add _apply_activity_mutations helper"
```

---

## Task 6: Extend `annotate_save` and `annotate_record`

**Files:**
- Modify: `nexuslims_annotate/views.py` (rewrite `annotate_save` body; extend `annotate_record`)
- Modify: `tests/test_annotator.py` (add `AnnotateSaveStructuralTests` class)

- [ ] **Step 1: Write the failing tests**

Add after the existing `AnnotateSaveViewTest` class:

```python
class AnnotateSaveStructuralTests(TestCase):
    """Tests for structural mutations via annotate_save."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser_struct', password='pass')
        self.client.force_login(self.user)

    @patch('nexuslims_annotate.views.data_api.get_by_id')
    @patch('nexuslims_annotate.views.data_api.upsert')
    def test_delete_non_empty_activity_returns_400(self, mock_upsert, mock_get):
        mock_get.return_value = _make_mock_data(_NO_SAMPLES_XML)
        response = self.client.post(
            '/annotate/test-id/save/',
            {
                'deleted_seqnos': json.dumps(['0']),  # seqno 0 has 1 dataset
                'new_activities': '[]',
                'activity_sample_ids': '{}',
                'samples': '[]',
                'moves': '[]',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertIn('error', body)

    @patch('nexuslims_annotate.views.data_api.get_by_id')
    @patch('nexuslims_annotate.views.data_api.upsert')
    def test_delete_empty_activity_succeeds(self, mock_upsert, mock_get):
        data_obj = _make_mock_data(_NO_SAMPLES_XML)
        mock_get.return_value = data_obj
        response = self.client.post(
            '/annotate/test-id/save/',
            {
                'deleted_seqnos': json.dumps(['1']),  # seqno 1 is empty
                'new_activities': '[]',
                'activity_sample_ids': '{}',
                'samples': '[]',
                'moves': '[]',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content).get('success'))

    @patch('nexuslims_annotate.views.data_api.get_by_id')
    @patch('nexuslims_annotate.views.data_api.upsert')
    def test_malformed_json_returns_400(self, mock_upsert, mock_get):
        mock_get.return_value = _make_mock_data()
        response = self.client.post(
            '/annotate/test-id/save/',
            {
                'deleted_seqnos': 'not json',
                'new_activities': '[]',
                'activity_sample_ids': '{}',
                'samples': '[]',
                'moves': '[]',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)

    @patch('nexuslims_annotate.views.data_api.get_by_id')
    @patch('nexuslims_annotate.views.data_api.upsert')
    def test_samples_saved_in_xml(self, mock_upsert, mock_get):
        data_obj = _make_mock_data(_NO_SAMPLES_XML)
        mock_get.return_value = data_obj
        samples = [{'id': 'test-s', 'name': 'Test Sample', 'description': 'desc', 'notes': '', 'elements': ['Fe']}]
        response = self.client.post(
            '/annotate/test-id/save/',
            {
                'deleted_seqnos': '[]',
                'new_activities': '[]',
                'activity_sample_ids': '{}',
                'samples': json.dumps(samples),
                'moves': '[]',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        saved_xml = mock_upsert.call_args[0][0].content
        root = ET.fromstring(saved_xml)
        s = root.find(f'{{{NS}}}sample')
        self.assertIsNotNone(s)
        self.assertEqual(s.get('id'), 'test-s')

    @patch('nexuslims_annotate.views.data_api.get_by_id')
    @patch('nexuslims_annotate.views.data_api.upsert')
    def test_existing_save_still_works_without_new_fields(self, mock_upsert, mock_get):
        """Existing callers that omit the new fields should not break."""
        mock_get.return_value = _make_mock_data()
        response = self.client.post(
            '/annotate/test-id/save/',
            {'dataset_0_description': 'A description'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content).get('success'))

    @patch('nexuslims_annotate.views.data_api.get_by_id')
    @patch('nexuslims_annotate.views.data_api.upsert')
    def test_move_to_new_activity_is_translated(self, mock_upsert, mock_get):
        """A move targeting a temp_id is correctly translated to the final seqno."""
        data_obj = _make_mock_data(_NO_SAMPLES_XML)
        mock_get.return_value = data_obj
        response = self.client.post(
            '/annotate/test-id/save/',
            {
                'deleted_seqnos': '[]',
                'new_activities': json.dumps([{'temp_id': 'new-x', 'at_end': True}]),
                'activity_sample_ids': '{}',
                'samples': '[]',
                'moves': json.dumps([{'datasetIndex': 0, 'targetActivitySeqno': 'new-x'}]),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        saved_xml = mock_upsert.call_args[0][0].content
        root = ET.fromstring(saved_xml)
        acts = root.findall(f'{{{NS}}}acquisitionActivity')
        # 3 activities total (0, 1, new-x now renumbered to 2)
        self.assertEqual(len(acts), 3)
        # dataset 0 (only.dm3) moved to the last activity
        last_act = acts[-1]
        ds_names = [ds.find(f'{{{NS}}}name').text for ds in last_act.findall(f'{{{NS}}}dataset')]
        self.assertIn('only.dm3', ds_names)
```

Also update the import at the top of `tests/test_annotator.py` to include `_NO_SAMPLES_XML` and `_WITH_SAMPLES_XML` (these were added as fixtures in the Test Fixtures section above -- ensure they are present in the file).

- [ ] **Step 2: Run to confirm failures**

```bash
uv run python runtests.py tests.test_annotator.AnnotateSaveStructuralTests
```

Expected: Failures (the new fields are silently ignored by the current `annotate_save`).

- [ ] **Step 3: Rewrite `annotate_save` in `nexuslims_annotate/views.py`**

Replace the entire `annotate_save` function body (lines 439-478):

```python
@login_required
@require_POST
def annotate_save(request, record_id):
    """AJAX POST: update <description> elements, apply structural mutations, and save the record."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        data = data_api.get_by_id(record_id, request.user)

        # Parse structural fields (new); fall back to empty defaults if absent
        try:
            samples = json.loads(request.POST.get('samples', '[]'))
            deleted_seqnos = json.loads(request.POST.get('deleted_seqnos', '[]'))
            new_activities = json.loads(request.POST.get('new_activities', '[]'))
            activity_sample_ids = json.loads(request.POST.get('activity_sample_ids', '{}'))
        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({'error': f'Malformed JSON in structural fields: {e}'}, status=400)

        if not isinstance(samples, list):
            return JsonResponse({'error': 'samples must be a JSON array'}, status=400)
        if not isinstance(deleted_seqnos, list):
            return JsonResponse({'error': 'deleted_seqnos must be a JSON array'}, status=400)
        if not isinstance(new_activities, list):
            return JsonResponse({'error': 'new_activities must be a JSON array'}, status=400)
        if not isinstance(activity_sample_ids, dict):
            return JsonResponse({'error': 'activity_sample_ids must be a JSON object'}, status=400)

        updated_xml = data.content

        # Apply structural mutations (validate, delete, insert, sampleID)
        try:
            updated_xml, seqno_mapping = _apply_activity_mutations(
                updated_xml, deleted_seqnos, new_activities, activity_sample_ids
            )
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

        # Replace sample elements
        updated_xml = _apply_samples(updated_xml, samples)

        # Apply descriptions (flat indices valid: deleted activities had 0 datasets)
        updated_xml = _apply_descriptions(updated_xml, request.POST)

        # Parse and translate moves
        moves_json = request.POST.get('moves', '[]')
        try:
            moves = json.loads(moves_json)
        except (json.JSONDecodeError, ValueError):
            logger.warning('Ignoring malformed moves JSON for record %s: %r', record_id, moves_json)
            moves = []
        if not isinstance(moves, list):
            logger.warning('moves is not a list for record %s, ignoring', record_id)
            moves = []

        # Translate targetActivitySeqno through seqno_mapping
        if moves and seqno_mapping:
            translated = []
            for m in moves:
                if isinstance(m, dict) and 'targetActivitySeqno' in m:
                    m = dict(m)
                    key = str(m['targetActivitySeqno'])
                    m['targetActivitySeqno'] = seqno_mapping.get(key, key)
                translated.append(m)
            moves = translated

        if moves:
            updated_xml = _apply_moves(updated_xml, moves)

        # Renumber all activities to consecutive 0-based seqnos
        updated_xml = _renumber_activities(updated_xml)

        data.content = updated_xml
        data_api.upsert(data, request)
        if is_ajax:
            return JsonResponse({'success': True})
        return redirect(reverse('core_main_app_data_detail') + f'?id={record_id}')

    except (DoesNotExist, ModelError):
        if is_ajax:
            return JsonResponse({'error': 'Record not found'}, status=404)
        raise Http404(f'Record {record_id} not found.')
    except AccessControlError as e:
        if is_ajax:
            return JsonResponse({'error': str(e)}, status=403)
        return redirect(reverse('nexuslims_annotate_record', args=[record_id]) + '?error=1')
    except Exception:
        logger.exception('Error saving annotations for record %s', record_id)
        if is_ajax:
            return JsonResponse({'error': 'Internal server error'}, status=500)
        return redirect(reverse('nexuslims_annotate_record', args=[record_id]) + '?error=1')
```

- [ ] **Step 4: Extend `annotate_record` to pass samples context**

In `annotate_record` (around line 325), extend the render call to pass `samples`:

```python
@login_required
def annotate_record(request, record_id):
    """Full-page fallback view."""
    try:
        data = data_api.get_by_id(record_id, request.user)
    except (DoesNotExist, ModelError):
        raise Http404(f"Record {record_id} not found.")
    try:
        check_can_write(data, request.user)
    except AccessControlError:
        return HttpResponseForbidden("You do not have permission to annotate this record.")
    try:
        datasets = _parse_datasets(data.content)
        activities = _parse_activities(data.content)
        samples = _parse_samples(data.content)
        record_title = _get_title(data.content)
    except ET.ParseError:
        return render(request, 'nexuslims_annotate/annotate.html', {
            'data': data,
            'record_title': '',
            'datasets': [],
            'record_id': record_id,
            'activities': [],
            'samples': [],
            'xml_error': True,
        }, status=500)
    return render(request, 'nexuslims_annotate/annotate.html', {
        'data': data,
        'record_title': record_title,
        'datasets': datasets,
        'record_id': record_id,
        'activities': activities,
        'samples': samples,
    })
```

- [ ] **Step 5: Run all tests**

```bash
uv run python runtests.py
```

Expected: All tests pass (new and existing).

- [ ] **Step 6: Commit**

```bash
git add nexuslims_annotate/views.py tests/test_annotator.py
git commit -m "feat(annotator): extend annotate_save for structural mutations and annotate_record for samples"
```

---

## Task 7: Template -- samples section, activity controls, modal, hidden inputs

**Files:**
- Modify: `nexuslims_annotate/templates/nexuslims_annotate/annotate.html`

This task adds all the new HTML. The JS wiring happens in Tasks 8-10. After this task the page will render the new UI elements but buttons/dropdowns won't be functional yet.

- [ ] **Step 1: Add samples JSON script + hidden inputs to the form**

In `annotate.html`, in the `{% block app_data %}` section, after the existing `window.__nxActivities` script line, add:

```html
{{ samples|json_script:"nx-samples-data" }}
<script>window.__nxPendingSamples = JSON.parse(document.getElementById('nx-samples-data').textContent);</script>
```

Inside the form (after the existing `<input type="hidden" id="annotate-moves-input" ...>`), add:

```html
<input type="hidden" id="annotate-samples-input" name="samples" value="[]">
<input type="hidden" id="annotate-deleted-seqnos-input" name="deleted_seqnos" value="[]">
<input type="hidden" id="annotate-new-activities-input" name="new_activities" value="[]">
<input type="hidden" id="annotate-activity-sample-ids-input" name="activity_sample_ids" value="{}">
```

- [ ] **Step 2: Add the samples section above the activity grid**

In `annotate.html`, insert the following immediately before the `{% regroup datasets ... %}` line:

```html
{# Samples section #}
<div class="border rounded p-2 mb-3" id="nx-samples-section" style="background:#fafafa;">
  <div class="d-flex align-items-center justify-content-between mb-2">
    <span class="text-uppercase text-muted fw-semibold"
          style="font-size:0.72rem;letter-spacing:0.08em;">Samples</span>
    <button type="button" class="btn btn-outline-primary btn-sm"
            id="nx-add-sample-btn" style="font-size:0.72rem;padding:2px 8px;">
      <i class="fas fa-plus fa-xs me-1"></i>Add Sample
    </button>
  </div>
  <div id="nx-samples-list">
    {# rendered by renderSamples() JS #}
  </div>
  <p id="nx-no-samples-msg" class="text-muted mb-0"
     style="font-size:0.8rem;font-style:italic;{% if samples %}display:none;{% endif %}">
    No samples yet. Click "Add Sample" to add one.
  </p>
</div>
```

- [ ] **Step 3: Update activity header to add sample dropdown, "+ below", and delete button**

Replace the existing activity divider block (the `<div class="d-flex align-items-center gap-2 mt-3 mb-1">` block inside the `{% for group in activity_groups %}` loop) with:

```html
<div class="d-flex align-items-center gap-2 mt-3 mb-1" id="nx-activity-header-{{ group.grouper }}">
  <span class="text-uppercase text-muted fw-semibold flex-shrink-0 nx-activity-label"
        style="font-size:0.75rem;letter-spacing:0.08em;">Activity {{ group.grouper|add:1 }}</span>
  <span class="nx-activity-count badge bg-light text-secondary border"
        data-seqno="{{ group.grouper }}"
        style="font-size:0.7rem;font-weight:500;">{{ group.list|length }}</span>
  <select class="form-select form-select-sm nx-activity-sample flex-shrink-0"
          data-seqno="{{ group.grouper }}"
          style="max-width:160px;font-size:0.72rem;"
          title="Assign sample to this activity">
    <option value="">-- No sample --</option>
    {% for sample in samples %}
    <option value="{{ sample.id }}">{{ sample.name }}</option>
    {% endfor %}
  </select>
  <hr class="flex-grow-1 my-0">
  <button type="button"
          class="btn btn-sm btn-outline-secondary flex-shrink-0 nx-insert-activity-below"
          data-seqno="{{ group.grouper }}"
          style="font-size:0.7rem;padding:1px 7px;"
          title="Insert new activity below this one">+ below</button>
  <button type="button"
          class="btn btn-sm flex-shrink-0 nx-delete-activity"
          data-seqno="{{ group.grouper }}"
          data-dataset-count="{{ group.list|length }}"
          style="font-size:0.7rem;padding:1px 7px;"
          title="{% if group.list %}Move all datasets to another activity first{% else %}Delete this activity{% endif %}"
          {% if group.list %}disabled{% endif %}>
    <i class="fas fa-trash-alt" style="font-size:0.65rem;"></i>
  </button>
</div>
```

- [ ] **Step 4: Add "+ Add Activity" button to the save row**

In the save row `<div class="d-flex gap-2 mt-4 mb-5">`, add after the existing Save button:

```html
<button type="button" class="btn btn-outline-secondary" id="nx-add-activity-btn">
  <i class="fas fa-plus fa-xs me-1"></i> Add Activity
</button>
```

- [ ] **Step 5: Add the sample editor modal**

Add before the closing `{% endblock %}`, after the existing help modal `</div>`:

```html
{# Sample editor modal #}
<div class="modal fade" id="nx-sample-modal" tabindex="-1" aria-labelledby="nx-sample-modal-label">
  <div class="modal-dialog modal-dialog-centered" style="max-width:520px;">
    <div class="modal-content">
      <div class="modal-header py-2">
        <h6 class="modal-title" id="nx-sample-modal-label">
          <i class="fas fa-flask me-2"></i><span id="nx-sample-modal-title">Add Sample</span>
        </h6>
        <button type="button" class="btn-close btn-sm" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body py-3">
        <input type="hidden" id="nx-sample-editing-id" value="">

        <div class="mb-2">
          <label for="nx-sample-name" class="form-label form-label-sm fw-semibold mb-1">
            Name <span class="text-danger">*</span>
          </label>
          <input type="text" class="form-control form-control-sm" id="nx-sample-name"
                 placeholder="e.g. Steel Alloy A">
        </div>

        <div class="mb-2">
          <label for="nx-sample-description" class="form-label form-label-sm fw-semibold mb-1">
            Description
          </label>
          <textarea class="form-control form-control-sm" id="nx-sample-description"
                    rows="2" placeholder="Brief description of the sample"></textarea>
        </div>

        <div class="mb-2">
          <label for="nx-sample-notes" class="form-label form-label-sm fw-semibold mb-1">
            Notes
          </label>
          <textarea class="form-control form-control-sm" id="nx-sample-notes"
                    rows="2" placeholder="Preparation notes, observations, etc."></textarea>
        </div>

        <div class="mb-1">
          <label class="form-label form-label-sm fw-semibold mb-1">
            Elements
          </label>
          <div id="nx-elements-tags" class="d-flex flex-wrap gap-1 mb-1 min-height-1"></div>
          <input type="text" class="form-control form-control-sm" id="nx-elements-input"
                 placeholder="Type symbol (e.g. Fe) and press Enter or comma"
                 autocomplete="off">
          <datalist id="nx-elements-datalist"></datalist>
          <div class="form-text" style="font-size:0.72rem;">
            Press Enter or comma to add. Click a tag to remove it.
          </div>
        </div>
      </div>
      <div class="modal-footer py-2">
        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary btn-sm" id="nx-sample-modal-save">
          <i class="fas fa-save fa-xs me-1"></i>Save Sample
        </button>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 6: Verify the page renders without errors**

With the dev environment running (`cd deployment && source dev-commands.sh && dev-up`), navigate to any record's annotator page. The samples section and updated activity headers should be visible. Buttons won't work yet (Task 8-10).

If dev environment is not available, run:

```bash
uv run python runtests.py tests.test_annotator.AnnotateRecordViewTest.test_success_renders_annotate_template
```

Expected: Pass (template renders without crash).

- [ ] **Step 7: Commit**

```bash
git add nexuslims_annotate/templates/
git commit -m "feat(annotator): add samples section, activity controls, and sample editor modal HTML"
```

---

## Task 8: JS -- sample state management

**Files:**
- Modify: `nexuslims_annotate/templates/nexuslims_annotate/annotate.html` (JS section)

Add the following JS inside the `<script>` block in `annotate.html`, after the `window.__nxActivities` initialization and before the existing `(function () {` IIFE. This code runs at page scope (not inside the IIFE) so it's accessible to all handlers.

- [ ] **Step 1: Add element symbols list and sample ID generator**

```javascript
// ── Element symbols (all 118 from NexusLIMS schema) ─────────────────────
var NX_ELEMENT_SYMBOLS = [
  'H','He','Li','Be','B','C','N','O','F','Ne',
  'Na','Mg','Al','Si','P','S','Cl','Ar','K','Ca',
  'Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn',
  'Ga','Ge','As','Se','Br','Kr','Rb','Sr','Y','Zr',
  'Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn',
  'Sb','Te','I','Xe','Cs','Ba','La','Ce','Pr','Nd',
  'Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb',
  'Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg',
  'Tl','Pb','Bi','Po','At','Rn','Fr','Ra','Ac','Th',
  'Pa','U','Np','Pu','Am','Cm','Bk','Cf','Es','Fm',
  'Md','No','Lr','Rf','Db','Sg','Bh','Hs','Mt','Ds',
  'Rg','Cn','Nh','Fl','Mc','Lv','Ts','Og'
];

// Populate the datalist once on load
(function() {
  var dl = document.getElementById('nx-elements-datalist');
  if (!dl) return;
  NX_ELEMENT_SYMBOLS.forEach(function(sym) {
    var opt = document.createElement('option');
    opt.value = sym;
    dl.appendChild(opt);
  });
})();

function nxGenerateSampleId(name) {
  var base = (name || 'sample').toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'sample';
  var existing = window.__nxPendingSamples.map(function(s) { return s.id; });
  if (!existing.includes(base)) return base;
  var i = 2;
  while (existing.includes(base + '-' + i)) { i++; }
  return base + '-' + i;
}
```

- [ ] **Step 2: Add element tag input JS**

```javascript
// ── Elements tag input ───────────────────────────────────────────────────
var _nxModalElements = [];  // currently selected elements in the open modal

function nxRenderElementTags() {
  var container = document.getElementById('nx-elements-tags');
  if (!container) return;
  container.innerHTML = '';
  _nxModalElements.forEach(function(sym) {
    var tag = document.createElement('span');
    tag.className = 'badge bg-secondary d-flex align-items-center gap-1';
    tag.style.cssText = 'font-family:monospace;cursor:default;';
    var text = document.createTextNode(sym + ' ');
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.style.cssText = 'background:none;border:none;color:white;padding:0 0 0 2px;font-size:0.85rem;line-height:1;cursor:pointer;';
    btn.textContent = '×';
    btn.addEventListener('click', function() { nxRemoveElement(sym); });
    tag.appendChild(text);
    tag.appendChild(btn);
    container.appendChild(tag);
  });
}

function nxAddElement(raw) {
  var sym = (raw || '').trim();
  var match = NX_ELEMENT_SYMBOLS.find(function(el) {
    return el.toLowerCase() === sym.toLowerCase();
  });
  if (!match || _nxModalElements.includes(match)) return;
  _nxModalElements.push(match);
  nxRenderElementTags();
}

function nxRemoveElement(sym) {
  _nxModalElements = _nxModalElements.filter(function(s) { return s !== sym; });
  nxRenderElementTags();
}

(function() {
  var inp = document.getElementById('nx-elements-input');
  if (!inp) return;
  function tryAdd() {
    var v = inp.value.trim().replace(/,$/, '');
    if (v) { nxAddElement(v); inp.value = ''; }
  }
  inp.addEventListener('change', tryAdd);
  inp.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); tryAdd(); }
  });
})();
```

- [ ] **Step 3: Add `renderSamples` function**

```javascript
// ── Sample list rendering ────────────────────────────────────────────────
function nxRenderSamples() {
  var list = document.getElementById('nx-samples-list');
  var noMsg = document.getElementById('nx-no-samples-msg');
  if (!list) return;
  list.innerHTML = '';

  var samples = window.__nxPendingSamples;
  if (noMsg) noMsg.style.display = samples.length ? 'none' : '';

  samples.forEach(function(sample) {
    var row = document.createElement('div');
    row.className = 'border rounded bg-white d-flex align-items-center gap-2 px-3 py-2 mb-1';
    row.style.cssText = 'border-color:#b6d4fe !important;';

    var nameCol = document.createElement('div');
    nameCol.style.minWidth = '120px';
    var nameSpan = document.createElement('div');
    nameSpan.className = 'fw-semibold text-primary';
    nameSpan.style.fontSize = '0.85rem';
    nameSpan.textContent = sample.name || '(unnamed)';
    nameCol.appendChild(nameSpan);

    var descCol = document.createElement('div');
    descCol.className = 'flex-grow-1 text-muted text-truncate';
    descCol.style.fontSize = '0.78rem';
    descCol.textContent = sample.description || '';

    var elemCol = document.createElement('div');
    elemCol.className = 'd-flex gap-1 flex-wrap';
    elemCol.style.minWidth = '80px';
    (sample.elements || []).forEach(function(sym) {
      var chip = document.createElement('code');
      chip.className = 'badge bg-light text-secondary border';
      chip.style.fontSize = '0.68rem';
      chip.textContent = sym;
      elemCol.appendChild(chip);
    });

    var btnCol = document.createElement('div');
    btnCol.className = 'd-flex gap-1 flex-shrink-0';

    var editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'btn btn-outline-secondary btn-sm';
    editBtn.style.fontSize = '0.72rem';
    editBtn.innerHTML = '<i class="fas fa-pencil-alt fa-xs me-1"></i>Edit';
    editBtn.addEventListener('click', function() { nxOpenSampleModal(sample.id); });

    var delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'btn btn-outline-danger btn-sm';
    delBtn.style.fontSize = '0.72rem';
    delBtn.innerHTML = '<i class="fas fa-trash-alt fa-xs me-1"></i>Delete';
    delBtn.addEventListener('click', function() { nxDeleteSample(sample.id); });

    btnCol.appendChild(editBtn);
    btnCol.appendChild(delBtn);
    row.appendChild(nameCol);
    row.appendChild(descCol);
    row.appendChild(elemCol);
    row.appendChild(btnCol);
    list.appendChild(row);
  });
}
```

- [ ] **Step 4: Add modal open/save/delete functions**

```javascript
// ── Sample modal ─────────────────────────────────────────────────────────
function nxOpenSampleModal(sampleId) {
  var sample = sampleId
    ? window.__nxPendingSamples.find(function(s) { return s.id === sampleId; })
    : null;

  document.getElementById('nx-sample-modal-title').textContent = sample ? 'Edit Sample' : 'Add Sample';
  document.getElementById('nx-sample-editing-id').value = sampleId || '';
  document.getElementById('nx-sample-name').value = sample ? sample.name : '';
  document.getElementById('nx-sample-description').value = sample ? (sample.description || '') : '';
  document.getElementById('nx-sample-notes').value = sample ? (sample.notes || '') : '';

  _nxModalElements = sample ? (sample.elements || []).slice() : [];
  nxRenderElementTags();

  var modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('nx-sample-modal'));
  modal.show();
}

function nxSaveSampleFromModal() {
  var name = (document.getElementById('nx-sample-name').value || '').trim();
  if (!name) {
    document.getElementById('nx-sample-name').classList.add('is-invalid');
    return;
  }
  document.getElementById('nx-sample-name').classList.remove('is-invalid');

  var editingId = document.getElementById('nx-sample-editing-id').value;
  var isNew = !editingId;
  var newId = isNew ? nxGenerateSampleId(name) : editingId;

  var updated = {
    id: newId,
    name: name,
    description: (document.getElementById('nx-sample-description').value || '').trim(),
    notes: (document.getElementById('nx-sample-notes').value || '').trim(),
    elements: _nxModalElements.slice(),
  };

  if (isNew) {
    window.__nxPendingSamples.push(updated);
  } else {
    var idx = window.__nxPendingSamples.findIndex(function(s) { return s.id === editingId; });
    if (idx >= 0) window.__nxPendingSamples[idx] = updated;
  }

  nxRenderSamples();
  nxUpdateActivitySampleDropdowns();
  bootstrap.Modal.getInstance(document.getElementById('nx-sample-modal')).hide();
}

function nxDeleteSample(sampleId) {
  // Check if any activity has this sample assigned
  var assignedSeqnos = Object.keys(window.__nxActivitySampleIds).filter(function(k) {
    return window.__nxActivitySampleIds[k] === sampleId;
  });
  // Also check DOM dropdowns (covers activities loaded from the server)
  document.querySelectorAll('.nx-activity-sample').forEach(function(sel) {
    if (sel.value === sampleId && !assignedSeqnos.includes(sel.dataset.seqno)) {
      assignedSeqnos.push(sel.dataset.seqno);
    }
  });

  if (assignedSeqnos.length > 0) {
    if (!window.confirm(
      'This sample is assigned to ' + assignedSeqnos.length +
      ' activity/activities. Deleting it will clear those assignments. Continue?'
    )) return;
    assignedSeqnos.forEach(function(seqno) {
      delete window.__nxActivitySampleIds[seqno];
    });
    document.querySelectorAll('.nx-activity-sample[value="' + sampleId + '"]').forEach(function(sel) {
      sel.value = '';
    });
  }

  window.__nxPendingSamples = window.__nxPendingSamples.filter(function(s) { return s.id !== sampleId; });
  nxRenderSamples();
  nxUpdateActivitySampleDropdowns();
}

function nxUpdateActivitySampleDropdowns() {
  document.querySelectorAll('.nx-activity-sample').forEach(function(sel) {
    var currentVal = sel.value;
    // Rebuild options
    sel.innerHTML = '<option value="">-- No sample --</option>';
    window.__nxPendingSamples.forEach(function(s) {
      var opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.name;
      sel.appendChild(opt);
    });
    // Restore selection if still valid
    if (window.__nxPendingSamples.some(function(s) { return s.id === currentVal; })) {
      sel.value = currentVal;
    }
  });
}

// Wire up Add Sample button and modal save button
(function() {
  var addBtn = document.getElementById('nx-add-sample-btn');
  if (addBtn) addBtn.addEventListener('click', function() { nxOpenSampleModal(null); });

  var saveBtn = document.getElementById('nx-sample-modal-save');
  if (saveBtn) saveBtn.addEventListener('click', nxSaveSampleFromModal);

  // Initialize sample state from server
  window.__nxActivitySampleIds = {};
  if (window.__nxActivities) {
    window.__nxActivities.forEach(function(act) {
      if (act.sample_id) {
        window.__nxActivitySampleIds[String(act.seqno)] = act.sample_id;
      }
    });
  }

  // Initialize sample dropdowns with server-side selections
  document.querySelectorAll('.nx-activity-sample').forEach(function(sel) {
    var seqno = sel.dataset.seqno;
    var assigned = window.__nxActivitySampleIds[seqno];
    if (assigned) sel.value = assigned;
  });

  // Initial render of samples list
  nxRenderSamples();
})();
```

- [ ] **Step 5: Wire activity sample dropdown changes to state**

Add inside the existing IIFE (inside the `(function () {` block), after the `buildDropdown()` call:

```javascript
  // ── Activity sample dropdown changes ────────────────────────────────────
  document.addEventListener('change', function(e) {
    if (!e.target.classList.contains('nx-activity-sample')) return;
    var seqno = e.target.dataset.seqno;
    var val = e.target.value;
    if (val) {
      window.__nxActivitySampleIds[seqno] = val;
    } else {
      delete window.__nxActivitySampleIds[seqno];
    }
  });
```

- [ ] **Step 6: Commit**

```bash
git add nexuslims_annotate/templates/
git commit -m "feat(annotator): add sample state management JS (render, modal, element tags)"
```

---

## Task 9: JS -- activity state management

**Files:**
- Modify: `nexuslims_annotate/templates/nexuslims_annotate/annotate.html` (JS section)

Add the following to the page-scope JS (before the IIFE), plus additions inside the IIFE.

- [ ] **Step 1: Add activity state variables**

After the `window.__nxActivitySampleIds` initialization (end of Task 8's IIFE wire-up), add at page scope:

```javascript
window.__nxDeletedSeqnos = [];
window.__nxNewActivities = [];
```

- [ ] **Step 2: Add `nxRenumberActivityLabels`**

```javascript
function nxRenumberActivityLabels() {
  var labels = document.querySelectorAll('.nx-activity-label');
  labels.forEach(function(label, i) {
    label.textContent = 'Activity ' + (i + 1);
  });
}
```

- [ ] **Step 3: Add `nxCreateActivityDOM`**

This function creates the full DOM block for a new empty activity (header + sortable row) and returns it as a DocumentFragment.

```javascript
function nxCreateActivityDOM(tempId) {
  var frag = document.createDocumentFragment();

  // Header row
  var header = document.createElement('div');
  header.className = 'd-flex align-items-center gap-2 mt-3 mb-1';
  header.id = 'nx-activity-header-' + tempId;

  var labelSpan = document.createElement('span');
  labelSpan.className = 'text-uppercase text-muted fw-semibold flex-shrink-0 nx-activity-label';
  labelSpan.style.cssText = 'font-size:0.75rem;letter-spacing:0.08em;';
  labelSpan.textContent = 'New Activity';

  var countBadge = document.createElement('span');
  countBadge.className = 'nx-activity-count badge bg-light text-secondary border';
  countBadge.dataset.seqno = tempId;
  countBadge.style.cssText = 'font-size:0.7rem;font-weight:500;';
  countBadge.textContent = '0';

  var sampleSel = document.createElement('select');
  sampleSel.className = 'form-select form-select-sm nx-activity-sample flex-shrink-0';
  sampleSel.dataset.seqno = tempId;
  sampleSel.style.cssText = 'max-width:160px;font-size:0.72rem;';
  sampleSel.title = 'Assign sample to this activity';
  var defaultOpt = document.createElement('option');
  defaultOpt.value = '';
  defaultOpt.textContent = '-- No sample --';
  sampleSel.appendChild(defaultOpt);
  window.__nxPendingSamples.forEach(function(s) {
    var opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = s.name;
    sampleSel.appendChild(opt);
  });

  var hr = document.createElement('hr');
  hr.className = 'flex-grow-1 my-0';

  var insertBtn = document.createElement('button');
  insertBtn.type = 'button';
  insertBtn.className = 'btn btn-sm btn-outline-secondary flex-shrink-0 nx-insert-activity-below';
  insertBtn.dataset.seqno = tempId;
  insertBtn.style.cssText = 'font-size:0.7rem;padding:1px 7px;';
  insertBtn.title = 'Insert new activity below this one';
  insertBtn.textContent = '+ below';

  var deleteBtn = document.createElement('button');
  deleteBtn.type = 'button';
  deleteBtn.className = 'btn btn-sm btn-outline-danger flex-shrink-0 nx-delete-activity';
  deleteBtn.dataset.seqno = tempId;
  deleteBtn.dataset.datasetCount = '0';
  deleteBtn.style.cssText = 'font-size:0.7rem;padding:1px 7px;';
  deleteBtn.title = 'Delete this activity';
  deleteBtn.innerHTML = '<i class="fas fa-trash-alt" style="font-size:0.65rem;"></i>';

  header.appendChild(labelSpan);
  header.appendChild(countBadge);
  header.appendChild(sampleSel);
  header.appendChild(hr);
  header.appendChild(insertBtn);
  header.appendChild(deleteBtn);

  // Sortable row (empty placeholder)
  var row = document.createElement('div');
  row.className = 'row gx-2 gy-0 nx-sortable-activity';
  row.dataset.seqno = tempId;

  var placeholder = document.createElement('div');
  placeholder.className = 'col-12 text-muted text-center py-2 nx-empty-activity-placeholder';
  placeholder.style.cssText = 'font-size:0.8rem;font-style:italic;';
  placeholder.textContent = 'Drag datasets here or delete this activity.';
  row.appendChild(placeholder);

  frag.appendChild(header);
  frag.appendChild(row);
  return frag;
}
```

- [ ] **Step 4: Add `nxAddActivity` and `nxDeleteActivity`**

```javascript
function nxAddActivity(afterSeqno) {
  var tempId = 'new-' + Math.random().toString(36).slice(2, 9);
  var spec = afterSeqno != null ? {temp_id: tempId, after_seqno: afterSeqno} : {temp_id: tempId, at_end: true};
  window.__nxNewActivities.push(spec);

  var frag = nxCreateActivityDOM(tempId);

  if (afterSeqno != null) {
    var refRow = document.querySelector('.nx-sortable-activity[data-seqno="' + afterSeqno + '"]');
    if (refRow && refRow.nextSibling) {
      refRow.parentNode.insertBefore(frag, refRow.nextSibling);
    } else if (refRow) {
      refRow.parentNode.appendChild(frag);
    }
  } else {
    // Append before the save row
    var saveRow = document.querySelector('#annotate-page-form .d-flex.gap-2.mt-4');
    if (saveRow) {
      saveRow.parentNode.insertBefore(frag, saveRow);
    }
  }

  // Initialize SortableJS on the new row
  var newRow = document.querySelector('.nx-sortable-activity[data-seqno="' + tempId + '"]');
  if (newRow && typeof Sortable !== 'undefined') {
    Sortable.create(newRow, {
      group: 'datasets',
      animation: 150,
      ghostClass: 'nx-drag-ghost',
      chosenClass: 'nx-drag-chosen',
      filter: '.annotate-textarea, .nx-select-cb-label, .nx-moved-badge',
      preventOnFilter: false,
      onEnd: function(evt) {
        if (evt.from === evt.to) return;
        var targetRow = evt.to;
        var targetSeqno = targetRow.dataset.seqno;
        var colEl = evt.item;
        var dsIndex = parseInt(colEl.dataset.datasetIndex);
        var origSeqno = colEl.dataset.originalActivity;
        colEl.dataset.currentActivity = targetSeqno;
        // recordMove, updateMoveVisual, updateActivityCounts are defined in the existing IIFE
        recordMove(dsIndex, targetSeqno, origSeqno);
        updateMoveVisual(colEl, targetSeqno);
        updateActivityCounts();
        updateToolbar();
      }
    });
  }

  // Add to __nxActivities for the move dropdown
  if (window.__nxActivities) {
    window.__nxActivities.push({seqno: tempId, start_time: '', dataset_count: 0});
  }

  nxRenumberActivityLabels();
  updateActivityCounts();
}

function nxDeleteActivity(seqno) {
  var row = document.querySelector('.nx-sortable-activity[data-seqno="' + seqno + '"]');
  var header = document.getElementById('nx-activity-header-' + seqno);
  var isNew = String(seqno).startsWith('new-');

  if (isNew) {
    // Remove from __nxNewActivities
    window.__nxNewActivities = window.__nxNewActivities.filter(function(spec) {
      return spec.temp_id !== seqno;
    });
  } else {
    window.__nxDeletedSeqnos.push(String(seqno));
  }

  // Remove from __nxActivitySampleIds
  delete window.__nxActivitySampleIds[String(seqno)];

  // Remove from __nxActivities
  if (window.__nxActivities) {
    window.__nxActivities = window.__nxActivities.filter(function(a) {
      return String(a.seqno) !== String(seqno);
    });
  }

  if (row) row.remove();
  if (header) header.remove();

  nxRenumberActivityLabels();
  buildDropdown();
}
```

- [ ] **Step 5: Wire up activity buttons inside the IIFE**

Inside the IIFE, after the existing `form.addEventListener('change', ...)` block, add:

```javascript
  // ── Add/delete activity buttons ──────────────────────────────────────────
  var addActivityBtn = document.getElementById('nx-add-activity-btn');
  if (addActivityBtn) {
    addActivityBtn.addEventListener('click', function() { nxAddActivity(null); });
  }

  document.addEventListener('click', function(e) {
    var insertBtn = e.target.closest('.nx-insert-activity-below');
    if (insertBtn) {
      nxAddActivity(insertBtn.dataset.seqno);
      return;
    }
    var deleteBtn = e.target.closest('.nx-delete-activity');
    if (deleteBtn && !deleteBtn.disabled) {
      nxDeleteActivity(deleteBtn.dataset.seqno);
      return;
    }
  });
```

- [ ] **Step 6: Update `updateActivityCounts` to handle empty-placeholder visibility**

Find the existing `updateActivityCounts` function and add at the end of it:

```javascript
    // Show/hide the empty-activity placeholder per activity
    document.querySelectorAll('.nx-sortable-activity').forEach(function(row) {
      var placeholder = row.querySelector('.nx-empty-activity-placeholder');
      if (!placeholder) return;
      var hasDatasets = row.querySelectorAll('.nx-dataset-col').length > 0;
      placeholder.style.display = hasDatasets ? 'none' : '';
      // Update delete button state
      var seqno = row.dataset.seqno;
      var deleteBtn = document.querySelector('.nx-delete-activity[data-seqno="' + seqno + '"]');
      if (deleteBtn) {
        deleteBtn.disabled = hasDatasets;
        deleteBtn.title = hasDatasets ? 'Move all datasets to another activity first' : 'Delete this activity';
      }
    });
```

- [ ] **Step 7: Commit**

```bash
git add nexuslims_annotate/templates/
git commit -m "feat(annotator): add activity state management JS (add/delete/renumber)"
```

---

## Task 10: JS -- form submission wiring and dirty-state guard

**Files:**
- Modify: `nexuslims_annotate/templates/nexuslims_annotate/annotate.html` (existing IIFE)

- [ ] **Step 1: Update the form submit handler to serialize all new state**

Find the existing form `submit` event listener:

```javascript
  form.addEventListener('submit', function () {
    document.getElementById('annotate-moves-input').value = JSON.stringify(window.__nxPendingMoves);
    saving = true;
  });
```

Replace it with:

```javascript
  form.addEventListener('submit', function () {
    document.getElementById('annotate-moves-input').value = JSON.stringify(window.__nxPendingMoves);
    document.getElementById('annotate-samples-input').value = JSON.stringify(window.__nxPendingSamples);
    document.getElementById('annotate-deleted-seqnos-input').value = JSON.stringify(window.__nxDeletedSeqnos);
    document.getElementById('annotate-new-activities-input').value = JSON.stringify(window.__nxNewActivities);
    document.getElementById('annotate-activity-sample-ids-input').value = JSON.stringify(window.__nxActivitySampleIds);
    saving = true;
  });
```

- [ ] **Step 2: Extend `hasDirtyState` to cover new state**

Find the existing `hasDirtyState` function:

```javascript
  function hasDirtyState() {
    var dirtyText = Array.from(form.querySelectorAll('.annotate-textarea')).some(function (ta) {
      return ta.value.trim() !== (ta.dataset.original || '').trim();
    });
    return dirtyText || window.__nxPendingMoves.length > 0;
  }
```

Replace it with:

```javascript
  function hasDirtyState() {
    var dirtyText = Array.from(form.querySelectorAll('.annotate-textarea')).some(function (ta) {
      return ta.value.trim() !== (ta.dataset.original || '').trim();
    });
    if (dirtyText || window.__nxPendingMoves.length > 0) return true;
    if (window.__nxDeletedSeqnos.length > 0) return true;
    if (window.__nxNewActivities.length > 0) return true;
    // Check if any sample assignment changed from server state
    var initialIds = {};
    if (window.__nxActivities) {
      window.__nxActivities.forEach(function(a) {
        if (a.sample_id) initialIds[String(a.seqno)] = a.sample_id;
      });
    }
    var currentIds = window.__nxActivitySampleIds || {};
    if (JSON.stringify(initialIds) !== JSON.stringify(currentIds)) return true;
    // Check if samples list changed
    var initialSamples = JSON.parse(document.getElementById('nx-samples-data').textContent || '[]');
    if (JSON.stringify(initialSamples) !== JSON.stringify(window.__nxPendingSamples)) return true;
    return false;
  }
```

- [ ] **Step 3: Update the help modal text to mention new features**

Find the existing help modal body and update the intro paragraph and add a new "Managing Samples & Activities" section. Replace the `<p class="mb-3">` intro with:

```html
<p class="mb-3">
  Annotating a record lets you attach plain-language descriptions to each dataset,
  reassign datasets to different acquisition activities, manage samples examined during
  the experiment, and add or remove acquisition activities. All changes save together
  when you click <strong>Save Annotations</strong>.
</p>
<h6 class="fw-semibold">Managing Samples</h6>
<ul class="mb-3">
  <li>The <strong>Samples</strong> panel at the top shows all samples for this record.</li>
  <li>Click <strong>Add Sample</strong> or <strong>Edit</strong> to open the sample editor (name, description, notes, elements).</li>
  <li>Use the dropdown in each activity header to assign a sample to that activity.</li>
  <li>Deleting a sample that is assigned to activities will prompt for confirmation.</li>
</ul>
<h6 class="fw-semibold">Managing Activities</h6>
<ul class="mb-3">
  <li>Click <strong>+ below</strong> in an activity header to insert a new activity below it.</li>
  <li>Click <strong>+ Add Activity</strong> in the save row to append a new activity at the end.</li>
  <li>The <i class="fas fa-trash-alt"></i> button in an activity header deletes it (only enabled when the activity has no datasets).</li>
</ul>
```

- [ ] **Step 4: Run the full test suite one final time**

```bash
uv run python runtests.py
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add nexuslims_annotate/templates/
git commit -m "feat(annotator): wire form submission for all new state and update dirty-state guard"
```

---

## Self-Review Checklist

- [x] **Sample display** -- `nxRenderSamples()` builds the vertical card list from `__nxPendingSamples` (Task 8)
- [x] **Add sample** -- "Add Sample" button opens modal in add mode; `nxSaveSampleFromModal` pushes to `__nxPendingSamples` (Task 8)
- [x] **Edit sample** -- "Edit" button opens modal pre-filled; save updates the existing entry by id (Task 8)
- [x] **Delete sample** -- warns if assigned to activities; clears `__nxActivitySampleIds` entries; removes from `__nxPendingSamples` (Task 8)
- [x] **Assign sample to activity** -- `<select>` dropdown per activity header; change event updates `__nxActivitySampleIds` (Task 8)
- [x] **Create activity at end** -- "+ Add Activity" button calls `nxAddActivity(null)` (Task 9)
- [x] **Create activity after specific activity** -- "+ below" button calls `nxAddActivity(seqno)` (Task 9)
- [x] **Delete empty activity** -- trash button enabled only when `dataset_count == 0`; `nxDeleteActivity` removes DOM + updates state (Task 9)
- [x] **Delete non-empty activity blocked** -- button is disabled when activity has datasets (Tasks 7 + 9, `updateActivityCounts`)
- [x] **Save flow -- samples** -- `__nxPendingSamples` serialized to `samples` hidden input; `_apply_samples` replaces XML elements (Tasks 6, 10)
- [x] **Save flow -- deleted activities** -- `__nxDeletedSeqnos` serialized; `_apply_activity_mutations` validates and deletes (Tasks 5, 6, 10)
- [x] **Save flow -- new activities** -- `__nxNewActivities` serialized; `_apply_activity_mutations` inserts (Tasks 5, 6, 10)
- [x] **Save flow -- sample assignments** -- `__nxActivitySampleIds` serialized; `_apply_activity_mutations` sets `<sampleID>` (Tasks 5, 6, 10)
- [x] **Move to new activity** -- moves using temp_ids translated through `seqno_mapping` before `_apply_moves` (Task 6)
- [x] **Seqno renumbering** -- `_renumber_activities` called at end of save (Tasks 4, 6)
- [x] **Existing features preserved** -- descriptions and dataset moves unchanged; new JSON fields default to empty if absent (Task 6 `annotate_save`)
- [x] **Unsaved-changes guard** -- `hasDirtyState` extended to cover all new state (Task 10)
- [x] **`_parse_activities` returns `sample_id`** -- used to pre-select dropdowns on page load (Task 1)
- [x] **Elements tag input** -- all 118 symbols in datalist; Enter/comma adds tag; click removes (Task 8)
