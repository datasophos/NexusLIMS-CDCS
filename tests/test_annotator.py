"""Unit tests for nexuslims_annotate helper functions and views."""
import json
import os
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from nexuslims_annotate.views import (
    _apply_activity_mutations,
    _apply_descriptions,
    _apply_moves,
    _apply_samples,
    _dataset_creation_time,
    _inject_setup_into_dataset,
    _parse_activities,
    _parse_datasets,
    _parse_samples,
    _recompute_activity_setup,
    _renumber_activities,
    _sort_datasets_by_creation_time,
)

# ---------------------------------------------------------------------------
# Namespace helpers
# ---------------------------------------------------------------------------

NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
NS_MAP = {"nx": NS}


def _t(tag):
    """Return the namespace-qualified tag string for ET operations."""
    return f"{{{NS}}}{tag}"


def _find_param(setup_el, name):
    """Find a <param name="..."> child in a setup element; return it or None."""
    for p in setup_el.findall(_t("param")):
        if p.get("name") == name:
            return p
    return None


def _find_meta(dataset_el, name):
    """Find a <meta name="..."> child in a dataset element; return it or None."""
    for m in dataset_el.findall(_t("meta")):
        if m.get("name") == name:
            return m
    return None


def _meta_names(dataset_el):
    """Return the set of meta param names for a dataset element."""
    return {m.get("name") for m in dataset_el.findall(_t("meta"))}


def _setup_param_names(activity_el):
    """Return the set of setup param names for an activity element, or empty set."""
    setup = activity_el.find(_t("setup"))
    if setup is None:
        return set()
    return {p.get("name") for p in setup.findall(_t("param"))}


def _dataset_names_in_activity(xml_str, seqno):
    """Return list of dataset <name> texts in the given activity (by seqno string)."""
    root = ET.fromstring(xml_str)
    for act in root.findall("nx:acquisitionActivity", NS_MAP):
        if act.get("seqno") == str(seqno):
            return [
                ds.find("nx:name", NS_MAP).text
                for ds in act.findall("nx:dataset", NS_MAP)
                if ds.find("nx:name", NS_MAP) is not None
            ]
    return []


def _dataset_count_in_activity(xml_str, seqno):
    return len(_dataset_names_in_activity(xml_str, seqno))


def _dump_activity_el(act):
    """Pretty-print a single <acquisitionActivity> Element. Call this while debugging."""
    seqno = act.get("seqno", "?")
    datasets = act.findall(_t("dataset"))
    setup = act.find(_t("setup"))
    setup_params = (
        {p.get("name"): p.text for p in setup.findall(_t("param"))}
        if setup is not None else {}
    )
    print(f"  activity seqno={seqno}: {len(datasets)} dataset(s), setup={setup_params}")
    for ds in datasets:
        name_el = ds.find(_t("name"))
        name = name_el.text if name_el is not None else "<unnamed>"
        metas = {m.get("name"): m.text for m in ds.findall(_t("meta"))}
        print(f"    - {name}  meta={metas}")


def _dump_activities(xml_str):
    """Pretty-print all activities in an XML string. Call this inside a test while debugging."""
    root = ET.fromstring(xml_str)
    for act in root.findall("nx:acquisitionActivity", NS_MAP):
        _dump_activity_el(act)


def _dump_el(el):
    """Pretty-print any Element as indented XML. Call this inside a test while debugging."""
    ET.indent(el, space="  ")
    print(ET.tostring(el, encoding="unicode"))
    print()


def _dump_xml(xml_str):
    """Pretty-print an XML string with indentation. Call this inside a test while debugging."""
    _dump_el(ET.fromstring(xml_str))


# ---------------------------------------------------------------------------
# Shared XML fixture
#
# Two activities:
#   Activity 0 (seqno=0): image_001 (10:01) + image_002 (10:02)
#     setup: Voltage=300000.0, Magnification=17677.0
#     image_001: description="First image", preview, StageX=-192.365, C2=44.7
#     image_002: no description, no preview,  StageX=-192.365, C2=41.9
#   Activity 1 (seqno=1): image_003 (11:01)
#     setup: Voltage=300000.0, Magnification=25000.0
#     image_003: no description, no preview,  StageX=-200.0,   C2=52.3
# ---------------------------------------------------------------------------

_TWO_ACTIVITY_XML = f"""\
<?xml version='1.0' encoding='UTF-8'?>
<Experiment xmlns="{NS}">
  <title>Test Experiment</title>
  <acquisitionActivity seqno="0">
    <startTime>2024-01-15T10:00:00-05:00</startTime>
    <setup>
      <param name="StageX">-192.365</param>
      <param name="Voltage">300000.0</param>
      <param name="Magnification">17677.0</param>
    </setup>
    <dataset type="Image">
      <name>image_001.dm3</name>
      <location>/data/image_001.dm3</location>
      <format>Digital Micrograph</format>
      <description>First image</description>
      <preview>/previews/image_001.png</preview>
      <meta name="C2">44.7</meta>
      <meta name="Creation Time">2024-01-15T10:01:00-05:00</meta>
      <meta name="Unique_to_1">test1</meta>
    </dataset>
    <dataset type="Image">
      <name>image_002.dm3</name>
      <location>/data/image_002.dm3</location>
      <format>Digital Micrograph</format>
      <meta name="C2">41.9</meta>
      <meta name="Creation Time">2024-01-15T10:02:00-05:00</meta>
      <meta name="Unique_to_2">test2</meta>
    </dataset>
  </acquisitionActivity>
  <acquisitionActivity seqno="1">
    <startTime>2024-01-15T11:00:00-05:00</startTime>
    <setup>
      <param name="Voltage">300000.0</param>
      <param name="Magnification">25000.0</param>
    </setup>
    <dataset type="Image">
      <name>image_003.dm3</name>
      <location>/data/image_003.dm3</location>
      <format>Digital Micrograph</format>
      <meta name="StageX">-200.0</meta>
      <meta name="C2">52.3</meta>
      <meta name="Creation Time">2024-01-15T11:01:00-05:00</meta>
      <meta name="Unique_to_3">test3</meta>
    </dataset>
    <dataset type="Image">
      <name>image_004.dm3</name>
      <location>/data/image_004.dm3</location>
      <format>Digital Micrograph</format>
      <meta name="StageX">-205.0</meta>
      <meta name="C2">62.3</meta>
      <meta name="Creation Time">2024-01-15T11:05:00-05:00</meta>
      <meta name="Unique_to_4">test4</meta>
    </dataset>
  </acquisitionActivity>
</Experiment>"""

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


# ===========================================================================
# _parse_datasets
# ===========================================================================

