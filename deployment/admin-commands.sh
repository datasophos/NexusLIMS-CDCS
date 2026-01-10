#!/bin/bash
# Administrative commands for NexusLIMS-CDCS
# These commands are for backup, restore, and system administration
#
# Works with both dev and production deployments by using COMPOSE_PROJECT_NAME
# from your .env file (e.g., nexuslims_dev or nexuslims_prod)

# Get COMPOSE_PROJECT_NAME from .env or use default
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep COMPOSE_PROJECT_NAME | xargs)
fi
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-nexuslims_dev}

# Backup and Restore
alias admin-backup="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/backup_cdcs.py"
alias admin-restore="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/restore_cdcs.py"

# Database dumps (PostgreSQL)
alias admin-db-dump="docker exec ${COMPOSE_PROJECT_NAME}_cdcs_postgres pg_dump -U \${POSTGRES_USER:-nexuslims} \${POSTGRES_DB:-nexuslims} > backup_\$(date +%Y%m%d_%H%M%S).sql"
alias admin-db-restore="docker exec -i ${COMPOSE_PROJECT_NAME}_cdcs_postgres psql -U \${POSTGRES_USER:-nexuslims} \${POSTGRES_DB:-nexuslims}"

# User management
alias admin-list-users="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); [print(f\\\"{u.username} ({u.email}) - Active: {u.is_active}, Admin: {u.is_superuser}\\\") for u in User.objects.all()]\""
alias admin-export-users="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python manage.py dumpdata auth.User --indent 2 > users_\$(date +%Y%m%d_%H%M%S).json"
alias admin-import-users="docker exec -i ${COMPOSE_PROJECT_NAME}_cdcs python manage.py loaddata"

# System maintenance
alias admin-clean-sessions="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python manage.py clearsessions"
alias admin-clean-cache="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python manage.py shell -c \"from django.core.cache import cache; cache.clear(); print('Cache cleared')\""

# Data statistics
alias admin-stats="docker exec ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/show_stats.py"

# Environment initialization
alias admin-init="docker exec -it ${COMPOSE_PROJECT_NAME}_cdcs python /srv/scripts/init_environment.py"

echo "NexusLIMS-CDCS Administrative Commands Loaded!"
echo "Project: ${COMPOSE_PROJECT_NAME}"
echo ""
echo "  💾 Backup & Restore:"
echo "    admin-backup          - Backup all CDCS data (templates, records, blobs, users)"
echo "    admin-restore         - Restore CDCS data from backup directory"
echo ""
echo "  🗄️  Database:"
echo "    admin-db-dump         - Create PostgreSQL database dump"
echo "    admin-db-restore      - Restore PostgreSQL database (pipe SQL file to stdin)"
echo ""
echo "  👥 User Management:"
echo "    admin-list-users      - List all users with status"
echo "    admin-export-users    - Export users to JSON fixture"
echo "    admin-import-users    - Import users from JSON fixture (provide filename)"
echo ""
echo "  🧹 Maintenance:"
echo "    admin-clean-sessions  - Remove expired sessions"
echo "    admin-clean-cache     - Clear Redis cache"
echo ""
echo "  📊 Statistics:"
echo "    admin-stats           - Show system statistics (users, records, templates)"
echo ""
echo "  🚀 Initialization:"
echo "    admin-init            - Initialize environment (create superuser, load schema & XSLT)"
echo ""
echo "To use these commands, run: source admin-commands.sh"
echo ""
