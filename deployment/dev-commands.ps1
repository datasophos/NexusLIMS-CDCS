# Quick reference commands for NexusLIMS-CDCS local development (PowerShell)

$env:COMPOSE_FILE = "docker-compose.base.yml:docker-compose.dev.yml"

# Parse .env file to get configuration
$envVars = @{}
if (Test-Path .env) {
    Get-Content .env | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' } | ForEach-Object {
        $key, $value = $_ -split '=', 2
        $envVars[$key.Trim()] = $value.Trim()
    }
}

$script:COMPOSE_PROJECT_NAME = if ($envVars['COMPOSE_PROJECT_NAME']) { $envVars['COMPOSE_PROJECT_NAME'] } else { 'nexuslims_dev' }

# Build the CDCS container
function dev-build {
    $env:COMPOSE_BAKE = "true"
    docker compose build cdcs
}

function dev-build-clean {
    $env:COMPOSE_BAKE = "true"
    docker compose build --no-cache cdcs
}

# Start in development mode (with local code mounting)
function dev-up {
    bash scripts/setup-test-data.sh
    docker compose up -d
}

function dev-up-logs {
    bash scripts/setup-test-data.sh
    docker compose up -d
    docker compose logs -f
}

# Stop development environment
function dev-down {
    docker compose down
}

function dev-clean {
    docker compose down -v
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue test-data/nx-data
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue test-data/nx-instrument-data
    Remove-Item -Force -ErrorAction SilentlyContinue test-data/example_record.xml
}

# View logs
function dev-logs {
    docker compose logs -f
}

function dev-logs-app {
    docker logs -f nexuslims_dev_cdcs
}

function dev-logs-caddy {
    docker logs -f nexuslims_dev_cdcs_caddy
}

# Restart services
function dev-restart {
    docker compose down cdcs
    docker compose up -d cdcs
}

function dev-restart-all {
    docker compose down
    docker compose up -d
}

# Shell access
function dev-shell {
    docker exec -it nexuslims_dev_cdcs bash
}

function dev-manage {
    docker exec -it nexuslims_dev_cdcs python manage.py @args
}

# Database operations
function dev-migrate {
    docker exec nexuslims_dev_cdcs python manage.py migrate
}

function dev-makemigrations {
    docker exec nexuslims_dev_cdcs python manage.py makemigrations
}

function dev-dbshell {
    docker exec -it nexuslims_dev_cdcs python manage.py dbshell
}

# User management
function dev-superuser {
    docker exec -it nexuslims_dev_cdcs python manage.py createsuperuser
}

# Collectstatic
function dev-collectstatic {
    docker exec nexuslims_dev_cdcs python manage.py collectstatic --noinput
}

# Django shell
function dev-djshell {
    docker exec -it nexuslims_dev_cdcs python manage.py shell
}

# XSLT stylesheet updates
function dev-update-xslt {
    bash scripts/update-xslt.sh
}

function dev-update-xslt-detail {
    bash scripts/update-xslt.sh detail
}

function dev-update-xslt-list {
    bash scripts/update-xslt.sh list
}

# UV dependency management
# Note: --no-install-project skips building the project itself (Django app, not a package)
function dev-uv-lock {
    Push-Location ..
    uv lock
    Pop-Location
}

function dev-uv-upgrade {
    Push-Location ..
    uv lock --upgrade
    Pop-Location
}

function dev-uv-sync {
    Push-Location ..
    uv sync --no-install-project --extra core --extra server
    Pop-Location
}

function dev-uv-add {
    Write-Host "Usage: cd .. && uv add package-name && cd deployment && dev-build-clean"
}

# Display help message
Write-Host "NexusLIMS-CDCS Development commands loaded!" -ForegroundColor Green
Write-Host "Available commands:"
Write-Host ""
Write-Host "  🏗️  Build:"
Write-Host "    dev-build           - Build CDCS container (with cache)"
Write-Host "    dev-build-clean     - Build CDCS container (no cache, clean build)"
Write-Host ""
Write-Host "  🚀 Lifecycle:"
Write-Host "    dev-up              - Start development environment (auto-extracts test data if needed)"
Write-Host "    dev-up-logs         - Start development environment and immediately log output"
Write-Host "    dev-down            - Stop development environment"
Write-Host "    dev-clean           - Stop and remove volumes + test data (clean slate)"
Write-Host "    dev-restart         - Restart CDCS app only"
Write-Host "    dev-restart-all     - Restart all services"
Write-Host ""
Write-Host "  📋 Logs:"
Write-Host "    dev-logs            - View all logs (follow mode)"
Write-Host "    dev-logs-app        - View CDCS app logs only"
Write-Host "    dev-logs-caddy      - View Caddy proxy logs"
Write-Host ""
Write-Host "  🔧 Shell Access:"
Write-Host "    dev-shell           - Open bash shell in CDCS container"
Write-Host "    dev-manage          - Run Django management commands"
Write-Host "    dev-djshell         - Open Django shell (Python REPL)"
Write-Host ""
Write-Host "  💾 Database:"
Write-Host "    dev-migrate         - Run database migrations"
Write-Host "    dev-makemigrations  - Create new migrations"
Write-Host "    dev-dbshell         - Open PostgreSQL shell"
Write-Host ""
Write-Host "  👤 User Management:"
Write-Host "    dev-superuser       - Create superuser"
Write-Host ""
Write-Host "  📦 Static Files:"
Write-Host "    dev-collectstatic   - Collect static files"
Write-Host ""
Write-Host "  🎨 XSLT Stylesheets:"
Write-Host "    dev-update-xslt        - Update both detail and list stylesheets in database"
Write-Host "    dev-update-xslt-detail - Update detail_stylesheet.xsl only"
Write-Host "    dev-update-xslt-list   - Update list_stylesheet.xsl only"
Write-Host ""
Write-Host "  📦 UV Dependencies:"
Write-Host "    dev-uv-lock            - Regenerate uv.lock from pyproject.toml"
Write-Host "    dev-uv-upgrade         - Upgrade all dependencies (respecting version constraints)"
Write-Host "    dev-uv-sync            - Sync local environment with lockfile (for local dev outside Docker)"
Write-Host "    dev-uv-add             - Show usage for adding new dependencies"
Write-Host "                             (After adding deps, run dev-build-clean to rebuild Docker)"
Write-Host ""
Write-Host "To use these commands, run: " -NoNewline
Write-Host ". .\dev-commands.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access NexusLIMS-CDCS at: " -NoNewline
Write-Host "https://nexuslims-dev.localhost" -ForegroundColor Cyan
Write-Host ""
