#!/usr/bin/env python
"""
Seed demo records for NexusLIMS public demo.

Reads all XML files from deployment/fixtures/demo_records/ and uploads them
via the core_main_app data API. Designed to run after init_environment.py.

Usage:
    docker exec nexuslims_demo_cdcs python /srv/scripts/seed_demo_records.py
"""

import os
import random
import sys
from pathlib import Path

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.demo_settings"),
)
sys.path.insert(0, "/srv/nexuslims")

import django

django.setup()

import logging

logging.getLogger("core_main_app").setLevel(logging.ERROR)


FIXTURES_DIR = Path("/srv/nexuslims/deployment/fixtures/demo_records")
UPLOADER_USERNAME = "admin"
SCHEMA_TITLE = "Nexus Experiment Schema"


def log_success(msg):
    print(f"✓ {msg}")


def log_warning(msg):
    print(f"⚠ {msg}")


def log_error(msg):
    print(f"✗ {msg}")


def log_info(msg):
    print(f"→ {msg}")


def seed_records():
    from django.contrib.auth import get_user_model
    from django.test import RequestFactory
    from core_main_app.components.data import api as data_api
    from core_main_app.components.data.models import Data
    from core_main_app.components.template import api as template_api
    from core_main_app.components.template_version_manager import api as tvm_api
    from core_main_app.components.workspace import api as workspace_api

    if not FIXTURES_DIR.exists():
        log_warning(f"Fixtures directory not found: {FIXTURES_DIR}")
        log_info("Skipping demo record seeding (no fixture files available yet)")
        log_info("To add records: place XML files in deployment/fixtures/demo_records/")
        return

    xml_files = sorted(FIXTURES_DIR.glob("*.xml"))
    random.shuffle(xml_files)
    if not xml_files:
        log_warning(f"No XML files found in {FIXTURES_DIR}")
        return

    log_info(f"Found {len(xml_files)} XML fixture files")

    # Get the uploader user and build a request
    User = get_user_model()
    uploader = User.objects.filter(username=UPLOADER_USERNAME).first()
    if not uploader:
        log_error(
            f"Uploader user '{UPLOADER_USERNAME}' not found - run init_environment.py first"
        )
        return

    factory = RequestFactory()
    request = factory.get("/")
    request.user = uploader

    # Get the NexusLIMS template via the version manager (same pattern as init_environment.py)
    try:
        tvm = tvm_api.get_active_global_version_manager_by_title(
            SCHEMA_TITLE, request=request
        )
        template = template_api.get_by_id(tvm.current, request=request)
    except Exception as e:
        log_error(f"Could not find '{SCHEMA_TITLE}' template: {e}")
        log_info("Run init_environment.py first to upload the schema")
        return

    # Get (or create) the global public workspace
    try:
        public_workspace = workspace_api.get_global_workspace()
    except Exception:
        try:
            public_workspace = workspace_api.create_and_get_global_workspace()
        except Exception as e:
            log_warning(f"Could not get/create global workspace: {e}")
            public_workspace = None

    uploaded = 0
    skipped = 0
    errors = 0

    for xml_file in xml_files:
        title = xml_file.stem

        # Skip if a record with this title already exists
        if Data.objects.filter(title=title).exists():
            log_info(f"Skipping (already exists): {title}")
            skipped += 1
            continue

        try:
            record = Data(template=template, title=title)
            record.content = xml_file.read_text(encoding="utf-8")
            record.user_id = uploader.id
            record = data_api.upsert(record, request=request)

            if public_workspace:
                record.workspace = public_workspace
                record = data_api.upsert(record, request=request)

            log_success(f"Uploaded: {title}")
            uploaded += 1
        except Exception as e:
            log_error(f"Failed to upload {title}: {e}")
            errors += 1

    print("=" * 60)
    log_success(
        f"Seeding complete: {uploaded} uploaded, {skipped} skipped, {errors} errors"
    )


def main():
    from django.conf import settings

    if not getattr(settings, "IS_PUBLIC_DEMO", False):
        log_warning("IS_PUBLIC_DEMO is not True - are you using demo_settings?")

    print("=" * 60)
    print("NexusLIMS Demo Record Seeding")
    print("=" * 60)

    seed_records()

    print("=" * 60)


if __name__ == "__main__":
    main()
