#!/bin/sh
# Caddy entrypoint script for NexusLIMS
#
# This script enables custom TLS certificates when CADDY_CERTS_HOST_PATH is set.
# If not set, Caddy uses automatic ACME (Let's Encrypt) certificate management.

set -e

CADDYFILE="/etc/caddy/Caddyfile"
CADDYFILE_WORK="/tmp/Caddyfile.patched"

# Always work on a copy so that subsequent steps (NEMO, TLS) can each
# modify it without touching the read-only mount.
cp "$CADDYFILE" "$CADDYFILE_WORK"

# ---------------------------------------------------------------------------
# Optional: append NEMO site block
# ---------------------------------------------------------------------------
# Caddyfile.nemo is mounted by docker-compose.nemo.yml; when present and
# NEMO_DOMAIN is set the block is appended to the working Caddyfile so
# Caddy serves the NEMO reverse proxy.
if [ -n "$NEMO_DOMAIN" ] && [ -f /etc/caddy/Caddyfile.nemo ]; then
    echo "NEMO_DOMAIN is set — appending NEMO site block to Caddyfile"
    cat /etc/caddy/Caddyfile.nemo >> "$CADDYFILE_WORK"
else
    echo "NEMO_DOMAIN not set or Caddyfile.nemo not mounted — skipping NEMO block"
fi

# ---------------------------------------------------------------------------
# Optional: enable custom TLS certificates
# ---------------------------------------------------------------------------
# When CADDY_CERTS_HOST_PATH is set the tls directive lines (commented out
# by default in every site block) are uncommented so Caddy uses the
# certificates mounted from the host instead of ACME.
if [ -n "$CADDY_CERTS_HOST_PATH" ]; then
    echo "Custom certificates enabled (CADDY_CERTS_HOST_PATH is set)"

    # Verify certificate files exist
    if [ ! -f /etc/caddy/certs/fullchain.pem ] || [ ! -f /etc/caddy/certs/privkey.pem ]; then
        echo "ERROR: Certificate files not found in /etc/caddy/certs/"
        echo "Expected files: fullchain.pem, privkey.pem"
        echo "Mounted from: $CADDY_CERTS_HOST_PATH"
        exit 1
    fi

    # Uncomment the tls directive lines (remove "# " prefix)
    sed -i 's|# tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem|tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem|g' "$CADDYFILE_WORK"

    echo "TLS directives enabled in Caddyfile"
else
    echo "Using automatic ACME (Let's Encrypt) certificate management"
fi

# Run Caddy with the working Caddyfile
exec caddy run --config "$CADDYFILE_WORK" --adapter caddyfile
