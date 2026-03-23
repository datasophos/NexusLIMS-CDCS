import os
import logging
import xml.etree.ElementTree as ET

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

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
    data = data_api.get_by_id(record_id, request.user)
    datasets = _parse_datasets(data.content)
    return render(request, 'nexuslims_annotate/annotate.html', {
        'data': data,
        'record_title': _get_title(data.content),
        'datasets': datasets,
        'record_id': record_id,
    })


@login_required
def annotate_panel(request, record_id):
    """AJAX: return HTML fragment for offcanvas body."""
    data = data_api.get_by_id(record_id, request.user)
    datasets = _parse_datasets(data.content)
    return render(request, 'nexuslims_annotate/_panel.html', {
        'data': data,
        'datasets': datasets,
        'record_id': record_id,
    })


@login_required
def annotate_save(request, record_id):
    """AJAX POST: update <description> elements and save the record."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        data = data_api.get_by_id(record_id, request.user)
        updated_xml = _apply_descriptions(data.content, request.POST)
        data.content = updated_xml
        data_api.upsert(data, request)
        if is_ajax:
            return JsonResponse({'success': True})
        return redirect(f'/data?id={record_id}')
    except Exception as e:
        logger.exception('Error saving annotations for record %s', record_id)
        if is_ajax:
            return JsonResponse({'error': str(e)}, status=500)
        return redirect(f'/annotate/{record_id}/?error=1')
