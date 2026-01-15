#!/usr/bin/env python3
"""
Backup NexusLIMS-CDCS data using REST API.

This script backs up:
- Templates (XSD schemas)
- Data records (XML)
- Binary blobs (images, files)
- Users (Django fixture)
- XSLT stylesheets
- Persistent queries

Based on the approach used in nest-r_backup but adapted for NexusLIMS-CDCS.
"""

import os
import sys
import json
import re
import requests
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin
import hashlib

# Django setup for access to models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev_settings"))
sys.path.insert(0, "/srv/nexuslims")
import django
django.setup()

from django.contrib.auth import get_user_model
from django.core import serializers
from django.test import RequestFactory
from core_main_app.components.template import api as template_api
from core_main_app.components.template_version_manager import api as template_version_manager_api
from core_main_app.components.xsl_transformation import api as xsl_transformation_api
from core_main_app.components.template_xsl_rendering import api as template_xsl_rendering_api
from core_main_app.components.data import api as data_api
from core_main_app.components.data.models import Data
from core_main_app.components.workspace.models import Workspace


class CDCSBackup:
    """Backup CDCS data via REST API and Django models."""

    def __init__(self, backup_dir=None, base_url=None, username=None, password=None):
        """
        Initialize backup configuration.

        Args:
            backup_dir: Directory to store backups (default: ./backups/YYYYMMDD_HHMMSS)
            base_url: CDCS base URL (default: from SERVER_URI env var)
            username: Admin username (default: 'admin')
            password: Admin password (default: 'admin')
        """
        # Backup directory
        if backup_dir is None:
            # Get timezone from environment or default to local system timezone
            tz_name = os.getenv("TZ", "America/New_York")
            try:
                tz = ZoneInfo(tz_name)
            except Exception:
                # Fallback to UTC if timezone is invalid
                tz = ZoneInfo("UTC")

            timestamp = datetime.now(tz).strftime("%Y%m%d_%H%M%S")
            backup_dir = f"/srv/nexuslims/backups/backup_{timestamp}"
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # API configuration
        self.base_url = base_url or os.getenv("SERVER_URI", "https://nexuslims-dev.localhost")
        self.username = username or "admin"
        self.password = password or "admin"
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = False  # For development with self-signed certs

        # Statistics
        self.stats = {
            "templates": 0,
            "records": 0,
            "blobs": 0,
            "users": 0,
            "xslt": 0,
            "queries": 0
        }

        # Get superuser for Django ORM operations
        User = get_user_model()
        self.superuser = User.objects.filter(is_superuser=True).first()
        if not self.superuser:
            print("⚠️  Warning: No superuser found. Creating one...")
            self.superuser = User.objects.create_superuser(
                username="admin", email="admin@localhost", password="admin"
            )

        # Create mock request for API calls
        factory = RequestFactory()
        self.request = factory.get("/")
        self.request.user = self.superuser

        print(f"Backup initialized:")
        print(f"  Directory: {self.backup_dir}")
        print(f"  Base URL: {self.base_url}")
        print(f"  User: {self.superuser.username}")
        print()

    def get_host_path(self, container_path):
        """
        Translate container path to host path for production deployments.

        Production volume mapping:
        - ${NX_CDCS_BACKUPS_HOST_PATH}:/srv/nexuslims/backups
        """
        container_path_str = str(container_path)

        # Check for production backup mount
        backups_host_path = os.getenv("NX_CDCS_BACKUPS_HOST_PATH")
        if backups_host_path and container_path_str.startswith("/srv/nexuslims/backups"):
            # Production: specific backup directory mount
            relative = container_path_str.replace("/srv/nexuslims/backups", "").lstrip("/")
            host_path = Path(backups_host_path) / relative
            return host_path

        # Fallback: return container path (e.g., for dev environments)
        return container_path

    def api_get(self, endpoint):
        """Make GET request to API."""
        url = urljoin(self.base_url, endpoint)
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def api_get_binary(self, endpoint):
        """Make GET request to API for binary data."""
        url = urljoin(self.base_url, endpoint)
        response = self.session.get(url)
        response.raise_for_status()
        return response.content

    def backup_templates(self):
        """Backup all templates (XSD schemas)."""
        print("📋 Backing up templates...")

        # Create schemas directory
        schemas_dir = self.backup_dir / "schemas"
        schemas_dir.mkdir(exist_ok=True)

        # Get all global template version managers using Django ORM
        try:
            template_managers = template_version_manager_api.get_global_version_managers(request=self.request)
        except Exception as e:
            print(f"  ⚠️  Could not retrieve templates: {e}")
            return

        # Backup each template
        for tm in template_managers:
            title = tm.title or "Untitled"
            template_id = tm.current

            if not template_id:
                print(f"  ⚠️  Template '{title}' has no current version, skipping")
                continue

            # Create directory for this template
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
            template_dir = schemas_dir / f"{safe_title}_{template_id}"
            template_dir.mkdir(exist_ok=True)

            try:
                # Get template content using Django ORM
                template = template_api.get_by_id(template_id, request=self.request)

                # Save schema file
                filename = template.filename or f"{safe_title}.xsd"
                schema_path = template_dir / f"Cur_{filename}"
                schema_path.write_text(template.content, encoding="utf-8")

                # Save metadata
                metadata = {
                    "id": str(template_id),
                    "title": title,
                    "filename": filename,
                    "version_manager_id": str(tm.id),
                }
                (template_dir / "metadata.json").write_text(
                    json.dumps(metadata, indent=2),
                    encoding="utf-8"
                )

                self.stats["templates"] += 1
                print(f"  ✓ {title} (ID: {template_id})")

                # Backup XSLT associations for this template
                self.backup_template_xslt_association(template_dir, template_id)

                # Backup records for this template
                self.backup_records_for_template(template_dir, template_id, title)

            except Exception as e:
                print(f"  ✗ Failed to backup template {title}: {e}")

    def backup_template_xslt_association(self, template_dir, template_id):
        """Backup XSLT-to-template associations for a specific template."""
        try:
            # Get TemplateXslRendering for this template
            rendering = template_xsl_rendering_api.get_by_template_id(template_id)

            # Handle list_detail_xslt - could be a list, array, or ManyRelatedManager
            list_detail_xslt_ids = []
            if hasattr(rendering, 'list_detail_xslt') and rendering.list_detail_xslt:
                # Check if it's a manager (has .all() method) or a list/array
                if hasattr(rendering.list_detail_xslt, 'all'):
                    # It's a ManyRelatedManager
                    list_detail_xslt_ids = [str(xslt.id) for xslt in rendering.list_detail_xslt.all()]
                elif isinstance(rendering.list_detail_xslt, (list, tuple)):
                    # It's already a list/tuple of IDs
                    list_detail_xslt_ids = [str(xid) for xid in rendering.list_detail_xslt]
                else:
                    # It might be a single value or array field
                    try:
                        list_detail_xslt_ids = [str(xid) for xid in rendering.list_detail_xslt]
                    except TypeError:
                        list_detail_xslt_ids = []

            # Build association metadata
            association = {
                "template_id": str(template_id),
                "rendering_id": str(rendering.id),
                "list_xslt_id": str(rendering.list_xslt.id) if rendering.list_xslt else None,
                "list_xslt_name": rendering.list_xslt.name if rendering.list_xslt else None,
                "default_detail_xslt_id": str(rendering.default_detail_xslt.id) if rendering.default_detail_xslt else None,
                "default_detail_xslt_name": rendering.default_detail_xslt.name if rendering.default_detail_xslt else None,
                "list_detail_xslt_ids": list_detail_xslt_ids,
            }

            # Save association metadata
            association_path = template_dir / "xslt_association.json"
            association_path.write_text(json.dumps(association, indent=2), encoding="utf-8")
            print(f"    → Saved XSLT associations")

        except Exception as e:
            # No XSLT rendering for this template (not an error, but log it)
            print(f"    ⚠️  No XSLT associations for this template: {e}")

    def backup_records_for_template(self, template_dir, template_id, template_title):
        """Backup all data records for a specific template."""
        files_dir = template_dir / "files"
        files_dir.mkdir(exist_ok=True)

        blobs_dir = template_dir / "blobs"
        blobs_dir.mkdir(exist_ok=True)

        try:
            # Get all records for this template using Django ORM
            records = Data.objects.filter(template=template_id)

            total_records = 0
            for record in records:
                try:
                    self.backup_single_record_from_orm(record, files_dir, blobs_dir)
                    total_records += 1
                except Exception as e:
                    print(f"    ✗ Failed to backup record {getattr(record, 'title', 'unknown')}: {e}")

            if total_records > 0:
                print(f"    → Saved {total_records} records")
                self.stats["records"] += total_records

        except Exception as e:
            print(f"    ✗ Failed to query records for template {template_title}: {e}")

    def backup_single_record(self, record, files_dir, blobs_dir):
        """Backup a single data record and its blobs (from API response dict)."""
        title = record.get("title", "untitled")
        record_id = record.get("id")
        xml_content = record.get("xml_content", "")

        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:100]

        # Handle duplicate titles
        counter = 1
        xml_path = files_dir / f"{safe_title}.xml"
        while xml_path.exists():
            xml_path = files_dir / f"{safe_title}_{counter}.xml"
            counter += 1

        # Save XML content
        xml_path.write_text(xml_content, encoding="utf-8")

        # Extract and backup blobs
        self.backup_blobs_from_xml(xml_content, blobs_dir)

    def backup_single_record_from_orm(self, record, files_dir, blobs_dir):
        """Backup a single data record and its blobs (from Django ORM object)."""
        title = getattr(record, "title", "untitled")
        xml_content = getattr(record, "xml_content", "")

        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:100]

        # Handle duplicate titles
        counter = 1
        xml_path = files_dir / f"{safe_title}.xml"
        while xml_path.exists():
            xml_path = files_dir / f"{safe_title}_{counter}.xml"
            counter += 1

        # Save XML content
        xml_path.write_text(xml_content, encoding="utf-8")

        # Save record metadata (workspace, user, etc.)
        metadata = {
            "id": str(record.id),
            "title": title,
            "user_id": str(record.user_id) if hasattr(record, 'user_id') else None,
            "workspace_id": None,
            "workspace_title": None,
            "is_global_workspace": False,
        }

        # Capture workspace information
        if hasattr(record, 'workspace') and record.workspace:
            metadata["workspace_id"] = str(record.workspace.id)
            metadata["workspace_title"] = getattr(record.workspace, 'title', None)
            metadata["is_global_workspace"] = record.workspace.is_global

        # Save metadata alongside XML
        metadata_path = xml_path.with_suffix('.xml.metadata.json')
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # Extract and backup blobs
        self.backup_blobs_from_xml(xml_content, blobs_dir)

    def backup_blobs_from_xml(self, xml_content, blobs_dir):
        """Extract blob references from XML and backup the files."""
        # Find blob references in XML
        # Pattern: <preview>http://127.0.0.1/pid/rest/local/cdcs/<blob-id></preview>
        blob_pattern = r'http://127\.0\.0\.1/pid/rest/local/cdcs/([^<]+)'
        blob_ids = re.findall(blob_pattern, xml_content)

        for blob_id in blob_ids:
            try:
                # Get blob metadata
                blob_data = self.api_get(f"/rest/blob/{blob_id}/")
                filename = blob_data.get("filename", f"blob_{blob_id}")

                # Download blob content
                blob_content = self.api_get_binary(f"/rest/blob/{blob_id}/download/")

                # Save with ID prefix to maintain relationship
                blob_path = blobs_dir / f"{blob_id}_{filename}"
                blob_path.write_bytes(blob_content)

                self.stats["blobs"] += 1

            except Exception as e:
                # Blob might not exist or might not be accessible
                pass

    def backup_users(self):
        """Backup user accounts as Django fixture."""
        print("👥 Backing up users...")

        User = get_user_model()
        users = User.objects.all()

        # Serialize users to JSON
        # NOTE: We must preserve primary keys so user_id references in records remain valid
        users_json = serializers.serialize(
            "json",
            users,
            indent=2,
            use_natural_foreign_keys=True
        )

        users_path = self.backup_dir / "users.json"
        users_path.write_text(users_json, encoding="utf-8")

        self.stats["users"] = len(users)
        print(f"  ✓ Backed up {len(users)} users")

    def backup_xslt_stylesheets(self):
        """Backup XSLT stylesheets from database."""
        print("🎨 Backing up XSLT stylesheets...")

        xslt_dir = self.backup_dir / "xslt"
        xslt_dir.mkdir(exist_ok=True)

        try:
            # Get all XSLT transformations from database
            stylesheets = xsl_transformation_api.get_all()

            for xslt in stylesheets:
                filename = xslt.name
                content = xslt.content

                # Save stylesheet
                xslt_path = xslt_dir / filename
                xslt_path.write_text(content, encoding="utf-8")

                # Save metadata
                metadata = {
                    "id": str(xslt.id),
                    "name": xslt.name,
                    "filename": xslt.filename
                }
                metadata_path = xslt_dir / f"{filename}.metadata.json"
                metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

                self.stats["xslt"] += 1
                print(f"  ✓ {filename}")

        except Exception as e:
            print(f"  ✗ Failed to backup XSLT stylesheets: {e}")

    def backup_queries(self):
        """Backup persistent queries."""
        print("🔍 Backing up persistent queries...")

        queries_dir = self.backup_dir / "queries"
        queries_dir.mkdir(exist_ok=True)

        try:
            # Try to use Django ORM to get persistent queries
            from core_explore_keyword_app.components.persistent_query_keyword import (
                api as persistent_query_api
            )

            queries = persistent_query_api.get_all(self.superuser)

            for query in queries:
                # Handle None query names
                query_name = getattr(query, "name", None) or f"query_{query.id}"
                safe_name = re.sub(r'[^\w\s-]', '', query_name).strip().replace(' ', '_')

                # Serialize query to dict
                query_data = {
                    "id": str(query.id),
                    "name": query.name,
                    "content": getattr(query, "content", ""),
                    "user_id": str(query.user_id) if hasattr(query, "user_id") else None,
                }

                query_path = queries_dir / f"{safe_name}.json"
                query_path.write_text(json.dumps(query_data, indent=2), encoding="utf-8")

                self.stats["queries"] += 1
                print(f"  ✓ {query_name}")

        except ImportError:
            print(f"  ⚠️  core_explore_keyword_app not available, skipping queries")
        except Exception as e:
            print(f"  ⚠️  Could not backup queries: {e}")

    def generate_restore_scripts(self):
        """Generate shell scripts for restoration."""
        print("📝 Generating restore scripts...")

        # Create restore script
        restore_script = self.backup_dir / "restore.sh"
        restore_script.write_text(f"""#!/bin/bash
# Auto-generated restore script
# Created: {datetime.now().isoformat()}

BACKUP_DIR="{self.backup_dir}"

python /srv/scripts/restore_cdcs.py --all "$BACKUP_DIR"
""", encoding="utf-8")

        restore_script.chmod(0o755)
        print(f"  ✓ Created {restore_script}")

    def create_backup_manifest(self):
        """Create a manifest file with backup metadata."""
        # Use same timezone as backup directory
        tz_name = os.getenv("TZ", "America/New_York")
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("UTC")

        manifest = {
            "created": datetime.now(tz).isoformat(),
            "timezone": tz_name,
            "source_url": self.base_url,
            "backup_dir": str(self.backup_dir),
            "statistics": self.stats,
            "django_settings": os.getenv("DJANGO_SETTINGS_MODULE"),
        }

        manifest_path = self.backup_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def run(self):
        """Execute complete backup."""
        print("=" * 60)
        print("NexusLIMS-CDCS Backup")
        print("=" * 60)
        print()

        try:
            self.backup_templates()
            print()

            self.backup_users()
            print()

            self.backup_xslt_stylesheets()
            print()

            self.backup_queries()
            print()

            self.generate_restore_scripts()
            print()

            self.create_backup_manifest()

            # Print summary
            print("=" * 60)
            print("Backup Complete!")
            print("=" * 60)

            # Show both container and host paths
            host_path = self.get_host_path(self.backup_dir)
            print(f"Container path: {self.backup_dir}")
            if str(host_path) != str(self.backup_dir):
                print(f"Host path:      {host_path}")
            print()

            print("Statistics:")
            print(f"  Templates: {self.stats['templates']}")
            print(f"  Records:   {self.stats['records']}")
            print(f"  Blobs:     {self.stats['blobs']}")
            print(f"  Users:     {self.stats['users']}")
            print(f"  XSLT:      {self.stats['xslt']}")
            print(f"  Queries:   {self.stats['queries']}")
            print()
            print(f"To restore: bash {self.backup_dir}/restore.sh")
            print("Or use the 'admin-restore' administration command")
            print()

            return 0

        except Exception as e:
            print(f"✗ Backup failed: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backup NexusLIMS-CDCS data")
    parser.add_argument("--dir", help="Backup directory (default: auto-generated)")
    parser.add_argument("--url", help="CDCS base URL (default: from SERVER_URI)")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", default="admin", help="Admin password")

    args = parser.parse_args()

    backup = CDCSBackup(
        backup_dir=args.dir,
        base_url=args.url,
        username=args.username,
        password=args.password
    )

    sys.exit(backup.run())