class ParseDatasetsTests(SimpleTestCase):
    def test_returns_correct_total_count(self):
        self.assertEqual(len(_parse_datasets(_TWO_ACTIVITY_XML)), 4)

    def test_indices_are_sequential_across_activities(self):
        indices = [d["index"] for d in _parse_datasets(_TWO_ACTIVITY_XML)]
        self.assertEqual(indices, [0, 1, 2, 3])

    def test_names_match_xml_order(self):
        names = [d["name"] for d in _parse_datasets(_TWO_ACTIVITY_XML)]
        self.assertEqual(names, ["image_001.dm3", "image_002.dm3", "image_003.dm3", "image_004.dm3"])

    def test_description_returned_when_present(self):
        ds = _parse_datasets(_TWO_ACTIVITY_XML)
        self.assertEqual(ds[0]["description"], "First image")

    def test_description_empty_string_when_absent(self):
        ds = _parse_datasets(_TWO_ACTIVITY_XML)
        self.assertEqual(ds[1]["description"], "")
        self.assertEqual(ds[2]["description"], "")

    def test_activity_seqno_assigned_correctly(self):
        ds = _parse_datasets(_TWO_ACTIVITY_XML)
        self.assertEqual(ds[0]["activity_seqno"], "0")
        self.assertEqual(ds[1]["activity_seqno"], "0")
        self.assertEqual(ds[2]["activity_seqno"], "1")
        self.assertEqual(ds[3]["activity_seqno"], "1")

    def test_preview_url_built_from_env_var(self):
        with patch.dict(os.environ, {"XSLT_PREVIEW_BASE_URL": "https://cdn.example.com"}):
            ds = _parse_datasets(_TWO_ACTIVITY_XML)
        self.assertEqual(ds[0]["preview_url"], "https://cdn.example.com/previews/image_001.png")

    def test_preview_url_none_when_no_preview_element(self):
        ds = _parse_datasets(_TWO_ACTIVITY_XML)
        self.assertIsNone(ds[1]["preview_url"])
        self.assertIsNone(ds[2]["preview_url"])

    def test_empty_xml_returns_empty_list(self):
        xml = f'<Experiment xmlns="{NS}"><title>Empty</title></Experiment>'
        self.assertEqual(_parse_datasets(xml), [])


# ===========================================================================
# _parse_activities
# ===========================================================================

class ParseActivitiesTests(SimpleTestCase):
    def test_returns_correct_count(self):
        self.assertEqual(len(_parse_activities(_TWO_ACTIVITY_XML)), 2)

    def test_seqno_values(self):
        acts = _parse_activities(_TWO_ACTIVITY_XML)
        self.assertEqual(acts[0]["seqno"], "0")
        self.assertEqual(acts[1]["seqno"], "1")

    def test_start_time_populated(self):
        acts = _parse_activities(_TWO_ACTIVITY_XML)
        self.assertEqual(acts[0]["start_time"], "2024-01-15T10:00:00-05:00")
        self.assertEqual(acts[1]["start_time"], "2024-01-15T11:00:00-05:00")

    def test_dataset_counts(self):
        acts = _parse_activities(_TWO_ACTIVITY_XML)
        self.assertEqual(acts[0]["dataset_count"], 2)
        self.assertEqual(acts[1]["dataset_count"], 2)

    def test_empty_xml_returns_empty_list(self):
        xml = f'<Experiment xmlns="{NS}"><title>Empty</title></Experiment>'
        self.assertEqual(_parse_activities(xml), [])

    def test_sample_id_returned_when_present(self):
        acts = _parse_activities(_WITH_SAMPLES_XML)
        self.assertEqual(acts[0]['sample_id'], 'steel-alloy-a')

    def test_sample_id_empty_string_when_absent(self):
        acts = _parse_activities(_NO_SAMPLES_XML)
        self.assertEqual(acts[0]['sample_id'], '')
        self.assertEqual(acts[1]['sample_id'], '')


# ===========================================================================
# _parse_samples
# ===========================================================================

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
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        xml = f'<Experiment xmlns="{NS}"><sample id="x"><name>X</name></sample></Experiment>'
        samples = _parse_samples(xml)
        self.assertEqual(samples[0]['description'], '')

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
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        xml = f'<Experiment xmlns="{NS}"><sample id="x"><name>X</name></sample></Experiment>'
        samples = _parse_samples(xml)
        self.assertEqual(samples[0]['elements'], [])

    def test_ref_attribute_captured(self):
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        xml = f'<Experiment xmlns="{NS}"><sample id="x" ref="https://doi.org/10.1/abc"><name>X</name></sample></Experiment>'
        samples = _parse_samples(xml)
        self.assertEqual(samples[0]['ref'], 'https://doi.org/10.1/abc')

    def test_ref_empty_string_when_absent(self):
        samples = _parse_samples(_WITH_SAMPLES_XML)
        self.assertEqual(samples[0]['ref'], '')


