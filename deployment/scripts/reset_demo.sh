#!/bin/bash
# reset_demo.sh - Wipe and re-seed the NexusLIMS demo environment.
#
# Stops all containers, removes data volumes (postgres, redis, app media/static),
# then restarts the stack. The entrypoint re-runs migrations, init_environment.py,
# and seed_demo_records.py on the fresh database.
#
# Caddy's Let's Encrypt data (caddy_data, caddy_config volumes) is intentionally
# preserved to avoid exhausting Let's Encrypt's rate limits (5 certs/domain/hour,
# 50/week).
#
# Usage:
#   ./reset_demo.sh                  # run directly
#   crontab: 0 */2 * * * /opt/nexuslims-cdcs/deployment/scripts/reset_demo.sh >> /var/log/nexuslims-demo-reset.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="${SCRIPT_DIR}/.."

cd "${DEPLOY_DIR}"

# Load .env to get COMPOSE_PROJECT_NAME and COMPOSE_FILE
if [ -f .env ]; then
    set -a
    # shellcheck source=.env
    source .env
    set +a
fi

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.base.yml:docker-compose.demo.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-nexuslims_demo}"
export COMPOSE_FILE

echo "=== NexusLIMS Demo Reset - $(date) ==="
echo "    Project: ${COMPOSE_PROJECT_NAME}"

# 1. Stop and remove containers (volumes are removed separately below)
echo "Stopping containers..."
docker compose down

# 2. Remove data volumes (caddy_data and caddy_config are intentionally excluded)
echo "Removing data volumes..."
for vol in postgres_data redis_data cdcs_media cdcs_static cdcs_socket; do
    if docker volume rm "${COMPOSE_PROJECT_NAME}_${vol}" 2>/dev/null; then
        echo "  Removed ${COMPOSE_PROJECT_NAME}_${vol}"
    else
        echo "  ${COMPOSE_PROJECT_NAME}_${vol} not found, skipping"
    fi
done

# 3. Restart the stack (entrypoint re-runs migrate + init + seed)
echo "Starting services..."
docker compose up -d

echo "=== Reset complete ==="
