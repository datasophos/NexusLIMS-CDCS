# Local Deployment Testing Environment (with HTTPS)

This guide explains how to set up a local production-like environment with HTTPS for testing production deployment procedures.

## Overview

This setup creates a local environment that closely mimics production, allowing you to test deployment procedures, SSL certificates, backups, and other operations before running them on a live server.

**Use this when you need to:**
- Test production deployment procedures from `PRODUCTION.md`
- Verify backup/restore processes
- Practice upgrades and rollbacks
- Test SSL/TLS certificate handling

## Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose on Linux)
- **`mkcert`** for local certificate generation
- **Root/sudo access** for certificate installation and `/etc/hosts` modification
- **NexusLIMS backend** configured (see [NexusLIMS documentation](https://github.com/datasophos/NexusLIMS))

## Setup Steps

### 1. Install mkcert

[mkcert](https://github.com/FiloSottile/mkcert) creates locally-trusted development certificates.

```bash
# macOS
brew install mkcert
brew install nss  # Firefox support
mkcert -install

# Ubuntu/Debian
sudo apt install libnss3-tools
wget https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-v*-linux-amd64
sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
sudo chmod +x /usr/local/bin/mkcert
mkcert -install

# Windows (PowerShell as Administrator)
scoop install mkcert
mkcert -install
```

### 2. Generate Certificates

Using `nexuslims-local.test` as the hostname:

```bash
sudo mkdir -p /opt/nexuslims/local-certs
sudo chown ${USER}:staff /opt/nexuslims/local-certs  # macOS
# or: sudo chown ${USER}:${USER} /opt/nexuslims/local-certs  # Linux

cd /opt/nexuslims/local-certs
mkcert \
  "nexuslims-local.test" \
  "files.nexuslims-local.test" \
  "localhost" \
  "127.0.0.1" \
  "::1"
```

**Generated files:**
- `nexuslims-local.test+4.pem` (certificate)
- `nexuslims-local.test+4-key.pem` (private key)

**Note:** The `+4` in the filename indicates 4 additional SANs (Subject Alternative Names) beyond the main domain.

These files should be renamed to `fullchain.pem` (certificate) and `privkey.pem` (private key) to be compatible with the automatic local HTTPS configuration below.

### 3. Update System Hosts File

Configure DNS resolution to route test domains to localhost:

```bash
sudo tee -a /etc/hosts << EOF
127.0.0.1 nexuslims-local.test
127.0.0.1 files.nexuslims-local.test
EOF
```

**Verification:**
```bash
ping -c 1 nexuslims-local.test  # Should resolve to 127.0.0.1
```

### 4. Create Backup Directory

```bash
sudo mkdir -p /opt/nexuslims/backups
sudo chown ${USER}:staff /opt/nexuslims/backups  # macOS
# or: sudo chown ${USER}:${USER} /opt/nexuslims/backups  # Linux
```

### 5. Configure Environment

```bash
cd deployment
cp .env.prod.example .env
```

Edit `.env` to configure test domains and paths:

```bash
# Domain configuration
DOMAIN=nexuslims-local.test
FILES_DOMAIN=files.nexuslims-local.test

# Certificate path (must match step 2)
CADDY_CERTS_HOST_PATH=/opt/nexuslims/local-certs

# Data paths (adjust to match your NexusLIMS backend configuration)
NX_DATA_HOST_PATH=/path/to/your/nexuslims/data
NX_INSTRUMENT_DATA_HOST_PATH=/path/to/your/nexuslims/instrument-data

# Backup path
BACKUPS_HOST_PATH=/opt/nexuslims/backups

# API key for backend communication (optional, only if using backend integration)
# (generate with: python3 -c "from secrets import token_urlsafe; print(token_urlsafe(30))")
NX_ADMIN_API_TOKEN=your-secure-api-key-here
```

**Important:** Ensure `NX_DATA_HOST_PATH` and `NX_INSTRUMENT_DATA_HOST_PATH` match your NexusLIMS backend `NX_DATA_PATH` and `NX_INSTRUMENT_DATA_PATH` respectively. Set `NX_ADMIN_API_TOKEN` if you need NexusLIMS backend to communicate with the frontend for testing.

### 6. Start Services

```bash
source admin-commands.sh
dc-prod up -d
admin-init   # Creates superuser, initializes XSLT transformations
```

**Monitor startup:**
```bash
dc-prod logs -f
```

Press `Ctrl+C` to stop following logs (containers keep running).

### 7. Verify Access

**Web Interface:**
- Main site: https://nexuslims-local.test
- File server: https://files.nexuslims-local.test/data or https://files.nexuslims-local.test/instrument-data

**Login credentials**: whatever you specified when running `admin-init`

**API Access:**
```bash
# If you did not set NX_ADMIN_API_TOKEN before running `admin-init`,
# get your API token by logging into the web interface first, navigating
# to: https://nexuslims-local.test/staff-admin/authtoken/tokenproxy
# and click "Add token"

# Test API
export CDCS_TOKEN="your-api-token-here"
curl -s https://nexuslims-local.test/rest/data/ `
  -H "Authorization: Token $CDCS_TOKEN" | jq '.'
```

## Testing Production Procedures

With the local test environment running, you can safely test procedures from `PRODUCTION.md`.

### Test Backups

```bash
source admin-commands.sh
admin-backup

# Verify backup creation
ls -lh /opt/nexuslims/backups/
```

Backups include:
- PostgreSQL database dump
- MongoDB dump
- Redis snapshot
- File server data (if configured)

### Test Database Operations

```bash
source admin-commands.sh

# Create database dump
admin-db-dump

# View statistics
admin-stats

# Access database shell (PostgreSQL)
dc-prod exec postgres psql -U postgres cdcs
```

### Test SSL Certificate

```bash
# Verify HTTPS with trusted certificate
curl -I https://nexuslims-local.test

# Check certificate details
openssl s_client -connect nexuslims-local.test:443 \
  -servername nexuslims-local.test < /dev/null 2>/dev/null \
  | openssl x509 -noout -dates -issuer -subject
```

### Test Upgrade Procedures

Use this environment to practice upgrades before running on production:

1. Create a backup (`admin-backup`)
2. Pull new images (`dc-prod pull`)
3. Restart services (`dc-prod up -d`)
4. Run migrations if needed
5. Verify functionality

## Stopping the Environment

```bash
cd deployment
source admin-commands.sh
dc-prod down
```

**To preserve data** (recommended for testing), use `dc-prod down` without flags.

**To remove all data**, use `dc-prod down -v` (removes volumes).

## Cleanup

To completely remove the local test environment:

```bash
# Stop and remove containers/volumes
cd deployment
source admin-commands.sh
dc-prod down -v

# Remove certificates
sudo rm -rf /opt/nexuslims/local-certs

# Remove backups
sudo rm -rf /opt/nexuslims/backups

# Remove /etc/hosts entries
sudo sed -i.bak '/nexuslims-local.test/d' /etc/hosts

# Uninstall mkcert CA (optional)
mkcert -uninstall
```

## Differences from Production

| Aspect | Local Test | Production |
|--------|-----------|------------|
| **Certificates** | mkcert (locally-trusted) | Let's Encrypt (publicly-trusted) |
| **Domains** | `.test` TLD | Real domains (e.g., `.com`, `.edu`) |
| **DNS** | `/etc/hosts` | Real DNS records |
| **Data** | Test/sample data | Real facility data |
| **Passwords** | Simple test passwords | Strong production passwords |
| **Monitoring** | Manual inspection | Automated monitoring/alerts |

## Troubleshooting

### Certificate Not Trusted

**Symptoms:** Browser shows "Your connection is not private" or "not secure"

**Solutions:**
```bash
# Reinstall mkcert CA
mkcert -install

# Verify installation
mkcert -CAROOT

# Restart browser completely
```

**macOS specific:** May need to manually trust certificate in Keychain Access.

### Cannot Access URLs

**Check `/etc/hosts` entries:**
```bash
cat /etc/hosts | grep nexuslims
```

Should show:
```
127.0.0.1 nexuslims-local.test
127.0.0.1 files.nexuslims-local.test
```

**Test DNS resolution:**
```bash
ping -c 1 nexuslims-local.test
```

### Port Already in Use

**Symptoms:** Error starting Caddy (ports 80/443 conflict)

**Diagnosis:**
```bash
# Find what's using the ports
sudo lsof -i :80
sudo lsof -i :443
```

**Solutions:**
- Stop conflicting service
- Change Caddy ports in `docker-compose.prod.yml` (not recommended)
- Use different test domains

### Container Won't Start

**Check logs:**
```bash
dc-prod logs <service-name>
```

**Common issues:**
- Missing environment variables in `.env`
- Incorrect file paths
- Insufficient permissions on mounted volumes

### Database Connection Errors

**Verify database is running:**
```bash
dc-prod ps
```

**Check database logs:**
```bash
dc-prod logs postgres
```

**Reset database** (if needed):
```bash
dc-prod down
dc-prod up -d postgres
# Wait for initialization, then start other services
dc-prod up -d
```

## Next Steps

Once your local HTTPS test environment is working:

1. **Walk through PRODUCTION.md**: Test each deployment procedure
2. **Practice backups**: Create and verify backups
3. **Test restore**: Practice restoring from backup
4. **Practice upgrades**: Test the upgrade procedure
5. **Test rollback**: Verify you can rollback if needed
6. **Document gaps**: Note any unclear or missing steps in PRODUCTION.md

## Related Documentation

- [PRODUCTION.md](PRODUCTION.md) - Production deployment guide
- [NexusLIMS Backend Setup](https://github.com/datasophos/NexusLIMS) - Configure data paths
- [mkcert Documentation](https://github.com/FiloSottile/mkcert) - Certificate tool details
- [Docker Compose Reference](https://docs.docker.com/compose/) - Container orchestration