# ===========================================================================
# _apply_samples
# ===========================================================================

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
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        NS_MAP = {'nx': NS}
        s = root.find('nx:sample', NS_MAP)
        self.assertEqual(s.get('id'), 'my-id')

    def test_elements_written_as_child_tags(self):
        new_samples = [{'id': 's', 'name': 'S', 'description': '', 'notes': '', 'elements': ['Fe', 'Ni']}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        NS_MAP = {'nx': NS}
        s = root.find('nx:sample', NS_MAP)
        elements_el = s.find(f'{{{NS}}}elements')
        self.assertIsNotNone(elements_el)
        syms = [c.tag.split('}')[-1] for c in elements_el]
        self.assertEqual(syms, ['Fe', 'Ni'])

    def test_notes_written_as_entry_child(self):
        new_samples = [{'id': 's', 'name': 'S', 'description': '', 'notes': 'My notes', 'elements': []}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        NS_MAP = {'nx': NS}
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
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        NS_MAP = {'nx': NS}
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

    def test_ref_attribute_written(self):
        new_samples = [{'id': 's', 'ref': 'https://doi.org/10.1/x', 'name': 'S', 'description': '', 'notes': '', 'elements': []}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        NS_STR = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        s = root.find(f'{{{NS_STR}}}sample')
        self.assertEqual(s.get('ref'), 'https://doi.org/10.1/x')

    def test_ref_attribute_omitted_when_empty(self):
        new_samples = [{'id': 's', 'ref': '', 'name': 'S', 'description': '', 'notes': '', 'elements': []}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        NS_STR = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        s = root.find(f'{{{NS_STR}}}sample')
        self.assertIsNone(s.get('ref'))

    def test_invalid_element_symbols_are_filtered(self):
        new_samples = [{'id': 's', 'name': 'S', 'description': '', 'notes': '', 'elements': ['Fe', 'NotAnElement', '1bad']}]
        result = _apply_samples(_NO_SAMPLES_XML, new_samples)
        root = ET.fromstring(result)
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        NS_MAP = {'nx': NS}
        s = root.find('nx:sample', NS_MAP)
        elements_el = s.find(f'{{{NS}}}elements')
        self.assertIsNotNone(elements_el)
        syms = [c.tag.split('}')[-1] for c in elements_el]
        self.assertEqual(syms, ['Fe'])  # only valid symbol retained


# ===========================================================================
# _renumber_activities
# ===========================================================================

class RenumberActivitiesTests(SimpleTestCase):
    def _seqnos(self, xml_str):
        root = ET.fromstring(xml_str)
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        NS_MAP = {'nx': NS}
        return [a.get('seqno') for a in root.findall('nx:acquisitionActivity', NS_MAP)]

    def test_already_consecutive_unchanged(self):
        result = _renumber_activities(_WITH_SAMPLES_XML)
        self.assertEqual(self._seqnos(result), ['0', '1'])

    def test_gaps_are_filled(self):
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        xml = f"""<Experiment xmlns="{NS}">
          <acquisitionActivity seqno="0"/>
          <acquisitionActivity seqno="2"/>
          <acquisitionActivity seqno="5"/>
        </Experiment>"""
        result = _renumber_activities(xml)
        self.assertEqual(self._seqnos(result), ['0', '1', '2'])

    def test_single_activity_stays_zero(self):
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        xml = f'<Experiment xmlns="{NS}"><acquisitionActivity seqno="3"/></Experiment>'
        result = _renumber_activities(xml)
        self.assertEqual(self._seqnos(result), ['0'])

    def test_no_activities_returns_valid_xml(self):
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        xml = f'<Experiment xmlns="{NS}"><title>X</title></Experiment>'
        result = _renumber_activities(xml)
        ET.fromstring(result)
        self.assertEqual(self._seqnos(result), [])


# ===========================================================================
# _apply_activity_mutations
# ===========================================================================

class ApplyActivityMutationsTests(SimpleTestCase):
    NS_STR = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
    NS_MAP_LOC = {'nx': "https://data.nist.gov/od/dm/nexus/experiment/v1.0"}

    def _seqnos(self, xml_str):
        root = ET.fromstring(xml_str)
        return [a.get('seqno') for a in root.findall('nx:acquisitionActivity', self.NS_MAP_LOC)]

    def _sample_id(self, xml_str, seqno):
        root = ET.fromstring(xml_str)
        for a in root.findall('nx:acquisitionActivity', self.NS_MAP_LOC):
            if a.get('seqno') == str(seqno):
                el = a.find(f'{{{self.NS_STR}}}sampleID')
                return el.text if el is not None else None
        return None

    # --- delete ---

    def test_delete_empty_activity(self):
        # seqno 1 is empty in _NO_SAMPLES_XML
        result, mapping = _apply_activity_mutations(
            _NO_SAMPLES_XML, deleted_seqnos=['1'], new_activities=[], activity_sample_ids={}
        )
        root = ET.fromstring(result)
        seqnos = [a.get('seqno') for a in root.findall('nx:acquisitionActivity', self.NS_MAP_LOC)]
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
        acts = root.findall('nx:acquisitionActivity', self.NS_MAP_LOC)
        self.assertEqual(len(acts), 3)

    def test_insert_after_seqno(self):
        result, mapping = _apply_activity_mutations(
            _NO_SAMPLES_XML,
            deleted_seqnos=[],
            new_activities=[{'temp_id': 'new-x', 'after_seqno': '0'}],
            activity_sample_ids={},
        )
        root = ET.fromstring(result)
        acts = root.findall('nx:acquisitionActivity', self.NS_MAP_LOC)
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
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
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
        NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        NS_MAP_L = {'nx': NS}
        for act in root.findall('nx:acquisitionActivity', NS_MAP_L):
            if act.get('seqno') == '0':
                tags = [c.tag.split('}')[-1] for c in act]
                start_pos = tags.index('startTime')
                sid_pos = tags.index('sampleID')
                self.assertGreater(sid_pos, start_pos)


# ===========================================================================
# _inject_setup_into_dataset
# ===========================================================================

class InjectSetupIntoDatasetTests(SimpleTestCase):
    def _activity_and_dataset(self, xml=_TWO_ACTIVITY_XML, activity_index=0, dataset_index=0):
        root = ET.fromstring(xml)
        activities = root.findall("nx:acquisitionActivity", NS_MAP)
        act = activities[activity_index]
        ds = act.findall("nx:dataset", NS_MAP)[dataset_index]
        return ds, act

    def test_setup_params_added_as_meta_elements(self):
        ds, act = self._activity_and_dataset()
        _inject_setup_into_dataset(ds, act)
        names = _meta_names(ds)
        self.assertEqual(
            {'Voltage', 'C2', 'Unique_to_1', 'StageX', 'Magnification', 'Creation Time'},
            names
        )

    def test_setup_param_value_preserved(self):
        ds, act = self._activity_and_dataset()
        _inject_setup_into_dataset(ds, act)
        meta = _find_meta(ds, "Voltage")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.text, "300000.0")

    def test_no_duplicate_meta_elements_for_existing_names(self):
        ds, act = self._activity_and_dataset()
        _inject_setup_into_dataset(ds, act)
        stagex_metas = [m for m in ds.findall(_t("meta")) if m.get("name") == "StageX"]
        self.assertEqual(len(stagex_metas), 1)

    def test_no_op_when_activity_has_no_setup(self):
        xml = f"""<Experiment xmlns="{NS}">
          <acquisitionActivity seqno="0">
            <dataset><name>a.dm3</name><meta name="A">1</meta></dataset>
          </acquisitionActivity>
        </Experiment>"""
        root = ET.fromstring(xml)
        act = root.find("nx:acquisitionActivity", NS_MAP)
        ds = act.find("nx:dataset", NS_MAP)
        before = len(ds.findall(_t("meta")))
        _inject_setup_into_dataset(ds, act)
        self.assertEqual(len(ds.findall(_t("meta"))), before)

    def test_unit_attribute_carried_over(self):
        xml = f"""<Experiment xmlns="{NS}">
          <acquisitionActivity seqno="0">
            <setup><param name="Voltage" unit="V">300000</param></setup>
            <dataset><name>a.dm3</name></dataset>
          </acquisitionActivity>
        </Experiment>"""
        root = ET.fromstring(xml)
        act = root.find("nx:acquisitionActivity", NS_MAP)
        ds = act.find("nx:dataset", NS_MAP)
        _inject_setup_into_dataset(ds, act)
        meta = _find_meta(ds, "Voltage")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.get("unit"), "V")
        self.assertEqual(meta.text, "300000")


# ===========================================================================
# _recompute_activity_setup
# ===========================================================================

class RecomputeActivitySetupTests(SimpleTestCase):
    def _make_activity(self, *dataset_meta_dicts, existing_setup=None):
        """Build an <acquisitionActivity> element with datasets having the given metas."""
        act = ET.Element(_t("acquisitionActivity"))
        act.set("seqno", "0")
        if existing_setup:
            setup_el = ET.SubElement(act, _t("setup"))
            for name, value in existing_setup.items():
                p = ET.SubElement(setup_el, _t("param"))
                p.set("name", name)
                p.text = value
        for meta_dict in dataset_meta_dicts:
            ds = ET.SubElement(act, _t("dataset"))
            for name, value in meta_dict.items():
                m = ET.SubElement(ds, _t("meta"))
                m.set("name", name)
                m.text = value
        return act

    def test_common_params_promoted_to_setup(self):
        act = self._make_activity(
            {"Voltage": "300", "Mode": "TEM", "StageX": "-192"},
            {"Voltage": "300", "Mode": "TEM", "StageX": "-195"},
        )
        _recompute_activity_setup(act)
        setup_names = _setup_param_names(act)
        self.assertIn("Voltage", setup_names)
        self.assertIn("Mode", setup_names)

    def test_non_common_params_not_in_setup(self):
        act = self._make_activity(
            {"Voltage": "300", "StageX": "-192"},
            {"Voltage": "300", "StageX": "-195"},
        )
        _recompute_activity_setup(act)
        self.assertNotIn("StageX", _setup_param_names(act))

    def test_promoted_params_removed_from_dataset_meta(self):
        act = self._make_activity(
            {"Voltage": "300", "StageX": "-192"},
            {"Voltage": "300", "StageX": "-195"},
        )
        _recompute_activity_setup(act)
        for ds in act.findall(_t("dataset")):
            self.assertNotIn("Voltage", _meta_names(ds))
            self.assertIn("StageX", _meta_names(ds))

    def test_non_promoted_params_remain_in_dataset_meta(self):
        act = self._make_activity(
            {"Voltage": "300", "StageX": "-192"},
            {"Voltage": "300", "StageX": "-195"},
        )
        _recompute_activity_setup(act)
        stagex_values = [
            _find_meta(ds, "StageX").text
            for ds in act.findall(_t("dataset"))
        ]
        self.assertIn("-192", stagex_values)
        self.assertIn("-195", stagex_values)

    def test_no_common_params_means_no_setup_element(self):
        act = self._make_activity(
            {"StageX": "-192"},
            {"StageX": "-195"},
        )
        _recompute_activity_setup(act)
        self.assertIsNone(act.find(_t("setup")))

    def test_single_dataset_all_meta_becomes_setup(self):
        act = self._make_activity({"Voltage": "300", "Mode": "TEM"})
        _recompute_activity_setup(act)
        self.assertEqual(_setup_param_names(act), {"Voltage", "Mode"})

    def test_single_dataset_meta_emptied_after_full_promotion(self):
        act = self._make_activity({"Voltage": "300", "Mode": "TEM"})
        _recompute_activity_setup(act)
        ds = act.find(_t("dataset"))
        self.assertEqual(len(ds.findall(_t("meta"))), 0)

    def test_empty_activity_has_no_setup(self):
        act = ET.Element(_t("acquisitionActivity"))
        act.set("seqno", "0")
        _recompute_activity_setup(act)
        self.assertIsNone(act.find(_t("setup")))

    def test_only_one_setup_element_after_recompute(self):
        act = self._make_activity(
            {"Voltage": "300"},
            {"Voltage": "300"},
            existing_setup={"OldParam": "stale"},
        )
        _recompute_activity_setup(act)
        self.assertEqual(len(act.findall(_t("setup"))), 1)

    def test_old_setup_values_preserved_in_dataset_meta_before_removal(self):
        # Datasets start with only StageX in their meta; Voltage is only in setup.
        # After recompute, Voltage must survive (injected into datasets first).
        act = self._make_activity(
            {"StageX": "-192"},
            {"StageX": "-195"},
            existing_setup={"Voltage": "300"},
        )
        _recompute_activity_setup(act)
        # Voltage is now common (same for both datasets after injection), so it goes to setup
        self.assertIn("Voltage", _setup_param_names(act))


# ===========================================================================
# _apply_moves
# ===========================================================================

class ApplyMovesTests(SimpleTestCase):
    # original dataset counts in each activity
    orig_0 = _dataset_count_in_activity(_TWO_ACTIVITY_XML, "0")
    orig_1 = _dataset_count_in_activity(_TWO_ACTIVITY_XML, "1")

    def test_dataset_moved_to_target_activity(self):
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 0, "targetActivitySeqno": "1"}])
        self.assertIn("image_001.dm3", _dataset_names_in_activity(result, "1"))

    def test_dataset_removed_from_source_activity(self):
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 0, "targetActivitySeqno": "1"}])
        self.assertNotIn("image_001.dm3", _dataset_names_in_activity(result, "0"))

    def test_source_activity_loses_one_dataset(self):
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 0, "targetActivitySeqno": "1"}])
        self.assertEqual(_dataset_count_in_activity(result, "0"), 1)

    def test_target_activity_gains_one_dataset(self):
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 0, "targetActivitySeqno": "1"}])
        self.assertEqual(_dataset_count_in_activity(result, "1"), self.orig_1 + 1)

    def test_no_op_when_target_is_same_activity(self):
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 0, "targetActivitySeqno": "0"}])
        self.assertEqual(_dataset_count_in_activity(result, "0"), self.orig_0)
        self.assertEqual(_dataset_count_in_activity(result, "1"), self.orig_1)

    def test_empty_moves_returns_identical_xml(self):
        result = _apply_moves(_TWO_ACTIVITY_XML, [])
        self.assertEqual(result, _TWO_ACTIVITY_XML)

    def test_deduplication_last_move_wins(self):
        # Two entries for index 0: first to activity 1, then back to activity 0.
        # After dedup, only the last (activity 0) survives -- a no-op.
        moves = [
            {"datasetIndex": 0, "targetActivitySeqno": "1"},
            {"datasetIndex": 0, "targetActivitySeqno": "0"},
        ]
        result = _apply_moves(_TWO_ACTIVITY_XML, moves)
        self.assertEqual(_dataset_count_in_activity(result, "0"), self.orig_0)
        self.assertEqual(_dataset_count_in_activity(result, "1"), self.orig_1)

    def test_multiple_datasets_moved_in_one_call(self):
        moves = [
            {"datasetIndex": 0, "targetActivitySeqno": "1"},
            {"datasetIndex": 1, "targetActivitySeqno": "1"},
        ]
        result = _apply_moves(_TWO_ACTIVITY_XML, moves)
        self.assertEqual(_dataset_count_in_activity(result, "0"), self.orig_0 - 2)
        self.assertEqual(_dataset_count_in_activity(result, "1"), self.orig_1 + 2)

    def test_out_of_range_index_ignored_gracefully(self):
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 999, "targetActivitySeqno": "1"}])
        self.assertEqual(_dataset_count_in_activity(result, "0"), self.orig_0)
        self.assertEqual(_dataset_count_in_activity(result, "1"), self.orig_1)

    def test_source_setup_injected_into_moved_dataset(self):
        # image_001.dm3 (index 0) had Voltage=300000 and Magnification=17677 in activity 0's
        # setup. After moving to activity 1, both values must be preserved in the output.
        # Voltage=300000 is common to all datasets in activity 1 so it ends up in setup;
        # Magnification=17677 differs from image_003 and image_004's 25000, so it gets demote
        # to meta. Only setup param in activity 1 should be Voltage, and image_003 and image_004
        # should gain Magnification meta elements
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 0, "targetActivitySeqno": "1"}])
        root = ET.fromstring(result)
        moved_ds = None
        act1 = None
        for act in root.findall("nx:acquisitionActivity", NS_MAP):
            if act.get("seqno") == "1":
                act1 = act
                for ds in act.findall("nx:dataset", NS_MAP):
                    name_el = ds.find("nx:name", NS_MAP)
                    if name_el is not None and name_el.text == "image_001.dm3":
                        moved_ds = ds
        self.assertIsNotNone(moved_ds, "image_001.dm3 not found in activity 1 after move")
        # Magnification differs between datasets so it must remain in meta for the moved dataset
        mag = _find_meta(moved_ds, "Magnification")
        self.assertIsNotNone(mag, "Magnification not found in image_001.dm3 meta after move")
        self.assertEqual(mag.text, "17677.0")
        # Voltage is common to all datasets in activity 1, so it must be in setup (not meta)
        self.assertIn("Voltage", _setup_param_names(act1))
        self.assertNotIn("Voltage", _meta_names(moved_ds))

    def test_moved_dataset_carries_correct_magnification_from_source(self):
        # image_001.dm3 comes from activity 0 (Magnification=17677.0);
        # after landing in activity 1 (setup Magnification=25000.0),
        # the injected value from source should be 17677.0, not 25000.0.
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 0, "targetActivitySeqno": "1"}])
        root = ET.fromstring(result)
        for act in root.findall("nx:acquisitionActivity", NS_MAP):
            if act.get("seqno") == "1":
                for ds in act.findall("nx:dataset", NS_MAP):
                    name_el = ds.find("nx:name", NS_MAP)
                    if name_el is not None and name_el.text == "image_001.dm3":
                        meta = _find_meta(ds, "Magnification")
                        self.assertIsNotNone(meta)
                        self.assertEqual(meta.text, "17677.0")
                        return
        self.fail("image_001.dm3 not found in activity 1")

    def test_target_setup_recomputed_to_reflect_common_values_only(self):
        # After moving image_001.dm3 (Voltage=300000, Magnification=17677) to activity 1
        # which already has image_003.dm3 and image_004.dm3 (Voltage=300000, 
        # Magnification=25000 after injection),
        # the common value is only Voltage. Magnification differs so must NOT be in setup.
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 0, "targetActivitySeqno": "1"}])
        root = ET.fromstring(result)
        for act in root.findall("nx:acquisitionActivity", NS_MAP):
            if act.get("seqno") == "1":
                setup_names = _setup_param_names(act)
                self.assertIn("Voltage", setup_names)
                self.assertNotIn("Magnification", setup_names)
                return
        self.fail("Activity 1 not found")

    def test_xml_result_is_valid_xml_string(self):
        result = _apply_moves(_TWO_ACTIVITY_XML, [{"datasetIndex": 0, "targetActivitySeqno": "1"}])
        self.assertIsInstance(result, str)
        # Must be parseable
        ET.fromstring(result)


