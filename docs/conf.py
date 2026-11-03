"""Sphinx configuration for the NexusLIMS-CDCS guide."""

project = "NexusLIMS CDCS"
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
    "navbar_start": ["navbar-logo", "doc_versions"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["search-button", "theme-switcher", "navbar-icon-links"],
    "navbar_persistent": [],
    "collapse_navigation": True,
    "header_links_before_dropdown": 5,
    "icon_links": [
        {"name": "NexusLIMS documentation", "url": "https://datasophos.github.io/NexusLIMS/stable/", "icon": "fa-solid fa-book"},
        {"name": "Datasophos", "url": "https://datasophos.co", "icon": "fa-solid fa-globe"},
    ],
}
exclude_patterns = ["_build", "changes/**", "doc-gen/**", "superpowers/**", "mdcs-dev-setup.md", "mdcs-install-pypi.md", "README.md"]
