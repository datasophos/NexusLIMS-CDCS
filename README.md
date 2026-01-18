# NexusLIMS-CDCS

<p align="center">
  <img src="static/img/logo_horizontal_text.png" alt="NexusLIMS Logo" width="400">


[![Documentation](https://img.shields.io/badge/📖%20docs-stable-blue?style=flat-square)](https://datasophos.github.io/NexusLIMS/stable/frontend_guide.html)
[![Django 4.2](https://img.shields.io/badge/django-4.2-green?style=flat-square&logo=django
)](https://docs.djangoproject.com/en/6.0/releases/4.2/)
[![Maintained by Datasophos](https://img.shields.io/badge/🏢%20maintained%20by-datasophos%20LLC-blue?style=flat-square)](https://datasophos.co)
</p>


NexusLIMS-CDCS is a customized deployment of the NIST Materials Data Curation System (MDCS) designed for managing and sharing microscopy and materials characterization data. It provides a web-based platform for capturing, organizing, searching, and visualizing experimental data using structured XML schemas.

> **⚠️ Notice**: This is a fork of the original NexusLIMS project, created after the lead developer (@jat255) left NIST and founded [Datasophos](https://datasophos.co). This fork is maintained by Datasophos and is **not affiliated with NIST** in any way. For the official NIST version, please visit the [original repository](https://github.com/usnistgov/NexusLIMS-CDCS).

## Overview

This system enables:
- **Structured data capture** using customizable XML schemas and web forms
- **Powerful search capabilities** across all stored datasets
- **Data visualization** with XSLT-based rendering of XML records
- **RESTful API access** for programmatic interaction
- **Secure data management** with user authentication and access control
- **Instrument data integration** for linking to raw experimental files

Visit the [📷 screenshot gallery](https://datasophos.github.io/NexusLIMS/stable/frontend_guide/gallery.html) for
a preview of the application's features and appearance.
The system is built on the NIST Configurable Data Curation System (CDCS) framework and uses PostgreSQL for data storage, Redis for caching, and Caddy for serving files and the application through a reverse proxy.

## Integration with NexusLIMS

This web application pairs with the [NexusLIMS backend](https://github.com/datasophos/NexusLIMS), which handles automated metadata extraction and record generation from microscopy session logs. The NexusLIMS backend creates XML records that are submitted to this CDCS instance for storage, search, and visualization.

## Getting Started

### For Users

If you're looking to use an existing NexusLIMS-CDCS deployment:
1. Access the web interface at your organization's deployment URL
2. Log in with your credentials (*optional*)
3. Use the search and explore features to find datasets

### For Administrators

To deploy and manage a NexusLIMS-CDCS instance:

- **📖 [Documentation](https://datasophos.github.io/NexusLIMS/stable/frontend_guide.html)** - Documentation development and production
- **🚀 [Production Deployment](https://datasophos.github.io/NexusLIMS/stable/frontend_guide/production.html)** - Detailed production setup instructions
- **🔧 [Admin Commands](https://datasophos.github.io/NexusLIMS/stable/frontend_guide/administration.html)** - Management scripts for backups, updates, and maintenance

## Key Features

- XML Schema-based data templates for structured metadata
- XSLT transformations for rich HTML presentation of data records
- Integration with instrument data file storage
- User workspace management for organizing datasets
- Advanced search and filtering capabilities
- RESTful API for automation and integration

## Technical Stack

- **Backend**: Django (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Web Server**: Caddy (with automatic HTTPS)
- **Container Platform**: Docker and Docker Compose
- **Package Management**: UV (with pyproject.toml and lockfile)

## Development

This project uses [UV](https://github.com/astral-sh/uv) for fast, reliable dependency management:

- **Dependencies**: Defined in `pyproject.toml` with organized groups (core, server)
- **Reproducibility**: `uv.lock` lockfile ensures identical builds across environments
- **Docker-first**: Development happens in containers (no local Python setup required)

For detailed build and deployment instructions, see [deployment/README.md](deployment/README.md).

## License

See [LICENSE](LICENSE) for details.

## Support & Professional Services

💼 **Need help with NexusLIMS?** Datasophos offers:

- 🚀 **Deployment & Integration** - Expert configuration for your lab environment
- 🔧 **Custom Development** - Custom extractors, harvesters, and workflow extensions
- 🎓 **Training & Support** - Team onboarding and ongoing technical support

**Contact**: [josh@datasophos.co](mailto:josh@datasophos.co) | [datasophos.co](https://datasophos.co)
