#!/bin/sh
# Caddy entrypoint script for NexusLIMS
#
# This script enables custom TLS certificates when CADDY_CERTS_HOST_PATH is set.
# If not set, Caddy uses automatic ACME (Let's Encrypt) certificate management.

set -e

CADDYFILE="/etc/caddy/Caddyfile"
TLS_DIRECTIVE="tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem"

# Check if custom certificates should be used
if [ -n "$CADDY_CERTS_HOST_PATH" ]; then
    echo "Custom certificates enabled (CADDY_CERTS_HOST_PATH is set)"
    
    # Verify certificate files exist
    if [ ! -f /etc/caddy/certs/fullchain.pem ] || [ ! -f /etc/caddy/certs/privkey.pem ]; then
        echo "ERROR: Certificate files not found in /etc/caddy/certs/"
        echo "Expected files: fullchain.pem, privkey.pem"
        echo "Mounted from: $CADDY_CERTS_HOST_PATH"
        exit 1
    fi
    
    # Create a working copy of the Caddyfile and enable TLS directives
    cp "$CADDYFILE" /tmp/Caddyfile.patched
    
    # Uncomment the tls directive lines (remove "# " prefix)
    sed -i 's|# tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem|tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem|g' /tmp/Caddyfile.patched
    
    # Use the patched Caddyfile
    CADDYFILE="/tmp/Caddyfile.patched"
    
    echo "TLS directives enabled in Caddyfile"
else
    echo "Using automatic ACME (Let's Encrypt) certificate management"
fi

# Run Caddy with the appropriate Caddyfile
exec caddy run --config "$CADDYFILE" --adapter caddyfile