# ===========================================================================
# _apply_descriptions
# ===========================================================================

class ApplyDescriptionsTests(SimpleTestCase):
    def _get_description(self, xml_str, dataset_index):
        """Parse xml_str and return the description text of the Nth dataset (flat order)."""
        root = ET.fromstring(xml_str)
        idx = 0
        for act in root.findall("nx:acquisitionActivity", NS_MAP):
            for ds in act.findall("nx:dataset", NS_MAP):
                if idx == dataset_index:
                    desc = ds.find("nx:description", NS_MAP)
                    return desc.text if desc is not None else None
                idx += 1
        return None

    def test_sets_description_by_flat_index(self):
        post = {"dataset_1_description": "Second dataset note"}
        result = _apply_descriptions(_TWO_ACTIVITY_XML, post)
        self.assertEqual(self._get_description(result, 1), "Second dataset note")

    def test_clears_existing_description_when_blank(self):
        # dataset 0 starts with "First image"
        post = {"dataset_0_description": ""}
        result = _apply_descriptions(_TWO_ACTIVITY_XML, post)
        self.assertIsNone(self._get_description(result, 0))

    def test_replaces_existing_description(self):
        post = {"dataset_0_description": "Updated description"}
        result = _apply_descriptions(_TWO_ACTIVITY_XML, post)
        self.assertEqual(self._get_description(result, 0), "Updated description")

    def test_missing_key_clears_existing_description(self):
        # If a key is absent, the description defaults to '' and is removed
        post = {}  # no key for dataset 0
        result = _apply_descriptions(_TWO_ACTIVITY_XML, post)
        self.assertIsNone(self._get_description(result, 0))

    def test_multiple_datasets_each_get_correct_value(self):
        post = {
            "dataset_0_description": "Desc A",
            "dataset_1_description": "Desc B",
            "dataset_2_description": "Desc C",
        }
        result = _apply_descriptions(_TWO_ACTIVITY_XML, post)
        self.assertEqual(self._get_description(result, 0), "Desc A")
        self.assertEqual(self._get_description(result, 1), "Desc B")
        self.assertEqual(self._get_description(result, 2), "Desc C")

    def test_description_inserted_after_format_element(self):
        # Our fixture datasets all have <format>. Description should follow it.
        post = {"dataset_1_description": "Some note"}
        result = _apply_descriptions(_TWO_ACTIVITY_XML, post)
        root = ET.fromstring(result)
        act = root.findall("nx:acquisitionActivity", NS_MAP)[0]
        ds = act.findall("nx:dataset", NS_MAP)[1]
        children_tags = [c.tag.split("}")[-1] for c in ds]
        format_pos = children_tags.index("format")
        desc_pos = children_tags.index("description")
        self.assertGreater(desc_pos, format_pos)

    def test_description_inserted_after_location_when_no_format(self):
        xml = f"""<Experiment xmlns="{NS}">
          <acquisitionActivity seqno="0">
            <dataset>
              <name>test.dm3</name>
              <location>/data/test.dm3</location>
            </dataset>
          </acquisitionActivity>
        </Experiment>"""
        post = {"dataset_0_description": "No format note"}
        result = _apply_descriptions(xml, post)
        root = ET.fromstring(result)
        act = root.find("nx:acquisitionActivity", NS_MAP)
        ds = act.find("nx:dataset", NS_MAP)
        children_tags = [c.tag.split("}")[-1] for c in ds]
        location_pos = children_tags.index("location")
        desc_pos = children_tags.index("description")
        self.assertGreater(desc_pos, location_pos)

    def test_only_one_description_element_after_update(self):
        # Start with a description (dataset 0) and overwrite it
        post = {"dataset_0_description": "Overwritten"}
        result = _apply_descriptions(_TWO_ACTIVITY_XML, post)
        root = ET.fromstring(result)
        act = root.findall("nx:acquisitionActivity", NS_MAP)[0]
        ds = act.findall("nx:dataset", NS_MAP)[0]
        descs = ds.findall("nx:description", NS_MAP)
        self.assertEqual(len(descs), 1)
        self.assertEqual(descs[0].text, "Overwritten")

    def test_returns_valid_xml_string(self):
        post = {"dataset_0_description": "Test"}
        result = _apply_descriptions(_TWO_ACTIVITY_XML, post)
        self.assertIsInstance(result, str)
        ET.fromstring(result)  # must parse without error


