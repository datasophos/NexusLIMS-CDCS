#!/usr/bin/env python3
"""
Restore NexusLIMS-CDCS data from backup.

This script restores:
- Users (Django fixtures)
- XSLT stylesheets
- Templates (XSD schemas)
- Data records (XML)
- Persistent queries
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Filter specific noisy log messages
class MessageFilter(logging.Filter):
    def filter(self, record):
        noisy_messages = [
            'SSL_CERTIFICATES_DIR',
            'Registered signals',
            'No request or session id is None',
        ]
        return not any(msg in record.getMessage() for msg in noisy_messages)

# Apply filter to root logger and common CDCS loggers
for logger_name in ['', 'core_main_app', 'django']:
    logger = logging.getLogger(logger_name)
    logger.addFilter(MessageFilter())

# Also filter stdout/stderr for print statements
class FilteredWriter:
    def __init__(self, stream):
        self.stream = stream
        self.noisy_patterns = [
            'SSL_CERTIFICATES_DIR',
            'Registered signals',
            'No request or session id is None',
        ]

    def write(self, text):
        # Allow empty strings (newlines) to pass through, filter only lines with noisy patterns
        if not text.strip() or not any(pattern in text for pattern in self.noisy_patterns):
            self.stream.write(text)

    def flush(self):
        self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)

# Wrap stdout and stderr
sys.stdout = FilteredWriter(sys.stdout)
sys.stderr = FilteredWriter(sys.stderr)

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev_settings"))
sys.path.insert(0, "/srv/nexuslims")
import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.core.management import call_command
from core_main_app.components.template import api as template_api
from core_main_app.components.template_version_manager import api as template_version_manager_api
from core_main_app.components.xsl_transformation import api as xsl_transformation_api
from core_main_app.components.template_xsl_rendering import api as template_xsl_rendering_api
from core_main_app.components.data import api as data_api
from core_main_app.components.workspace.models import Workspace


def log_success(msg):
    """Print success message."""
    print(f"✓ {msg}")


def log_warning(msg):
    """Print warning message."""
    print(f"⚠ {msg}")


def log_error(msg):
    """Print error message."""
    print(f"✗ {msg}")


def log_info(msg):
    """Print info message."""
    print(f"→ {msg}")


def get_admin_user():
    """Get or create admin user for API calls."""
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()

    if not admin_user:
        log_warning("No superuser found, creating one...")
        admin_user = User.objects.create_superuser(
            username="admin", email="admin@localhost", password="admin"
        )

    return admin_user


def get_admin_request():
    """Create a mock request object with admin user for API calls."""
    admin_user = get_admin_user()

    factory = RequestFactory()
    request = factory.get("/")
    request.user = admin_user
    return request


def get_global_workspace():
    """Get the global public workspace."""
    try:
        return Workspace.get_global_workspace()
    except Exception as e:
        log_warning(f"Could not get global workspace: {e}")
        return None


def restore_users(users_file):
    """Restore users from JSON fixture."""
    print("👥 Restoring users...")

    users_path = Path(users_file)
    if not users_path.exists():
        log_error(f"Users file not found: {users_file}")
        return False

    try:
        # Use Django's loaddata command
        call_command("loaddata", str(users_path))
        log_success(f"Users restored from {users_file}")
        return True
    except Exception as e:
        log_error(f"Failed to restore users: {e}")
        return False


def restore_xslt(xslt_dir):
    """Restore XSLT stylesheets."""
    print("🎨 Restoring XSLT stylesheets...")

    xslt_path = Path(xslt_dir)
    if not xslt_path.exists():
        log_error(f"XSLT directory not found: {xslt_dir}")
        return False

    success_count = 0

    # Find all .xsl files
    xsl_files = list(xslt_path.glob("*.xsl"))

    for xsl_file in xsl_files:
        try:
            # Read stylesheet content
            with xsl_file.open(encoding="utf-8") as f:
                content = f.read()

            # Read metadata if exists
            metadata_file = xslt_path / f"{xsl_file.name}.metadata.json"
            metadata = {}
            if metadata_file.exists():
                with metadata_file.open(encoding="utf-8") as f:
                    metadata = json.load(f)

            stylesheet_name = metadata.get("name", xsl_file.name)

            # Check if stylesheet already exists
            try:
                existing_xslt = xsl_transformation_api.get_by_name(stylesheet_name)
                # Update existing stylesheet
                existing_xslt.content = content
                xsl_transformation_api.upsert(existing_xslt)
                log_success(f"Updated stylesheet: {stylesheet_name}")
            except Exception:
                # Create new stylesheet
                from core_main_app.components.xsl_transformation.models import XslTransformation

                xslt = XslTransformation()
                xslt.name = stylesheet_name
                xslt.filename = xsl_file.name
                xslt.content = content
                xsl_transformation_api.upsert(xslt)
                log_success(f"Created stylesheet: {stylesheet_name}")

            success_count += 1

        except Exception as e:
            log_error(f"Failed to restore stylesheet {xsl_file.name}: {e}")

    log_info(f"Restored {success_count}/{len(xsl_files)} stylesheets")
    return success_count > 0


def restore_template_xslt_association(template_dir, template_id, request):
    """Restore XSLT-to-template association for a specific template."""
    association_file = template_dir / "xslt_association.json"

    list_xslt_name = None
    detail_xslt_name = None

    if not association_file.exists():
        # No XSLT association file - try to auto-link standard XSLTs
        log_info("  No xslt_association.json found - attempting auto-link with standard XSLTs")
        list_xslt_name = "list_stylesheet.xsl"
        detail_xslt_name = "detail_stylesheet.xsl"
    else:
        # Read association file
        try:
            with association_file.open(encoding="utf-8") as f:
                association = json.load(f)

            list_xslt_name = association.get("list_xslt_name")
            detail_xslt_name = association.get("default_detail_xslt_name")

            if not list_xslt_name and not detail_xslt_name:
                return
        except Exception as e:
            log_error(f"  Failed to read xslt_association.json: {e}")
            return

    if not list_xslt_name and not detail_xslt_name:
        return

    # Get the template object
    try:
        template = template_api.get_by_id(template_id, request=request)
    except Exception as e:
        log_error(f"  Failed to get template {template_id}: {e}")
        return

    # Get XSLT objects by name
    list_xslt = None
    detail_xslt = None

    if list_xslt_name:
        try:
            list_xslt = xsl_transformation_api.get_by_name(list_xslt_name)
        except Exception as e:
            log_warning(f"  List XSLT '{list_xslt_name}' not found: {e}")

    if detail_xslt_name:
        try:
            detail_xslt = xsl_transformation_api.get_by_name(detail_xslt_name)
        except Exception as e:
            log_warning(f"  Detail XSLT '{detail_xslt_name}' not found: {e}")

    if not list_xslt and not detail_xslt:
        log_warning("  No XSLTs found to link")
        return

    # Check if TemplateXslRendering already exists
    try:
        rendering = template_xsl_rendering_api.get_by_template_id(template_id)
        log_info("  Updating existing TemplateXslRendering...")
    except Exception:
        # Doesn't exist, create new
        rendering = None
        log_info("  Creating TemplateXslRendering...")

    # Create or update the rendering
    # The upsert() API expects: upsert(template, list_xslt, default_detail_xslt, list_detail_xslt)
    try:
        rendering = template_xsl_rendering_api.upsert(
            template,  # Pass template, not rendering object
            list_xslt=list_xslt,
            default_detail_xslt=detail_xslt,
            list_detail_xslt=[list_xslt] if list_xslt else []
        )

        log_success(f"  Linked XSLTs to template (Rendering ID: {rendering.id})")

    except Exception as e:
        log_error(f"  Failed to restore XSLT associations: {e}")
        import traceback
        traceback.print_exc()


def restore_data(schemas_dir):
    """Restore templates and data records."""
    print("📋 Restoring templates and data...")

    schemas_path = Path(schemas_dir)
    if not schemas_path.exists():
        log_error(f"Schemas directory not found: {schemas_dir}")
        return False

    request = get_admin_request()
    admin_user = get_admin_user()
    global_workspace = get_global_workspace()

    if not global_workspace:
        log_error("Could not retrieve global workspace! Records will not be visible.")
        log_info("You may need to create the global workspace first.")
    else:
        log_info(f"Using global workspace: {global_workspace.title} (ID: {global_workspace.id})")

    # Find all template directories
    template_dirs = [d for d in schemas_path.iterdir() if d.is_dir()]

    for template_dir in template_dirs:
        try:
            # Read metadata
            metadata_file = template_dir / "metadata.json"
            if not metadata_file.exists():
                log_warning(f"No metadata.json found in {template_dir.name}, skipping")
                continue

            with metadata_file.open(encoding="utf-8") as f:
                metadata = json.load(f)

            template_title = metadata.get("title", "Untitled")

            # Find XSD file (starts with "Cur_")
            xsd_files = list(template_dir.glob("Cur_*.xsd"))
            if not xsd_files:
                log_warning(f"No XSD file found in {template_dir.name}, skipping")
                continue

            xsd_file = xsd_files[0]

            # Read schema content
            with xsd_file.open(encoding="utf-8") as f:
                schema_content = f.read()

            # Check if template already exists
            try:
                existing_tvm = template_version_manager_api.get_active_global_version_manager_by_title(
                    template_title, request=request
                )
                log_warning(f"Template '{template_title}' already exists, skipping")
                template_id = existing_tvm.current
            except Exception:
                # Create new template
                from core_main_app.components.template.models import Template
                from core_main_app.components.template_version_manager.models import TemplateVersionManager
                import hashlib

                # Create template
                template = Template()
                template.filename = metadata.get("filename", xsd_file.name)
                template.content = schema_content
                template.hash = hashlib.sha1(schema_content.encode("utf-8")).hexdigest()

                # Create TemplateVersionManager
                template_vm = TemplateVersionManager()
                template_vm.title = template_title
                template_vm.user = None  # Global template
                template_vm.is_disabled = False

                # Insert template_vm with template (CDCS 3.18.0 handles everything internally)
                # The insert() method will:
                # 1. Link template to template_vm
                # 2. Call template_api.upsert(template)
                # 3. Set template_vm.current
                # 4. Save everything
                template_vm = template_version_manager_api.insert(template_vm, template, request=request)

                # Get template ID from the inserted template_vm
                template_id = template_vm.current
                log_success(f"Created template: {template_title}")

            # Restore XSLT associations for this template
            restore_template_xslt_association(template_dir, template_id, request)

            # Restore data records
            files_dir = template_dir / "files"
            if files_dir.exists():
                xml_files = list(files_dir.glob("*.xml"))
                restored_count = 0

                for xml_file in xml_files:
                    try:
                        with xml_file.open(encoding="utf-8") as f:
                            xml_content = f.read()

                        # Read record metadata if exists
                        metadata_file = xml_file.with_suffix('.xml.metadata.json')
                        metadata = {}
                        if metadata_file.exists():
                            with metadata_file.open(encoding="utf-8") as f:
                                metadata = json.load(f)

                        # Create data record using data API
                        from core_main_app.components.data.models import Data

                        # Use title from metadata, fallback to filename if not available
                        title = metadata.get("title", xml_file.stem)

                        # Get template
                        template = template_api.get_by_id(template_id, request=request)

                        # Determine owner - use original user if exists, otherwise admin
                        User = get_user_model()
                        original_user_id = metadata.get("user_id")
                        owner_id = str(admin_user.id)  # Default to admin

                        if original_user_id:
                            try:
                                original_user = User.objects.get(id=original_user_id)
                                owner_id = str(original_user.id)
                            except User.DoesNotExist:
                                log_warning(f"  Original user (ID: {original_user_id}) not found, using admin")

                        # Create Data object
                        record = Data()
                        record.template = template
                        record.title = title
                        record.user_id = owner_id

                        # Set content (this triggers convert_to_dict() which populates dict_content)
                        # NOTE: Use 'content' not 'xml_content' so convert_to_dict() works
                        record.content = xml_content

                        # Save the record using data_api.upsert() - this auto-generates dict_content
                        record = data_api.upsert(record, request=request)

                        # Determine workspace and assign if needed
                        workspace = global_workspace if metadata.get("is_global_workspace", True) else None
                        if workspace:
                            record.workspace = workspace
                            record = data_api.upsert(record, request=request)

                        # Get owner username for display
                        try:
                            owner_user = User.objects.get(id=owner_id)
                            owner_display = owner_user.username
                        except User.DoesNotExist:
                            owner_display = f"ID:{owner_id}"

                        # Format workspace info
                        workspace_display = f"{workspace.title} (ID: {workspace.id})" if workspace else "None"

                        restored_count += 1
                        # Fixed-width columns for easy comparison
                        log_info(f"  Restored record: {title:<40} | Owner: {owner_display:<15} | Workspace: {workspace_display}")

                    except Exception as e:
                        log_error(f"  Failed to restore record {xml_file.name}: {e}")

                if xml_files:
                    skipped_count = len(xml_files) - restored_count
                    if skipped_count > 0:
                        log_success(f"Restored {restored_count}/{len(xml_files)} records for template '{template_title}' ({skipped_count} skipped)")
                    else:
                        log_success(f"Restored {restored_count} records for template '{template_title}'")

        except Exception as e:
            log_error(f"Failed to restore template from {template_dir.name}: {e}")
            import traceback
            traceback.print_exc()

    return True


def restore_queries(queries_dir):
    """Restore persistent queries."""
    print("🔍 Restoring persistent queries...")

    queries_path = Path(queries_dir)
    if not queries_path.exists():
        log_error(f"Queries directory not found: {queries_dir}")
        return False

    try:
        from core_explore_keyword_app.components.persistent_query_keyword import (
            api as persistent_query_api
        )
        from core_explore_keyword_app.components.persistent_query_keyword.models import (
            PersistentQueryKeyword
        )
    except ImportError:
        log_warning("core_explore_keyword_app not available, skipping queries")
        return False

    admin_user = get_admin_user()
    query_files = list(queries_path.glob("*.json"))
    success_count = 0

    for query_file in query_files:
        try:
            with query_file.open(encoding="utf-8") as f:
                query_data = json.load(f)

            query_name = query_data.get("name", query_file.stem)

            # Check if query already exists
            try:
                existing_queries = persistent_query_api.get_all(admin_user)
                if any(q.name == query_name for q in existing_queries):
                    log_warning(f"Query '{query_name}' already exists, skipping")
                    continue
            except Exception:
                pass

            # Create new query
            query = PersistentQueryKeyword()
            query.name = query_name
            query.content = query_data.get("content", "")
            query.user_id = query_data.get("user_id") or str(admin_user.id)
            query.save()

            log_success(f"Restored query: {query_name}")
            success_count += 1

        except Exception as e:
            log_error(f"Failed to restore query {query_file.name}: {e}")

    log_info(f"Restored {success_count}/{len(query_files)} queries")
    return success_count > 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Restore NexusLIMS-CDCS data from backup"
    )
    parser.add_argument("--users", help="Path to users JSON fixture")
    parser.add_argument("--xslt", help="Path to XSLT directory")
    parser.add_argument("--data", help="Path to schemas/data directory")
    parser.add_argument("--queries", help="Path to queries directory")
    parser.add_argument("--all", help="Path to backup directory (restore everything)")

    args = parser.parse_args()

    # If no arguments provided, show usage
    if not any([args.users, args.xslt, args.data, args.queries, args.all]):
        parser.print_help()
        return 1

    print("=" * 70)
    print("NexusLIMS-CDCS Restore")
    print("=" * 70)
    print()

    success = True

    # Restore everything from a backup directory
    if args.all:
        backup_path = Path(args.all)
        if not backup_path.exists():
            log_error(f"Backup directory not found: {args.all}")
            return 1

        if (backup_path / "users.json").exists():
            success &= restore_users(backup_path / "users.json")
            print()

        if (backup_path / "xslt").exists():
            success &= restore_xslt(backup_path / "xslt")
            print()

        if (backup_path / "schemas").exists():
            success &= restore_data(backup_path / "schemas")
            print()

        if (backup_path / "queries").exists():
            success &= restore_queries(backup_path / "queries")
            print()

    # Restore individual components
    else:
        if args.users:
            success &= restore_users(args.users)
            print()

        if args.xslt:
            success &= restore_xslt(args.xslt)
            print()

        if args.data:
            success &= restore_data(args.data)
            print()

        if args.queries:
            success &= restore_queries(args.queries)
            print()

    print("=" * 70)
    if success:
        log_success("Restore complete!")
    else:
        log_warning("Restore completed with some errors")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
