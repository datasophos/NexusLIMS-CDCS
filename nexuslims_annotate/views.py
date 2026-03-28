import json
import os
import re
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from core_main_app.access_control.api import check_can_write
from core_main_app.access_control.exceptions import AccessControlError
from core_main_app.commons.exceptions import DoesNotExist, ModelError
from core_main_app.components.data import api as data_api

logger = logging.getLogger(__name__)

NS = 'https://data.nist.gov/od/dm/nexus/experiment/v1.0'
NS_MAP = {'nx': NS}


def _get_title(xml_content):
    """Extract the experiment title from XML content."""
    root = ET.fromstring(xml_content)
    title_el = root.find('nx:title', NS_MAP)
    return title_el.text if title_el is not None else ''


def _parse_datasets(xml_content):
    """Parse XML content and return a list of dataset dicts."""
    ET.register_namespace('', NS)
    root = ET.fromstring(xml_content)

    preview_base = os.getenv('XSLT_PREVIEW_BASE_URL', '').rstrip('/')
    datasets = []
    index = 0

    for activity in root.findall(f'nx:acquisitionActivity', NS_MAP):
        seqno = activity.get('seqno', '')
        for dataset_el in activity.findall(f'nx:dataset', NS_MAP):
            name_el = dataset_el.find('nx:name', NS_MAP)
            desc_el = dataset_el.find('nx:description', NS_MAP)
            preview_el = dataset_el.find('nx:preview', NS_MAP)

            name = name_el.text if name_el is not None else ''
            description = desc_el.text if desc_el is not None else ''
            preview_path = preview_el.text if preview_el is not None else None
            preview_url = f'{preview_base}/{preview_path.lstrip("/")}' if preview_path else None

            datasets.append({
                'index': index,
                'name': name,
                'description': description or '',
                'preview_url': preview_url,
                'activity_seqno': seqno,
            })
            index += 1

    return datasets


def _parse_activities(xml_content):
    """Return a list of activity dicts for the move UI."""
    root = ET.fromstring(xml_content)
    activities = []
    for activity in root.findall('nx:acquisitionActivity', NS_MAP):
        seqno = activity.get('seqno', '')
        start_el = activity.find('nx:startTime', NS_MAP)
        start_time = start_el.text if start_el is not None else ''
        dataset_count = len(activity.findall('nx:dataset', NS_MAP))
        activities.append({'seqno': seqno, 'start_time': start_time, 'dataset_count': dataset_count})
    return activities


def _inject_setup_into_dataset(dataset_el, activity_el):
    """Copy source activity setup params into a dataset's meta elements (non-destructively)."""
    setup_el = activity_el.find(f'{{{NS}}}setup')
    if setup_el is None:
        return
    existing_names = {m.get('name') for m in dataset_el.findall(f'{{{NS}}}meta')}
    for param in setup_el.findall(f'{{{NS}}}param'):
        name = param.get('name')
        if name and name not in existing_names:
            meta_el = ET.Element(f'{{{NS}}}meta')
            meta_el.set('name', name)
            unit = param.get('unit')
            if unit:
                meta_el.set('unit', unit)
            meta_el.text = param.text
            dataset_el.append(meta_el)


def _recompute_activity_setup(activity_el, skip_inject=None):
    """Recompute <setup> for an activity as the intersection of all datasets' meta values.

    skip_inject: optional set of dataset elements that should NOT receive the current
                 activity's setup params.  Pass the datasets that were moved *into* this
                 activity so they keep only their source-activity metadata and do not
                 pick up unrelated params from the receiving activity.
    """
    datasets = activity_el.findall(f'{{{NS}}}dataset')
    skip_inject = skip_inject or set()

    old_setup = activity_el.find(f'{{{NS}}}setup')
    if old_setup is not None:
        # Preserve current setup values in each dataset's meta before clearing the setup,
        # so that datasets which stay in this activity don't silently lose their metadata.
        # Datasets that were moved in already carry their source-activity params; skip them.
        for ds in datasets:
            if ds not in skip_inject:
                _inject_setup_into_dataset(ds, activity_el)
        activity_el.remove(old_setup)

    if not datasets:
        return

    # Collect {name: (value, unit)} per dataset
    dataset_metas = []
    for ds in datasets:
        metas = {}
        for meta in ds.findall(f'{{{NS}}}meta'):
            metas[meta.get('name')] = (meta.text, meta.get('unit'))
        dataset_metas.append(metas)

    # Intersection: params with identical name+value+unit across all datasets
    common = {}
    for name, val_unit in dataset_metas[0].items():
        if all(d.get(name) == val_unit for d in dataset_metas[1:]):
            common[name] = val_unit

    if not common:
        return

    setup_el = ET.Element(f'{{{NS}}}setup')
    for name, (value, unit) in common.items():
        param_el = ET.SubElement(setup_el, f'{{{NS}}}param')
        param_el.set('name', name)
        if unit:
            param_el.set('unit', unit)
        param_el.text = value

    # Insert before first dataset
    first_ds_idx = list(activity_el).index(datasets[0])
    activity_el.insert(first_ds_idx, setup_el)

    # Remove promoted params from individual dataset meta elements
    for ds in datasets:
        for meta in list(ds.findall(f'{{{NS}}}meta')):
            if meta.get('name') in common:
                ds.remove(meta)


