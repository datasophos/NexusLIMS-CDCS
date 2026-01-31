# Administrative commands for NexusLIMS-CDCS (PowerShell)
# These commands are for backup, restore, and system administration
#
# Works with both dev and production deployments by using COMPOSE_PROJECT_NAME
# from your .env file (e.g., nexuslims_dev or nexuslims_prod)

# Parse .env file to get configuration
$envVars = @{}
if (Test-Path .env) {
    Get-Content .env | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' } | ForEach-Object {
        $key, $value = $_ -split '=', 2
        $envVars[$key.Trim()] = $value.Trim()
    }
}

$script:COMPOSE_PROJECT_NAME = if ($envVars['COMPOSE_PROJECT_NAME']) { $envVars['COMPOSE_PROJECT_NAME'] } else { 'nexuslims_prod' }
$script:NX_CDCS_BACKUPS_HOST_PATH = if ($envVars['NX_CDCS_BACKUPS_HOST_PATH']) { $envVars['NX_CDCS_BACKUPS_HOST_PATH'] } else { '.\backups' }
$script:POSTGRES_USER = if ($envVars['POSTGRES_USER']) { $envVars['POSTGRES_USER'] } else { 'nexuslims' }
$script:POSTGRES_DB = if ($envVars['POSTGRES_DB']) { $envVars['POSTGRES_DB'] } else { 'nexuslims' }

# Hide docker feature advertisements
$env:DOCKER_CLI_HINTS = "false"

# Docker Compose function for production
function dc-prod {
    $env:COMPOSE_BAKE = "true"
    docker compose -f docker-compose.base.yml -f docker-compose.prod.yml @args
}

# Backup and Restore
function admin-backup {
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs" python /srv/scripts/backup_cdcs.py 2>&1 | Where-Object { $_ -notmatch 'SSL_CERTIFICATES_DIR|Registered signals' }
}

function admin-restore {
    param(
        [Parameter(Position = 0)]
        [string]$BackupDir
    )

    if (-not $BackupDir) {
        Write-Host "Usage: admin-restore <backup_directory>"
        Write-Host ""
        Write-Host "Available backups:"
        
        $backups = Get-ChildItem -Path $script:NX_CDCS_BACKUPS_HOST_PATH -Filter "backup_*" -Directory -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 10
        
        if ($backups) {
            $backups | ForEach-Object { Write-Host "  $($_.FullName)" }
        } else {
            Write-Host "  No backups found in $script:NX_CDCS_BACKUPS_HOST_PATH"
        }
        return
    }

    # Check if backup directory exists on host
    if (-not (Test-Path $BackupDir -PathType Container)) {
        Write-Host "✗ Error: Backup directory not found: $BackupDir"
        return
    }

    # Convert host path to container path
    # Host: C:\nexuslims\backups\... -> Container: /srv/nexuslims/backups/...
    $containerBackupDir = $BackupDir -replace [regex]::Escape($script:NX_CDCS_BACKUPS_HOST_PATH), '/srv/nexuslims/backups' -replace '\\', '/'

    Write-Host "Restoring from: $BackupDir"
    Write-Host ""
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs" python /srv/scripts/restore_cdcs.py --all $containerBackupDir
}

# Database dumps (PostgreSQL)
function admin-db-dump {
    Write-Host "⚠️  WARNING: This creates a raw PostgreSQL dump for disaster recovery."
    Write-Host "   For normal backups, use 'admin-backup' instead."
    Write-Host ""
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = Join-Path $script:NX_CDCS_BACKUPS_HOST_PATH "db_backup_$timestamp.sql"
    
    Write-Host "Creating database dump..."
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs_postgres" pg_dump -U $script:POSTGRES_USER $script:POSTGRES_DB | Out-File -FilePath $backupFile -Encoding utf8
    Write-Host "✓ Database dump written to: $backupFile"
}

