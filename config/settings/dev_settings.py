"""
Development settings for NexusLIMS-CDCS
Extends the main settings.py with development-specific configurations
"""

from mdcs.settings import *

# Override DEBUG for development
DEBUG = True

# Development-specific logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Allow all hosts in development (restricted by Docker network)
ALLOWED_HOSTS = ['*']

# Development-specific CORS settings (if needed)
# CORS_ALLOW_ALL_ORIGINS = True

# Add config/static_files for deployment-specific custom assets
# This allows users to place custom logos and images in config/static_files
# without modifying the base applicaiton code
STATICFILES_DIRS = [
    "static",  # Base static directory from mdcs
    "/srv/nexuslims/config/static_files",  # Custom deployment assets
]

# NX_DOCUMENTATION_LINK = "https://examplechanged.com"
# NX_HOMEPAGE_TEXT = "dev_settings HOMEPAGE_TEXT content."
# NX_FOOTER_LINK = "https://example.com"
NX_CUSTOM_MENU_LINKS = [
    {"title": "LINK 1", "url": "https://datasophos.co", "icon": "anchor"},
    # {"title": "LINK 2", "url": "https://example.com", "icon": "fish"},
    # {"title": "LINK 3", "url": "https://example.com", "icon": "users"},
]
NX_ENABLE_TUTORIALS = True
# NX_NAV_LOGO = "nexuslims/img/nav_logo.png"

# ============================================================================
# API AUTHENTICATION
# ============================================================================

# Fixed API token for development/testing (DO NOT USE IN PRODUCTION)
# This token will be auto-created for the 'admin' user
# this token cannot be larger than 40 characters
NX_DEV_API_TOKEN = "nexuslims-dev-token-not-for-production"