# ===========================================================================
# _dataset_creation_time
# ===========================================================================

class DatasetCreationTimeTests(SimpleTestCase):
    def _ds_with_meta(self, creation_time_value=None, name=None):
        ds = ET.Element(_t("dataset"))
        if name:
            n = ET.SubElement(ds, _t("name"))
            n.text = name
        if creation_time_value is not None:
            m = ET.SubElement(ds, _t("meta"))
            m.set("name", "Creation Time")
            m.text = creation_time_value
        return ds

    def test_parses_iso_creation_time_meta(self):
        ds = self._ds_with_meta("2024-01-15T10:01:00-05:00")
        t = _dataset_creation_time(ds)
        self.assertIsNotNone(t)
        self.assertEqual(t.year, 2024)
        self.assertEqual(t.hour, 10)
        self.assertEqual(t.minute, 1)

    def test_falls_back_to_filename_timestamp(self):
        ds = self._ds_with_meta(name="2024-01-15 10:05:00 scan_0001.dm3")
        t = _dataset_creation_time(ds)
        self.assertIsNotNone(t)
        self.assertEqual(t.year, 2024)
        self.assertEqual(t.minute, 5)

    def test_returns_none_when_no_timestamp(self):
        ds = self._ds_with_meta(name="no_timestamp_here.dm3")
        self.assertIsNone(_dataset_creation_time(ds))

    def test_meta_takes_precedence_over_filename(self):
        ds = self._ds_with_meta(
            creation_time_value="2024-01-15T10:01:00-05:00",
            name="2024-01-15 11:00:00 filename.dm3",
        )
        t = _dataset_creation_time(ds)
        self.assertEqual(t.hour, 10)  # meta value, not filename value


# ===========================================================================
# _sort_datasets_by_creation_time
# ===========================================================================

class SortDatasetsByCreationTimeTests(SimpleTestCase):
    def _activity_with_datasets(self, *name_time_pairs):
        """Build activity with datasets given as (name, creation_time_iso) tuples."""
        act = ET.Element(_t("acquisitionActivity"))
        act.set("seqno", "0")
        for name, ct in name_time_pairs:
            ds = ET.SubElement(act, _t("dataset"))
            n = ET.SubElement(ds, _t("name"))
            n.text = name
            if ct:
                m = ET.SubElement(ds, _t("meta"))
                m.set("name", "Creation Time")
                m.text = ct
        return act

    def _names(self, activity_el):
        return [
            ds.find(_t("name")).text
            for ds in activity_el.findall(_t("dataset"))
        ]

    def test_sorts_ascending_by_creation_time(self):
        act = self._activity_with_datasets(
            ("c.dm3", "2024-01-15T10:03:00"),
            ("a.dm3", "2024-01-15T10:01:00"),
            ("b.dm3", "2024-01-15T10:02:00"),
        )
        _sort_datasets_by_creation_time(act)
        self.assertEqual(self._names(act), ["a.dm3", "b.dm3", "c.dm3"])

    def test_datasets_without_timestamp_sort_last(self):
        act = self._activity_with_datasets(
            ("no_ts.dm3", None),
            ("b.dm3", "2024-01-15T10:02:00"),
            ("a.dm3", "2024-01-15T10:01:00"),
        )
        _sort_datasets_by_creation_time(act)
        names = self._names(act)
        self.assertEqual(names[0], "a.dm3")
        self.assertEqual(names[1], "b.dm3")
        self.assertEqual(names[2], "no_ts.dm3")

    def test_single_dataset_unchanged(self):
        act = self._activity_with_datasets(("only.dm3", "2024-01-15T10:00:00"))
        _sort_datasets_by_creation_time(act)
        self.assertEqual(self._names(act), ["only.dm3"])

    def test_already_sorted_unchanged(self):
        act = self._activity_with_datasets(
            ("a.dm3", "2024-01-15T10:01:00"),
            ("b.dm3", "2024-01-15T10:02:00"),
        )
        _sort_datasets_by_creation_time(act)
        self.assertEqual(self._names(act), ["a.dm3", "b.dm3"])


