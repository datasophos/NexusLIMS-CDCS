import os
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core_main_app.components.data import api as data_api
from core_main_app.components.workspace import api as workspace_api
from core_main_app.utils.rendering import admin_render

from .models import GallerySettings

NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
NS_MAP = {"nx": NS}


def normalize_experimenter(raw):
    """Convert 'Firstname Lastname (username)' to 'F. Lastname'. Returns raw on fallback."""
    if not raw:
        return raw
    s = re.sub(r"\s*\(.*?\)\s*$", "", raw).strip()
    parts = s.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return raw


def _get_preview_url(dataset_el, preview_base):
    """Return full preview URL for a dataset element, or None."""
    preview_el = dataset_el.find("nx:preview", NS_MAP)
    if preview_el is None or not preview_el.text or not preview_el.text.strip():
        return None
    return f"{preview_base.rstrip('/')}/{preview_el.text.strip().lstrip('/')}"


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


def _selectable_datasets(record_xml, preview_base, mode="all", minimum_rating=1):
    """Return all datasets that can win selection for this record and policy."""
    try:
        root = ET.fromstring(record_xml)
    except ET.ParseError:
        return []
    candidates = []
    for activity in root.findall("nx:acquisitionActivity", NS_MAP):
        for ds in activity.findall("nx:dataset", NS_MAP):
            url = _get_preview_url(ds, preview_base)
            if not url:
                continue
            rating, featured = _get_curation(ds)
            candidates.append(
                {
                    "preview_url": url,
                    "rating": rating,
                    "featured": featured,
                    "name": ds.findtext("nx:name", default="", namespaces=NS_MAP),
                    "description": ds.findtext(
                        "nx:description", default="", namespaces=NS_MAP
                    ).strip()
                    or None,
                }
            )
    featured = [candidate for candidate in candidates if candidate["featured"]]
    if featured:
        return featured
    if mode == "featured":
        return []
    rated = [
        candidate
        for candidate in candidates
        if candidate["rating"] is not None
        and (mode != "curated" or candidate["rating"] >= minimum_rating)
    ]
    if rated:
        highest = max(candidate["rating"] for candidate in rated)
        return [candidate for candidate in rated if candidate["rating"] == highest]
    return candidates[:1] if mode == "all" else []


def _select_best_dataset(record_xml, preview_base, mode="all"):
    candidates = _selectable_datasets(record_xml, preview_base, mode)
    return random.choice(candidates) if candidates else None


def _gallery_settings():
    return GallerySettings.objects.filter(pk=1).first() or GallerySettings()


def _gallery_records(mode, preview_base, minimum_rating=1):
    workspace = workspace_api.get_global_workspace()
    records = data_api.get_all_by_workspace(workspace, AnonymousUser())
    return [
        (record, candidates)
        for record in records
        if (
            candidates := _selectable_datasets(
                record.content, preview_base, mode, minimum_rating
            )
        )
    ]


class GallerySettingsForm(forms.Form):
    selection_mode = forms.ChoiceField(
        choices=GallerySettings.MODES, label="Gallery selection"
    )
    minimum_rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        label="Minimum rating",
        help_text="In featured or rated mode, rated datasets must meet this threshold. Featured datasets always qualify. Other modes are unchanged.",
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def gallery_admin(request):
    gallery_settings = _gallery_settings()
    mode = gallery_settings.selection_mode
    form = GallerySettingsForm(
        request.POST if request.method == "POST" else None,
        initial={
            "selection_mode": mode,
            "minimum_rating": gallery_settings.minimum_rating,
        },
    )
    if request.method == "POST" and form.is_valid():
        GallerySettings.objects.update_or_create(pk=1, defaults=form.cleaned_data)
        return redirect("nexuslims_gallery_admin")
    rows = []
    error = None
    try:
        for record, candidates in _gallery_records(
            mode,
            os.getenv("XSLT_PREVIEW_BASE_URL", ""),
            gallery_settings.minimum_rating,
        ):
            root = ET.fromstring(record.content)
            experimenter = root.findtext(
                "nx:summary/nx:experimenter", default="", namespaces=NS_MAP
            )
            title = root.findtext("nx:title", default="", namespaces=NS_MAP)
            for candidate in candidates:
                rows.append(
                    {
                        **candidate,
                        "experimenter": experimenter,
                        "title": title,
                        "record_id": record.id,
                    }
                )
    except Exception:
        error = "Could not fetch gallery records. Please try again."
    return admin_render(
        request,
        "nexuslims_gallery/admin.html",
        context={"form": form, "rows": rows, "error": error},
    )


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
        gallery_settings = _gallery_settings()
        eligible = _gallery_records(
            gallery_settings.selection_mode,
            preview_base,
            gallery_settings.minimum_rating,
        )
    except Exception:
        return JsonResponse({"error": "Could not fetch records"}, status=500)
    if not eligible:
        return JsonResponse({"error": "No previewable records found"}, status=404)
    record, candidates = random.choice(eligible)
    dataset = random.choice(candidates)
    root = ET.fromstring(record.content)

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
