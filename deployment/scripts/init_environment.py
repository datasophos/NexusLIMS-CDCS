#!/usr/bin/env python
"""
Complete environment initialization for NexusLIMS-CDCS.

This script handles:
1. Verifying database migrations are complete
2. Creating default superuser (if needed)
   - Development: username=admin, password=admin
   - Production: prompts for credentials (or skips if exists)
3. Creating default regular user (development only): username=user, password=user
4. Setting up API authentication tokens
   - Development: Creates fixed token from NX_DEV_API_TOKEN setting
   - Production: Creates token from NX_ADMIN_API_TOKEN environment variable
5. Compiling Django message translations ("label" and "record", controlled by locale/en/LC_MESSAGES/django.po)
6. Configuring anonymous group permissions for explore keyword app
7. Uploading NexusLIMS schema and XSLT templates
8. Loading exporters

Usage:
    Development:
        Runs automatically on container startup (see docker-compose.dev.yml)
        Manual run: docker exec nexuslims_dev_cdcs python /srv/scripts/init_environment.py

    Production:
        docker exec nexuslims_prod_cdcs python /srv/scripts/init_environment.py
        Or via alias (after sourcing admin-commands.sh):
            admin-init

Environment Detection:
    Automatically detects environment from DJANGO_SETTINGS_MODULE:
    - config.settings.dev_settings -> Development mode
    - config.settings.prod_settings -> Production mode
"""

import hashlib
import os
import sys
from pathlib import Path

# Set up Django environment
# Use DJANGO_SETTINGS_MODULE from environment, or fall back to config.settings.dev_settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev_settings"))
sys.path.insert(0, "/srv/nexuslims")

import django

django.setup()

# Suppress verbose logging from core_main_app
import logging
logging.getLogger("core_main_app").setLevel(logging.ERROR)


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


def is_production():
    """Check if running in production environment.

    Works with custom_settings by checking Django's DEBUG setting.
    Production = DEBUG is False.
    """
    from django.conf import settings
    return not settings.DEBUG


def is_development():
    """Check if running in development environment.

    Works with custom_settings by checking Django's DEBUG setting.
    Development = DEBUG is True.
    """
    from django.conf import settings
    return settings.DEBUG


def is_demo():
    """Check if running in public demo mode."""
    from django.conf import settings
    return getattr(settings, 'IS_PUBLIC_DEMO', False)


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
    """Get or create superuser."""
    log_info("Checking for superuser...")

    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    User = get_user_model()

    # Check if any superuser exists
    superuser = User.objects.filter(is_superuser=True).first()

    if superuser:
        log_success(f"Superuser already exists: {superuser.username}")
        return superuser

    # Production: Use Django's createsuperuser command (interactive)
    if is_production():
        log_info("No superuser found. Creating superuser (you will be prompted for credentials)...")
        try:
            call_command('createsuperuser')
            # Fetch the newly created superuser
            superuser = User.objects.filter(is_superuser=True).first()
            if superuser:
                log_success(f"Superuser created: {superuser.username}")
                return superuser
            else:
                log_warning("Superuser creation skipped or failed")
                return None
        except Exception as e:
            log_error(f"Failed to create superuser: {e}")
            log_warning("Continuing initialization without superuser")
            return None

    # Development: Create default superuser automatically
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


def get_or_create_regular_user():
    """Get or create default regular user for testing (development only)."""
    # Skip in production
    if is_production():
        return None

    log_info("Checking for regular test user...")

    from django.contrib.auth import get_user_model

    User = get_user_model()

    # Check if regular user exists
    regular_user = User.objects.filter(username="user").first()

    if regular_user:
        log_success(f"Regular user already exists: {regular_user.username}")
        return regular_user

    # Create default regular user
    log_info("Creating default regular user (username: user, password: user)...")
    try:
        regular_user = User.objects.create_user(
            username="user",
            email="user@localhost",
            password="user"
        )
        log_success(f"Regular user created: {regular_user.username}")
        return regular_user
    except Exception as e:
        log_error(f"Failed to create regular user: {e}")
        raise