# ===========================================================================
# _apply_moves -- creation-time ordering
# ===========================================================================

class ApplyMovesOrderingTests(SimpleTestCase):
    def _names_in_activity(self, xml_str, seqno):
        return _dataset_names_in_activity(xml_str, seqno)

    def test_moved_dataset_inserted_in_creation_time_order(self):
        # image_001 (10:01) is moved to activity 1 which has image_003 (11:01).
        # image_001 should appear before image_003 in activity 1.
        result = _apply_moves(
            _TWO_ACTIVITY_XML,
            [{"datasetIndex": 0, "targetActivitySeqno": "1"}],
        )
        names = self._names_in_activity(result, "1")
        self.assertEqual(names.index("image_001.dm3"), 0)
        self.assertEqual(names.index("image_003.dm3"), 1)

    def test_later_dataset_appended_at_end(self):
        # image_003 (11:01) is moved to activity 0 which has image_001 (10:01) + image_002 (10:02).
        # image_003 should appear last.
        result = _apply_moves(
            _TWO_ACTIVITY_XML,
            [{"datasetIndex": 2, "targetActivitySeqno": "0"}],
        )
        names = self._names_in_activity(result, "0")
        self.assertEqual(names[-1], "image_003.dm3")

    def test_source_activity_order_preserved_after_removal(self):
        # After moving image_001 out of activity 0, image_002 should still be there
        # and since it's the only dataset, order is trivially preserved.
        result = _apply_moves(
            _TWO_ACTIVITY_XML,
            [{"datasetIndex": 0, "targetActivitySeqno": "1"}],
        )
        names = self._names_in_activity(result, "0")
        self.assertEqual(names, ["image_002.dm3"])


# ===========================================================================
# _apply_moves -- setup contamination regression (skip_inject fix)
#
# Fixture: two activities with completely non-overlapping setup params to make
# contamination unambiguous.
#
#   Activity 0 (TEM): setup TEM_DataType + TEM_Mag; two TEM datasets
#   Activity 1 (STEM): setup STEM_DataType + STEM_Mag; two STEM datasets
#
# Datasets (flat indices):
#   0 = tem_001.dm3  (activity 0)
#   1 = tem_002.dm3  (activity 0)
#   2 = stem_001.ser (activity 1)  <-- used as the moved dataset
#   3 = stem_002.ser (activity 1)
# ===========================================================================

_TEM_STEM_XML = f"""\
<?xml version='1.0' encoding='UTF-8'?>
<Experiment xmlns="{NS}">
  <acquisitionActivity seqno="0">
    <startTime>2024-01-15T10:00:00-05:00</startTime>
    <setup>
      <param name="TEM_DataType">TEM_Imaging</param>
      <param name="TEM_Mag">17677.0</param>
    </setup>
    <dataset type="Image">
      <name>tem_001.dm3</name>
      <location>/data/tem_001.dm3</location>
      <meta name="StageX">-192.0</meta>
      <meta name="Creation Time">2024-01-15T10:01:00-05:00</meta>
    </dataset>
    <dataset type="Image">
      <name>tem_002.dm3</name>
      <location>/data/tem_002.dm3</location>
      <meta name="StageX">-193.0</meta>
      <meta name="Creation Time">2024-01-15T10:02:00-05:00</meta>
    </dataset>
  </acquisitionActivity>
  <acquisitionActivity seqno="1">
    <startTime>2024-01-15T12:00:00-05:00</startTime>
    <setup>
      <param name="STEM_DataType">STEM_Imaging</param>
      <param name="STEM_Mag">20000.0</param>
    </setup>
    <dataset type="Image">
      <name>stem_001.ser</name>
      <location>/data/stem_001.ser</location>
      <meta name="DwellTime">0.000048</meta>
      <meta name="Creation Time">2024-01-15T12:01:00-05:00</meta>
    </dataset>
    <dataset type="Image">
      <name>stem_002.ser</name>
      <location>/data/stem_002.ser</location>
      <meta name="DwellTime">0.000048</meta>
      <meta name="Creation Time">2024-01-15T12:02:00-05:00</meta>
    </dataset>
  </acquisitionActivity>
</Experiment>"""


def _get_dataset(xml_str, name):
    """Return the dataset element with the given <name> text, or None."""
    root = ET.fromstring(xml_str)
    for act in root.findall("nx:acquisitionActivity", NS_MAP):
        for ds in act.findall("nx:dataset", NS_MAP):
            n = ds.find("nx:name", NS_MAP)
            if n is not None and n.text == name:
                return ds
    return None


class ApplyMovesNoContaminationTests(SimpleTestCase):
    """Regression tests for the skip_inject fix in _apply_moves / _recompute_activity_setup.

    Before the fix, _recompute_activity_setup injected the receiving activity's old
    setup params into ALL its datasets, including datasets that were just moved in.
    This caused moved datasets to pick up unrelated metadata from the destination.
    """

    def _move_stem_to_tem(self):
        """Move stem_001.ser (index 2) from activity 1 into activity 0."""
        return _apply_moves(
            _TEM_STEM_XML,
            [{"datasetIndex": 2, "targetActivitySeqno": "0"}],
        )

    # -- Core contamination assertions ------------------------------------

    def test_moved_dataset_does_not_receive_tem_datatype(self):
        result = self._move_stem_to_tem()
        ds = _get_dataset(result, "stem_001.ser")
        self.assertIsNotNone(ds)
        self.assertNotIn("TEM_DataType", _meta_names(ds))

    def test_moved_dataset_does_not_receive_tem_magnification(self):
        result = self._move_stem_to_tem()
        ds = _get_dataset(result, "stem_001.ser")
        self.assertIsNotNone(ds)
        self.assertNotIn("TEM_Mag", _meta_names(ds))

    # -- Source params preserved ------------------------------------------

    def test_moved_dataset_retains_stem_datatype_from_source(self):
        result = self._move_stem_to_tem()
        ds = _get_dataset(result, "stem_001.ser")
        self.assertIsNotNone(ds)
        # STEM_DataType was in activity 1's setup; it must be carried over as meta
        # (it won't be promoted to activity 0's setup since TEM datasets don't share it)
        self.assertIn("STEM_DataType", _meta_names(ds))
        self.assertEqual(_find_meta(ds, "STEM_DataType").text, "STEM_Imaging")

    def test_moved_dataset_retains_stem_magnification_from_source(self):
        result = self._move_stem_to_tem()
        ds = _get_dataset(result, "stem_001.ser")
        self.assertIsNotNone(ds)
        self.assertIn("STEM_Mag", _meta_names(ds))
        self.assertEqual(_find_meta(ds, "STEM_Mag").text, "20000.0")

    # -- Native datasets in receiving activity unaffected -----------------

    def test_native_tem_datasets_still_have_their_setup_params_after_move(self):
        # tem_001 and tem_002 must still carry TEM_DataType and TEM_Mag after the
        # recompute (injected from old setup before it is cleared, then promoted back
        # to setup or kept in meta depending on intersection).
        result = self._move_stem_to_tem()
        root = ET.fromstring(result)
        for act in root.findall("nx:acquisitionActivity", NS_MAP):
            if act.get("seqno") != "0":
                continue
            for ds in act.findall("nx:dataset", NS_MAP):
                name_el = ds.find("nx:name", NS_MAP)
                if name_el is None or name_el.text == "stem_001.ser":
                    continue
                # The TEM param must exist somewhere: either in the activity setup or
                # in the dataset's own meta (depends on intersection result).
                setup_names = _setup_param_names(act)
                has_tem_mag = (
                    "TEM_Mag" in setup_names or "TEM_Mag" in _meta_names(ds)
                )
                self.assertTrue(
                    has_tem_mag,
                    f"{name_el.text} lost TEM_Mag after move",
                )

    # -- Batch move: multiple STEM datasets moved simultaneously ----------

    def test_batch_move_no_contamination_on_any_moved_dataset(self):
        # Move both stem_001.ser (index 2) and stem_002.ser (index 3) to activity 0.
        result = _apply_moves(
            _TEM_STEM_XML,
            [
                {"datasetIndex": 2, "targetActivitySeqno": "0"},
                {"datasetIndex": 3, "targetActivitySeqno": "0"},
            ],
        )
        for name in ("stem_001.ser", "stem_002.ser"):
            ds = _get_dataset(result, name)
            self.assertIsNotNone(ds, f"{name} not found after batch move")
            self.assertNotIn(
                "TEM_DataType", _meta_names(ds),
                f"{name} was contaminated with TEM_DataType",
            )
            self.assertNotIn(
                "TEM_Mag", _meta_names(ds),
                f"{name} was contaminated with TEM_Mag",
            )


