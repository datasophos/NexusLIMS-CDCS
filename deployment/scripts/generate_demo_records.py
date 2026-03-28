"""
generate_demo_records.py - Generate NexusLIMS XML records from public datasets.

Each folder in --input is treated as one experiment record. Sub-directories
within a folder become separate acquisitionActivity elements.

Usage:
    uv run python deployment/scripts/generate_demo_records.py \\
        --input /Users/josh/Downloads/example_datasets \\
        --output-records deployment/fixtures/demo_records \\
        --output-demo-data deployment/fixtures/demo_data \\
        [--no-fetch]
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from lxml import etree
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: uv run python deployment/scripts/generate_demo_records.py ...")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NS = "https://data.nist.gov/od/dm/nexus/experiment/v1.0"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

FAKE_NAMES = [
    "Sarah Chen",
    "Marcus Webb",
    "Priya Nair",
    "James Okafor",
    "Elena Vasquez",
    "Thomas Kirchner",
    "Amara Diallo",
    "Luca Ferretti",
    "Yuki Tanaka",
    "David Osei",
    "Claire Moreau",
    "Ravi Subramanian",
]

# Extractor module -> (instrument PID, display name)
INSTRUMENT_MAP = {
    "quanta_tif_extractor": ("FEI-Quanta-SEM", "FEI Quanta/Apreo SEM"),
    "tescan_tif_extractor": ("TESCAN-FERA-FIB-SEM", "TESCAN FERA FIB-SEM"),
    "ser_emi_extractor": ("FEI-Tecnai-TEM", "FEI Tecnai TEM"),
    "dm5_extractor": ("FEI-Titan-TEM", "FEI Titan TEM"),
    "fei_tif_extractor": ("FEI-Titan-TEM", "FEI Titan TEM"),
}

# Fields excluded from setup params (and per-dataset meta where noted).
# Creation Time is the only field excluded from setup params — it's added
# explicitly as per-dataset meta to avoid duplication.
NEVER_SETUP_FIELDS = {
    "Creation Time",
}

# ---------------------------------------------------------------------------
# JSON parsing (handles ANSI escape codes and non-array formats)
# ---------------------------------------------------------------------------


def _load_json_file(path: Path) -> dict | None:
    """Load a NexusLIMS extractor JSON sidecar, returning the nx_meta dict."""
    try:
        raw = path.read_bytes()
    except OSError:
        return None

    # Strip ANSI escape sequences
    clean = re.sub(rb"\x1b\[[^m]*m", b"", raw)
    text = clean.decode("utf-8", errors="replace")

    # Try standard JSON parse (list of objects)
    try:
        data = json.loads(text)
        if isinstance(data, list) and data:
            return data[0].get("nx_meta") or {}
        if isinstance(data, dict):
            return data.get("nx_meta") or {}
    except json.JSONDecodeError:
        pass

    # Fall back: extract first JSON value (object or array)
    decoder = json.JSONDecoder()
    idx = next((i for i, ch in enumerate(text) if ch in ("{", "[")), -1)
    while 0 <= idx < len(text):
        try:
            obj, end = decoder.raw_decode(text, idx)
            if isinstance(obj, list) and obj:
                return obj[0].get("nx_meta") or {}
            if isinstance(obj, dict) and "nx_meta" in obj:
                return obj["nx_meta"]
            idx = end
        except json.JSONDecodeError:
            idx += 1

    return {}


# ---------------------------------------------------------------------------
# Webloc parsing
# ---------------------------------------------------------------------------


def parse_webloc(path: Path) -> str:
    """Extract URL from a macOS .webloc plist file."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # <dict><key>URL</key><string>...</string></dict>
        keys = root.iter("key")
        for key in keys:
            if key.text == "URL":
                sibling = key.getnext() if hasattr(key, "getnext") else None
                break
        # Use ElementTree iteration instead
        d = root.find("dict")
        if d is not None:
            items = list(d)
            for i, el in enumerate(items):
                if el.tag == "key" and el.text == "URL" and i + 1 < len(items):
                    return items[i + 1].text or ""
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Metadata fetching
# ---------------------------------------------------------------------------


