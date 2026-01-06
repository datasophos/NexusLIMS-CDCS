# Dockerfile.caddy-custom
FROM golang:1.25.5 AS builder

# Install xcaddy (the Caddy builder with plugin support)
RUN go install github.com/caddyserver/xcaddy/cmd/xcaddy@latest

# Build Caddy with your desired modules
RUN xcaddy build --with github.com/mediafoundation/caddy-bandwidth \
                 --output /usr/bin/caddy

# Use the custom-built Caddy
FROM alpine:latest

COPY --from=builder /usr/bin/caddy /usr/bin/caddy

# # Your existing Caddy configuration
# COPY --from=builder /etc/caddy/Caddyfile /etc/caddy/Caddyfile
# COPY --from=builder /etc/ssl/caddy /etc/ssl/caddy

# # Expose ports
# EXPOSE 80 443

# Run Caddy
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
