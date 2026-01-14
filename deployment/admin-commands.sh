#!/bin/bash
# Administrative commands for NexusLIMS-CDCS
# These commands are for backup, restore, and system administration
#
# Works with both dev and production deployments by using COMPOSE_PROJECT_NAME
# from your .env file (e.g., nexuslims_dev or nexuslims_prod)

# Get COMPOSE_PROJECT_NAME from .env or use default
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep COMPOSE_PROJECT_NAME | xargs)
    export $(grep -v '^#' .env | grep NX_CDCS_BACKUPS_HOST_PATH | xargs)
fi
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-nexuslims_dev}
NX_CDCS_BACKUPS_HOST_PATH=${NX_CDCS_BACKUPS_HOST_PATH:-./backups}

# hide docker feature advertisements
export DOCKER_CLI_HINTS=false

# Docker Compose alias for production
alias dc-prod="COMPOSE_BAKE=true docker compose -f docker-compose.base.yml -f docker-compose.prod.yml"

# Backup and Restore
alias admin-backup="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/backup_cdcs.py 2>&1 | grep -v 'SSL_CERTIFICATES_DIR\|Registered signals'"
unalias admin-restore 2>/dev/null || true
admin-restore() {
    if [ -z "$1" ]; then
        echo "Usage: admin-restore <backup_directory>"
        echo ""
        echo "Available backups:"
        ls -1dt ${NX_CDCS_BACKUPS_HOST_PATH}/backup_* 2>/dev/null | head -10 || echo "  No backups found in ${NX_CDCS_BACKUPS_HOST_PATH}"
        return 1
    fi

    local backup_dir="$1"

    # Check if backup directory exists on host
    if [ ! -d "$backup_dir" ]; then
        echo "✗ Error: Backup directory not found: $backup_dir"
        return 1
    fi

    # Convert host path to container path
    # Host: /opt/nexuslims/backups/... -> Container: /srv/nexuslims/backups/...
    local container_backup_dir=$(echo "$backup_dir" | sed "s|${NX_CDCS_BACKUPS_HOST_PATH}|/srv/nexuslims/backups|")

    echo "Restoring from: $backup_dir"
    echo ""
    docker exec ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/restore_cdcs.py --all "$container_backup_dir"
}

# Database dumps (PostgreSQL)
# WARNING: These commands are for disaster recovery only.
# For normal backup/restore, use admin-backup and admin-restore instead.
unalias admin-db-dump 2>/dev/null || true
admin-db-dump() {
    echo "⚠️  WARNING: This creates a raw PostgreSQL dump for disaster recovery."
    echo "   For normal backups, use 'admin-backup' instead."
    echo ""
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${NX_CDCS_BACKUPS_HOST_PATH}/db_backup_${timestamp}.sql"
    echo "Creating database dump..."
    docker exec ${COMPOSE_PROJECT_NAME}_cdcs_postgres pg_dump -U ${POSTGRES_USER:-nexuslims} ${POSTGRES_DB:-nexuslims} > "$backup_file"
    echo "✓ Database dump written to: $backup_file"
}
unalias admin-db-restore 2>/dev/null || true
admin-db-restore() {
    if [ -z "$1" ]; then
        echo "Usage: admin-db-restore <path_to_backup.sql>"
        return 1
    fi

    local backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        echo "✗ Error: File not found: $backup_file"
        return 1
    fi

    echo "⚠️  WARNING: This restores a raw PostgreSQL dump for disaster recovery."
    echo "   This will DROP and RECREATE the entire database!"
    echo "   ALL EXISTING DATA WILL BE LOST!"
    echo "   For normal restore, use 'admin-restore <backup_dir>' instead."
    echo ""
    echo -n "Continue with restore? (y/N) "
    read REPLY
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        return 0
    fi

    echo ""
    echo "🚨 FINAL WARNING: This will permanently delete all data in the database!"
    echo -n "Type 'DELETE' to confirm: "
    read CONFIRM
    if [[ "$CONFIRM" != "DELETE" ]]; then
        echo "Restore cancelled"
        return 0
    fi

    echo ""
    echo "Stopping application containers..."
    dc-prod stop cdcs caddy 2>/dev/null

    echo "Terminating database connections..."
    docker exec ${COMPOSE_PROJECT_NAME}_cdcs_postgres psql -U ${POSTGRES_USER:-nexuslims} postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB:-nexuslims}' AND pid <> pg_backend_pid();" 2>&1 | grep -v 'SSL_CERTIFICATES_DIR\|Registered signals' > /dev/null

    echo "Dropping database..."
    docker exec ${COMPOSE_PROJECT_NAME}_cdcs_postgres psql -U ${POSTGRES_USER:-nexuslims} postgres -c "DROP DATABASE IF EXISTS ${POSTGRES_DB:-nexuslims};" 2>&1 | grep -v 'SSL_CERTIFICATES_DIR\|Registered signals'

    echo "Recreating database..."
    docker exec ${COMPOSE_PROJECT_NAME}_cdcs_postgres psql -U ${POSTGRES_USER:-nexuslims} postgres -c "CREATE DATABASE ${POSTGRES_DB:-nexuslims} OWNER ${POSTGRES_USER:-nexuslims};" 2>&1 | grep -v 'SSL_CERTIFICATES_DIR\|Registered signals'

    echo "Restoring database from: $backup_file"
    cat "$backup_file" | docker exec -i ${COMPOSE_PROJECT_NAME}_cdcs_postgres psql -U ${POSTGRES_USER:-nexuslims} ${POSTGRES_DB:-nexuslims} 2>&1 | grep -v 'SSL_CERTIFICATES_DIR\|Registered signals\|ERROR:.*already exists'

    echo "Restarting application containers..."
    dc-prod start cdcs caddy 2>/dev/null

    echo "✓ Database restore completed"
}