def get_or_create_demo_users():
    """Create demo accounts for the public demo (idempotent).

    Creates three accounts:
      - admin / admin          (superuser, all permissions)
      - readonly_user / readonly  (view only - anonymous-level perms)
      - project_lead / lead    (can create/edit records)
    """
    if not is_demo():
        return

    log_info("Setting up demo user accounts...")

    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Permission

    User = get_user_model()

    # --- admin (superuser) ---
    admin = User.objects.filter(username="admin").first()
    if admin:
        log_success("Demo user already exists: admin")
    else:
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@demo.nexuslims",
            password="admin",
        )
        log_success("Demo user created: admin (superuser)")

    # --- readonly_user ---
    readonly = User.objects.filter(username="readonly_user").first()
    if readonly:
        log_success("Demo user already exists: readonly_user")
    else:
        readonly = User.objects.create_user(
            username="readonly_user",
            email="readonly@demo.nexuslims",
            password="readonly",
        )
        log_success("Demo user created: readonly_user (view-only)")

    # --- project_lead (can add/change records) ---
    lead = User.objects.filter(username="project_lead").first()
    if lead:
        log_success("Demo user already exists: project_lead")
    else:
        lead = User.objects.create_user(
            username="project_lead",
            email="lead@demo.nexuslims",
            password="lead",
        )
        log_success("Demo user created: project_lead")

    # Grant project_lead add/change data permissions
    data_perms = Permission.objects.filter(
        codename__in=["add_data", "change_data"],
        content_type__app_label="core_main_app",
    )
    if data_perms.exists():
        lead.user_permissions.set(data_perms)
        log_success(f"Granted project_lead permissions: {', '.join(p.codename for p in data_perms)}")
    else:
        log_warning("core_main_app data permissions not found yet - project_lead will have default perms")


def get_request_for_user(user):
    """Create a mock request object for API calls."""
    from django.test import RequestFactory

    factory = RequestFactory()
    request = factory.get("/")
    request.user = user
    return request


def grant_anonymous_explore_permission():
    """
    Grant the anonymous group permission to access explore keyword app.

    NOTE: This is now handled by the Django migration:
    nexuslims_overrides/migrations/0002_grant_anonymous_explore_permission.py

    This function is kept for backwards compatibility with existing deployments
    that may not have run the migration yet.
    """
    log_info("Checking anonymous group permissions...")

    from django.contrib.auth.models import Group, Permission

    try:
        # Check if permission is already granted
        anonymous_group = Group.objects.filter(name='anonymous').first()
        if not anonymous_group:
            log_info("Anonymous group not found - will be created by migration")
            return

        permission = Permission.objects.filter(codename='access_explore_keyword').first()
        if not permission:
            log_info("Explore permission not found yet - will be handled by migration")
            return

        if anonymous_group.permissions.filter(codename='access_explore_keyword').exists():
            log_success("Anonymous group already has explore permission (from migration)")
        else:
            # Grant it if not already there (fallback for pre-migration deployments)
            anonymous_group.permissions.add(permission)
            log_success("Granted explore permission to anonymous group")

    except Exception as e:
        log_warning(f"Could not check permissions: {e}")
        log_info("This is handled by migrations, so no action needed")


