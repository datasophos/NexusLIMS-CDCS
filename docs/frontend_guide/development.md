(cdcs-development)=
# Development Setup

This guide walks you through setting up a local NexusLIMS CDCS development environment with hot-reload, test data, and HTTPS support.

## Prerequisites

- **Docker Desktop** or Docker Engine with Docker Compose
- **Git** for cloning the repository
- **4GB RAM** minimum available for Docker

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/datasophos/NexusLIMS-CDCS.git
cd NexusLIMS-CDCS/deployment
```

### 2. Set Up Environment

```bash
cp .env.dev .env
```

The development defaults work out of the box - no modifications needed.

### 3. Load Development Commands

```bash
source dev-commands.sh
```

This loads convenient aliases for common development tasks (see {ref}`development-commands` for common commands).

### 4. Start the Environment

```bash
dev-up
```

This command:
- Extracts test data (preview images and sample records)
- Builds the CDCS Docker image
- Pulls supporting images (PostgreSQL, Redis, Caddy)
- Starts all services
- Initializes the database with a superuser and sample schema

### 5. Trust the Development CA Certificate

The development environment uses a local Certificate Authority for HTTPS. To avoid browser warnings, trust the CA certificate once:

`````{tab-set}

````{tab-item} macOS
```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain caddy/certs/ca.crt
```
````

````{tab-item} Ubuntu/Debian
```bash
sudo cp caddy/certs/ca.crt /usr/local/share/ca-certificates/nexuslims-dev-ca.crt
sudo update-ca-certificates
```
````

````{tab-item} Fedora/RHEL
```bash
sudo cp caddy/certs/ca.crt /etc/pki/ca-trust/source/anchors/nexuslims-dev-ca.crt
sudo update-ca-trust
```
````

````{tab-item} Windows
1. Open `certmgr.msc`
2. Navigate to "Trusted Root Certification Authorities" > "Certificates"
3. Right-click > "All Tasks" > "Import"
4. Select `caddy/certs/ca.crt`
````

`````

**Alternative - Browser-specific import:**

If you prefer not to trust the certificate system-wide:
- **Chrome/Edge**: Settings > Privacy and security > Security > Manage certificates > Authorities > Import
- **Firefox**: Settings > Privacy & Security > Certificates > View Certificates > Authorities > Import

### 6. Access the Application

| URL | Purpose |
|-----|---------|
| https://nexuslims-dev.localhost | Main application |
| https://files.nexuslims-dev.localhost/data/ | Preview images and metadata |
| https://files.nexuslims-dev.localhost/instrument-data/ | Instrument data files |

**Default credentials:**
- Superuser: `admin` / `admin`
- Regular user: `user` / `user`

## Next steps

Continue with the {doc}`development workflow <development-workflow>` for common
commands and development features, or use the section navigation to explore the
architecture, XSLT workflow, and troubleshooting guides.

<span id="development-commands"></span>

```{toctree}
:hidden:

Development workflow <development-workflow>
Architecture and directory structure <development-architecture>
XSLT stylesheet development <development-xslt>
Development troubleshooting <development-troubleshooting>
```