# User management
alias admin-list-users="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); [print(f\\\"{u.username} ({u.email}) - Active: {u.is_active}, Admin: {u.is_superuser}\\\") for u in User.objects.all()]\" 2>&1 | grep -v 'SSL_CERTIFICATES_DIR\|Registered signals'"
unalias admin-export-users 2>/dev/null || true
admin-export-users() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${NX_CDCS_BACKUPS_HOST_PATH}/users_${timestamp}.json"
    echo "Exporting users..."
    docker exec ${COMPOSE_PROJECT_NAME}_cdcs python manage.py dumpdata auth.User --indent 2 2> >(grep -v 'SSL_CERTIFICATES_DIR\|Registered signals' >&2) > "$backup_file"
    echo "✓ Users exported to: $backup_file"
}
unalias admin-import-users 2>/dev/null || true
admin-import-users() {
    if [ -z "$1" ]; then
        echo "Usage: admin-import-users <path_to_users.json>"
        return 1
    fi

    local host_file="$1"
    if [ ! -f "$host_file" ]; then
        echo "✗ Error: File not found: $host_file"
        return 1
    fi

    # Copy file into container and run loaddata
    local container_file="/tmp/users_import.json"
    docker cp "$host_file" ${COMPOSE_PROJECT_NAME}_cdcs:"$container_file"
    docker exec ${COMPOSE_PROJECT_NAME}_cdcs python manage.py loaddata "$container_file" 2>&1 | grep -v 'SSL_CERTIFICATES_DIR\|Registered signals'
    docker exec ${COMPOSE_PROJECT_NAME}_cdcs rm "$container_file"
}

# Data statistics
alias admin-stats="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/show_stats.py 2>&1 | grep -v 'SSL_CERTIFICATES_DIR\|Registered signals'"

# Environment initialization
alias admin-init="docker exec -it ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/init_environment.py"

echo "NexusLIMS-CDCS Administrative Commands Loaded!"
echo "Project: ${COMPOSE_PROJECT_NAME}"
echo ""
echo "  🐳 Docker Compose:"
echo "    dc-prod               - Shortcut for 'docker compose -f docker-compose.base.yml -f docker-compose.prod.yml'"
echo ""
echo "  💾 Backup & Restore:"
echo "    admin-backup          - Backup all CDCS data (templates, records, blobs, users)"
echo "    admin-restore <dir>   - Restore from backup directory"
echo ""
echo "  🗄️  Database:"
echo "    admin-db-dump         - Create PostgreSQL database dump"
echo "    admin-db-restore      - Restore PostgreSQL database from dumped file"
echo ""
echo "  👥 User Management:"
echo "    admin-list-users      - List all users with status"
echo "    admin-export-users    - Export users to JSON fixture"
echo "    admin-import-users    - Import users from JSON fixture (provide filename)"
echo ""
echo "  📊 Statistics:"
echo "    admin-stats           - Show system statistics (users, records, templates)"
echo ""
echo "  🚀 Initialization:"
echo "    admin-init            - Initialize environment (create superuser, load schema & XSLT)"
echo ""
echo "To use these commands, run: source admin-commands.sh"
echo ""
