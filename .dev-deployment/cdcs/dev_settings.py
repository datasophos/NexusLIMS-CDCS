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

NX_DOCUMENTATION_LINK = "https://examplechanged.com"
# NX_HOMEPAGE_TEXT = "dev_settings HOMEPAGE_TEXT content."