# ---------------------------------------------------------------------------
# Sort fix: multiple datasets without timestamps must not raise TypeError
# ---------------------------------------------------------------------------

class SortNoTimestampTest(SimpleTestCase):
    """_sort_datasets_by_creation_time must not raise when multiple datasets lack timestamps."""

    def _make_activity_xml(self, names):
        """Build an activity element whose datasets have the given names and no timestamps."""
        activity = ET.Element(f"{{{NS}}}acquisitionActivity")
        activity.set("seqno", "0")
        for name in names:
            ds = ET.SubElement(activity, f"{{{NS}}}dataset")
            name_el = ET.SubElement(ds, f"{{{NS}}}name")
            name_el.text = name
        return activity

    def test_all_datasets_missing_timestamp_no_error(self):
        """Three datasets without any timestamp should not raise TypeError."""
        activity = self._make_activity_xml(["a.dm3", "b.dm3", "c.dm3"])
        # Must not raise TypeError
        from nexuslims_annotate.views import _sort_datasets_by_creation_time
        _sort_datasets_by_creation_time(activity)
        names_after = [
            ds.find(f"{{{NS}}}name").text
            for ds in activity.findall(f"{{{NS}}}dataset")
        ]
        # All names still present (order is stable for ties)
        self.assertEqual(set(names_after), {"a.dm3", "b.dm3", "c.dm3"})

    def test_mixed_timestamp_and_no_timestamp(self):
        """Datasets with timestamps sort before those without."""
        activity = self._make_activity_xml(["no_ts_1.dm3", "no_ts_2.dm3"])
        # Add a third dataset that does have a timestamp
        ds_with_ts = ET.SubElement(activity, f"{{{NS}}}dataset")
        name_el = ET.SubElement(ds_with_ts, f"{{{NS}}}name")
        name_el.text = "has_ts.dm3"
        meta = ET.SubElement(ds_with_ts, f"{{{NS}}}meta")
        meta.set("name", "Creation Time")
        meta.text = "2024-01-15T10:00:00"

        from nexuslims_annotate.views import _sort_datasets_by_creation_time
        _sort_datasets_by_creation_time(activity)
        names_after = [
            ds.find(f"{{{NS}}}name").text
            for ds in activity.findall(f"{{{NS}}}dataset")
        ]
        # Timestamped dataset sorts first
        self.assertEqual(names_after[0], "has_ts.dm3")
        self.assertIn("no_ts_1.dm3", names_after[1:])
        self.assertIn("no_ts_2.dm3", names_after[1:])


# ---------------------------------------------------------------------------
# View integration tests
# ---------------------------------------------------------------------------

User = get_user_model()


def _make_mock_data(xml_content=None):
    """Return a minimal mock data object mimicking core_main_app Data."""
    if xml_content is None:
        xml_content = _TWO_ACTIVITY_XML
    data = MagicMock()
    data.content = xml_content
    data.id = "test-record-id"
    return data


class AnnotateRecordViewTest(TestCase):
    """Tests for the annotate_record full-page view."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser_rec", password="pass")
        self.client.force_login(self.user)

    def test_unauthenticated_redirects(self):
        self.client.logout()
        response = self.client.get("/annotate/some-id/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response["Location"])

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    def test_missing_record_returns_404(self, mock_get):
        from core_main_app.commons.exceptions import DoesNotExist
        mock_get.side_effect = DoesNotExist("not found")
        response = self.client.get("/annotate/bad-id/")
        self.assertEqual(response.status_code, 404)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.check_can_write")
    def test_unauthorized_returns_403(self, mock_check, mock_get):
        from core_main_app.access_control.exceptions import AccessControlError
        mock_get.return_value = _make_mock_data()
        mock_check.side_effect = AccessControlError("no access")
        response = self.client.get("/annotate/test-id/")
        self.assertEqual(response.status_code, 403)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.check_can_write")
    def test_malformed_xml_returns_500_with_template(self, _mock_check, mock_get):
        mock_get.return_value = _make_mock_data(xml_content="<not valid xml <<")
        response = self.client.get("/annotate/test-id/")
        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, "nexuslims_annotate/annotate.html")

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.check_can_write")
    def test_success_renders_annotate_template(self, _mock_check, mock_get):
        mock_get.return_value = _make_mock_data()
        response = self.client.get("/annotate/test-id/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nexuslims_annotate/annotate.html")

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.check_can_write")
    def test_error_query_param_shows_save_error_banner(self, _mock_check, mock_get):
        mock_get.return_value = _make_mock_data()
        response = self.client.get("/annotate/test-id/?error=1")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An error occurred while saving")


class AnnotateDescriptionsViewTest(TestCase):
    """Tests for the annotate_descriptions view permission check."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client.force_login(self.user)

    def test_unauthenticated_redirects_to_login(self):
        self.client.logout()
        response = self.client.get("/annotate/some-id/descriptions/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response["Location"])

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.check_can_write")
    def test_authenticated_with_access_returns_200(self, mock_check, mock_get):
        mock_get.return_value = _make_mock_data()
        # check_can_write succeeds (no exception)
        response = self.client.get("/annotate/test-id/descriptions/")
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertIn("datasets", body)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.check_can_write")
    def test_authenticated_without_write_access_returns_403(self, mock_check, mock_get):
        from core_main_app.access_control.exceptions import AccessControlError
        mock_get.return_value = _make_mock_data()
        mock_check.side_effect = AccessControlError("no access")
        response = self.client.get("/annotate/test-id/descriptions/")
        self.assertEqual(response.status_code, 403)
        body = json.loads(response.content)
        self.assertIn("error", body)


class AnnotateSaveOneViewTest(TestCase):
    """Tests for the annotate_save_one view."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser2", password="pass")
        self.client.force_login(self.user)

    def test_get_method_returns_405(self):
        response = self.client.get("/annotate/test-id/save-one/")
        self.assertEqual(response.status_code, 405)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.data_api.upsert")
    def test_non_integer_dataset_index_returns_400(self, mock_upsert, mock_get):
        """A non-integer dataset_index should return 400."""
        mock_get.return_value = _make_mock_data()
        response = self.client.post(
            "/annotate/test-id/save-one/",
            {"dataset_index": "not-an-int", "description": "hello"},
        )
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertIn("error", body)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.data_api.upsert")
    def test_valid_post_returns_success(self, mock_upsert, mock_get):
        mock_get.return_value = _make_mock_data()
        response = self.client.post(
            "/annotate/test-id/save-one/",
            {"dataset_index": "0", "description": "A test description"},
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertTrue(body.get("success"))

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.data_api.upsert")
    def test_out_of_range_dataset_index_returns_400(self, mock_upsert, mock_get):
        """dataset_index beyond the number of datasets returns 400."""
        mock_get.return_value = _make_mock_data()
        response = self.client.post(
            "/annotate/test-id/save-one/",
            {"dataset_index": "999", "description": "hello"},
        )
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertIn("error", body)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.data_api.upsert")
    def test_unauthorized_returns_403(self, mock_upsert, mock_get):
        """upsert raising AccessControlError returns 403."""
        from core_main_app.access_control.exceptions import AccessControlError
        mock_get.return_value = _make_mock_data()
        mock_upsert.side_effect = AccessControlError("no write access")
        response = self.client.post(
            "/annotate/test-id/save-one/",
            {"dataset_index": "0", "description": "hello"},
        )
        self.assertEqual(response.status_code, 403)
        body = json.loads(response.content)
        self.assertIn("error", body)


class AnnotatePanelViewTest(TestCase):
    """Tests for the annotate_panel view."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser3", password="pass")
        self.client.force_login(self.user)

    def test_unauthenticated_redirects(self):
        self.client.logout()
        response = self.client.get("/annotate/some-id/panel/")
        self.assertEqual(response.status_code, 302)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    def test_missing_record_returns_404(self, mock_get):
        from core_main_app.commons.exceptions import DoesNotExist
        mock_get.side_effect = DoesNotExist("not found")
        response = self.client.get("/annotate/bad-id/panel/")
        self.assertEqual(response.status_code, 404)

    def test_post_method_returns_405(self):
        response = self.client.post("/annotate/some-id/panel/")
        self.assertEqual(response.status_code, 405)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.check_can_write")
    def test_malformed_xml_returns_500(self, _mock_check, mock_get):
        mock_get.return_value = _make_mock_data(xml_content="<not valid xml <<")
        response = self.client.get("/annotate/test-id/panel/")
        self.assertEqual(response.status_code, 500)
        body = json.loads(response.content)
        self.assertIn("error", body)


