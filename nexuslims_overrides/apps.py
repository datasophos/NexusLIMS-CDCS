"""
NexusLIMS Overrides App Configuration
"""
from django.apps import AppConfig


class NexusLIMSOverridesConfig(AppConfig):
    """Configuration for NexusLIMS customization app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nexuslims_overrides'
    verbose_name = 'NexusLIMS Customizations'
    
    def ready(self):
        """
        Called when Django starts.
        Use this to register signal handlers, apply patches, etc.
        """
        # Import menu configuration to register menu items
        from . import menus  # noqa: F401

        # Import signal handlers
        from . import signals  # noqa: F401
