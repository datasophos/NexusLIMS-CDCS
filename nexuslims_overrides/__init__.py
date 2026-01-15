"""
NexusLIMS Overrides App

This Django app contains all NexusLIMS-specific customizations to the base MDCS system.
It provides a centralized location for template overrides, static files, and custom logic.

Design Pattern:
- Template inheritance to minimize duplication
- Centralized static files (CSS, JS, images)
- Context processors for global template variables
- Custom template tags for reusable components
"""

default_app_config = 'nexuslims_overrides.apps.NexusLIMSOverridesConfig'
