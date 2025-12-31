#!/usr/bin/env python
"""
Complete development environment initialization for NexusLIMS-CDCS.

This script handles:
1. Verifying database migrations are complete
2. Creating default superuser (if needed): username=admin, password=admin
3. Uploading NexusLIMS schema and XSLT templates

Usage:
    docker exec nexuslims_dev_cdcs python /scripts/init_dev_environment.py
    
Or via alias:
    dev-init

This is a convenience script that combines all setup steps. For more control,
use the individual commands: dev-superuser, dev-init-schema
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


def check_migrations():
    """Check if database migrations have been run."""
    log_info("Checking database migrations...")
    
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check if auth_user table exists
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'auth_user'
            """)
            result = cursor.fetchone()
            
            if result[0] == 0:
                log_error("Database migrations have not been run!")
                log_info("Please wait for the container to finish initializing.")
                log_info("Check initialization logs with: dev-logs-app")
                return False
            
            log_success("Database migrations are complete")
            return True
            
    except Exception as e:
        log_error(f"Failed to check migrations: {e}")
        return False


def get_or_create_superuser():
    """Get or create default superuser for development."""
    log_info("Checking for superuser...")
    
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Check if any superuser exists
    superuser = User.objects.filter(is_superuser=True).first()
    
    if superuser:
        log_success(f"Superuser already exists: {superuser.username}")
        return superuser
    
    # Create default superuser
    log_info("Creating default superuser (username: admin, password: admin)...")
    try:
        superuser = User.objects.create_superuser(
            username="admin",
            email="admin@localhost",
            password="admin"
        )
        log_success(f"Superuser created: {superuser.username}")
        return superuser
    except Exception as e:
        log_error(f"Failed to create superuser: {e}")
        raise


def get_request_for_user(user):
    """Create a mock request object for API calls."""
    from django.test import RequestFactory
    
    factory = RequestFactory()
    request = factory.get("/")
    request.user = user
    return request


def upload_schema(request):
    """Upload NexusLIMS schema template."""
    log_info("Uploading NexusLIMS schema...")
    
    from core_main_app.components.template import api as template_api
    from core_main_app.components.template.models import Template
    from core_main_app.components.template_version_manager import (
        api as template_version_manager_api,
    )
    from core_main_app.components.template_version_manager.models import (
        TemplateVersionManager,
    )
    
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
        log_success(f"Template '{template_title}' already exists")
        return existing_tvm
    except Exception:
        # Template doesn't exist, create it
        pass
    
    # Create the template
    try:
        # First create the template instance (without version manager)
        template = Template()
        template.filename = "nexus-experiment.xsd"
        template.content = schema_content
        template.hash = hashlib.sha1(schema_content.encode("utf-8")).hexdigest()
        
        # Save the template first to get an ID
        template = template_api.upsert(template, request=request)
        
        # Create TemplateVersionManager with the template
        template_vm = TemplateVersionManager()
        template_vm.title = template_title
        template_vm.user = None  # None makes it a global template
        template_vm.is_disabled = False
        
        # Insert requires (template_version_manager, template, request)
        template_vm = template_version_manager_api.insert(
            template_vm, 
            template=template,
            request=request
        )
        
        # Link template back to version manager and save
        template.version_manager = template_vm
        template = template_api.upsert(template, request=request)
        
        log_success(f"Template '{template_title}' created (ID: {template.id})")
        return template_vm
        
    except Exception as e:
        log_error(f"Failed to create template: {e}")
        import traceback
        traceback.print_exc()
        raise


def upload_xslt_stylesheets(request, template_vm):
    """Upload XSLT stylesheets for the template."""
    log_info("Uploading XSLT stylesheets...")
    
    from core_main_app.components.template import api as template_api
    from core_main_app.components.xsl_transformation import (
        api as xsl_transformation_api,
    )
    from core_main_app.components.xsl_transformation.models import (
        XslTransformation,
    )
    from core_main_app.components.template_xsl_rendering import (
        api as template_xsl_rendering_api,
    )
    from core_main_app.components.template_xsl_rendering.models import (
        TemplateXslRendering,
    )
    
    # Get the current template
    template = template_api.get_by_id(template_vm.current, request=request)
    
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
            log_success(f"Stylesheet '{stylesheet_name}' already exists")
            xslt_map[stylesheet_type] = existing_xslt
            continue
        except Exception:
            pass
        
        # Read and create stylesheet
        with stylesheet_path.open(encoding="utf-8") as f:
            stylesheet_content = f.read()
        
        try:
            xslt = XslTransformation()
            xslt.name = stylesheet_name
            xslt.filename = stylesheet_name
            xslt.content = stylesheet_content
            xslt = xsl_transformation_api.upsert(xslt)
            xslt_map[stylesheet_type] = xslt
            log_success(f"Stylesheet '{stylesheet_name}' created (ID: {xslt.id})")
        except Exception as e:
            log_error(f"Failed to create stylesheet '{stylesheet_name}': {e}")
            raise
    
    # Link stylesheets to template
    if xslt_map:
        try:
            # Check if TemplateXslRendering already exists
            try:
                rendering = template_xsl_rendering_api.get_by_template_id(template.id)
                log_success("XSLT rendering already configured")
            except Exception:
                # Create new rendering configuration using the API
                list_detail_xslt_ids = [xslt_map["list"].id] if "list" in xslt_map else []
                
                rendering = template_xsl_rendering_api.upsert(
                    template=template,
                    list_xslt=xslt_map.get("list"),
                    default_detail_xslt=xslt_map.get("detail"),
                    list_detail_xslt=list_detail_xslt_ids
                )
                log_success(f"XSLT rendering configured (ID: {rendering.id})")
        except Exception as e:
            log_error(f"Failed to configure XSLT rendering: {e}")
            raise


def main():
    """Main entry point."""
    print("=" * 70)
    print("NexusLIMS Development Environment Initialization")
    print("=" * 70)
    
    try:
        from django.db import transaction
        
        # Step 1: Check migrations
        if not check_migrations():
            sys.exit(1)
        
        # Step 2: Get or create superuser
        superuser = get_or_create_superuser()
        request = get_request_for_user(superuser)
        
        # Step 3: Upload schema and stylesheets
        with transaction.atomic():
            template_vm = upload_schema(request)
            if template_vm:
                upload_xslt_stylesheets(request, template_vm)
        
        print("=" * 70)
        log_success("Initialization complete!")
        print(f"  Superuser: {superuser.username}")
        if template_vm:
            print(f"  Template: {template_vm.title}")
        print()
        print("You can now:")
        print("  - Access the site: https://nexuslims-dev.localhost")
        print("  - Login with: admin / admin")
        print("  - Start uploading data using the Nexus Experiment Schema")
        print("=" * 70)
        
    except Exception as e:
        log_error(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