class AnnotateSaveViewTest(TestCase):
    """Tests for the annotate_save view."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser4", password="pass")
        self.client.force_login(self.user)

    def test_get_method_returns_405(self):
        response = self.client.get("/annotate/test-id/save/")
        self.assertEqual(response.status_code, 405)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    def test_missing_record_returns_404_for_ajax(self, mock_get):
        from core_main_app.commons.exceptions import DoesNotExist
        mock_get.side_effect = DoesNotExist("not found")
        response = self.client.post(
            "/annotate/bad-id/save/",
            {"dataset_0_description": "hello"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)
        body = json.loads(response.content)
        self.assertIn("error", body)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.data_api.upsert")
    def test_valid_post_returns_success(self, _mock_upsert, mock_get):
        mock_get.return_value = _make_mock_data()
        response = self.client.post(
            "/annotate/test-id/save/",
            {"dataset_0_description": "A description"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertTrue(body.get("success"))


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

    @patch('nexuslims_annotate.views.data_api.get_by_id')
    @patch('nexuslims_annotate.views.data_api.upsert')
    def test_missing_samples_field_preserves_existing_samples(self, mock_upsert, mock_get):
        """If 'samples' is absent from POST, existing samples must not be removed."""
        data_obj = _make_mock_data(_WITH_SAMPLES_XML)
        mock_get.return_value = data_obj
        response = self.client.post(
            '/annotate/test-id/save/',
            {'dataset_0_description': 'A description'},  # no 'samples' field
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        saved_xml = mock_upsert.call_args[0][0].content
        root = ET.fromstring(saved_xml)
        NS_STR = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        samples = root.findall(f'{{{NS_STR}}}sample')
        self.assertEqual(len(samples), 2)  # _WITH_SAMPLES_XML has 2 samples

    @patch('nexuslims_annotate.views.data_api.get_by_id')
    @patch('nexuslims_annotate.views.data_api.upsert')
    def test_move_after_deletion_uses_original_seqno(self, mock_upsert, mock_get):
        """Moving a dataset to an activity whose seqno did not change still works after a deletion."""
        NS_STR = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
        # XML: seqno 0 has 'only.dm3', seqno 1 is empty (to be deleted), seqno 2 is also empty
        xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<Experiment xmlns="{NS_STR}">
  <title>T</title>
  <acquisitionActivity seqno="0">
    <startTime>2024-01-15T10:00:00-05:00</startTime>
    <dataset type="Image">
      <name>only.dm3</name>
      <location>/data/only.dm3</location>
    </dataset>
  </acquisitionActivity>
  <acquisitionActivity seqno="1"/>
  <acquisitionActivity seqno="2"/>
</Experiment>"""
        data_obj = _make_mock_data(xml)
        mock_get.return_value = data_obj
        # Delete seqno 1, move dataset from seqno 0 to seqno 2
        response = self.client.post(
            '/annotate/test-id/save/',
            {
                'deleted_seqnos': json.dumps(['1']),
                'new_activities': '[]',
                'activity_sample_ids': '{}',
                'samples': '[]',
                'moves': json.dumps([{'datasetIndex': 0, 'targetActivitySeqno': '2'}]),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        saved_xml = mock_upsert.call_args[0][0].content
        root = ET.fromstring(saved_xml)
        acts = root.findall(f'{{{NS_STR}}}acquisitionActivity')
        # After deletion + renumber, 2 activities remain
        self.assertEqual(len(acts), 2)
        # The last activity should now have 'only.dm3'
        last_act = acts[-1]
        ds_names = [ds.find(f'{{{NS_STR}}}name').text for ds in last_act.findall(f'{{{NS_STR}}}dataset')]
        self.assertIn('only.dm3', ds_names)


class AnnotateSaveOneDoesNotExistTest(TestCase):
    """DoesNotExist handling in annotate_save_one."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser5", password="pass")
        self.client.force_login(self.user)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    def test_missing_record_returns_404(self, mock_get):
        from core_main_app.commons.exceptions import DoesNotExist
        mock_get.side_effect = DoesNotExist("not found")
        response = self.client.post(
            "/annotate/bad-id/save-one/",
            {"dataset_index": "0", "description": "hello"},
        )
        self.assertEqual(response.status_code, 404)
        body = json.loads(response.content)
        self.assertIn("error", body)


class MalformedXmlViewTest(TestCase):
    """Malformed XML is handled cleanly in read-path views."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser6", password="pass")
        self.client.force_login(self.user)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.check_can_write")
    def test_descriptions_malformed_xml_returns_500(self, _mock_check, mock_get):
        mock_get.return_value = _make_mock_data(xml_content="<not valid xml <<")
        response = self.client.get("/annotate/test-id/descriptions/")
        self.assertEqual(response.status_code, 500)
        body = json.loads(response.content)
        self.assertIn("error", body)

    @patch("nexuslims_annotate.views.data_api.get_by_id")
    @patch("nexuslims_annotate.views.check_can_write")
    def test_save_one_malformed_xml_returns_500(self, _mock_check, mock_get):
        mock_get.return_value = _make_mock_data(xml_content="<not valid xml <<")
        response = self.client.post(
            "/annotate/test-id/save-one/",
            {"dataset_index": "0", "description": "hello"},
        )
        self.assertEqual(response.status_code, 500)
        body = json.loads(response.content)
        self.assertIn("error", body)