def _dataset_creation_time(dataset_el):
    """Return a sortable datetime for a dataset, or None if no timestamp is found.

    Checks (in order):
    1. <meta name="Creation Time"> element
    2. Leading timestamp in the dataset <name> (e.g. "2024-01-15 10:05:00 file.dm3")
    """
    for meta in dataset_el.findall(f'{{{NS}}}meta'):
        if meta.get('name') == 'Creation Time' and meta.text:
            try:
                return datetime.fromisoformat(meta.text.strip())
            except ValueError:
                pass
    name_el = dataset_el.find(f'{{{NS}}}name')
    if name_el is not None and name_el.text:
        m = re.match(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', name_el.text)
        if m:
            try:
                return datetime.fromisoformat(m.group(1).replace(' ', 'T'))
            except ValueError:
                pass
    return None


def _sort_datasets_by_creation_time(activity_el):
    """Re-order datasets within an activity by ascending creation time.

    Datasets without a parseable timestamp keep their relative order and sort last.
    """
    datasets = list(activity_el.findall(f'{{{NS}}}dataset'))
    if len(datasets) <= 1:
        return
    _EPOCH = datetime.min

    def _sort_key(ds):
        t = _dataset_creation_time(ds)
        return (t is None, t if t is not None else _EPOCH)

    sorted_datasets = sorted(datasets, key=_sort_key)
    for ds in datasets:
        activity_el.remove(ds)
    for ds in sorted_datasets:
        activity_el.append(ds)


def _apply_moves(xml_content, moves):
    """Move dataset elements between activities and reconcile setup parameters.

    moves: list of {"datasetIndex": int, "targetActivitySeqno": str}
    """
    if not moves:
        return xml_content

    # Deduplicate: last move wins for each dataset index
    seen = {}
    for m in moves:
        seen[m['datasetIndex']] = m
    moves = list(seen.values())

    ET.register_namespace('', NS)
    root = ET.fromstring(xml_content)

    # Flat dataset list [(dataset_el, activity_el), ...]
    flat_datasets = []
    for activity in root.findall('nx:acquisitionActivity', NS_MAP):
        for ds in activity.findall('nx:dataset', NS_MAP):
            flat_datasets.append((ds, activity))

    activities_by_seqno = {
        a.get('seqno', ''): a
        for a in root.findall('nx:acquisitionActivity', NS_MAP)
    }

    affected = set()
    # Maps target_seqno -> set of dataset elements moved INTO that activity.
    # Used in Phase 3 so _recompute_activity_setup does not inject the receiving
    # activity's old setup into datasets that were moved in from elsewhere.
    moved_into: dict[str, set] = {}

    # Phase 1: inject setup params into each moving dataset before any moves happen
    for m in moves:
        idx = m['datasetIndex']
        target_seqno = str(m['targetActivitySeqno'])
        if idx >= len(flat_datasets):
            continue
        ds_el, src_activity = flat_datasets[idx]
        src_seqno = src_activity.get('seqno', '')
        if src_seqno == target_seqno:
            continue
        _inject_setup_into_dataset(ds_el, src_activity)
        affected.add(src_seqno)
        affected.add(target_seqno)
        moved_into.setdefault(target_seqno, set()).add(ds_el)

    # Phase 2: physically relocate dataset elements
    for m in moves:
        idx = m['datasetIndex']
        target_seqno = str(m['targetActivitySeqno'])
        if idx >= len(flat_datasets):
            continue
        ds_el, src_activity = flat_datasets[idx]
        if src_activity.get('seqno', '') == target_seqno:
            continue
        target_activity = activities_by_seqno.get(target_seqno)
        if target_activity is None:
            logger.warning('Target activity seqno %s not found', target_seqno)
            continue
        src_activity.remove(ds_el)
        target_activity.append(ds_el)

    # Phase 3: recompute setup for all affected activities.
    # Pass the moved-in dataset set for target activities so those datasets are not
    # contaminated with the receiving activity's pre-move setup parameters.
    for seqno in affected:
        activity = activities_by_seqno.get(seqno)
        if activity is not None:
            _recompute_activity_setup(activity, skip_inject=moved_into.get(seqno))

    # Phase 4: restore creation-time order within each affected activity
    for seqno in affected:
        activity = activities_by_seqno.get(seqno)
        if activity is not None:
            _sort_datasets_by_creation_time(activity)

    return ET.tostring(root, encoding='unicode', xml_declaration=False)


def _apply_descriptions(xml_content, post_data):
    """Update <description> elements in the XML with submitted values."""
    ET.register_namespace('', NS)
    root = ET.fromstring(xml_content)

    index = 0
    for activity in root.findall(f'nx:acquisitionActivity', NS_MAP):
        for dataset_el in activity.findall(f'nx:dataset', NS_MAP):
            # Remove existing description elements
            for desc_el in dataset_el.findall('nx:description', NS_MAP):
                dataset_el.remove(desc_el)

            new_text = post_data.get(f'dataset_{index}_description', '').strip()
            if new_text:
                desc_el = ET.Element(f'{{{NS}}}description')
                desc_el.text = new_text

                # Find insertion point: after <format> if present, else after <location>
                children = list(dataset_el)
                insert_after = None
                for child in children:
                    local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if local in ('format', 'location'):
                        insert_after = child

                if insert_after is not None:
                    pos = list(dataset_el).index(insert_after)
                    dataset_el.insert(pos + 1, desc_el)
                else:
                    dataset_el.insert(0, desc_el)

            index += 1

    return ET.tostring(root, encoding='unicode', xml_declaration=False)


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
    except ET.ParseError:
        return JsonResponse({'error': 'Record XML is malformed'}, status=500)
    return render(request, 'nexuslims_annotate/annotate.html', {
        'data': data,
        'record_title': _get_title(data.content),
        'datasets': datasets,
        'record_id': record_id,
        'activities': activities,
    })


@login_required
@require_GET
def annotate_panel(request, record_id):
    """AJAX: return HTML fragment for offcanvas body."""
    try:
        data = data_api.get_by_id(record_id, request.user)
    except (DoesNotExist, ModelError):
        return JsonResponse({'error': 'Record not found'}, status=404)
    try:
        check_can_write(data, request.user)
    except AccessControlError:
        return HttpResponseForbidden("You do not have permission to annotate this record.")
    try:
        datasets = _parse_datasets(data.content)
    except ET.ParseError:
        return JsonResponse({'error': 'Record XML is malformed'}, status=500)
    return render(request, 'nexuslims_annotate/_panel.html', {
        'data': data,
        'datasets': datasets,
        'record_id': record_id,
    })


@login_required
def annotate_descriptions(request, record_id):
    """Return current dataset names and descriptions as JSON."""
    try:
        data = data_api.get_by_id(record_id, request.user)
    except (DoesNotExist, ModelError):
        return JsonResponse({'error': 'Record not found'}, status=404)
    try:
        check_can_write(data, request.user)
    except AccessControlError:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    try:
        datasets = _parse_datasets(data.content)
    except ET.ParseError:
        return JsonResponse({'error': 'Record XML is malformed'}, status=500)
    return JsonResponse({
        'datasets': [{'index': d['index'], 'name': d['name'], 'description': d['description']} for d in datasets]
    })


@login_required
def annotate_save_one(request, record_id):
    """AJAX POST: update a single dataset's description by index."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    idx = None
    raw_idx = request.POST.get('dataset_index')
    if raw_idx is None:
        return JsonResponse({'error': 'dataset_index is required'}, status=400)
    try:
        idx = int(raw_idx)
        if idx < 0:
            return JsonResponse({'error': 'Invalid dataset_index'}, status=400)
        description = request.POST.get('description', '').strip()
        data = data_api.get_by_id(record_id, request.user)
        # Build full post_data from current state, replacing only the target index
        datasets = _parse_datasets(data.content)
        post_data = {f'dataset_{d["index"]}_description': d['description'] for d in datasets}
        post_data[f'dataset_{idx}_description'] = description
        data.content = _apply_descriptions(data.content, post_data)
        data_api.upsert(data, request)
        return JsonResponse({'success': True})
    except (DoesNotExist, ModelError):
        return JsonResponse({'error': 'Record not found'}, status=404)
    except AccessControlError as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        logger.exception('Error saving annotation for record %s dataset %s', record_id, idx)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def annotate_save(request, record_id):
    """AJAX POST: update <description> elements and save the record."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        data = data_api.get_by_id(record_id, request.user)
        # Apply descriptions first (uses pre-move indices)
        updated_xml = _apply_descriptions(data.content, request.POST)
        # Apply moves if present
        moves_json = request.POST.get('moves', '[]')
        try:
            moves = json.loads(moves_json)
        except (json.JSONDecodeError, ValueError):
            moves = []
        if moves:
            updated_xml = _apply_moves(updated_xml, moves)
        data.content = updated_xml
        data_api.upsert(data, request)
        if is_ajax:
            return JsonResponse({'success': True})
        return redirect(reverse('core_main_app_data_detail') + f'?id={record_id}')
    except (DoesNotExist, ModelError):
        if is_ajax:
            return JsonResponse({'error': 'Record not found'}, status=404)
        raise Http404(f"Record {record_id} not found.")
    except AccessControlError as e:
        if is_ajax:
            return JsonResponse({'error': str(e)}, status=403)
        return redirect(reverse('nexuslims_annotate_record', args=[record_id]) + '?error=1')
    except Exception as e:
        logger.exception('Error saving annotations for record %s', record_id)
        if is_ajax:
            return JsonResponse({'error': str(e)}, status=500)
        return redirect(reverse('nexuslims_annotate_record', args=[record_id]) + '?error=1')
