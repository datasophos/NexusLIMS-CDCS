# NexusLIMS Deployment Customization
#
# Customize your deployment by overriding settings in this file.
# Changes take effect after restarting containers - no rebuild required.
#
# For detailed documentation on all available settings, see:
#   nexuslims_overrides/CUSTOMIZATION.md
#
# Workflow:
#   1. Never modify nexuslims_overrides/settings.py directly
#   2. Override settings in this file
#   3. Set DJANGO_SETTINGS_MODULE in deployment/.env:
#      DJANGO_SETTINGS_MODULE=config.settings.custom_settings
#   4. Place custom assets (logos, images) in config/static_files/
#   5. Restart: docker compose restart cdcs
#
# Static Files:
#   - Place assets in: config/static_files/
#   - Reference as: "filename.png" or "subfolder/filename.png"
#   - Example: config/static_files/my_logo.png → NX_NAV_LOGO = "my_logo.png"

# Choose one: Import either prod_settings or dev_settings (not both)
from config.settings.prod_settings import *
# from config.settings.dev_settings import *  # Uncomment for development

# ----------------------------------
# Add customizations below this line
# ----------------------------------

# ============================================================================
# BRANDING & LOGOS
# ============================================================================
# NX_NAV_LOGO = "my_nav_logo.png"             # Navigation bar (top-left)
# NX_FOOTER_LOGO = "my_footer_logo.png"       # Footer logo
# NX_FOOTER_LINK = "https://your-org.example.com/"  # Footer logo link
# NX_HOMEPAGE_LOGO = "my_homepage_logo.png"   # Homepage logo

# ============================================================================
# THEME COLORS (CSS Custom Properties)
# ============================================================================
# These override the defaults in nexuslims/css/main.css
# Only set the ones you want to change - others use CSS defaults

# NX_THEME_COLORS = {
#     "primary": "#11659c",           # Main brand color
#     "primary_dark": "#0d528a",      # Darker variant
#     "info_badge_dark": "#505050",   # Info badge background color
#     "secondary": "#f9f9f9",         # Secondary (light) buttons
#     "secondary_dark": "#e2e2e2",    # Secondary darker for hover
#     "success": "#28a745",           # Success states
#     "danger": "#dc3545",            # Errors/warnings
#     "warning": "#ffc107",           # Warnings and button hover color
#     "info": "#17a2b8",              # Info messages
#     "light_gray": "#e3e3e3",
#     "dark_gray": "#212529",
# }

# ============================================================================
# HOMEPAGE CONTENT
# ============================================================================
# CUSTOM_TITLE = "Welcome to Your LIMS!"

# NX_HOMEPAGE_TEXT = """
# This laboratory information management system allows for automated creation
# and curation of experimental records. This text supports HTML such as
# <a href='https://example.org'>links</a>.
# """

# Documentation link (comment out to use default)
# NX_DOCUMENTATION_LINK = "https://docs.your-org.example.com"

# ============================================================================
# NAVIGATION MENU
# ============================================================================
# Custom links in navigation bar (supports Font Awesome icons)
# NX_CUSTOM_MENU_LINKS = [
#     {
#         "title": "Scheduler",
#         "url": "https://scheduler.your-org.example.com/",
#         "icon": "calendar",
#         "iconClass": "far"
#     },
#     {
#         "title": "Documentation",
#         "url": "https://docs.your-org.example.com/",
#         "icon": "question-circle",
#         "iconClass": "far"
#     }
# ]

# ============================================================================
# XSLT DISPLAY SETTINGS
# ============================================================================
# NX_MAX_DATASET_DISPLAY_COUNT = 100  # Threshold for simple display mode

# Badge colors for instrument PIDs in detail/list views
# NX_INSTRUMENT_COLOR_MAPPINGS = {
#     "FEI-Titan-TEM": "#2E86AB",
#     "JEOL-JEM3010-TEM": "#5DADE2",
# }
