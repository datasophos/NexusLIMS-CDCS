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

# Static files
STATIC_ROOT = "/srv/curator/static.prod"
STATIC_URL = "/static/"

# Media files
MEDIA_ROOT = "/srv/curator/media"
MEDIA_URL = "/media/"

# Session & Cache configuration
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
NX_ENABLE_TUTORIALS = False  # Disable tutorials in production