function admin-db-restore {
    param(
        [Parameter(Position = 0)]
        [string]$BackupFile
    )

    if (-not $BackupFile) {
        Write-Host "Usage: admin-db-restore <path_to_backup.sql>"
        return
    }

    if (-not (Test-Path $BackupFile)) {
        Write-Host "✗ Error: File not found: $BackupFile"
        return
    }

    Write-Host "⚠️  WARNING: This restores a raw PostgreSQL dump for disaster recovery."
    Write-Host "   This will DROP and RECREATE the entire database!"
    Write-Host "   ALL EXISTING DATA WILL BE LOST!"
    Write-Host "   For normal restore, use 'admin-restore <backup_dir>' instead."
    Write-Host ""
    
    $response = Read-Host "Continue with restore? (y/N)"
    if ($response -notmatch '^[Yy]$') {
        Write-Host "Restore cancelled"
        return
    }

    Write-Host ""
    Write-Host "🚨 FINAL WARNING: This will permanently delete all data in the database!"
    $confirm = Read-Host "Type 'DELETE' to confirm"
    if ($confirm -ne "DELETE") {
        Write-Host "Restore cancelled"
        return
    }

    Write-Host ""
    Write-Host "Stopping application containers..."
    dc-prod stop cdcs caddy 2>$null

    Write-Host "Terminating database connections..."
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs_postgres" psql -U $script:POSTGRES_USER postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$script:POSTGRES_DB' AND pid <> pg_backend_pid();" 2>&1 | Where-Object { $_ -notmatch 'SSL_CERTIFICATES_DIR|Registered signals' } | Out-Null

    Write-Host "Dropping database..."
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs_postgres" psql -U $script:POSTGRES_USER postgres -c "DROP DATABASE IF EXISTS $script:POSTGRES_DB;" 2>&1 | Where-Object { $_ -notmatch 'SSL_CERTIFICATES_DIR|Registered signals' }

    Write-Host "Recreating database..."
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs_postgres" psql -U $script:POSTGRES_USER postgres -c "CREATE DATABASE $script:POSTGRES_DB OWNER $script:POSTGRES_USER;" 2>&1 | Where-Object { $_ -notmatch 'SSL_CERTIFICATES_DIR|Registered signals' }

    Write-Host "Restoring database from: $BackupFile"
    Get-Content $BackupFile | docker exec -i "$script:COMPOSE_PROJECT_NAME`_cdcs_postgres" psql -U $script:POSTGRES_USER $script:POSTGRES_DB 2>&1 | Where-Object { $_ -notmatch 'SSL_CERTIFICATES_DIR|Registered signals|ERROR:.*already exists' }

    Write-Host "Restarting application containers..."
    dc-prod start cdcs caddy 2>$null

    Write-Host "✓ Database restore completed"
}

# User management
function admin-list-users {
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs" python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); [print(f`"{u.username} ({u.email}) - Active: {u.is_active}, Admin: {u.is_superuser}`") for u in User.objects.all()]" 2>&1 | Where-Object { $_ -notmatch 'SSL_CERTIFICATES_DIR|Registered signals' }
}

function admin-export-users {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = Join-Path $script:NX_CDCS_BACKUPS_HOST_PATH "users_$timestamp.json"
    
    Write-Host "Exporting users..."
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs" python manage.py dumpdata auth.User --indent 2 2>&1 | 
        Where-Object { $_ -notmatch 'SSL_CERTIFICATES_DIR|Registered signals' } | 
        Out-File -FilePath $backupFile -Encoding utf8
    Write-Host "✓ Users exported to: $backupFile"
}

function admin-import-users {
    param(
        [Parameter(Position = 0)]
        [string]$HostFile
    )

    if (-not $HostFile) {
        Write-Host "Usage: admin-import-users <path_to_users.json>"
        return
    }

    if (-not (Test-Path $HostFile)) {
        Write-Host "✗ Error: File not found: $HostFile"
        return
    }

    # Copy file into container and run loaddata
    $containerFile = "/tmp/users_import.json"
    docker cp $HostFile "$script:COMPOSE_PROJECT_NAME`_cdcs`:$containerFile"
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs" python manage.py loaddata $containerFile 2>&1 | Where-Object { $_ -notmatch 'SSL_CERTIFICATES_DIR|Registered signals' }
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs" rm $containerFile
}

# Data statistics
function admin-stats {
    docker exec "$script:COMPOSE_PROJECT_NAME`_cdcs" python /srv/scripts/show_stats.py 2>&1 | Where-Object { $_ -notmatch 'SSL_CERTIFICATES_DIR|Registered signals' }
}

# Environment initialization
function admin-init {
    docker exec -it "$script:COMPOSE_PROJECT_NAME`_cdcs" python /srv/scripts/init_environment.py
}

# Display help message
Write-Host "NexusLIMS-CDCS Administrative Commands Loaded!" -ForegroundColor Green
Write-Host "Project: $script:COMPOSE_PROJECT_NAME"
Write-Host ""
Write-Host "  🐳 Docker Compose:"
Write-Host "    dc-prod               - Shortcut for 'docker compose -f docker-compose.base.yml -f docker-compose.prod.yml'"
Write-Host ""
Write-Host "  💾 Backup & Restore:"
Write-Host "    admin-backup          - Backup all CDCS data (templates, records, blobs, users)"
Write-Host "    admin-restore <dir>   - Restore from backup directory"
Write-Host ""
Write-Host "  🗄️  Database:"
Write-Host "    admin-db-dump         - Create PostgreSQL database dump"
Write-Host "    admin-db-restore      - Restore PostgreSQL database from dumped file"
Write-Host ""
Write-Host "  👥 User Management:"
Write-Host "    admin-list-users      - List all users with status"
Write-Host "    admin-export-users    - Export users to JSON fixture"
Write-Host "    admin-import-users    - Import users from JSON fixture (provide filename)"
Write-Host ""
Write-Host "  📊 Statistics:"
Write-Host "    admin-stats           - Show system statistics (users, records, templates)"
Write-Host ""
Write-Host "  🚀 Initialization:"
Write-Host "    admin-init            - Initialize environment (create superuser, load schema & XSLT)"
Write-Host ""
Write-Host "To use these commands, run: " -NoNewline
Write-Host ". .\admin-commands.ps1" -ForegroundColor Cyan
Write-Host ""
