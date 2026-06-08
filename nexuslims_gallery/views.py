import os
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.shortcuts import render

from core_main_app.components.data import api as data_api
from core_main_app.components.workspace import api as workspace_api

NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
NS_MAP = {"nx": NS}


def normalize_experimenter(raw):
    """Convert 'Firstname Lastname (username)' to 'F. Lastname'. Returns raw on fallback."""
    if not raw:
        return raw
    s = re.sub(r'\s*\(.*?\)\s*$', '', raw).strip()
    parts = s.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return raw


def _get_preview_url(dataset_el, preview_base):
    """Return full preview URL for a dataset element, or None."""
    preview_el = dataset_el.find("nx:preview", NS_MAP)
    if preview_el is None or not preview_el.text:
        return None
    return f"{preview_base.rstrip('/')}/{preview_el.text.lstrip('/')}"


def _get_curation(dataset_el):
    """Return (rating, featured) from a dataset element."""
    curation_el = dataset_el.find("nx:curation", NS_MAP)
    if curation_el is None:
        return None, False
    rating_el = curation_el.find("nx:rating", NS_MAP)
    featured_el = curation_el.find("nx:featured", NS_MAP)
    rating = None
    if rating_el is not None and rating_el.text:
        try:
            rating = int(rating_el.text)
        except ValueError:
            pass
    featured = featured_el is not None and featured_el.text == "true"
    return rating, featured


def _select_best_dataset(record_xml, preview_base):
    """Return a dict with preview_url (and curation info) for the best dataset.

    Priority: featured first, then highest rating, then first with a preview URL.
    Returns None if the record has no previewable datasets or XML is malformed.
    """
    try:
        root = ET.fromstring(record_xml)
    except ET.ParseError:
        return None

    candidates = []
    for activity in root.findall("nx:acquisitionActivity", NS_MAP):
        for ds in activity.findall("nx:dataset", NS_MAP):
            url = _get_preview_url(ds, preview_base)
            if url is None:
                continue
            rating, featured = _get_curation(ds)
            desc_el = ds.find("nx:description", NS_MAP)
            description = desc_el.text.strip() if desc_el is not None and desc_el.text else None
            candidates.append({
                "preview_url": url,
                "rating": rating,
                "featured": featured,
                "description": description,
            })

    if not candidates:
        return None

    featured_list = [c for c in candidates if c["featured"]]
    if featured_list:
        return random.choice(featured_list)

    rated_list = [c for c in candidates if c["rating"] is not None]
    if rated_list:
        max_rating = max(c["rating"] for c in rated_list)
        return random.choice([c for c in rated_list if c["rating"] == max_rating])

    return candidates[0]


def gallery_page(request):
    """Serve the jumbotron gallery page (no auth required)."""
    logo = getattr(settings, "NX_GALLERY_LOGO", None) or getattr(
        settings, "NX_NAV_LOGO", ""
    )
    return render(
        request,
        "nexuslims_gallery/gallery.html",
        {
            "NX_GALLERY_ROTATION_INTERVAL": getattr(
                settings, "NX_GALLERY_ROTATION_INTERVAL", 30
            ),
            "NX_GALLERY_LOGO": logo,
            "NX_GALLERY_FACILITY_NAME": getattr(
                settings, "NX_GALLERY_FACILITY_NAME", "NexusLIMS"
            ),
        },
    )


def api_next(request):
    """Return JSON for the next gallery slide (no auth required)."""
    preview_base = os.getenv("XSLT_PREVIEW_BASE_URL", "").rstrip("/")

    try:
        workspace = workspace_api.get_global_workspace()
        all_records = list(data_api.get_all_by_workspace(workspace, AnonymousUser()))
    except Exception:
        return JsonResponse({"error": "Could not fetch records"}, status=500)

    eligible = []
    for record in all_records:
        try:
            root = ET.fromstring(record.content)
        except ET.ParseError:
            continue
        has_preview = any(
            ds.find("nx:preview", NS_MAP) is not None
            for activity in root.findall("nx:acquisitionActivity", NS_MAP)
            for ds in activity.findall("nx:dataset", NS_MAP)
        )
        if has_preview:
            eligible.append(record)

    if not eligible:
        return JsonResponse({"error": "No previewable records found"}, status=404)

    record = random.choice(eligible)

    try:
        root = ET.fromstring(record.content)
    except ET.ParseError:
        return JsonResponse({"error": "Record XML is malformed"}, status=500)

    dataset = _select_best_dataset(record.content, preview_base)
    if dataset is None:
        return JsonResponse({"error": "No previewable dataset"}, status=500)

    title_el = root.find("nx:title", NS_MAP)
    title = title_el.text if title_el is not None else ""

    summary_el = root.find("nx:summary", NS_MAP)
    response_data = {
        "title": title,
        "preview_url": dataset["preview_url"],
        "record_url": f"/data?id={record.id}",
        "featured": dataset["featured"],
    }

    if dataset.get("description"):
        response_data["description"] = dataset["description"]

    if summary_el is not None:
        exp_el = summary_el.find("nx:experimenter", NS_MAP)
        if exp_el is not None and exp_el.text:
            normed = normalize_experimenter(exp_el.text)
            if normed:
                response_data["experimenter"] = normed

        inst_el = summary_el.find("nx:instrument", NS_MAP)
        if inst_el is not None and inst_el.text:
            response_data["instrument"] = inst_el.text.strip()

        start_el = summary_el.find("nx:reservationStart", NS_MAP)
        if start_el is not None and start_el.text:
            try:
                dt = datetime.fromisoformat(start_el.text[:10])
                response_data["month_year"] = dt.strftime("%B %Y")
            except ValueError:
                pass

    return JsonResponse(response_data)
