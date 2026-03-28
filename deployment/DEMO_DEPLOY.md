# NexusLIMS Public Demo - Deployment Guide

Deployment target: `nexuslims-demo.datasophos.co` on Fly.io.

The demo stack consists of three Fly apps:
- `nexuslims-demo` - Django/Gunicorn app (this repo)
- `nexuslims-demo-db` - Self-hosted PostgreSQL 17
- `nexuslims-demo-redis` - Redis 8

Data resets every 2 hours via a scheduled Fly machine that drops and recreates
the database and restarts the app. The entrypoint re-initializes everything from
scratch on each start (migrate -> init users -> seed records).

---

## Prerequisites

- [Fly CLI](https://fly.io/docs/flyctl/install/) installed and authenticated
- [GitHub CLI](https://cli.github.com/) installed and authenticated (`gh auth login`)
- DNS access for `datasophos.co` to add CNAME records

---

## First-time Deployment

### 1. Authenticate with Fly

```bash
fly auth login
```

### 2. Create Fly apps

```bash
fly apps create nexuslims-demo
fly apps create nexuslims-demo-db
fly apps create nexuslims-demo-redis
```

### 3. Create persistent volumes

```bash
# PostgreSQL data volume (in iad region, 10GB)
fly volumes create postgres_data --app nexuslims-demo-db --region iad --size 10

# Redis data volume (in iad region, 1GB)
fly volumes create redis_data --app nexuslims-demo-redis --region iad --size 1
```

### 4. Set secrets

```bash
# Generate secrets first:
python3 -c "from secrets import token_urlsafe; print('DJANGO_SECRET_KEY:', token_urlsafe(50))"
python3 -c "from secrets import token_urlsafe; print('POSTGRES_PASS:', token_urlsafe(32))"
python3 -c "from secrets import token_urlsafe; print('REDIS_PASS:', token_urlsafe(32))"

fly secrets set \
  DJANGO_SECRET_KEY=<generated> \
  POSTGRES_PASS=<generated> \
  REDIS_PASS=<generated> \
  ALLOWED_HOSTS=nexuslims-demo.datasophos.co \
  CSRF_TRUSTED_ORIGINS=https://nexuslims-demo.datasophos.co \
  SERVER_URI=https://nexuslims-demo.datasophos.co \
  --app nexuslims-demo
```

### 5. Deploy PostgreSQL

Create `fly-db.toml`:
```toml
app = "nexuslims-demo-db"
primary_region = "iad"

[build]
  image = "postgres:17"

[env]
  POSTGRES_DB = "nexuslims"
  POSTGRES_USER = "nexuslims"

[mounts]
  source = "postgres_data"
  destination = "/var/lib/postgresql/data"

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

```bash
fly deploy --config fly-db.toml
```

### 6. Deploy Redis

Create `fly-redis.toml`:
```toml
app = "nexuslims-demo-redis"
primary_region = "iad"

[build]
  image = "redis:8-alpine"

[mounts]
  source = "redis_data"
  destination = "/data"

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

```bash
fly deploy --config fly-redis.toml
```

### 7. Deploy the main app

```bash
# From the repo root:
fly deploy --config fly.toml
```

The entrypoint automatically:
1. Runs migrations
2. Downloads demo fixture data from the `demo-fixtures-latest` GitHub Release if not already present
3. Runs `init_environment.py` and `seed_demo_records.py`

### 8. Configure DNS

Add these CNAMEs in your DNS provider:

| Name | Type | Value |
|------|------|-------|
| `nexuslims-demo` | CNAME | `nexuslims-demo.fly.dev` |
| `files.nexuslims-demo` | CNAME | `nexuslims-demo.fly.dev` |

Add Fly's custom domain (for TLS):
```bash
fly certs add nexuslims-demo.datasophos.co --app nexuslims-demo
fly certs add files.nexuslims-demo.datasophos.co --app nexuslims-demo
```

---

## Scheduled Reset (every 2 hours)

The reset is handled by a scheduled Fly machine that:
1. Drops and recreates the PostgreSQL database
2. Flushes Redis
3. Restarts the main app machine (entrypoint re-initializes everything)

Create `fly-reset.toml`:
```toml
app = "nexuslims-demo"
primary_region = "iad"

[processes]
  reset = "/deployment/scripts/reset_demo.sh"

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

Create `deployment/scripts/reset_demo.sh`:
```bash
#!/bin/bash
set -e

echo "Resetting demo environment..."

# 1. Wipe Postgres: drop + recreate database
PGPASSWORD="$POSTGRES_PASS" psql \
  -h "$POSTGRES_HOST" -U "$POSTGRES_USER" \
  -c "DROP DATABASE IF EXISTS nexuslims;" \
  -c "CREATE DATABASE nexuslims;"

# 2. Flush Redis
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASS" FLUSHALL

# 3. Restart the cdcs machine (entrypoint re-initializes everything)
CDCS_MACHINE_ID=$(fly machines list --app nexuslims-demo --json | jq -r '.[0].id')
fly machine restart "$CDCS_MACHINE_ID" --app nexuslims-demo

echo "Reset complete."
```

Deploy as a scheduled machine:
```bash
fly machine run \
  --app nexuslims-demo \
  --schedule every_2h \
  --entrypoint /deployment/scripts/reset_demo.sh \
  --region iad \
  --memory 256 \
  registry.fly.io/nexuslims-demo:latest
```

---

## Local Demo Testing

```bash
cd deployment
cp .env.demo.example .env   # edit secrets as needed

# Download fixture data (first time, or after updating fixtures)
./scripts/manage-demo-fixtures.sh download

source demo-commands.sh
demo-up
```

Visit `https://nexuslims-demo.localhost` (after Caddy issues local cert).

Simulate the 2-hour reset:
```bash
demo-reset
```

---

## Verification Checklist

1. Visit `https://nexuslims-demo.datasophos.co` - auto-logged in as `admin`
2. Browse to any record - verify download warning is visible
3. Visit `/admin/` - verify full Django admin access
4. Log out, visit `/accounts/login/` - verify credentials panel with 3 accounts
5. Login as `readonly_user` / `readonly` - verify cannot create/edit records
6. Login as `project_lead` / `lead` - verify can edit records
7. Run `demo-reset` locally - verify data fully restored
8. Wait for scheduled reset - verify it fires at the 2-hour mark

---

## Managing Demo Fixture Data

`deployment/fixtures/demo_data/` (~195MB of preview images) is not stored in git.
It is managed via a dedicated GitHub Release tag (`demo-fixtures-latest`) using
`deployment/scripts/manage-demo-fixtures.sh`.

**Download fixtures locally** (required before `demo-up`):
```bash
./deployment/scripts/manage-demo-fixtures.sh download
```

**Update fixtures** (after adding/changing files in `demo_data/`):
```bash
./deployment/scripts/manage-demo-fixtures.sh upload
```

**Check what is in the release:**
```bash
./deployment/scripts/manage-demo-fixtures.sh status
```

On Fly.io, the entrypoint downloads fixtures automatically at container startup if
`demo_data/` is absent. The release tag never moves -- only its attached assets are
replaced -- so no code changes are needed when fixture content is updated.

---

## Troubleshooting

**App not starting:**
```bash
fly logs --app nexuslims-demo
```

**Re-run initialization manually:**
```bash
fly ssh console --app nexuslims-demo
python /srv/scripts/init_environment.py
python /srv/scripts/seed_demo_records.py
```

**Check TLS certificate status:**
```bash
fly certs list --app nexuslims-demo
```
