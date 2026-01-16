#!/bin/bash
# Quick reference commands for NexusLIMS-CDCS local development

export COMPOSE_FILE="docker-compose.base.yml:docker-compose.dev.yml"

# Get COMPOSE_PROJECT_NAME from .env or use default
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep COMPOSE_PROJECT_NAME | xargs)
fi
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-nexuslims_dev}

# Build the CDCS container
alias dev-build='COMPOSE_BAKE=true docker compose build cdcs'
alias dev-build-clean='COMPOSE_BAKE=true docker compose build --no-cache cdcs'

# Start in development mode (with local code mounting)
alias dev-up='bash scripts/setup-test-data.sh && docker compose up -d'
alias dev-up-logs='bash scripts/setup-test-data.sh && docker compose up -d && docker compose logs -f'

# Stop development environment
alias dev-down='docker compose down'
alias dev-clean='docker compose down -v && rm -rf test-data/nx-data test-data/nx-instrument-data test-data/example_record.xml'

# View logs
alias dev-logs='docker compose logs -f'
alias dev-logs-app='docker logs -f nexuslims_dev_cdcs'
alias dev-logs-caddy='docker logs -f nexuslims_dev_cdcs_caddy'

# Restart services
alias dev-restart='docker compose down cdcs && docker compose up -d cdcs'
alias dev-restart-all='docker compose down && docker compose up -d'

# Shell access
alias dev-shell='docker exec -it nexuslims_dev_cdcs bash'
alias dev-manage='docker exec -it nexuslims_dev_cdcs python manage.py'

# Database operations
alias dev-migrate='docker exec nexuslims_dev_cdcs python manage.py migrate'
alias dev-makemigrations='docker exec nexuslims_dev_cdcs python manage.py makemigrations'
alias dev-dbshell='docker exec -it nexuslims_dev_cdcs python manage.py dbshell'

# User management
alias dev-superuser='docker exec -it nexuslims_dev_cdcs python manage.py createsuperuser'

# Collectstatic
alias dev-collectstatic='docker exec nexuslims_dev_cdcs python manage.py collectstatic --noinput'

# Django shell
alias dev-djshell='docker exec -it nexuslims_dev_cdcs python manage.py shell'

# XSLT stylesheet updates
alias dev-update-xslt='bash scripts/update-xslt.sh'
alias dev-update-xslt-detail='bash scripts/update-xslt.sh detail'
alias dev-update-xslt-list='bash scripts/update-xslt.sh list'

echo "NexusLIMS-CDCS Development aliases loaded! Available commands:"
echo ""
echo "  🏗️  Build:"
echo "    dev-build           - Build CDCS container (with cache)"
echo "    dev-build-clean     - Build CDCS container (no cache, clean build)"
echo ""
echo "  🚀 Lifecycle:"
echo "    dev-up              - Start development environment (auto-extracts test data if needed)"
echo "    dev-up-logs         - Start development environment and immediately log output"
echo "    dev-down            - Stop development environment"
echo "    dev-clean           - Stop and remove volumes + test data (clean slate)"
echo "    dev-restart         - Restart CDCS app only"
echo "    dev-restart-all     - Restart all services"
echo ""
echo "  📋 Logs:"
echo "    dev-logs            - View all logs (follow mode)"
echo "    dev-logs-app        - View CDCS app logs only"
echo "    dev-logs-caddy      - View Caddy proxy logs"
echo ""
echo "  🔧 Shell Access:"
echo "    dev-shell           - Open bash shell in CDCS container"
echo "    dev-manage          - Run Django management commands"
echo "    dev-djshell         - Open Django shell (Python REPL)"
echo ""
echo "  💾 Database:"
echo "    dev-migrate         - Run database migrations"
echo "    dev-makemigrations  - Create new migrations"
echo "    dev-dbshell         - Open PostgreSQL shell"
echo ""
echo "  👤 User Management:"
echo "    dev-superuser       - Create superuser"
echo ""
echo "  📦 Static Files:"
echo "    dev-collectstatic   - Collect static files"
echo ""
echo "  🎨 XSLT Stylesheets:"
echo "    dev-update-xslt        - Update both detail and list stylesheets in database"
echo "    dev-update-xslt-detail - Update detail_stylesheet.xsl only"
echo "    dev-update-xslt-list   - Update list_stylesheet.xsl only"
echo ""
echo "To use these aliases, run: source dev-commands.sh"
echo ""
echo "Access NexusLIMS-CDCS at: https://nexuslims-dev.localhost"
