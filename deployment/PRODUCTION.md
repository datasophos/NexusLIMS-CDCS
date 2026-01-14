# NexusLIMS-CDCS Production Deployment Guide

This guide covers deploying NexusLIMS-CDCS to a production environment with
proper security, SSL certificates, and data management.

## Table of Contents

- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Domain and DNS Setup](#domain-and-dns-setup)
- [SSL Certificate Options](#ssl-certificate-options)
- [Environment Configuration](#environment-configuration)
- [File Storage Setup](#file-storage-setup)
- [Deployment](#deployment)
- [Post-Deployment](#post-deployment)
- [Security Hardening](#security-hardening)
- [Backup and Recovery](#backup-and-recovery)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [Upgrading](#upgrading)

## Prerequisites

### Required Knowledge
- Linux system administration
- Docker and Docker Compose
- Basic understanding of DNS and SSL/TLS certificates
- Basic PostgreSQL database administration
- Web server/reverse proxy concepts

### Required Access
- Root or sudo access to production server
- DNS management for your domain
- (Optional) CIFS/SMB or NFS for data files
- (Optional) SMTP server for application notifications

## System Requirements

These instructions assume you are running on a Linux system. They should generally
also work on a Mac, but there are some peculiarities with how Docker mounts work on MacOS.
Please see the [docker documentation](https://docs.docker.com/desktop/settings/mac/#file-sharing)
for details.

### Minimum Hardware
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 50 GB minimum (excluding data files)
  - System: 20 GB
  - Docker volumes: 10 GB
  - Database: 10 GB
  - Logs: 10 GB

### Recommended Hardware
- **CPU**: 8 cores
- **RAM**: 16 GB
- **Disk**: 100+ GB SSD (excluding data files)
- **Network**: 1 Gbps

### Software
- **OS**: Ubuntu 22.04 LTS or RHEL 8+ (recommended)
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Git**: 2.0+

### Network Requirements
- **Firewall**: Ports 80 and 443 open to the internet (for ACME certificate validation, can be avoided with manual certificate management)
- **DNS**: Ability to set or request DNS records pointing to your server
- **Optional**: Firewall rules for database and Redis ports if accessed externally

## Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] Production server provisioned and accessible
- [ ] Domain name(s) registered and DNS configured
- [ ] SSL certificate strategy determined (ACME recommended)
- [ ] Data storage locations identified
- [ ] Backup strategy planned
- [ ] Monitoring solution chosen
- [ ] Strong passwords generated for database and Redis
- [ ] Django secret key generated (minimum 50 characters)
- [ ] SMTP server configured for email notifications (optional)

## Domain and DNS Setup

### Required DNS Records

(Throughout this guide, `nexuslims.example.com` will be used as a placeholder to
represent whatever URL you are using)

You need two subdomains:
1. **Main application**: `nexuslims.example.com`
2. **File server**: `files.nexuslims.example.com`

### DNS Configuration

Create A records pointing to your server's public IP:

```
nexuslims.example.com.       A    203.0.113.42
files.nexuslims.example.com. A    203.0.113.42
```

### Verify DNS Propagation

Before deployment, verify DNS is working:

```bash
dig nexuslims.example.com
dig files.nexuslims.example.com
```

Both should return your server's IP address.

## SSL Certificate Options

The default NexusLIMS-CDCS deployment uses Caddy as a reverse proxy, which supports multiple certificate options.

### Option 1: Automatic ACME (Let's Encrypt) - **RECOMMENDED**

**Best for**: Production deployments with external network access

**Advantages**:
- [Fully automated certificate issuance and renewal](https://caddyserver.com/docs/automatic-https)
- Free
- Trusted by all browsers
- No manual intervention required

**Requirements**:
1. Domain DNS points to server's public IP
2. Ports 80 and 443 accessible from internet
3. Valid email address for notifications

**Configuration**:

Set in your `.env` file:
```bash
CADDY_ACME_EMAIL=admin@example.com
```

No changes needed in `Caddyfile.prod` - it's configured for ACME by default.

**How it works**:
1. Caddy automatically requests certificates from Let's Encrypt on first HTTPS request
2. Let's Encrypt validates domain ownership via HTTP-01 challenge
3. Certificates are stored in Docker volume `caddy_data`
4. Caddy automatically renews certificates before expiration

**Verification**:
```bash
# Check certificate after deployment
openssl s_client -connect nexuslims.example.com:443 -servername nexuslims.example.com < /dev/null 2>/dev/null | openssl x509 -noout -dates -issuer
```

Should show Let's Encrypt as issuer.

### Option 2: Manual Certificates

**Best for**: Organizations with existing PKI or certificate vendors

**Use when**:
- You have existing certificates from a vendor
- Your organization requires specific internal CA for certificate signing
- You have wildcard certificates

**Configuration**:

*FYI:* for local testing of a production config, you can use the [`mkcert`](https://github.com/FiloSottile/mkcert)
tool (for trusted self-signed certs) and edits to `/etc/hosts` to generate a pseudo-deployment config.

1. **Prepare certificates**:
   - Full chain certificate: `fullchain.pem`
   - Private key: `privkey.pem`

2. **Create certificate directory**:
   ```bash
   mkdir -p /opt/nexuslims/certs
   chmod 700 /opt/nexuslims/certs
   cp fullchain.pem /opt/nexuslims/certs/
   cp privkey.pem /opt/nexuslims/certs/
   chmod 600 /opt/nexuslims/certs/*
   ```

3. **Mount certificates in `docker-compose.prod.yml`**:
   ```yaml
   services:
     caddy:
       volumes:
         - /opt/nexuslims/certs:/etc/caddy/certs:ro
   ```

4. **Update `caddy/Caddyfile.prod`**:
  - Add `tls` lines pointing at the certificates
  
   ```caddyfile
   # Main application
   https://{$DOMAIN} {
       tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem
       # ... rest of config
   }

   # File server
   https://{$FILES_DOMAIN} {
       tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem
       # ... rest of config
   }
   ```

**Certificate Renewal**:
You're responsible for renewing certificates before expiration.

## Environment Configuration

### 1. Clone Repository

```bash
cd /opt/nexuslims
git clone https://github.com/datasophos/NexusLIMS-CDCS.git
cd NexusLIMS-CDCS/deployment
```

### 2. Create `.env` File

```bash
cp .env.prod.example .env
```

### 3. Configure Environment Variables

Edit `.env` with production values, following the instructions in the file.

### 4. Secure the `.env` File

```bash
chmod 600 .env
```

**CRITICAL**: Never commit `.env` to version control!

## File Server Setup

### Overview

NexusLIMS-CDCS comes bundled with a Caddy fileserver that serves two types of files:

1. **NexusLIMS data**: Thumbnail images, metadata files, and other data (read-only)
2. **Instrument data**: Raw microscopy data files from instruments (read-only)

In production, these locations will likely be remote network-mounted locations, but
that is not strictly necessary. This section reviews some different possible configs.

### Storage Options

#### Option 1: Local Storage

Best for small research group or individual setups.

```bash
# Create directories
sudo mkdir -p /mnt/nexuslims/data
sudo mkdir -p /mnt/nexuslims/instrument-data  # instruments should store their data here

# Set ownership
sudo chown -R $USER:$USER /mnt/nexuslims

# Set permissions
sudo chmod -R 755 /mnt/nexuslims
```

#### Option 2: NFS Mount

Best for shared storage across multiple servers.

```bash
# Install NFS client
sudo apt-get install nfs-common  # Ubuntu/Debian
# or
sudo yum install nfs-utils        # RHEL/CentOS

# Create mount points
sudo mkdir -p /mnt/nexuslims/data
sudo mkdir -p /mnt/nexuslims/instrument-data

# Mount NFS shares
sudo mount -t nfs nfs-server:/export/nexuslims/data /mnt/nexuslims/data
sudo mount -t nfs nfs-server:/export/nexuslims/instrument-data /mnt/nexuslims/instrument-data

# Add to /etc/fstab for persistence
echo "nfs-server:/export/nexuslims/data /mnt/nexuslims/data nfs defaults 0 0" | sudo tee -a /etc/fstab
echo "nfs-server:/export/nexuslims/instrument-data /mnt/nexuslims/instrument-data nfs defaults 0 0" | sudo tee -a /etc/fstab
```

#### Option 3: CIFS/SMB Mount

Best for Windows file shares or NAS devices using SMB protocol (common in enterprise environments).

```bash
# Install CIFS utilities
sudo apt-get install cifs-utils  # Ubuntu/Debian
# or
sudo yum install cifs-utils       # RHEL/CentOS

# Create mount points
sudo mkdir -p /mnt/nexuslims/data
sudo mkdir -p /mnt/nexuslims/instrument-data

# Create credentials file for security (recommended)
sudo mkdir -p /etc/smbcredentials
sudo touch /etc/smbcredentials/nexuslims.cred
sudo chmod 600 /etc/smbcredentials/nexuslims.cred

# Add credentials to file
sudo tee /etc/smbcredentials/nexuslims.cred > /dev/null << EOF
username=your_smb_username
password=your_smb_password
domain=WORKGROUP
EOF

# Mount CIFS shares
sudo mount -t cifs //nas-server/nexuslims-data /mnt/nexuslims/data \
  -o credentials=/etc/smbcredentials/nexuslims.cred,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755

sudo mount -t cifs //nas-server/nexuslims-instrument-data /mnt/nexuslims/instrument-data \
  -o credentials=/etc/smbcredentials/nexuslims.cred,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755

# Add to /etc/fstab for persistence
echo "//nas-server/nexuslims-data /mnt/nexuslims/data cifs credentials=/etc/smbcredentials/nexuslims.cred,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755,_netdev 0 0" | sudo tee -a /etc/fstab
echo "//nas-server/nexuslims-instrument-data /mnt/nexuslims/instrument-data cifs credentials=/etc/smbcredentials/nexuslims.cred,uid=$(id -u),gid=$(id -g),file_mode=0755,dir_mode=0755,_netdev 0 0" | sudo tee -a /etc/fstab

# Verify mounts
sudo mount -a
```

**Notes**:
- Replace `nas-server` with your NAS hostname or IP address
- Replace share names (`nexuslims-data`, `nexuslims-instrument-data`) with your actual share names
- The `_netdev` option prevents mounting before network is available
- The `uid` and `gid` options ensure proper file ownership
- For Active Directory domains, update the `domain` value in the credentials file

## Deployment

> **Tip**: This guide uses the `dc-prod` alias (shortcut for `docker compose -f docker-compose.base.yml -f docker-compose.prod.yml`).
> This alias is available when you source the admin commands:
> ```bash
> cd /opt/nexuslims/NexusLIMS-CDCS/deployment
> source admin-commands.sh
> ```
> Then use `dc-prod up -d`, `dc-prod logs -f`, etc.

### 1. Build and Pull Images

```bash
cd /opt/nexuslims/NexusLIMS-CDCS/deployment

# Source admin commands to get dc-prod alias
source admin-commands.sh

# Build custom images (caddy, cdcs) and pull standard images (postgres, redis)
dc-prod build  # this will probably take a few minutes the first time you build the images, but will be nearly instant after
dc-prod pull
```

### 2. Start Services

```bash
dc-prod up -d
```

### 3. Monitor Startup

```bash
# Watch logs
dc-prod logs -f

# Check service status
dc-prod ps
```

All services should show `Up` and `healthy`.

### 4. Verify Certificate Acquisition

If using ACME, watch Caddy logs for certificate issuance:

```bash
dc-prod logs -f caddy
```

You should see:
```
certificate obtained successfully
```

### 5. Access Application

Navigate to your domain:
```
https://nexuslims.example.com
```

You should see the NexusLIMS-CDCS login page with a valid SSL certificate.

## Post-Deployment

### 1. Run Initialization Script

The initialization script automates all post-deployment setup:

```bash
# Source admin commands
cd /opt/nexuslims/NexusLIMS-CDCS/deployment
source admin-commands.sh

# Run initialization (interactive - will prompt for superuser credentials)
admin-init
```

The script will:
1. ✅ Verify database migrations are complete
2. ✅ Compile Django translations
3. ✅ Create superuser (prompts for username, email, password)
4. ✅ Configure anonymous group permissions for explore app
5. ✅ Upload NexusLIMS schema from `/srv/test-data/nexus-experiment.xsd`
6. ✅ Load and configure XSLT stylesheets (automatically patched with production URLs)
7. ✅ Load data exporters

**Expected Output**:
```
======================================================================
NexusLIMS-CDCS Production Environment Initialization
======================================================================
→ Checking database migrations...
✓ Database migrations are complete
→ Compiling translations...
✓ Translations compiled successfully
→ Checking for superuser...
→ No superuser found. Creating superuser (you will be prompted for credentials)...
Username (leave blank to use 'root'): admin
Email address: admin@example.com
Password: *****
Password (again): *****
Superuser created successfully.
✓ Superuser created: admin
→ Configuring anonymous group permissions...
✓ Granted 'core_explore_keyword_app' permission to 'anonymous' group
→ Uploading NexusLIMS schema...
✓ Template 'Nexus Experiment Schema' created (ID: 1)
→ Uploading XSLT stylesheets...
→ Patching URLs in detail_stylesheet.xsl...
→   datasetBaseUrl: https://files.nexuslims.example.com/instrument-data
→   previewBaseUrl: https://files.nexuslims.example.com/data
✓   ✓ datasetBaseUrl patched
✓   ✓ previewBaseUrl patched
✓ Stylesheet 'detail_stylesheet.xsl' created (ID: 1)
→ Patching URLs in list_stylesheet.xsl...
→   datasetBaseUrl: https://files.nexuslims.example.com/instrument-data
→   previewBaseUrl: https://files.nexuslims.example.com/data
✓   ✓ datasetBaseUrl patched
✓   ✓ previewBaseUrl patched
✓ Stylesheet 'list_stylesheet.xsl' created (ID: 2)
✓ XSLT rendering configured (ID: 1)
→ Loading exporters...
Exporters were loaded in database.
→ Removed BLOB exporter (ID: None)
✓ Loaded 2 exporters: JSON, XML
======================================================================
✓ Initialization complete!
  Superuser: admin
  Schema: Nexus Experiment Schema

Next steps:
  1. Access the site: https://nexuslims.example.com
  2. Login with your superuser credentials
  3. Begin uploading data records via the NexusLIMS backend
  4. Explore data: https://nexuslims.example.com/explore/keyword/
======================================================================
```

### 2. Verify Installation

Check that everything was set up correctly:

```bash
# Source admin commands
cd /opt/nexuslims/NexusLIMS-CDCS/deployment
source admin-commands.sh

# View system statistics
admin-stats
```

Expected output:
```
============================================================
NexusLIMS-CDCS System Statistics
============================================================

👥 Users:
  Total:      2
  Active:     2
  Superusers: 1

📋 Templates:
  Total: 1
    - Nexus Experiment Schema (Version 1)

📄 Data Records:
  Total: 2

🎨 XSLT Stylesheets:
  Total: 2
    - detail_stylesheet.xsl
    - list_stylesheet.xsl

============================================================
```

### 3. Test File Serving

Navigate to file server:
```
https://files.nexuslims.example.com/data/
https://files.nexuslims.example.com/instrument-data/
```

Both should show directory listings of your data.

### 4. Create Backup Directory

Create the backup directory on the host that will be mounted into the container:

```bash
# Create backup directory on host
sudo mkdir -p /opt/nexuslims/backups
sudo chown $USER:$USER /opt/nexuslims/backups
```

**Important - Permissions**: The backup directory MUST be owned by the user running Docker (not root), otherwise the backup script will fail with permission errors when trying to create backup subdirectories. This is especially critical for:
- **Docker Desktop for Mac/Windows**: These systems map your host user to the container, so the directory must be owned by your user account
- **Linux**: The directory should be owned by the user who will run the docker compose commands

If you see "Permission denied" errors when running backups, verify ownership with:
```bash
ls -la /opt/nexuslims/
# Should show: drwxr-xr-x ... yourusername yourgroup ... backups
```

**Important**: After creating this directory, you need to restart the services for the mount to take effect:

```bash
cd /opt/nexuslims/NexusLIMS-CDCS/deployment
source admin-commands.sh
dc-prod down
dc-prod up -d
```

### 5. Configure Automated Backups

Set up a daily backup script:

```bash
# Create backup script
cat > /opt/nexuslims-backup.sh << 'EOF'
#!/bin/bash
set -e

cd /opt/nexuslims/NexusLIMS-CDCS/deployment
source admin-commands.sh

# Run backup (stored directly on host at /opt/nexuslims/backups/)
admin-backup

# Also create a database dump
admin-db-dump
mv backup_*.sql /opt/nexuslims/backups/

# Remove backups older than 30 days
find /opt/nexuslims/backups -type d -name "backup_*" -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
find /opt/nexuslims/backups -type f -name "backup_*.sql" -mtime +30 -delete 2>/dev/null || true
EOF

chmod +x /opt/nexuslims-backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/nexuslims-backup.sh") | crontab -
```

## Security Hardening

*Note:* these are general recommendations, not a full security audit of the application.

### 1. Firewall Configuration

**UFW (Ubuntu)**:
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

**firewalld (RHEL)**:
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### 2. Database Security

**Don't expose PostgreSQL port** externally unless absolutely necessary. If you must:

```bash
# Restrict to specific IPs
sudo ufw allow from 10.0.0.0/8 to any port 5532
```

**Strong passwords**: Already set in `.env`

**Regular updates**: Keep PostgreSQL container updated

### 3. Redis Security

**Bind to localhost**: Already configured in base compose

**Password protected**: Set via `REDIS_PASS`

**Don't expose port**: Keep `REDIS_HOST_PORT` unmapped unless needed

### 4. Application Security

**HTTPS only**: Enforced by Caddy

**CSRF protection**: Enabled in Django settings

**Secure cookies**: `SESSION_COOKIE_SECURE=True` in prod settings

**XSS protection**: Django templates auto-escape

### 5. Container Security

**Keep images updated**:
```bash
cd /opt/nexuslims/NexusLIMS-CDCS/deployment
source admin-commands.sh
dc-prod pull
dc-prod up -d
```

### 6. System Security

**Keep OS updated**:
```bash
sudo apt-get update && sudo apt-get upgrade  # Ubuntu
sudo yum update                               # RHEL
```

**Disable root login**:
```bash
sudo vim /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd
```

**Use SSH keys**: Disable password authentication

**Enable automatic security updates**: Consider unattended-upgrades (Ubuntu)

### 7. Monitoring and Logging

**Log retention**: Rotate Docker logs

```bash
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

## Backup and Recovery

### Automated Backups

Backups include:
- Templates (XSD schemas)
- Data records (XML)
- Binary blobs (images, files)
- Users (Django fixture)
- XSLT stylesheets
- Persistent queries

**Location**: Backups are stored at `/opt/nexuslims/backups/backup_YYYYMMDD_HHMMSS/` on the host.

**Volume Mount**: The backup directory is mounted as a Docker volume:
- **Host path**: `/opt/nexuslims/backups` (configurable via `NX_CDCS_BACKUPS_HOST_PATH`)
- **Container path**: `/srv/nexuslims/backups`

This means:
- ✅ Backups written by the container are immediately accessible on the host
- ✅ No need to copy files out of the container after backup
- ✅ No need to copy files into the container for restore
- ✅ Backups persist even if containers are removed
- ✅ Easy to access backups for off-site copying or examination

### Manual Backup

```bash
cd /opt/nexuslims/NexusLIMS-CDCS/deployment
source admin-commands.sh
admin-backup
```

### Database Dump

```bash
admin-db-dump
# Creates: backup_YYYYMMDD_HHMMSS.sql
```

### Restore from Backup

**Important**: Because the backup directory is mounted as a volume (`/opt/nexuslims/backups` → `/srv/nexuslims/backups`), the container can directly access backup files on the host. There is no need to copy files into the container before restoring.

**Database Restore** (for full disaster recovery):

```bash
cd /opt/nexuslims/NexusLIMS-CDCS/deployment
source admin-commands.sh

# Stop services
dc-prod down

# Start database only
dc-prod up -d postgres redis

# Wait for postgres to be ready
sleep 10

# Restore database from SQL dump
cat backup_20260109_120000.sql | admin-db-restore

# Start all services
dc-prod up -d
```

**Note**: The backup script generates a `restore.sh` script inside the backup directory with instructions for restoring CDCS application data. However, for most disaster recovery scenarios, restoring the PostgreSQL database dump is sufficient as it contains all application state.

### Disaster Recovery Plan

1. **Off-site backups**: Copy backups to remote location
   ```bash
   # Sync backups to remote backup server
   rsync -avz /opt/nexuslims/backups/ backup-server:/backups/nexuslims/
   ```

2. **Data file backups**: Backup instrument data separately (large)
   ```bash
   rsync -avz /mnt/nexuslims/ backup-server:/data/nexuslims/
   ```

3. **Configuration backup**: Keep `.env` file backed up securely

4. **Recovery time objective (RTO)**: Plan for acceptable downtime

5. **Test restores**: Regularly test backup restoration

## Monitoring and Maintenance

> **Note**: The commands in this section use the `dc-prod` alias and admin commands. Make sure to source the admin commands first:
> ```bash
> cd /opt/nexuslims/NexusLIMS-CDCS/deployment
> source admin-commands.sh
> ```

### System Monitoring

**Container health**:
```bash
dc-prod ps
```

**Resource usage**:
```bash
docker stats
```

**System statistics**:
```bash
source admin-commands.sh
admin-stats
```

### Log Monitoring

**Application logs**:
```bash
dc-prod logs -f cdcs
```

**Database logs**:
```bash
dc-prod logs -f postgres
```

**Caddy logs**:
```bash
dc-prod logs -f caddy
```

### Maintenance Tasks

**Clear expired sessions** (weekly):
```bash
source admin-commands.sh
admin-clean-sessions
```

**Clear Redis cache** (as needed):
```bash
admin-clean-cache
```

**Update Docker images** (monthly):
```bash
dc-prod pull
dc-prod up -d
```

**Database vacuum** (monthly):
```bash
docker exec nexuslims_prod_cdcs_postgres vacuumdb -U nexuslims --all --analyze
```

### External Monitoring

Consider integrating:
- **Uptime monitoring**: Pingdom, UptimeRobot
- **Application monitoring**: Sentry, New Relic
- **Log aggregation**: ELK stack, Splunk
- **Alerting**: PagerDuty, Slack webhooks

## Troubleshooting

> **Note**: Commands in this section use the `dc-prod` alias. Source admin commands first if not already done:
> ```bash
> cd /opt/nexuslims/NexusLIMS-CDCS/deployment && source admin-commands.sh
> ```

### Certificate Issues

**Problem**: "Certificate not trusted" or "NET::ERR_CERT_AUTHORITY_INVALID"

**Solution**:
1. Verify DNS points to server:
   ```bash
   dig nexuslims.example.com
   ```

2. Check Caddy logs for certificate acquisition errors:
   ```bash
   dc-prod logs caddy | grep -i cert
   ```

3. Verify ports 80 and 443 are accessible:
   ```bash
   sudo netstat -tlnp | grep -E ':(80|443)'
   ```

4. Test ACME challenge:
   ```bash
   curl http://nexuslims.example.com/.well-known/acme-challenge/test
   ```

### Database Connection Errors

**Problem**: "FATAL: password authentication failed"

**Solution**:
1. Verify `POSTGRES_PASS` matches in `.env`
2. Restart services:
   ```bash
   dc-prod restart
   ```

### File Serving Issues

**Problem**: 404 errors on file server

**Solution**:
1. Verify file paths in `.env`:
   ```bash
   echo $NX_DATA_HOST_PATH
   echo $NX_INSTRUMENT_DATA_HOST_PATH
   ```

2. Check directory permissions:
   ```bash
   ls -la /mnt/nexuslims/data
   ls -la /mnt/nexuslims/instrument-data
   ```

3. Verify mounts in container:
   ```bash
   docker exec nexuslims_prod_cdcs ls -la /srv/nx-data
   docker exec nexuslims_prod_cdcs ls -la /srv/nx-instrument-data
   ```

### Application Not Starting

**Problem**: Container exits immediately

**Solution**:
1. Check logs:
   ```bash
   dc-prod logs cdcs
   ```

2. Verify environment variables:
   ```bash
   dc-prod config
   ```

3. Check health status:
   ```bash
   docker inspect nexuslims_prod_cdcs | grep -A 10 Health
   ```

### Performance Issues

**Problem**: Slow response times

**Solution**:
1. Check resource usage:
   ```bash
   docker stats
   ```

2. Review database performance:
   ```bash
   # Check active queries and locks
   docker exec nexuslims_prod_cdcs_postgres psql -U nexuslims -d nexuslims -c "SELECT pid, query, state, wait_event FROM pg_stat_activity WHERE state != 'idle';"

   # Check table statistics
   docker exec nexuslims_prod_cdcs_postgres psql -U nexuslims -d nexuslims -c "SELECT relname, n_tup_ins, n_tup_upd, n_tup_del FROM pg_stat_user_tables ORDER BY n_tup_ins DESC LIMIT 10;"
   ```

3. Clear cache:
   ```bash
   source admin-commands.sh
   admin-clean-cache
   ```

4. Optimize database:
   ```bash
   docker exec nexuslims_prod_cdcs_postgres vacuumdb -U nexuslims --all --full --analyze
   ```

## Upgrading

> **Note**: Upgrade commands use the `dc-prod` alias and admin commands. These are sourced automatically in the steps below.

### Application Updates

1. **Backup current deployment**:
   ```bash
   source admin-commands.sh
   admin-backup
   ```

2. **Pull latest code**:
   ```bash
   cd /opt/nexuslims/NexusLIMS-CDCS
   git fetch
   git checkout v3.19.0  # or desired version
   ```

3. **Review changelog**: Check for breaking changes

4. **Update environment**: Check for new variables in `.env.prod.example`

5. **Rebuild images**:
   ```bash
   cd deployment
   source admin-commands.sh
   dc-prod build
   ```

6. **Stop services**:
   ```bash
   dc-prod down
   ```

7. **Start services**:
   ```bash
   dc-prod up -d
   ```

8. **Run migrations**:
   ```bash
   docker exec nexuslims_prod_cdcs python manage.py migrate
   ```

9. **Verify**: Test application functionality

### Rollback

If upgrade fails:

1. **Stop services**:
   ```bash
   dc-prod down
   ```

2. **Checkout previous version**:
   ```bash
   git checkout v3.18.0
   ```

3. **Rebuild images with previous version**:
   ```bash
   cd deployment
   source admin-commands.sh
   dc-prod build
   ```

4. **Restore backup** (if database schema changed):
   ```bash
   source admin-commands.sh
   cat /opt/nexuslims/backups/backup_20260109_120000.sql | admin-db-restore
   ```

5. **Start services**:
   ```bash
   dc-prod up -d
   ```

## Support

For issues or questions:
- Review logs: `dc-prod logs`
- Check container status: `dc-prod ps`
- View system stats: `source admin-commands.sh && admin-stats`
- Consult main README: `../README.md`
- Review development docs: `README.md`

## Additional Resources

- **MDCS Documentation**: https://github.com/usnistgov/MDCS
- **Caddy Documentation**: https://caddyserver.com/docs/
- **Docker Compose**: https://docs.docker.com/compose/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Let's Encrypt**: https://letsencrypt.org/docs/
