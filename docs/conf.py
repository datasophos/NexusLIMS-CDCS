"""Sphinx configuration for the NexusLIMS-CDCS guide."""

import os

project = "NexusLIMS CDCS"

# Published releases are built from their tags; previews use their own label.
if os.environ.get("GITHUB_EVENT_NAME") == "release":
    version_match = os.environ["GITHUB_REF_NAME"]
elif os.environ.get("GITHUB_REF") == "refs/heads/main":
    version_match = "dev"
else:
    version_match = "preview"
version = release = version_match
author = "Datasophos LLC"
extensions = ["myst_parser", "sphinx_design", "sphinxcontrib.mermaid", "sphinx_copybutton"]
myst_enable_extensions = ["colon_fence", "deflist", "linkify", "substitution"]
templates_path = ["_templates"]
html_theme = "pydata_sphinx_theme"
html_title = "NexusLIMS CDCS Documentation"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_js_files = ["gallery.js"]
html_favicon = "_static/nexusLIMS_bare_logo.ico"
html_sidebars = {"index": [], "**": ["section-nav"]}
html_theme_options = {
    "logo": {
        "image_light": "_static/logo_horizontal_light.png",
        "image_dark": "_static/logo_horizontal_dark.png",
        "alt_text": "NexusLIMS CDCS documentation home",
    },
    "github_url": "https://github.com/datasophos/NexusLIMS-CDCS",
    "navbar_start": ["navbar-logo", "version-switcher"],
    # The index is created by the first deployment, after the site is built.
    "check_switcher": False,
    "switcher": {
        "json_url": "https://datasophos.github.io/NexusLIMS-CDCS/switcher.json",
        "version_match": version_match,
    },
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["search-button", "theme-switcher", "navbar-icon-links"],
    "navbar_persistent": [],
    "collapse_navigation": True,
    "header_links_before_dropdown": 6,
    "icon_links": [
        {"name": "NexusLIMS documentation", "url": "https://datasophos.github.io/NexusLIMS/stable/", "icon": "fa-solid fa-book"},
        {"name": "Datasophos", "url": "https://datasophos.co", "icon": "fa-solid fa-globe"},
    ],
}
exclude_patterns = ["_build", "changes/**", "doc-gen/**", "superpowers/**", "mdcs-dev-setup.md", "mdcs-install-pypi.md", "README.md"]
