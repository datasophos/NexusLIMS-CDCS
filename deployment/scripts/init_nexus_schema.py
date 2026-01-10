#!/usr/bin/env python
"""
Initialize NexusLIMS schema and XSLT templates in CDCS.

This is a standalone script that can be run via:
    docker exec nexuslims_dev_cdcs python /scripts/init_nexus_schema.py [--force]

This script:
1. Uploads the Nexus Experiment XSD schema as a global template
2. Registers XSLT stylesheets (detail and list views)
3. Links the stylesheets to the template

Note: Adapted for CDCS 3.18.0 - may need adjustments based on actual API.
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mdcs.dev_settings")
sys.path.insert(0, "/srv/curator")

import django

django.setup()


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


def get_admin_request():
    """Create a mock request object with admin user for API calls."""
    from django.contrib.auth import get_user_model
    from django.test import RequestFactory

    User = get_user_model()
    
    # Get or create admin user
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            log_warning("No superuser found, creating one...")
            admin_user = User.objects.create_superuser(
                username="admin", email="admin@localhost", password="admin"
            )
    except Exception as e:
        log_error(f"Failed to get admin user: {e}")
        raise

    # Create mock request
    factory = RequestFactory()
    request = factory.get("/")
    request.user = admin_user
    return request


def load_schema(template_api, template_version_manager_api, force):
    """Load the Nexus Experiment XSD schema as a global template."""
    print("\nLoading Nexus Experiment schema...")
    
    # Get admin request for API calls
    request = get_admin_request()

    schema_path = Path("/srv/curator/mdcs/nexus-experiment.xsd")
    if not schema_path.exists():
        log_error(f"Schema file not found at {schema_path}")
        return None

    with schema_path.open(encoding="utf-8") as f:
        schema_content = f.read()

    template_title = "Nexus Experiment Schema"

    # Check if template already exists
    try:
        existing_tvm = template_version_manager_api.get_active_global_version_manager_by_title(
            template_title
        )
        if not force:
            log_warning(
                f"Template '{template_title}' already exists (use --force to recreate)"
            )
            return existing_tvm
        else:
            log_info("Deleting existing template...")
            existing_tvm.delete()
    except Exception:
        # Template doesn't exist, which is fine
        pass

    # Create the template
    try:
        # Import the Template model to create instance
        from core_main_app.components.template.models import Template

        # Create template instance
        template = Template()
        template.filename = "nexus-experiment.xsd"
        template.content = schema_content
        # Compute hash manually
        template.hash = hashlib.sha1(schema_content.encode("utf-8")).hexdigest()

        # Create TemplateVersionManager with user=None to make it global
        from core_main_app.components.template_version_manager.models import (
            TemplateVersionManager,
        )

        template_vm = TemplateVersionManager()
        template_vm.title = template_title
        template_vm.user = None  # None makes it a global template
        template_vm.is_disabled = False
        template_vm = template_version_manager_api.insert(template_vm, request=request)

        # Link template to version manager before saving
        template.version_manager = template_vm

        # Save the template using upsert
        template = template_api.upsert(template, request=request)

        # Set current version in TVM
        template_vm.versions = [str(template.id)]
        template_vm.current = str(template.id)
        template_vm.save()

        log_success(f"Template '{template_title}' created (ID: {template.id})")
        return template_vm

    except Exception as e:
        log_error(f"Failed to create template: {e}")
        import traceback
        traceback.print_exc()
        raise


def register_xslt_stylesheets(
    template_api,
    template_version_manager_api,
    xsl_transformation_api,
    template_xsl_rendering_api,
    template_vm,
    force,
):
    """Register XSLT stylesheets for the template."""
    print("\nRegistering XSLT stylesheets...")
    
    # Get admin request for API calls
    request = get_admin_request()

    # Get the current template
    try:
        template = template_api.get_by_id(template_vm.current, request=request)
    except Exception as e:
        log_error(f"Failed to get template: {e}")
        raise

    stylesheet_dir = Path("/srv/curator/mdcs")
    stylesheets = {
        "detail": stylesheet_dir / "detail_stylesheet.xsl",
        "list": stylesheet_dir / "list_stylesheet.xsl",
    }

    xslt_map = {}

    for stylesheet_type, stylesheet_path in stylesheets.items():
        stylesheet_name = stylesheet_path.name

        if not stylesheet_path.exists():
            log_warning(f"Stylesheet not found: {stylesheet_path}")
            continue

        # Check if stylesheet already exists
        try:
            existing_xslt = xsl_transformation_api.get_by_name(stylesheet_name)
            if not force:
                log_warning(f"Stylesheet '{stylesheet_name}' already exists")
                xslt_map[stylesheet_type] = existing_xslt
                continue
            else:
                log_info("Deleting existing stylesheet...")
                existing_xslt.delete()
        except Exception:
            # Doesn't exist, which is fine
            pass

        # Read stylesheet content
        with stylesheet_path.open(encoding="utf-8") as f:
            stylesheet_content = f.read()

        # Create XSLT transformation
        try:
            from core_main_app.components.xsl_transformation.models import (
                XslTransformation,
            )
            
            xslt = XslTransformation()
            xslt.name = stylesheet_name
            xslt.filename = stylesheet_name
            xslt.content = stylesheet_content
            xslt = xsl_transformation_api.upsert(xslt)
            xslt_map[stylesheet_type] = xslt
            log_success(f"Stylesheet '{stylesheet_name}' registered (ID: {xslt.id})")
        except Exception as e:
            log_error(f"Failed to create stylesheet '{stylesheet_name}': {e}")
            raise

    # Link stylesheets to template
    if xslt_map:
        try:
            # Check if TemplateXslRendering already exists
            try:
                rendering = template_xsl_rendering_api.get_by_template_id(template.id)
                log_info("Updating existing TemplateXslRendering...")
            except Exception:
                # Doesn't exist, create new
                rendering = None
                log_info("Creating TemplateXslRendering...")

            # Update or create the rendering configuration
            from core_main_app.components.template_xsl_rendering.models import (
                TemplateXslRendering,
            )

            if rendering:
                if "list" in xslt_map:
                    rendering.list_xslt = xslt_map["list"]
                    rendering.list_detail_xslt = [xslt_map["list"].id]
                if "detail" in xslt_map:
                    rendering.default_detail_xslt = xslt_map["detail"]
                rendering = template_xsl_rendering_api.upsert(rendering)
            else:
                rendering = TemplateXslRendering()
                rendering.template = template
                rendering.list_xslt = xslt_map.get("list")
                rendering.default_detail_xslt = xslt_map.get("detail")
                rendering.list_detail_xslt = [xslt_map["list"].id] if "list" in xslt_map else []
                rendering = template_xsl_rendering_api.upsert(rendering)

            log_success(f"Stylesheets linked to template (Rendering ID: {rendering.id})")

        except Exception as e:
            log_error(f"Failed to link stylesheets: {e}")
            import traceback
            traceback.print_exc()
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize NexusLIMS schema and XSLT templates"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-initialization even if template exists",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("NexusLIMS Schema Initialization")
    print("=" * 70)

    try:
        # Import CDCS APIs
        from core_main_app.components.template import api as template_api
        from core_main_app.components.template_version_manager import (
            api as template_version_manager_api,
        )
        from core_main_app.components.template_xsl_rendering import (
            api as template_xsl_rendering_api,
        )
        from core_main_app.components.xsl_transformation import (
            api as xsl_transformation_api,
        )

        log_success("Imports successful")

    except ImportError as e:
        log_error(
            f"Failed to import CDCS components: {e}\n"
            f"This script may need updates for CDCS 3.18.0 API changes"
        )
        sys.exit(1)

    try:
        from django.db import transaction

        with transaction.atomic():
            # Load and register the XSD schema
            template_vm = load_schema(
                template_api, template_version_manager_api, args.force
            )
            if template_vm is None:
                log_error("Failed to load schema")
                sys.exit(1)

            # Register XSLT stylesheets
            register_xslt_stylesheets(
                template_api,
                template_version_manager_api,
                xsl_transformation_api,
                template_xsl_rendering_api,
                template_vm,
                args.force,
            )

            print("=" * 70)
            log_success("Initialization complete!")
            print(f"  Template: {template_vm.title}")
            print("=" * 70)

    except Exception as e:
        log_error(f"Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
