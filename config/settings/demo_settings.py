"""
Demo settings for NexusLIMS-CDCS public demo deployment.

Extends prod_settings with demo-specific configuration:
- IS_PUBLIC_DEMO = True (enables auto-login, homepage hero, download warning)
- No email sending (dummy backend)
- Demo user whitelist for ?demo_as= URL param
"""

from config.settings.prod_settings import *  # noqa
import os

# Demo mode flag - gates all demo-specific behavior
IS_PUBLIC_DEMO = True

# Allow DEBUG to be controlled via environment variable (for local development)
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# No email sending in the demo
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Whitelist of usernames that can be selected via ?demo_as=<username>
DEMO_USERNAMES = ['admin', 'readonly_user', 'project_lead']

# Additional instrument color mappings for demo datasets
NX_INSTRUMENT_COLOR_MAPPINGS = {
    **NX_INSTRUMENT_COLOR_MAPPINGS,  # noqa: F821 - imported via prod_settings
    "TESCAN-FERA-FIB-SEM": "#4e6e8e",
    "FEI-Tecnai-TEM": "#b07d1a",
    "FEI-Quanta-SEM": "#d62728",
}

# Django 5.2 always wraps template loaders in CachedLoader regardless of DEBUG.
# When debugging locally, override to use uncached loaders so template edits are
# reflected immediately without restarting the container.
if DEBUG:
    TEMPLATES[0] = {  # noqa: F821
        **TEMPLATES[0],  # noqa: F821
        'APP_DIRS': False,  # must be False when 'loaders' is explicitly set
        'OPTIONS': {
            **TEMPLATES[0]['OPTIONS'],  # noqa: F821
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    }

# Auto-login middleware - insert after AuthenticationMiddleware
_demo_middleware = 'nexuslims_overrides.middleware.DemoAutoLoginMiddleware'
MIDDLEWARE = list(MIDDLEWARE)  # noqa: F821 - may be a tuple from base settings
if _demo_middleware not in MIDDLEWARE:
    try:
        _auth_idx = MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware')
        MIDDLEWARE.insert(_auth_idx + 1, _demo_middleware)
    except ValueError:
        MIDDLEWARE.append(_demo_middleware)

# Top bar links
NX_CUSTOM_MENU_LINKS = [
    {
        "title": "Datasophos",
        "url": "https://datasophos.co/",
        "icon": "globe",
        "iconClass": "fas"
    },
    {
        "title": "Github Repository",
        "url": "https://github.com/datasophos/NexusLIMS-CDCS",
        "icon": "github",
        "iconClass": "fab"
    }
]