def upload_schema(request, schema_path=None):
    """Upload NexusLIMS schema template.

    Args:
        request: Django request object
        schema_path: Optional path to schema file. If not provided, uses default location.
    """
    log_info("Uploading NexusLIMS schema...")

    from django.db import IntegrityError
    from core_main_app.components.template import api as template_api
    from core_main_app.components.template.models import Template
    from core_main_app.components.template_version_manager import (
        api as template_version_manager_api,
    )
    from core_main_app.components.template_version_manager.models import (
        TemplateVersionManager,
    )

    # Default schema path (mounted from deployment/schemas/)
    if schema_path is None:
        schema_path = Path("/srv/nexuslims/schemas/nexus-experiment.xsd")
    else:
        schema_path = Path(schema_path)

    if not schema_path.exists():
        log_warning(f"Schema file not found at {schema_path}")
        if is_production():
            log_info("In production, upload your schema via the web interface:")
            log_info("  1. Login as superuser")
            log_info("  2. Navigate to: Curator > Template > Upload Schema")
            log_info("  3. Upload the nexus-experiment.xsd schema file")
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

    except IntegrityError as e:
        # Template already exists (race condition or duplicate)
        log_info("Template already exists, fetching existing template...")
        try:
            existing_tvm = template_version_manager_api.get_active_global_version_manager_by_title(
                template_title, request=request
            )
            log_success(f"Template '{template_title}' found")
            return existing_tvm
        except Exception as fetch_error:
            log_error(f"Failed to fetch existing template: {fetch_error}")
            return None
    except Exception as e:
        # Check if it's a NotUniqueError (CDCS wraps IntegrityError)
        error_str = str(e)
        if "duplicate key" in error_str or "already exists" in error_str.lower():
            log_info("Template already exists, fetching existing template...")
            try:
                existing_tvm = template_version_manager_api.get_active_global_version_manager_by_title(
                    template_title, request=request
                )
                log_success(f"Template '{template_title}' found")
                return existing_tvm
            except Exception as fetch_error:
                log_error(f"Failed to fetch existing template: {fetch_error}")
                return None
        else:
            # Unexpected error - show details
            log_error(f"Failed to create template: {e}")
            import traceback
            traceback.print_exc()
            # Don't raise - let the script continue
            return None


def upload_example_records(request, template_vm):
    """Upload example records associated with the schema (development only)."""
    # Skip in production
    if is_production():
        return None

    log_info("Uploading example records...")

    from core_main_app.components.data import api as data_api
    from core_main_app.components.workspace import api as workspace_api
    from core_main_app.components.data.models import Data

    record_paths = [
        Path("/srv/test-data/example_record.xml"),
        Path("/srv/test-data/example_record_large.xml")
    ]
    uploaded = []
    for record_path in record_paths:
        if not record_path.exists():
            log_warning(f"Example record not found at {record_path}")
            return None

        try:
            # Generate the title for this record
            title = record_path.name.replace("_", " ").replace(".xml", "").capitalize()

            # Check if this record already exists
            existing_record = Data.objects.filter(title=title).first()
            if existing_record:
                log_success(f"Example record '{title}' already exists (ID: {existing_record.id})")
                uploaded.append(existing_record)
                continue

            # Read the example record
            with record_path.open(encoding="utf-8") as f:
                record_content = f.read()

            # Get the current template
            from core_main_app.components.template import api as template_api
            template = template_api.get_by_id(template_vm.current, request=request)

            # Create the data record
            data_record = Data(
                template=template,
                title=title
            )

            # Set the content and user
            # NOTE: Use 'content' not 'xml_content' so convert_to_dict() works
            data_record.content = record_content
            data_record.user_id = request.user.id

            # Save the data record (this will populate dict_content via convert_to_dict())
            data_record = data_api.upsert(data_record, request=request)

            log_success(f"Example record uploaded (ID: {data_record.id}, title: {data_record.title})")

            # Get or create the global public workspace
            try:
                public_workspace = workspace_api.get_global_workspace()
            except Exception:
                # If no global workspace exists, create one
                log_warning("Global workspace not found, creating one...")
                try:
                    public_workspace = workspace_api.create_and_get_global_workspace()
                except Exception as ws_error:
                    log_warning(f"Could not create global workspace: {ws_error}")
                    return data_record

            # Assign record to the public workspace
            data_record.workspace = public_workspace
            data_record = data_api.upsert(data_record, request=request)
            uploaded.append(data_record)
            log_success(f"Example record assigned to global public workspace")

        except Exception as e:
            log_error(f"Failed to upload example record: {e}")
            import traceback
            traceback.print_exc()
            # Don't raise - let the script continue
            return None

    return uploaded


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

    stylesheet_dir = Path("/srv/nexuslims/xslt")
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

        # Patch URLs for file serving
        # Get URLs from environment variables
        dataset_base_url = os.getenv(
            "XSLT_DATASET_BASE_URL",
            "https://files.nexuslims-dev.localhost/instrument-data"
        )
        preview_base_url = os.getenv(
            "XSLT_PREVIEW_BASE_URL",
            "https://files.nexuslims-dev.localhost/data"
        )

        log_info(f"Patching URLs in {stylesheet_name}...")
        log_info(f"  datasetBaseUrl: {dataset_base_url}")
        log_info(f"  previewBaseUrl: {preview_base_url}")

        # Perform replacements
        stylesheet_content = stylesheet_content.replace(
            '<xsl:variable name="datasetBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>',
            f'<xsl:variable name="datasetBaseUrl">{dataset_base_url}</xsl:variable>'
        )
        stylesheet_content = stylesheet_content.replace(
            '<xsl:variable name="previewBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>',
            f'<xsl:variable name="previewBaseUrl">{preview_base_url}</xsl:variable>'
        )

        # Verify replacements
        if dataset_base_url in stylesheet_content:
            log_success("  ✓ datasetBaseUrl patched")
        else:
            log_warning("  ✗ datasetBaseUrl patch failed or not found")

        if preview_base_url in stylesheet_content:
            log_success("  ✓ previewBaseUrl patched")
        else:
            log_warning("  ✗ previewBaseUrl patch failed or not found")

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
            # Don't raise - try to continue with what we have
            continue

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
            log_warning("Continuing without XSLT rendering configuration")
            # Don't raise - let the script continue


