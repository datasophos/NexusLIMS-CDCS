#!/usr/bin/env python
"""
Upgrade NexusLIMS-CDCS schema, records, and XSLT in the database.

Compares the on-disk schema hash to the active template version. If different,
adds a new template version, migrates all records to it, then refreshes both
XSLT stylesheets. Safe to run on every deployment — idempotent.

Usage (production):
    docker exec nexuslims_prod_cdcs python /srv/scripts/upgrade_schema.py

Usage (development):
    docker exec nexuslims_dev_cdcs python /srv/scripts/upgrade_schema.py
"""

import hashlib
import logging
import os
import sys
from pathlib import Path

SCHEMA_PATH = Path("/srv/nexuslims/schemas/nexus-experiment.xsd")
XSLT_DIR = Path("/srv/nexuslims/xslt")
TEMPLATE_TITLE = "Nexus Experiment Schema"


def log_success(msg):
    print(f"  ✓ {msg}")


def log_info(msg):
    print(f"  → {msg}")


def log_warning(msg):
    print(f"  ⚠ {msg}", file=sys.stderr)


def log_error(msg):
    print(f"  ✗ {msg}", file=sys.stderr)


def detect_schema_change(schema_path=SCHEMA_PATH):
    """Compare on-disk schema hash to active DB template version.

    Returns (tvm, new_content) if upgrade is needed, None if already current.
    Raises FileNotFoundError if schema file is missing.
    Raises RuntimeError if template version manager is not in the DB.
    """
    from core_main_app.components.template_version_manager.models import (
        TemplateVersionManager,
    )
    from core_main_app.components.template.models import Template

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    new_content = schema_path.read_text(encoding="utf-8")
    # Use the same normalized XSD hash that CDCS computes on insert so that the
    # comparison is apples-to-apples (CDCS strips whitespace, comments, and
    # annotations before hashing — a raw SHA-1 of file bytes would never match).
    from xml_utils.xsd_hash import xsd_hash as _xsd_hash
    new_hash = _xsd_hash.get_hash(new_content)

    tvm = TemplateVersionManager.objects.filter(
        title=TEMPLATE_TITLE, is_disabled=False
    ).first()
    if tvm is None:
        raise RuntimeError(
            f"Template '{TEMPLATE_TITLE}' not found in DB. Run init_environment.py first."
        )

    current_template = Template.objects.get(id=tvm.current)
    if current_template.hash == new_hash:
        return None
    return (tvm, new_content)


def add_schema_version(tvm, new_content, request):
    """Add a new template version with new_content and set it as current.

    Returns the new Template object.
    """
    from core_main_app.components.template.models import Template
    from core_main_app.components.template_version_manager import api as tvm_api
    from core_main_app.components.version_manager import api as vm_api

    new_template = Template()
    new_template.filename = "nexus-experiment.xsd"
    new_template.content = new_content
    new_template.hash = hashlib.sha1(new_content.encode("utf-8")).hexdigest()

    tvm_api.insert(tvm, new_template, request=request)
    vm_api.set_current(new_template, request=request)
    return new_template


def migrate_records(old_template_ids, new_template):
    """Bulk-update all Data records on old_template_ids to new_template.

    Returns count of migrated records.
    """
    from core_main_app.components.data.models import Data

    if not old_template_ids:
        return 0
    return Data.objects.filter(template_id__in=old_template_ids).update(
        template=new_template
    )


def update_xslt(xslt_dir=XSLT_DIR):
    """Refresh both XSLT stylesheets in the DB from mounted xslt/ directory."""
    from core_main_app.components.xsl_transformation import api as xslt_api

    dataset_base_url = os.environ.get(
        "XSLT_DATASET_BASE_URL",
        "https://files.nexuslims-dev.localhost/instrument-data",
    )
    preview_base_url = os.environ.get(
        "XSLT_PREVIEW_BASE_URL",
        "https://files.nexuslims-dev.localhost/data",
    )

    for xsl_name in ["detail_stylesheet.xsl", "list_stylesheet.xsl"]:
        content = (xslt_dir / xsl_name).read_text(encoding="utf-8")

        if xsl_name == "detail_stylesheet.xsl":
            content = content.replace(
                '<xsl:variable name="datasetBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>',
                f'<xsl:variable name="datasetBaseUrl">{dataset_base_url}</xsl:variable>',
            )
            content = content.replace(
                '<xsl:variable name="previewBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>',
                f'<xsl:variable name="previewBaseUrl">{preview_base_url}</xsl:variable>',
            )

        xslt = xslt_api.get_by_name(xsl_name)
        xslt.content = content
        xslt_api.upsert(xslt)
        log_success(f"{xsl_name} updated")


def main():
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        os.getenv("DJANGO_SETTINGS_MODULE", "mdcs.settings"),
    )
    sys.path.insert(0, "/srv/nexuslims")

    import django
    django.setup()
    logging.getLogger("core_main_app").setLevel(logging.ERROR)

    from django.contrib.auth.models import User
    from django.test import RequestFactory

    admin = User.objects.filter(is_superuser=True).first()
    if admin is None:
        log_error("No superuser found. Run init_environment.py first.")
        sys.exit(1)

    request = RequestFactory().get("/")
    request.user = admin

    upgraded = False

    # ── Step 1: Schema ──────────────────────────────────────────────────────
    print("\nStep 1/3: Schema check")
    try:
        result = detect_schema_change()
    except FileNotFoundError as exc:
        log_error(str(exc))
        sys.exit(1)
    except RuntimeError as exc:
        log_error(str(exc))
        sys.exit(1)

    if result is None:
        log_success("Active version hash matches on-disk schema — no upgrade needed")
    else:
        tvm, new_content = result
        old_ids = list(tvm.versions)
        try:
            new_template = add_schema_version(tvm, new_content, request)
        except Exception as exc:
            log_error(f"Failed to add schema version: {exc}")
            sys.exit(1)
        version_number = len(tvm.versions)
        log_success(f"Added Version {version_number} to '{TEMPLATE_TITLE}'")
        log_success(f"Version {version_number} set as current")
        upgraded = True

    # ── Step 2: Records ─────────────────────────────────────────────────────
    print("\nStep 2/3: Record migration")
    # Always check — handles both "just upgraded" and "records left behind" cases.
    from core_main_app.components.template_version_manager.models import (
        TemplateVersionManager,
    )
    from core_main_app.components.template.models import Template

    tvm_now = TemplateVersionManager.objects.filter(
        title=TEMPLATE_TITLE, is_disabled=False
    ).first()
    current_tmpl = Template.objects.get(id=tvm_now.current)
    non_current_ids = [v for v in tvm_now.versions if str(v) != str(current_tmpl.id)]

    try:
        count = migrate_records(non_current_ids, current_tmpl)
    except Exception as exc:
        log_error(f"Record migration failed: {exc}")
        sys.exit(1)

    if count:
        log_success(f"Migrated {count} record(s) to current schema version")
        upgraded = True
    else:
        log_success("All records already on current version — no migration needed")

    # ── Step 3: XSLT ────────────────────────────────────────────────────────
    print("\nStep 3/3: XSLT update")
    try:
        update_xslt()
    except Exception as exc:
        log_warning(f"XSLT update failed (schema/records unchanged): {exc}")

    print()
    print("Schema upgrade complete." if upgraded else "Nothing to upgrade.")


if __name__ == "__main__":
    main()
