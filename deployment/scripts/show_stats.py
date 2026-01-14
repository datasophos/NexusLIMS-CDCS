#!/usr/bin/env python3
"""
Show NexusLIMS-CDCS system statistics.
"""

import os
import sys

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev_settings"))
sys.path.insert(0, "/srv/nexuslims")
import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from core_main_app.components.template import api as template_api
from core_main_app.components.data import api as data_api
from core_main_app.components.xsl_transformation import api as xsl_transformation_api

# Create a request object with superuser permissions for API calls
User = get_user_model()
superuser = User.objects.filter(is_superuser=True).first()

if superuser:
    factory = RequestFactory()
    request = factory.get("/")
    request.user = superuser
else:
    request = None
    print("⚠️  Warning: No superuser found. Some statistics may be unavailable.")
    print()

print("=" * 60)
print("NexusLIMS-CDCS System Statistics")
print("=" * 60)
print()

# Users
User = get_user_model()
total_users = User.objects.count()
active_users = User.objects.filter(is_active=True).count()
superusers = User.objects.filter(is_superuser=True).count()

print("👥 Users:")
print(f"  Total:      {total_users}")
print(f"  Active:     {active_users}")
print(f"  Superusers: {superusers}")
print()

# Templates
try:
    if request:
        templates = template_api.get_all(request=request)
        print("📋 Templates:")
        print(f"  Total: {len(templates)}")
        for template in templates:
            print(f"    - {template.display_name or template.filename}")
        print()
    else:
        print("  ⚠️  Cannot retrieve templates: No superuser available")
        print()
except Exception as e:
    print(f"  ⚠️  Could not retrieve templates: {e}")
    print()

# Data records
try:
    if superuser:
        records = data_api.get_all(superuser)
        print("📄 Data Records:")
        print(f"  Total: {len(records)}")
        print()
    else:
        print("  ⚠️  Cannot retrieve records: No superuser available")
        print()
except Exception as e:
    print(f"  ⚠️  Could not retrieve records: {e}")
    print()

# XSLT Stylesheets
try:
    xslts = xsl_transformation_api.get_all()
    print("🎨 XSLT Stylesheets:")
    print(f"  Total: {len(xslts)}")
    for xslt in xslts:
        print(f"    - {xslt.name}")
    print()
except Exception as e:
    print(f"  ⚠️  Could not retrieve XSLTs: {e}")
    print()

print("=" * 60)