def compile_translations():
    """Compile Django translation files."""
    log_info("Compiling translations...")

    try:
        from django.core.management import call_command
        call_command('compilemessages', verbosity=0)
        log_success("Translations compiled successfully")
    except Exception as e:
        log_error(f"Failed to compile translations: {e}")
        # Don't raise - let the script continue


def setup_api_tokens(superuser):
    """
    Create or update API tokens for the superuser based on environment settings.

    In development: Uses NX_DEV_API_TOKEN setting (fixed token for testing)
    In production: Uses NX_ADMIN_API_TOKEN setting (from environment variable)

    Args:
        superuser: User object for which to create/update token
    """
    if superuser is None:
        log_warning("No superuser provided - skipping API token setup")
        return

    from django.conf import settings
    from rest_framework.authtoken.models import Token

    log_info("Checking API token configuration...")

    # Determine which token setting to use based on environment
    if is_development():
        token_value = getattr(settings, 'NX_DEV_API_TOKEN', None)
        token_name = "development"
    else:
        token_value = getattr(settings, 'NX_ADMIN_API_TOKEN', None)
        token_name = "production admin"

    if not token_value:
        log_info(f"No {token_name} API token configured - skipping token setup")
        if is_development():
            log_info("To configure: Set NX_DEV_API_TOKEN in config/settings/dev_settings.py")
        else:
            log_info("To configure: Set NX_ADMIN_API_TOKEN environment variable in .env")
        return

    # Check if token already exists for this user
    try:
        existing_token = Token.objects.get(user=superuser)

        # If token key matches, we're done
        if existing_token.key == token_value:
            log_success(f"{token_name.capitalize()} API token already exists for user '{superuser.username}'")
            return

        # Token exists but key is different - delete and recreate
        existing_token.delete()
        log_info(f"Removed existing token with different key for user '{superuser.username}'")
    except Token.DoesNotExist:
        # No existing token, will create new one
        pass

    # Create new token with desired key
    Token.objects.create(user=superuser, key=token_value)
    log_success(f"Created {token_name} API token for user '{superuser.username}'")


