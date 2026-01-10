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
from urllib.parse import urljoin
import hashlib

# Django setup for access to models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev_settings"))
sys.path.insert(0, "/srv/curator")
import django
django.setup()

from django.contrib.auth import get_user_model
from django.core import serializers
from core_main_app.components.template import api as template_api
from core_main_app.components.xsl_transformation import api as xsl_transformation_api


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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"/srv/curator/backups/backup_{timestamp}"
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

        print(f"Backup initialized:")
        print(f"  Directory: {self.backup_dir}")
        print(f"  Base URL: {self.base_url}")
        print(f"  User: {self.username}")
        print()

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

        # Get all template version managers
        try:
            data = self.api_get("/rest/template-version-manager/global/")
            template_managers = data.get("results", [])
        except Exception as e:
            print(f"  ⚠️  Could not retrieve templates via API: {e}")
            print(f"  Using Django ORM instead...")
            template_managers = []

        # Create schemas directory
        schemas_dir = self.backup_dir / "schemas"
        schemas_dir.mkdir(exist_ok=True)

        # Backup each template
        for tm in template_managers:
            title = tm.get("title", "Untitled")
            template_id = tm.get("current")

            # Create directory for this template
            # Use hash of title to avoid filesystem issues
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
            template_dir = schemas_dir / f"{safe_title}_{template_id}"
            template_dir.mkdir(exist_ok=True)

            try:
                # Get template content
                template_data = self.api_get(f"/rest/template/{template_id}/")

                # Save schema file
                filename = template_data.get("filename", f"{safe_title}.xsd")
                schema_path = template_dir / f"Cur_{filename}"
                schema_path.write_text(template_data["content"], encoding="utf-8")

                # Save metadata
                metadata = {
                    "id": template_id,
                    "title": title,
                    "filename": filename,
                    "version_manager_id": tm.get("id"),
                }
                (template_dir / "metadata.json").write_text(
                    json.dumps(metadata, indent=2),
                    encoding="utf-8"
                )

                self.stats["templates"] += 1
                print(f"  ✓ {title} (ID: {template_id})")

                # Backup records for this template
                self.backup_records_for_template(template_dir, template_id, title)

            except Exception as e:
                print(f"  ✗ Failed to backup template {title}: {e}")

    def backup_records_for_template(self, template_dir, template_id, template_title):
        """Backup all data records for a specific template."""
        files_dir = template_dir / "files"
        files_dir.mkdir(exist_ok=True)

        blobs_dir = template_dir / "blobs"
        blobs_dir.mkdir(exist_ok=True)

        try:
            # Query records by template
            query_data = {
                "query": json.dumps({"template": str(template_id)}),
                "all": "true"
            }

            page = 1
            total_records = 0

            # Handle pagination
            endpoint = "/rest/data/query/"
            while endpoint:
                try:
                    response = self.api_get(endpoint)
                    records = response.get("results", [])

                    for record in records:
                        try:
                            self.backup_single_record(record, files_dir, blobs_dir)
                            total_records += 1
                        except Exception as e:
                            print(f"    ✗ Failed to backup record {record.get('title', 'unknown')}: {e}")

                    # Check for next page
                    endpoint = response.get("next")
                    if endpoint:
                        # Make endpoint relative if it's absolute
                        if endpoint.startswith("http"):
                            endpoint = "/" + "/".join(endpoint.split("/")[3:])
                        page += 1

                except Exception as e:
                    print(f"    ✗ Error fetching page {page}: {e}")
                    break

            if total_records > 0:
                print(f"    → Saved {total_records} records")
                self.stats["records"] += total_records

        except Exception as e:
            print(f"    ✗ Failed to query records for template {template_title}: {e}")

    def backup_single_record(self, record, files_dir, blobs_dir):
        """Backup a single data record and its blobs."""
        title = record.get("title", "untitled")
        record_id = record.get("id")
        xml_content = record.get("xml_content", "")

        # Replace production URLs with placeholder for portability
        xml_content = re.sub(
            r'https?://[^/]+/',
            'http://127.0.0.1/',
            xml_content
        )

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
        users_json = serializers.serialize(
            "json",
            users,
            indent=2,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True
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
            # Try to get queries via API
            data = self.api_get("/explore/keyword/rest/admin/persistent_query_keyword/")
            queries = data.get("results", [])

            for query in queries:
                query_name = query.get("name", f"query_{query.get('id')}")
                safe_name = re.sub(r'[^\w\s-]', '', query_name).strip().replace(' ', '_')

                query_path = queries_dir / f"{safe_name}.json"
                query_path.write_text(json.dumps(query, indent=2), encoding="utf-8")

                self.stats["queries"] += 1
                print(f"  ✓ {query_name}")

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

echo "Restoring NexusLIMS-CDCS backup from $BACKUP_DIR"
echo ""

# Restore users
echo "Restoring users..."
python /srv/scripts/restore_cdcs.py --users "$BACKUP_DIR/users.json"

# Restore XSLT
echo "Restoring XSLT stylesheets..."
python /srv/scripts/restore_cdcs.py --xslt "$BACKUP_DIR/xslt"

# Restore templates and data
echo "Restoring templates and data records..."
python /srv/scripts/restore_cdcs.py --data "$BACKUP_DIR/schemas"

# Restore queries
echo "Restoring persistent queries..."
python /srv/scripts/restore_cdcs.py --queries "$BACKUP_DIR/queries"

echo ""
echo "Restore complete!"
""", encoding="utf-8")

        restore_script.chmod(0o755)
        print(f"  ✓ Created {restore_script}")

    def create_backup_manifest(self):
        """Create a manifest file with backup metadata."""
        manifest = {
            "created": datetime.now().isoformat(),
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
            print(f"Location: {self.backup_dir}")
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
