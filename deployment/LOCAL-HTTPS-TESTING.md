# Local HTTPS Testing Environment

This guide explains how to set up a local production-like environment with HTTPS for testing production deployment procedures.

## 1. Install mkcert

See [https://github.com/FiloSottile/mkcert](https://github.com/FiloSottile/mkcert) for details.
This tool allows you to easily make locally trusted development certificates with any hostname.

```bash
# These instructions are for MacOS; for other platforms, follow the mkcert docs
brew install mkcert
brew install nss  # Firefox support
mkcert -install
```

## 2. Generate Certificates

Our hostname in this example will be `nexuslims-local.test`:

```bash
sudo mkdir -p /opt/nexuslims/local-certs
sudo chown $USER:staff /opt/nexuslims/local-certs

cd /opt/nexuslims/local-certs
mkcert \
  "nexuslims-local.test" \
  "files.nexuslims-local.test" \
  "localhost" \
  "127.0.0.1" \
  "::1"
```

This creates:
- `nexuslims-local.test+4.pem` (certificate)
- `nexuslims-local.test+4-key.pem` (private key)

### 3. Update /etc/hosts

This will redirect the two domains to your localhost address:

```bash
sudo tee -a /etc/hosts << EOF
127.0.0.1 nexuslims-local.test
127.0.0.1 files.nexuslims-local.test
EOF
```

### 4. Create Backups Directory

```bash
sudo mkdir -p /opt/nexuslims/backups
sudo chown $USER:staff /opt/nexuslims/backups
```

### 5. Configure Environment

```bash
cd deployment
cp .env.prod.example .env
```

Change the domain URLS and Caddy cert path in the `.env` file:

```bash
DOMAIN=nexuslims-local.test
FILES_DOMAIN=files.nexuslims-local.test

CADDY_CERTS_HOST_PATH=/opt/nexuslims/local-certs
```

Also change the host paths for the fileserver to match your setup:

```bash
NX_DATA_HOST_PATH=/mnt/nexuslims/data
NX_INSTRUMENT_DATA_HOST_PATH=/mnt/nexuslims/instrument-data
```

### 6. Start Services

```bash
source admin-commands.sh
dc-prod up -d
admin-init   # set up superuser, initialize XSLT, etc.
```

## Testing Production Procedures

With this setup, you can now test production procedures from `PRODUCTION.md`:

### Test Backups

```bash
source admin-commands.sh
admin-backup

# Check backup was created
ls -la /opt/nexuslims/backups/
```

### Test Compose Alias

```bash
source admin-commands.sh

# Use the dc-prod alias (though for local testing you might want dc-local-test)
dc-prod ps
dc-prod logs -f
```

### Test Database Operations

```bash
source admin-commands.sh

# Create a database dump
admin-db-dump

# View statistics
admin-stats
```

### Test SSL Certificate

```bash
# Verify HTTPS is working with trusted certificate
curl -I https://nexuslims-local.test

# Check certificate details
openssl s_client -connect nexuslims-local.test:443 -servername nexuslims-local.test < /dev/null 2>/dev/null | openssl x509 -noout -dates -issuer
```

## Stopping the Environment

```bash
cd deployment
source admin-commands.sh

dc-prod down
```

## Cleanup

To completely remove the local test environment:

```bash
# Stop containers
cd deployment
source admin-commands.sh

dc-prod down -v     # also removes volumes/data

# Remove certificates
sudo rm -rf /opt/nexuslims/local-certs

# Remove backups
sudo rm -rf /opt/nexuslims/backups

# Remove /etc/hosts entries (manually edit or run):
sudo sed -i.bak '/nexuslims-local.test/d' /etc/hosts
```

## Differences from Production

This local test environment differs from production in these ways:

1. **Certificates**: Uses mkcert instead of Let's Encrypt
2. **Domains**: Uses `.test` TLD instead of real domains
3. **DNS**: Uses `/etc/hosts` instead of real DNS
4. **Data**: Uses test data from `deployment/test-data/`
5. **Passwords**: Uses simple test passwords (don't use in production!)

## Troubleshooting

### Certificate Not Trusted

If browsers show "not secure":

```bash
# Reinstall mkcert CA
mkcert -install

# Restart browser
```

### Cannot Access URLs

Check `/etc/hosts`:
```bash
cat /etc/hosts | grep nexuslims
```

Should show:
```
127.0.0.1 nexuslims-local.test
127.0.0.1 files.nexuslims-local.test
```

### Port Already in Use

If ports 80/443 are in use:
```bash
# Find what's using the ports
sudo lsof -i :80
sudo lsof -i :443

# Stop the conflicting service
```

## Next Steps

Once your local HTTPS test environment is working:

1. **Test PRODUCTION.md procedures**: Walk through each section to verify instructions
2. **Test backup/restore**: Ensure backup system works correctly
3. **Test upgrades**: Practice the upgrade procedure
4. **Test rollback**: Verify rollback works
5. **Document issues**: Note any problems for fixing in PRODUCTION.md

## Support

For issues with this local test setup, check:
- mkcert documentation: https://github.com/FiloSottile/mkcert
- Docker Compose documentation: https://docs.docker.com/compose/
- Main PRODUCTION.md guide