def setup_terms_of_use():
    """Insert a default Terms of Use page if none exists.

    The content is stored as a WebPage record in the database and can be
    updated at any time through the admin UI at:
        /admin/core-admin/core_website_app_terms
    """
    log_info("Checking Terms of Use page...")

    try:
        from core_main_app.components.web_page.models import WebPage
        from core_website_app.commons.enums import WEB_PAGE_TYPES

        t = WEB_PAGE_TYPES["terms_of_use"]

        # If any non-empty record exists, leave it alone so admins can customise freely
        pages = WebPage.objects.filter(type=t)
        if pages.filter(content__regex=r'\S').exists():
            log_success("Terms of Use page already exists")
            return

        # Clean up any empty/blank records before inserting
        pages.delete()

    except Exception:
        pass  # No record yet -- fall through to create one

    default_content = """
<p>
  These Terms of Use govern your access to and use of this NexusLIMS instance.
  By accessing this site you agree to the terms below. The system administrator
  may update these terms at any time; continued use of the system after changes
  are posted constitutes acceptance of the revised terms.
</p>

<h5>1. Authorised Use</h5>
<p>Access to this system is granted solely for legitimate scientific research,
data management, and analysis activities consistent with the mission of the
operating institution. You must not use the system for any unlawful purpose
or in any way that disrupts the availability of the service for other users.</p>

<h5>2. User Accounts</h5>
<p>You are responsible for maintaining the confidentiality of your login
credentials and for all activity that occurs under your account. Notify the
system administrator immediately if you suspect unauthorised access.
Accounts that have been inactive for an extended period may be suspended
at the discretion of the administrator.</p>

<h5>3. Data and Intellectual Property</h5>
<p>You retain ownership of any data you upload. By uploading data you grant
the system the right to store, process, and display that data as necessary
to provide the service. You are responsible for ensuring that you have the
right to upload and share any data you submit, and that doing so does not
violate applicable laws or third-party agreements.</p>

<h5>4. Acceptable Data Standards</h5>
<p>Uploaded records should conform to the NexusLIMS schema and represent
genuine experimental data. Falsification, fabrication, or misrepresentation
of research data is a serious violation and may result in account suspension
and referral to institutional authorities.</p>

<h5>5. Privacy</h5>
<p>This system may collect information about your usage (such as login times
and records accessed) for administrative and audit purposes. This information
is not shared with third parties except as required by law or institutional
policy.</p>

<h5>6. Disclaimer of Warranties</h5>
<p>This system is provided &ldquo;as is&rdquo; without warranty of any kind. The operating
institution makes no guarantees regarding uptime, data integrity, or fitness
for a particular purpose. Users are encouraged to maintain independent
backups of critical data.</p>

<h5>7. Limitation of Liability</h5>
<p>To the fullest extent permitted by applicable law, the operating institution
shall not be liable for any indirect, incidental, or consequential damages
arising from your use of or inability to use this system.</p>

<h5>8. Contact</h5>
<p>Questions about these terms or your account should be directed to the
system administrator via the <a href="/contact/">contact page</a>.</p>
"""

    try:
        from core_main_app.components.web_page.models import WebPage
        from core_website_app.commons.enums import WEB_PAGE_TYPES
        from core_website_app.components.terms_of_use import api as terms_api

        page = WebPage()
        page.type = WEB_PAGE_TYPES["terms_of_use"]
        page.content = default_content.strip()
        terms_api.upsert(page)
        log_success("Default Terms of Use page created")
        log_info("  Update it any time at: /admin/core-admin/core_website_app_terms")

    except Exception as e:
        log_error(f"Failed to create Terms of Use page: {e}")


def load_exporters():
    """Load the exporters into the database."""
    log_info("Loading exporters...")

    try:
        from core_exporters_app.components.exporter import api as exporter_api

        # Check if exporters already exist
        existing_exporters = exporter_api.get_all()
        if len(existing_exporters) > 0:
            log_info(f"Exporters already loaded ({len(existing_exporters)} found)")

            # Remove BLOB exporter if it exists (NexusLIMS doesn't use blobs)
            blob_exporters = [exp for exp in existing_exporters if exp.name.upper() == 'BLOB']
            if blob_exporters:
                for blob_exp in blob_exporters:
                    blob_exp.delete()
                    log_info(f"Removed BLOB exporter (ID: {blob_exp.id})")

                remaining = exporter_api.get_all()
                log_success(f"Exporters configured: {', '.join(exp.name for exp in remaining)}")
            else:
                log_success(f"Exporters configured: {', '.join(exp.name for exp in existing_exporters)}")
            return

        # Load exporters using Django management command
        from django.core.management import call_command
        call_command('loadexporters')

        # Remove BLOB exporter (NexusLIMS doesn't use blobs)
        all_exporters = exporter_api.get_all()
        blob_exporters = [exp for exp in all_exporters if exp.name.upper() == 'BLOB']
        if blob_exporters:
            for blob_exp in blob_exporters:
                blob_exp.delete()
                log_info(f"Removed BLOB exporter (ID: {blob_exp.id})")

        # Verify final state
        exporters = exporter_api.get_all()
        log_success(f"Loaded {len(exporters)} exporters: {', '.join(exp.name for exp in exporters)}")

    except Exception as e:
        log_error(f"Failed to load exporters: {e}")
        # Don't raise - let the script continue


