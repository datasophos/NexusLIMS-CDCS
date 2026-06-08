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
    new_hash = hashlib.sha1(new_content.encode("utf-8")).hexdigest()

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
    pass  # implemented in Task 5


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

    print("\nStep 1/3: Schema check")
    print("\nStep 2/3: Record migration")
    print("\nStep 3/3: XSLT update")
    print()
    print("(stub — tasks 2-5 will fill this in)")


if __name__ == "__main__":
    main()
