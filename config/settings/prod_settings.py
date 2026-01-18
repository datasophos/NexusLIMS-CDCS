"""
Production settings for NexusLIMS-CDCS.

This module extends the base MDCS settings with production-specific configuration.
"""

from mdcs.settings import *  # noqa
import os

# Security
DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

# Database - use environment variables
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "NAME": os.getenv("POSTGRES_DB", "nexuslims"),
        "USER": os.getenv("POSTGRES_USER", "nexuslims"),
        "PASSWORD": os.getenv("POSTGRES_PASS", ""),
    }
}

# Redis - use environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASS", "")

# Add config/static_files for deployment-specific custom assets
# This allows users to place custom logos and images in config/static_files
# without modifying the base applicaiton code
STATICFILES_DIRS = [
    "static",  # Base static directory from mdcs
    "/srv/nexuslims/config/static_files",  # Custom deployment assets
]

# Static files
STATIC_ROOT = "/srv/nexuslims/static.prod"
STATIC_URL = "/static/"

# Media files
MEDIA_ROOT = "/srv/nexuslims/media"
MEDIA_URL = "/media/"

# Session & Cache configuration
# NexusLIMS Production Enhancement: Redis-backed sessions and caching
#
# Deviation from base MDCS:
# - Base MDCS uses Django's default LocMemCache (in-memory, single process)
# - We use Redis for production because:
#   1. Sessions persist across container restarts (important for deployments)
#   2. Cache is shared across multiple app instances (enables horizontal scaling)
#   3. Better performance than database-backed sessions
#   4. Atomic operations for session data
#
# Trade-off: Adds Redis as a required dependency (already needed for Celery)
# Requires: django-redis package (see requirements.txt)
#
# To disable Redis caching: Comment out the CACHES block below and uncomment
# the alternative configuration. You should also switch to database-backed sessions.

# Option 1: Redis-backed cache (default, recommended)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Option 2: Database-backed sessions with in-memory cache (fallback)
# Use this if you don't want to use django-redis or Redis is unavailable
# Note: Sessions will persist, but cache is per-process (not shared)
#
# SESSION_ENGINE = "django.contrib.sessions.backends.db"
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "unique-snowflake",
#     }
# }

# Security settings
SECURE_SSL_REDIRECT = False  # Caddy handles SSL termination
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# NexusLIMS customizations
from nexuslims_overrides.settings import *  # noqa

# Production-specific NexusLIMS settings
NX_XSLT_DEBUG = False
NX_ENABLE_TUTORIALS = True

# To limit access to the API docs to logged in users, uncomment the following lines:
# SPECTACULAR_SETTINGS.update({
#     "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
# })

# ============================================================================
# API AUTHENTICATION
# ============================================================================

# Admin API token for production (set via environment variable)
# Set NX_ADMIN_API_TOKEN in your environment to create/update the admin user's token
# If not set, no token will be auto-created (you'll need to create one manually)
NX_ADMIN_API_TOKEN = os.getenv("NX_ADMIN_API_TOKEN", None)