def main():
    """Main entry point."""
    import argparse

    # Parse command line arguments for schema path (production use)
    parser = argparse.ArgumentParser(description="Initialize NexusLIMS-CDCS environment")
    parser.add_argument(
        "--schema",
        help="Path to schema file (e.g., /tmp/nexus-experiment.xsd)",
        default=None
    )
    args = parser.parse_args()

    env_name = "Production" if is_production() else "Development"
    print("=" * 70)
    print(f"NexusLIMS-CDCS {env_name} Environment Initialization")
    print("=" * 70)

    try:
        # Step 1: Check migrations
        if not check_migrations():
            log_warning("Skipping initialization - migrations not complete")
            return

        # Step 1.5: Compile translations
        compile_translations()

        # Step 2: Get or create superuser
        superuser = get_or_create_superuser()

        # If no superuser was created (production, user skipped), try to get any existing user
        if superuser is None:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Try to get first superuser or first user
            superuser = User.objects.filter(is_superuser=True).first() or User.objects.first()

        # Create request object for API calls (may be None if no users exist)
        request = get_request_for_user(superuser) if superuser else None

        # Step 2.5: Get or create regular user for testing (development only)
        regular_user = get_or_create_regular_user()

        # Step 2.6: Create demo accounts (demo mode only)
        get_or_create_demo_users()

        # Step 2.7: Setup API tokens based on environment settings
        setup_api_tokens(superuser)

        # Step 3: Configure anonymous group permissions
        grant_anonymous_explore_permission()

        # Step 4: Upload schema and stylesheets (no transaction - handle errors gracefully)
        # Only proceed if we have a request object
        if request:
            template_vm = upload_schema(request, schema_path=args.schema)
            if template_vm:
                upload_xslt_stylesheets(request, template_vm)
                # Example records only in development
                upload_example_records(request, template_vm)
        else:
            log_warning("No user available - skipping schema upload")
            log_info("Please run this script again after creating a superuser")
            template_vm = None

        # Step 5: Load exporters
        load_exporters()

        # Step 6: Set up default Terms of Use page
        setup_terms_of_use()

        print("=" * 70)
        log_success("Initialization complete!")

        # Environment-specific success messages
        if is_production():
            if superuser:
                print(f"  Superuser: {superuser.username}")
            if template_vm:
                print(f"  Schema: {template_vm.title}")
            print()
            print("Next steps:")
            print(f"  1. Access the site: {os.getenv('SERVER_URI', 'https://nexuslims.example.com')}")
            if superuser:
                print(f"  2. Login with your superuser credentials")
            print(f"  3. Begin uploading data records via the NexusLIMS backend")
            print(f"  4. Explore data: {os.getenv('SERVER_URI', 'https://nexuslims.example.com')}/explore/keyword/")
            print(f"  5. As an admin, you can manually add records at {os.getenv('SERVER_URI', 'https://nexuslims.example.com')}/curate/")
        else:
            if superuser:
                print(f"  Superuser: {superuser.username}")
            if regular_user:
                print(f"  Regular user: {regular_user.username}")
            if template_vm:
                print(f"  Template: {template_vm.title}")
            print()
            print("You can now:")
            print("  - Access the site: https://nexuslims-dev.localhost")
            print("  - Login with: admin / admin")
            if regular_user:
                print("  - Login with: user / user (regular user for testing)")
            print("  - View example record: https://nexuslims-dev.localhost/data?id=1")
            print("  - Explore data: https://nexuslims-dev.localhost/explore/keyword/")
            print("  - Start uploading data using the Nexus Experiment Schema or at https://nexuslims-dev.localhost/curate")

        print("=" * 70)

    except Exception as e:
        log_error(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        log_warning("Continuing despite errors...")


if __name__ == "__main__":
    main()
