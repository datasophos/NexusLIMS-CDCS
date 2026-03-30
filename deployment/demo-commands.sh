#!/bin/bash
# Quick reference commands for NexusLIMS-CDCS public demo

export COMPOSE_FILE="docker-compose.base.yml:docker-compose.demo.yml"

# Read COMPOSE_PROJECT_NAME, DOMAIN, and COMPOSE_FILE from .env if present.
# COMPOSE_FILE in .env overrides the default above.
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -E '^(COMPOSE_PROJECT_NAME|DOMAIN|COMPOSE_FILE)=' | xargs)
fi
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-nexuslims_demo}
DOMAIN=${DOMAIN:-nexuslims-demo.datasophos.co}

# Build the CDCS container
alias demo-build='COMPOSE_BAKE=true docker compose build cdcs'
alias demo-build-clean='COMPOSE_BAKE=true docker compose build --no-cache cdcs'

# Start the demo stack
alias demo-up='docker compose up -d'
alias demo-up-logs='docker compose up -d && docker compose logs -f'

# Stop the demo stack
alias demo-down='docker compose down'

# Full wipe and restart - simulates the 2hr scheduled reset
alias demo-reset='docker compose down -v && docker compose up -d'

# Restart without wiping volumes
alias demo-restart='docker compose restart cdcs'
alias demo-restart-all='docker compose down && docker compose up -d'

# View logs
alias demo-logs='docker compose logs -f'
alias demo-logs-cdcs='docker logs -f ${COMPOSE_PROJECT_NAME}_cdcs'
alias demo-logs-caddy='docker logs -f ${COMPOSE_PROJECT_NAME}_cdcs_caddy'

# Shell access
alias demo-shell='docker exec -it ${COMPOSE_PROJECT_NAME}_cdcs bash'
alias demo-manage='docker exec -it ${COMPOSE_PROJECT_NAME}_cdcs python manage.py'

# Re-run init script without full restart (useful during development)
alias demo-init='docker exec ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/init_environment.py'
alias demo-seed='docker exec ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/seed_demo_records.py'
alias demo-collectstatic='docker exec ${COMPOSE_PROJECT_NAME}_cdcs python manage.py collectstatic --noinput'

echo "NexusLIMS-CDCS Demo aliases loaded! Available commands:"
echo ""
echo "  Build:"
echo "    demo-build           - Build CDCS container (with cache)"
echo "    demo-build-clean     - Build CDCS container (no cache, clean build)"
echo ""
echo "  Lifecycle:"
echo "    demo-up              - Start demo stack"
echo "    demo-up-logs         - Start demo stack and tail logs"
echo "    demo-down            - Stop demo stack"
echo "    demo-reset           - Full wipe + restart (simulates 2hr scheduled reset)"
echo "    demo-restart         - Restart CDCS container only (keeps data)"
echo "    demo-restart-all     - Restart all services (keeps data)"
echo ""
echo "  Logs:"
echo "    demo-logs            - View all logs (follow mode)"
echo "    demo-logs-cdcs       - View CDCS app logs only"
echo "    demo-logs-caddy      - View Caddy proxy logs"
echo ""
echo "  Shell Access:"
echo "    demo-shell           - Open bash shell in CDCS container"
echo "    demo-manage          - Run Django management commands"
echo ""
echo "  Data Management:"
echo "    demo-init            - Re-run init script (migrate + users + schema)"
echo "    demo-seed            - Re-run seed script (upload demo records)"
echo "    demo-collectstatic   - Collect static files"
echo ""
echo "To use these aliases, run: cd deployment && source demo-commands.sh"
echo ""
echo "Access NexusLIMS Demo at: https://${DOMAIN}"
