"""Sphinx configuration for the NexusLIMS-CDCS guide."""

project = "NexusLIMS-CDCS"
author = "Datasophos LLC"
extensions = ["myst_parser", "sphinx_design", "sphinxcontrib.mermaid", "sphinx_copybutton"]
myst_enable_extensions = ["colon_fence", "deflist", "linkify", "substitution"]
templates_path = ["_templates"]
html_theme = "pydata_sphinx_theme"
html_title = "NexusLIMS-CDCS Documentation"
html_theme_options = {
    "github_url": "https://github.com/datasophos/NexusLIMS-CDCS",
    "navbar_end": ["doc_versions", "theme-switcher", "navbar-icon-links"],
}
exclude_patterns = ["_build", "changes/**", "doc-gen/**", "superpowers/**", "mdcs-dev-setup.md", "mdcs-install-pypi.md", "README.md"]
