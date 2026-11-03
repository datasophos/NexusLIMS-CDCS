# Development Workflow

## Development Features

### Hot Reload

Application code is mounted into the container. Changes to Python files automatically reload the application - no rebuild required.

### Test Data

The development environment includes sample microscopy data (~149MB extracted):
- Preview images at `https://files.nexuslims-dev.localhost/data/`
- Instrument data at `https://files.nexuslims-dev.localhost/instrument-data/`
- Example XML records in the database
- The test data contains only zero-data so it is highly compressible, meaning the preview images
  will appear to be all black or blank. This is expected.
- Test data is automatically extracted by `dev-up` and is gitignored.

### Local HTTPS

Caddy uses a local CA for HTTPS. Follow the certificate instructions in
{doc}`development setup <development>` to trust it in your browser.

### Direct Database Access

For debugging, PostgreSQL and Redis are exposed on host ports:
- PostgreSQL: `localhost:5532`
- Redis: `localhost:6479`

---

(development-commands)=
## Development Commands

Load commands with `source dev-commands.sh` from the `deployment/` directory.

### Lifecycle

| Command | Description |
|---------|-------------|
| `dev-up` | Start all services (includes test data setup) |
| `dev-down` | Stop all services |
| `dev-restart` | Restart CDCS application |
| `dev-clean` | Stop and remove all data (clean slate) |

### Viewing Logs

| Command | Description |
|---------|-------------|
| `dev-logs` | View all service logs |
| `dev-logs-app` | CDCS application logs only |
| `dev-logs-caddy` | Caddy proxy logs |

### Shell Access

| Command | Description |
|---------|-------------|
| `dev-shell` | Bash shell in CDCS container |
| `dev-djshell` | Django Python shell |
| `dev-dbshell` | PostgreSQL shell |

### Database

| Command | Description |
|---------|-------------|
| `dev-migrate` | Run Django migrations |
| `dev-makemigrations` | Create new migrations |

### NexusLIMS-Specific

| Command | Description |
|---------|-------------|
| `dev-update-xslt` | Update both XSLT stylesheets in database |
| `dev-update-xslt-detail` | Update only detail_stylesheet.xsl |
| `dev-update-xslt-list` | Update only list_stylesheet.xsl |

### Dependency Management

The project uses [UV](https://github.com/astral-sh/uv) for fast, reliable Python dependency management with lockfiles for reproducibility.

| Command | Description |
|---------|-------------|
| `dev-uv-lock` | Regenerate `uv.lock` from `pyproject.toml` |
| `dev-uv-upgrade` | Upgrade all dependencies (respecting version constraints) |
| `dev-uv-sync` | Sync local environment with lockfile (for local dev outside Docker) |
| `dev-uv-add` | Show usage for adding new dependencies |

```{note}
After adding or updating dependencies, rebuild the Docker image with `dev-build-clean` to apply changes.
```

**Key Files:**
- `pyproject.toml` - Single source of truth for all dependencies
- `uv.lock` - Lockfile ensuring reproducible builds (must be committed)
- `.python-version` - Required Python version (3.13)

The main dependencies include the application, CDCS packages, and production
servers. The `dev` group contains testing tools, and the `docs` group contains
the documentation build tools.

For detailed dependency workflows, see the repository's `CLAUDE.md` and `deployment/README.md`.
