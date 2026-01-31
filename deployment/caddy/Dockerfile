# Dockerfile.caddy-custom
FROM golang:1.25.5 AS builder

# Install xcaddy (the Caddy builder with plugin support)
RUN go install github.com/caddyserver/xcaddy/cmd/xcaddy@latest

# Building with the caddy-bandwidth plugin allows us to limit bandwidth, if needed
RUN xcaddy build --with github.com/mediafoundation/caddy-bandwidth \
                 --output /usr/bin/caddy

# Use the custom-built Caddy
FROM alpine:latest

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Run Caddy via entrypoint (handles conditional TLS configuration)
ENTRYPOINT ["/docker-entrypoint.sh"]
