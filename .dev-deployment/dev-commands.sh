#!/bin/bash
# Quick reference commands for NexusLIMS-CDCS local development

# Build the CDCS container
alias dev-build='COMPOSE_BAKE=true docker compose build cdcs'
alias dev-build-clean='COMPOSE_BAKE=true docker compose build --no-cache cdcs'

# Start in development mode (with local code mounting)
alias dev-up='docker compose -f docker-compose.yml -f mongo/docker-compose.yml -f docker-compose.dev.yml up -d'

# Stop development environment
alias dev-down='docker compose -f docker-compose.yml -f mongo/docker-compose.yml -f docker-compose.dev.yml down'
alias dev-clean='docker compose -f docker-compose.yml -f mongo/docker-compose.yml -f docker-compose.dev.yml down -v'

# View logs
alias dev-logs='docker compose -f docker-compose.yml -f mongo/docker-compose.yml -f docker-compose.dev.yml logs -f'
alias dev-logs-app='docker logs -f nexuslims_dev_cdcs'
alias dev-logs-caddy='docker logs -f nexuslims_dev_cdcs_caddy'

# Restart services
alias dev-restart='docker compose -f docker-compose.yml -f mongo/docker-compose.yml -f docker-compose.dev.yml restart cdcs'
alias dev-restart-all='docker compose -f docker-compose.yml -f mongo/docker-compose.yml -f docker-compose.dev.yml restart'

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

echo "NexusLIMS-CDCS Development aliases loaded! Available commands:"
echo ""
echo "  🏗️  Build:"
echo "    dev-build           - Build CDCS container (with cache)"
echo "    dev-build-clean     - Build CDCS container (no cache, clean build)"
echo ""
echo "  🚀 Lifecycle:"
echo "    dev-up              - Start development environment"
echo "    dev-down            - Stop development environment"
echo "    dev-clean           - Stop and remove volumes (clean slate)"
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
echo "To use these aliases, run: source dev-commands.sh"
echo ""
echo "Access NexusLIMS-CDCS at: https://nexuslims-dev.localhost:8443"
