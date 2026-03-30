OK here's the plan. I'll implement this cleanly:

1. **Create `caddy/tls.caddy`** — an empty file (no-op for ACME production)
2. **Create `caddy/tls.local.caddy`** — contains the `tls` directive using env vars
3. **Add `import` directives** to `Caddyfile.prod` in both server blocks, importing `/etc/caddy/tls.caddy`
4. **Create `docker-compose.local-certs.yml`** — mounts the cert files AND mounts `tls.local.caddy` over `tls.caddy`
5. **Add a `dc-local` alias** to `admin-commands.sh`
6. **Update the docs** to just say "set `CADDY_CERTS_HOST_PATH` and use `dc-local`"
