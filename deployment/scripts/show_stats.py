#!/usr/bin/env python3
"""
Show NexusLIMS-CDCS system statistics.
"""

import os
import sys

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev_settings"))
sys.path.insert(0, "/srv/curator")
import django
django.setup()

from django.contrib.auth import get_user_model
from core_main_app.components.template import api as template_api
from core_main_app.components.data import api as data_api
from core_main_app.components.blob import api as blob_api
from core_main_app.components.xsl_transformation import api as xsl_transformation_api

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
    templates = template_api.get_all()
    print("📋 Templates:")
    print(f"  Total: {len(templates)}")
    for template in templates:
        print(f"    - {template.display_name or template.filename}")
    print()
except Exception as e:
    print(f"  ⚠️  Could not retrieve templates: {e}")
    print()

# Data records
try:
    records = data_api.get_all()
    print("📄 Data Records:")
    print(f"  Total: {len(records)}")
    print()
except Exception as e:
    print(f"  ⚠️  Could not retrieve records: {e}")
    print()

# Blobs
try:
    blobs = blob_api.get_all()
    total_size = sum(blob.blob.size for blob in blobs if hasattr(blob, 'blob'))
    print("📎 Blobs:")
    print(f"  Total:      {len(blobs)}")
    print(f"  Total size: {total_size / (1024*1024):.2f} MB")
    print()
except Exception as e:
    print(f"  ⚠️  Could not retrieve blobs: {e}")
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