def _strip_html(html: str) -> str:
    """Strip HTML tags and decode basic entities."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_metadata(url: str, cache_path: Path, no_fetch: bool) -> dict:
    """Fetch title, description, doi, license from Zenodo or NIST."""
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except Exception:
            pass

    if no_fetch:
        return {}

    result = {}
    try:
        if "zenodo.org" in url:
            record_id = url.rstrip("/").split("/")[-1]
            api_url = f"https://zenodo.org/api/records/{record_id}"
            resp = requests.get(api_url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            meta = data.get("metadata", {})
            result["title"] = meta.get("title", "")
            desc_html = meta.get("description", "")
            result["description"] = _strip_html(desc_html)
            result["doi"] = data.get("doi") or data.get("conceptdoi") or ""
            result["license"] = "CC BY 4.0"
            result["source"] = "zenodo"

        elif "data.nist.gov" in url:
            record_id = url.rstrip("/").split("/")[-1]
            api_url = f"https://data.nist.gov/od/id/{record_id}"
            resp = requests.get(
                api_url,
                timeout=30,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            result["title"] = data.get("title", "")
            desc = data.get("description", "")
            if isinstance(desc, list):
                desc = " ".join(desc)
            result["description"] = _strip_html(str(desc))
            result["doi"] = data.get("doi", "")
            result["license"] = "U.S. Government work (public domain)"
            result["source"] = "nist"
    except Exception as e:
        print(f"  Warning: metadata fetch failed for {url}: {e}")

    if result:
        cache_path.write_text(json.dumps(result, indent=2))
    return result


# ---------------------------------------------------------------------------
# Instrument detection
# ---------------------------------------------------------------------------


def detect_instrument(
    all_nx_meta: list[dict],
) -> tuple[str, str]:
    """Return (pid, display_name) for the dominant instrument in a folder."""
    module_counts: Counter = Counter()
    data_types: Counter = Counter()

    for nx in all_nx_meta:
        if not nx:
            continue
        mod = nx.get("NexusLIMS Extraction", {}).get("Module", "")
        short = mod.split(".")[-1] if mod else ""
        if short:
            module_counts[short] += 1
        dt = nx.get("Data Type", "")
        if dt:
            data_types[dt] += 1

    if not module_counts:
        return ("FEI-Titan-TEM", "FEI Titan TEM")

    dominant = module_counts.most_common(1)[0][0]

    # Direct lookup first
    if dominant in INSTRUMENT_MAP:
        return INSTRUMENT_MAP[dominant]

    # DM3/DM4 - distinguish TEM vs STEM by Data Type
    if dominant in ("dm3_extractor", "dm4_extractor"):
        stem_count = sum(
            c
            for dt, c in data_types.items()
            if "STEM" in dt.upper() or "HAADF" in dt.upper()
        )
        tem_count = sum(
            c
            for dt, c in data_types.items()
            if "TEM" in dt.upper() and "STEM" not in dt.upper()
        )
        if stem_count > tem_count:
            return ("FEI-Titan-STEM", "FEI Titan STEM")
        return ("FEI-Titan-TEM", "FEI Titan TEM")

    # MSA only - inherit from any other extractor present
    if dominant == "msa_extractor":
        others = [m for m in module_counts if m != "msa_extractor"]
        if others:
            secondary = max(others, key=lambda m: module_counts[m])
            if secondary in INSTRUMENT_MAP:
                return INSTRUMENT_MAP[secondary]
            if secondary in ("dm3_extractor", "dm4_extractor"):
                return ("FEI-Titan-TEM", "FEI Titan TEM")

    return ("FEI-Titan-TEM", "FEI Titan TEM")


# ---------------------------------------------------------------------------
# File collection
# ---------------------------------------------------------------------------

SKIP_SUFFIXES = {".json", ".thumb.png", ".DS_Store"}
SKIP_NAMES = {"README.md", "README.txt", "README", "metadata.md"}
SKIP_PREFIXES = ("README",)


def is_data_file(path: Path) -> bool:
    name = path.name
    if name.startswith("."):
        return False
    if name in SKIP_NAMES or any(name.startswith(p) for p in SKIP_PREFIXES):
        return False
    if name.endswith(".webloc") or ".webloc." in name:
        return False
    for suf in SKIP_SUFFIXES:
        if name.endswith(suf):
            return False
    return True


def collect_activities(folder: Path) -> dict[str, list[Path]]:
    """
    Return ordered dict: activity_name -> [data_file_paths]

    Root-level files -> activity "root"
    Each subdirectory -> activity named after that subdir
    """
    activities: dict[str, list[Path]] = {}

    root_files = sorted(
        [f for f in folder.iterdir() if f.is_file() and is_data_file(f)],
        key=lambda p: p.name,
    )
    if root_files:
        activities["root"] = root_files

    for subdir in sorted(folder.iterdir()):
        if not subdir.is_dir():
            continue
        files = sorted(
            [f for f in subdir.rglob("*") if f.is_file() and is_data_file(f)],
            key=lambda p: str(p),
        )
        if files:
            activities[subdir.name] = files

    return activities


# ---------------------------------------------------------------------------
# Setup parameter extraction
# ---------------------------------------------------------------------------

UNIT_RE = re.compile(r"^([-+]?[\d.eE+\-]+)\s+(\S+)$")


def _parse_value_unit(val) -> tuple[str, str]:
    """Split '1000.0 volt' into ('1000.0', 'volt'). Returns (str(val), '')."""
    if not isinstance(val, str):
        return str(val), ""
    m = UNIT_RE.match(val.strip())
    if m:
        return m.group(1), m.group(2)
    return val, ""


def _get_display_name(field_name: str) -> str:
    """Convert snake_case lowercase field names to Title Case, matching NexusLIMS em_glossary fallback."""
    if "_" in field_name and field_name.islower():
        return field_name.replace("_", " ").title()
    return field_name


def _flatten_nx_meta(nx: dict, prefix: str = "") -> dict:
    """
    Flatten nx_meta following NexusLIMS activity.py conventions:
    - extensions keys are merged into root level (no prefix)
    - Other nested dicts are flattened with ' \u2013 ' (en-dash) separator
    - snake_case all-lowercase field names are converted to Title Case display names
    """
    out = {}

    # At root level, merge extensions directly in (NexusLIMS activity.py lines 370-372)
    nx = nx.copy()
    if not prefix and "extensions" in nx and isinstance(nx["extensions"], dict):
        nx.update(nx.pop("extensions"))

    for k, v in nx.items():
        if k in NEVER_SETUP_FIELDS:
            continue
        display_k = _get_display_name(k)
        full_key = display_k if not prefix else f"{prefix} \u2013 {display_k}"
        if isinstance(v, dict):
            out.update(_flatten_nx_meta(v, full_key))
        elif v is None:
            continue
        elif isinstance(v, list):
            if v:  # skip empty lists
                out[full_key] = "; ".join(str(i) for i in v)
        else:
            out[full_key] = v
    return out


def extract_setup_params(
    nx_metas: list[dict],
) -> tuple[dict[str, tuple], dict[str, list]]:
    """
    Returns:
        setup_params: {name: (value_str, unit_str)} - consistent across >=50% files
        per_file_params: {name: [values...]} - varies per file
    """
    if not nx_metas:
        return {}, {}

    all_flat = [_flatten_nx_meta(nx) for nx in nx_metas if nx]
    if not all_flat:
        return {}, {}

    # Count field occurrences and value consistency
    field_values: dict[str, list] = {}
    for flat in all_flat:
        for k, v in flat.items():
            if k not in field_values:
                field_values[k] = []
            field_values[k].append(v)

    threshold = max(1, len(all_flat) * 0.5)
    setup: dict[str, tuple] = {}
    per_file: dict[str, list] = {}

    for field, values in field_values.items():
        if len(values) < threshold:
            per_file[field] = values
            continue
        # Check if all values are identical
        str_vals = [str(v) for v in values]
        if len(set(str_vals)) == 1:
            val, unit = _parse_value_unit(values[0])
            setup[field] = (val, unit)
        else:
            per_file[field] = values

    return setup, per_file


# ---------------------------------------------------------------------------
# Time utilities
# ---------------------------------------------------------------------------


def _parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    # Normalize Z suffix
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _format_dt(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def get_time_range(nx_metas: list[dict]) -> tuple[str, str]:
    times = []
    for nx in nx_metas:
        if not nx:
            continue
        t = _parse_dt(nx.get("Creation Time", ""))
        if t:
            times.append(t)
    if not times:
        return ("", "")
    return (_format_dt(min(times)), _format_dt(max(times)))


# ---------------------------------------------------------------------------
# Sample name derivation
# ---------------------------------------------------------------------------


def derive_sample_name(folder_name: str, webloc_title: str) -> tuple[str, str]:
    """Return (sample_name, sample_description)."""
    # Use folder name to derive sample, webloc title for description
    name = folder_name.replace("_", " ").strip()
    desc = ""
    if webloc_title:
        # Truncate at first sentence boundary
        sentences = re.split(r"[.;]", webloc_title)
        desc = sentences[0].strip()
        if desc and not desc.endswith("."):
            desc += "."
    return name, desc


# ---------------------------------------------------------------------------
# Motivation field
# ---------------------------------------------------------------------------


def build_motivation(meta: dict, webloc_title: str) -> str:
    """Construct the motivation text (may contain HTML <a> tags)."""
    parts = []

    desc = meta.get("description", "")
    if not desc and webloc_title:
        desc = webloc_title
    if desc:
        # Take first 2 sentences
        sentences = re.split(r"(?<=[.!?])\s+", desc.strip())
        short = " ".join(sentences[:2])
        if len(short) > 500:
            short = short[:497] + "..."
        parts.append(short)

    doi = meta.get("doi", "")
    if doi:
        # Normalize "doi:10.xxx/..." or bare "10.xxx/..." to a full URL
        if doi.startswith("http"):
            doi_url = doi
        elif doi.startswith("doi:"):
            doi_url = f"https://doi.org/{doi[4:]}"
        else:
            doi_url = f"https://doi.org/{doi}"
        parts.append(f'Data source: <a href="{doi_url}">{doi_url}</a>')

    license_text = meta.get("license", "")
    if license_text:
        parts.append(license_text + ".")

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Experimenter assignment
# ---------------------------------------------------------------------------


def assign_experimenters(folder_name: str, total_files: int) -> list[str]:
    h = int(hashlib.sha256(folder_name.encode()).hexdigest(), 16)
    return [FAKE_NAMES[h % len(FAKE_NAMES)]]


# ---------------------------------------------------------------------------
# XML building
# ---------------------------------------------------------------------------


def _el(parent, tag, text=None, **attrs):
    el = etree.SubElement(parent, f"{{{NS}}}{tag}", **attrs)
    if text is not None:
        el.text = str(text)
    return el


def build_xml(
    folder_name: str,
    activities: dict[str, list[Path]],
    all_nx_metas: dict[str, dict],  # path -> nx_meta
    instrument: tuple[str, str],
    metadata: dict,
    webloc_title: str,
    webloc_url: str,
) -> etree._Element:
    pid, display_name = instrument

    all_metas = list(all_nx_metas.values())
    total_files = sum(len(v) for v in activities.values())
    experimenters = assign_experimenters(folder_name, total_files)

    res_start, res_end = get_time_range(all_metas)

    # Title
    title_text = metadata.get("title", webloc_title) or folder_name
    if len(title_text) > 120:
        title_text = title_text[:117] + "..."

    # Motivation
    motivation = build_motivation(metadata, webloc_title)

    # Sample
    sample_name, sample_desc = derive_sample_name(folder_name, webloc_title)

    root = etree.Element(
        f"{{{NS}}}Experiment",
        nsmap={
            None: NS,
            "xsi": NS_XSI,
        },
    )

    _el(root, "title", title_text)

    summary = _el(root, "summary")
    if webloc_url:
        summary.set("ref", webloc_url)

    for exp in experimenters:
        _el(summary, "experimenter", exp)

    inst_el = _el(summary, "instrument", display_name)
    inst_el.set("pid", pid)

    if res_start:
        _el(summary, "reservationStart", res_start)
    if res_end:
        _el(summary, "reservationEnd", res_end)

    if motivation:
        _el(summary, "motivation", motivation)

    sample = _el(root, "sample")
    sample.set("id", "sample-1")
    _el(sample, "name", sample_name)
    if sample_desc:
        _el(sample, "description", sample_desc)

    for seqno, (activity_name, files) in enumerate(activities.items()):
        act_metas = [all_nx_metas.get(str(f), {}) for f in files]
        act_start, _ = get_time_range(act_metas)
        setup_params, _per_file = extract_setup_params(act_metas)

        act = _el(root, "acquisitionActivity")
        act.set("seqno", str(seqno))

        if act_start:
            _el(act, "startTime", act_start)
        _el(act, "sampleID", "sample-1")

        setup = _el(act, "setup")
        for pname, (pval, punit) in sorted(setup_params.items()):
            p = _el(setup, "param", pval)
            p.set("name", pname)
            if punit:
                p.set("unit", punit)

        for f in files:
            nx = all_nx_metas.get(str(f), {})
            dataset_type = nx.get("DatasetType", "")
            if not dataset_type:
                # Guess from extension
                ext = f.suffix.lower()
                dataset_type = {
                    ".tif": "Image",
                    ".tiff": "Image",
                    ".dm3": "Image",
                    ".dm4": "Image",
                    ".dm5": "Image",
                    ".ser": "Image",
                    ".msa": "Spectrum",
                    ".emi": "Unknown",
                }.get(ext, "Unknown")

            # Build relative path for location
            rel = f.relative_to(f.parents[len(f.parts) - f.parts.index(folder_name) - 1])
            location = "/" + str(rel).replace(os.sep, "/")

            ds = _el(act, "dataset")
            ds.set("type", dataset_type)
            ds.set("role", "Experimental")

            _el(ds, "name", f.name)
            _el(ds, "location", location)
            _el(ds, "format", f.suffix.lstrip(".").upper() if f.suffix else "Unknown")
            _el(ds, "description")  # empty, for annotator

            # Thumbnail (must come after description per XSD)
            # Try both naming conventions: stem.thumb.png and full-name.thumb.png
            thumb = next(
                (p for p in [
                    f.parent / (f.stem + ".thumb.png"),
                    f.parent / (f.name + ".thumb.png"),
                ] if p.exists()),
                None,
            )
            if thumb is not None:
                thumb_rel = "/" + str(
                    thumb.relative_to(
                        thumb.parents[len(thumb.parts) - thumb.parts.index(folder_name) - 1]
                    )
                ).replace(os.sep, "/")
                _el(ds, "preview", thumb_rel)

            # Per-dataset meta from nx_meta — use full flattened view so nested
            # dicts (e.g. extensions) are included.  Skip fields already emitted
            # as setup params and DatasetType (used for the type attribute).
            per_ds_skip = set(setup_params.keys()) | {"DatasetType"}
            if nx:
                flat_nx = _flatten_nx_meta(nx)
                for mkey in sorted(flat_nx.keys()):
                    if mkey in per_ds_skip:
                        continue
                    mval, munit = _parse_value_unit(flat_nx[mkey])
                    m = _el(ds, "meta", mval)
                    m.set("name", mkey)
                    if munit:
                        m.set("unit", munit)
                # Always include Creation Time
                ct = nx.get("Creation Time", "")
                if ct:
                    m = _el(ds, "meta", ct)
                    m.set("name", "Creation Time")

    return root


# ---------------------------------------------------------------------------
# Demo data population
# ---------------------------------------------------------------------------


def populate_demo_data(
    folder: Path,
    folder_name: str,
    activities: dict[str, list[Path]],
    nx_data_root: Path,
    nx_instrument_data_root: Path,
) -> None:
    all_files = [f for files in activities.values() for f in files]

    for data_file in all_files:
        # Relative to folder root
        try:
            rel = data_file.relative_to(folder)
        except ValueError:
            rel = Path(data_file.name)

        # nx-data: JSON + thumbnail
        json_src = data_file.parent / (data_file.name + ".json")
        thumb_src = next(
            (p for p in [
                data_file.parent / (data_file.stem + ".thumb.png"),
                data_file.parent / (data_file.name + ".thumb.png"),
            ] if p.exists()),
            None,
        )

        nx_dest = nx_data_root / folder_name / rel.parent
        nx_dest.mkdir(parents=True, exist_ok=True)

        if json_src.exists():
            shutil.copy2(json_src, nx_dest / json_src.name)
        if thumb_src is not None:
            shutil.copy2(thumb_src, nx_dest / thumb_src.name)

        # nx-instrument-data: 1-byte stub
        inst_dest = nx_instrument_data_root / folder_name / rel.parent
        inst_dest.mkdir(parents=True, exist_ok=True)
        stub = inst_dest / data_file.name
        if not stub.exists():
            stub.write_bytes(b"\x00")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def process_folder(
    folder: Path,
    output_records: Path,
    output_demo_data: Path,
    no_fetch: bool,
    schema: etree.XMLSchema | None,
) -> bool:
    folder_name = folder.name
    print(f"\n{'='*60}")
    print(f"Processing: {folder_name}")

    # Find .webloc file
    webloc_files = list(folder.glob("*.webloc"))
    # Exclude .webloc.cache.json and .webloc.json files
    webloc_files = [
        w for w in webloc_files if not any(w.name.endswith(s) for s in [".cache.json"])
    ]
    # Also exclude webloc.json etc (not real webloc)
    webloc_files = [w for w in webloc_files if w.suffix == ".webloc"]

    webloc_url = ""
    webloc_title = ""
    metadata = {}

    if webloc_files:
        wf = webloc_files[0]
        webloc_url = parse_webloc(wf)
        webloc_title = wf.stem  # filename without .webloc
        # Strip leading "DATASET " prefix sometimes present
        webloc_title = re.sub(r"^DATASET\s+", "", webloc_title).strip()
        print(f"  Source URL: {webloc_url}")

        cache_path = wf.parent / (wf.name + ".cache.json")
        metadata = fetch_metadata(webloc_url, cache_path, no_fetch)
    else:
        print("  No .webloc file found")

    # Collect activities and files
    activities = collect_activities(folder)
    if not activities:
        print("  No data files found, skipping.")
        return False

    total = sum(len(v) for v in activities.values())
    print(f"  Activities: {list(activities.keys())}")
    print(f"  Total data files: {total}")

    # Load all nx_meta
    all_nx_metas: dict[str, dict] = {}
    for files in activities.values():
        for f in files:
            json_path = f.parent / (f.name + ".json")
            if json_path.exists():
                all_nx_metas[str(f)] = _load_json_file(json_path) or {}
            else:
                all_nx_metas[str(f)] = {}

    # Detect instrument
    instrument = detect_instrument(list(all_nx_metas.values()))
    print(f"  Instrument: {instrument[0]} ({instrument[1]})")

    # Build XML
    xml_root = build_xml(
        folder_name=folder_name,
        activities=activities,
        all_nx_metas=all_nx_metas,
        instrument=instrument,
        metadata=metadata,
        webloc_title=webloc_title,
        webloc_url=webloc_url,
    )

    # Serialize
    xml_bytes = etree.tostring(
        xml_root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )

    # Validate if schema provided
    if schema is not None:
        try:
            doc = etree.fromstring(xml_bytes)
            schema.assertValid(doc)
            print("  XML validation: PASSED")
        except etree.DocumentInvalid as e:
            print(f"  XML validation: FAILED - {e}")
            # Continue anyway - write invalid file for inspection

    # Write XML record
    output_records.mkdir(parents=True, exist_ok=True)
    out_path = output_records / f"{folder_name}.xml"
    out_path.write_bytes(xml_bytes)
    print(f"  Written: {out_path}")

    # Populate demo data directories
    nx_data_root = output_demo_data / "nx-data"
    nx_instrument_data_root = output_demo_data / "nx-instrument-data"
    populate_demo_data(
        folder=folder,
        folder_name=folder_name,
        activities=activities,
        nx_data_root=nx_data_root,
        nx_instrument_data_root=nx_instrument_data_root,
    )
    print(f"  Demo data populated: {nx_data_root / folder_name}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate NexusLIMS XML demo records from public datasets"
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Directory containing dataset folders",
    )
    parser.add_argument(
        "--output-records",
        required=True,
        type=Path,
        help="Output directory for XML records",
    )
    parser.add_argument(
        "--output-demo-data",
        required=True,
        type=Path,
        help="Output directory for demo fixture data (nx-data/, nx-instrument-data/)",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Skip web fetches; use webloc filename as title",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output XML against nexus-experiment.xsd",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).parent.parent / "schemas" / "nexus-experiment.xsd",
        help="Path to nexus-experiment.xsd for validation",
    )
    parser.add_argument(
        "--folder",
        type=str,
        help="Process only a specific folder name (for testing)",
    )
    args = parser.parse_args()

    if not args.input.is_dir():
        print(f"Error: --input {args.input} is not a directory")
        sys.exit(1)

    # Load schema if requested
    schema = None
    if args.validate:
        if args.schema.exists():
            schema_doc = etree.parse(str(args.schema))
            schema = etree.XMLSchema(schema_doc)
            print(f"Loaded schema: {args.schema}")
        else:
            print(f"Warning: schema not found at {args.schema}, skipping validation")

    # Find dataset folders
    folders = sorted(
        [f for f in args.input.iterdir() if f.is_dir()],
        key=lambda p: p.name,
    )

    if args.folder:
        folders = [f for f in folders if f.name == args.folder]
        if not folders:
            print(f"Error: folder '{args.folder}' not found in {args.input}")
            sys.exit(1)

    print(f"Found {len(folders)} dataset folders")

    success = 0
    failed = 0
    for folder in folders:
        try:
            ok = process_folder(
                folder=folder,
                output_records=args.output_records,
                output_demo_data=args.output_demo_data,
                no_fetch=args.no_fetch,
                schema=schema,
            )
            if ok:
                success += 1
            else:
                failed += 1
        except Exception as e:
            import traceback

            print(f"  ERROR processing {folder.name}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print(f"Done: {success} succeeded, {failed} failed/skipped")
    print(f"XML records: {args.output_records}")
    print(f"Demo data:   {args.output_demo_data}")


if __name__ == "__main__":
    main()
