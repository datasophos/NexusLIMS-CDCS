# Public Demo for NexusLIMS-CDCS

## Context

We want a publicly accessible demo at `nexuslims-demo.datasophos.co` so anyone can explore
NexusLIMS without setting up their own instance. The demo provides full Django admin
access (self-healing via 2-hour reset), realistic microscopy data (real previews from
public datasets, stub data files), and a redesigned homepage that explains what
NexusLIMS does with a prominent CTA to Datasophos.

Hosting: Fly.io. All changes live on `main`. Reset strategy: re-run init from scratch
every 2 hours (drop DB, re-migrate, re-seed).

All demo-specific behavior is gated behind `IS_PUBLIC_DEMO` (default `False`) so real
deployments are completely unaffected. This includes the homepage hero section, CTA,
auto-login middleware, download warning, and credentials panel on the login page.

---

## Phase 1: `IS_PUBLIC_DEMO` Feature Flag

**Create** `config/settings/demo_settings.py`
- Extends `prod_settings`
- `IS_PUBLIC_DEMO = True`
- `EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'` (no spam)
- `DEBUG = False`
- `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` from env vars

**Modify** `nexuslims_overrides/settings.py`
- Add `IS_PUBLIC_DEMO = False` default

**Modify** `nexuslims_overrides/context_processors.py`
- Add `IS_PUBLIC_DEMO` to `nexuslims_features()` return dict

---

## Phase 2: Auto-Login Middleware

Add a Django middleware that auto-logs in anonymous users when `IS_PUBLIC_DEMO = True`.
Designed to be extensible for future "role-specific demo experiences."

**Create** `nexuslims_overrides/middleware.py`
```python
DEMO_USER_PARAM = "demo_as"
DEMO_DEFAULT_USER = "admin"
EXCLUDED_PATHS = {"/accounts/login/", "/accounts/logout/", "/admin/login/"}

class DemoAutoLoginMiddleware:
    def __call__(self, request):
        if settings.IS_PUBLIC_DEMO and not request.user.is_authenticated:
            if request.path not in EXCLUDED_PATHS:
                # ?demo_as=<username> selects role; defaults to admin
                username = request.GET.get(DEMO_USER_PARAM, DEMO_DEFAULT_USER)
                # Whitelist to valid demo usernames only (security)
                if username not in settings.DEMO_USERNAMES:
                    username = DEMO_DEFAULT_USER
                user = User.objects.filter(username=username).first()
                if user:
                    login(request, user, backend='...')
        return self.get_response(request)
```

`DEMO_USERNAMES = ['admin', 'readonly_user', 'project_lead']` defined in
`demo_settings.py`. Future demo landing pages can link to `/?demo_as=readonly_user`
or `/?demo_as=project_lead` to give role-specific experiences.

**Modify** `config/settings/demo_settings.py` - add middleware to `MIDDLEWARE`

**Modify** `templates/account/login.html` - when `IS_PUBLIC_DEMO`, show a panel
with all three account credentials and quick-login buttons for each.

---

## Phase 3: Homepage Redesign (IS_PUBLIC_DEMO-gated)

**Modify** `nexuslims_overrides/templates/mdcs_home/tiles.html` (or create as a
template override):

When `IS_PUBLIC_DEMO` is True, the template renders additional sections above the
existing tiles:
1. **Hero section** - "NexusLIMS: A Laboratory Information Management System for
   Electron Microscopy" with 2-3 sentence description
2. **Feature highlights grid** (4 cards): Browse records, Annotate datasets,
   Download files, Full-text search
3. **CTA section** - "Need NexusLIMS for your facility? Contact Datasophos" with
   button to `datasophos.co`
4. **Browse/search tile** - existing navigation tile (unchanged)

When `IS_PUBLIC_DEMO` is False (all real deployments), the template renders exactly
as it does today - no visible difference.

Implementation uses `{% if IS_PUBLIC_DEMO %}` blocks around the new sections, where
`IS_PUBLIC_DEMO` is provided by the `nexuslims_features()` context processor.

---

## Phase 4: Download Modal Warning

The download system is in `nexuslims_overrides/static/nexuslims/js/detail/downloads/`
and the detail template is at
`nexuslims_overrides/templates/core_main_app/user/data/detail.html`.

**Modify** `nexuslims_overrides/templates/core_main_app/user/data/detail.html`
- When `IS_PUBLIC_DEMO`, render a `<div class="alert alert-warning">` inside the
  download modal area explaining that data files are stubs and not real instrument data.

Prefer the template approach (data attribute or inline conditional) to avoid JS
complexity in the download modules.

---

## Phase 5: User Accounts & Permissions

**Modify** `deployment/scripts/init_environment.py`
- When demo mode detected (check `DJANGO_SETTINGS_MODULE` contains `demo`):
  - Create `admin` / `admin` (superuser, all permissions)
  - Create `readonly_user` / `readonly` (can view only - default CDCS anonymous-level
    perms assigned to a logged-in user)
  - Create `project_lead` / `lead` (can create/edit records - assign
    `add_data` / `change_data` permissions from `core_main_app`)
- Keep these credentials idempotent (skip if users already exist)

---

## Phase 6: Seed Data (30 Records, 6 Instruments)

### Step 6a: Public Dataset Sourcing (prerequisite - manual)

Search these repositories for open-licensed microscopy files:
- **Zenodo** (search `.dm3`, `.dm4`, `.ser`, `.spc`, `.msa` + "microscopy")
- **Materials Data Facility** (materialsdatafacility.org)
- **NIST Public Data** (data.nist.gov)
- **figshare** (microscopy datasets)

All 8 specialized NexusLIMS extractors must be exercised. 6 instruments, 5 records each:

| Instrument | Extractor(s) Used | File Types | DatasetType |
|---|---|---|---|
| FEI Titan TEM (Gatan DM) | DM3Extractor | .dm3, .dm4 | Image, Diffraction, Spectrum, SpectrumImage (EELS/EDS) |
| FEI Quanta/Helios SEM+EDS | QuantaTiffExtractor, SpcExtractor, MsaExtractor | .tif + .spc + .msa | Image + Spectrum |
| Tescan FIB/SEM | TescanTiffExtractor | .tif | Image (SEM_Imaging) |
| Zeiss Orion HIM | OrionTiffExtractor | .tif | Image (HIM_Imaging) |
| FEI Tecnai TEM (TIA) | SerEmiExtractor | .ser + .emi | Image, SpectrumImage, STEM_EDS |
| Tofwerk fibTOF pFIB-ToF-SIMS | TofwerkPfibExtractor | .h5 | SpectrumImage (PFIB_TOFSIMS) |

The BasicFileInfoExtractor (fallback, any extension) can be exercised by including a
few supporting files (e.g., `.txt` notes or `.csv` logs) in a record or two.

Extractor coverage checklist: DM3Extractor ✓, QuantaTiffExtractor ✓, SpcExtractor ✓,
MsaExtractor ✓, TescanTiffExtractor ✓, OrionTiffExtractor ✓, SerEmiExtractor ✓,
TofwerkPfibExtractor ✓, BasicFileInfoExtractor ✓

### Step 6b: Preview Generation
Run NexusLIMS extractor/preview pipeline on sourced files:
```bash
# in NexusLIMS repo:
python -m nexusLIMS.preview <file> --output <output_dir>
```
This produces: thumbnail `.png`, metadata `.json`/`.xml` per file.

### Step 6c: Fixture Structure
```
deployment/fixtures/
  demo_records/        # 30 XML files (01_titan_tem_steel_sample.xml, etc.)
  demo_data/
    nx-data/           # Real preview images + metadata (from Step 6b)
      titan_tem/session_20230415/...
      helios_fibsem/...
      ...
    nx-instrument-data/ # 1-byte stub files mirroring real path structure
      titan_tem/session_20230415/image_001.dm3
      ...
```

### Step 6d: XML Record Design
Records span:
- 4 researchers: `jsmith` (project_lead), `mjones`, `lchen` (regular users), `admin`
- 5 sample types: steel alloy, silicon wafer, polymer film, ceramic powder, copper thin film
- Mix of single-dataset and multi-dataset (5-15 per record) activities

Each record XML references:
- `<location>` pointing to stub file URL (`{XSLT_DATASET_BASE_URL}/instrument/...`)
- `<preview>` pointing to real preview image URL (`{XSLT_PREVIEW_BASE_URL}/...`)

### Step 6e: Seed Script
**Create** `deployment/scripts/seed_demo_records.py`
- Reads all XMLs from `deployment/fixtures/demo_records/`
- Uploads via `core_main_app.components.data.api.upsert()`
- Called by entrypoint after user creation

---

## Phase 7: Docker Infrastructure

**Create** `deployment/docker-compose.demo.yml`
```yaml
services:
  cdcs:
    entrypoint: /docker-entrypoint.demo.sh
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.demo_settings
    volumes:
      - ../deployment/fixtures/demo_data/nx-data:/srv/nx-data:ro
      - ../deployment/fixtures/demo_data/nx-instrument-data:/srv/nx-instrument-data:ro
    restart: unless-stopped
```

**Create** `deployment/docker-entrypoint.demo.sh` (mirrors `dev` entrypoint but):
- Calls `python /srv/scripts/init_environment.py` (demo-aware via settings module)
- Calls `python /srv/scripts/seed_demo_records.py`

**Create** `deployment/demo-commands.sh` - mirrors `dev-commands.sh` with `demo-` prefixed
aliases for local demo management:
- `demo-up` - Start the demo stack
- `demo-down` - Stop the demo stack
- `demo-reset` - Full wipe and restart (`down -v && up -d`) - simulates the 2hr reset
- `demo-restart` - Restart without wiping volumes
- `demo-logs` - Follow all service logs
- `demo-logs-cdcs` - Follow cdcs service logs
- `demo-shell` - Shell into the cdcs container
- `demo-build` - Build the demo image
- `demo-build-clean` - Clean rebuild
- `demo-init` - Re-run init script without full restart (for development iteration)

Sourced the same way: `cd deployment && source demo-commands.sh`

**Create** `deployment/.env.demo.example`
- `DJANGO_SETTINGS_MODULE=config.settings.demo_settings`
- `DOMAIN=nexuslims-demo.datasophos.co`
- `FILES_DOMAIN=files.nexuslims-demo.datasophos.co`
- Secure random `POSTGRES_PASS`, `REDIS_PASS`, `DJANGO_SECRET_KEY`

**Reset mechanism** = wipe the stack + restart (no separate reset script needed):

**Local development:**
```bash
docker compose -f docker-compose.base.yml -f docker-compose.demo.yml down -v
docker compose -f docker-compose.base.yml -f docker-compose.demo.yml up -d
```
Named volumes are destroyed and recreated; the entrypoint handles everything from
scratch on startup (migrate → init users → seed records).

**Fly.io (scheduled machine, every 2 hours):**
A small bash script run by a scheduled Fly machine:
```bash
# 1. Wipe Postgres: drop + recreate database
psql $DATABASE_URL -c "DROP DATABASE nexuslims; CREATE DATABASE nexuslims;"
# 2. Flush Redis
redis-cli -h $REDIS_HOST -a $REDIS_PASS FLUSHALL
# 3. Restart the cdcs machine (entrypoint re-initializes everything)
fly machine restart $CDCS_MACHINE_ID --app nexuslims-demo
```
The cdcs machine's entrypoint (migrate → init → seed) handles full re-initialization
on each restart, so no separate state management is needed.

---

## Phase 8: Fly.io Configuration

**Create** `fly.toml` at repo root:
```toml
app = "nexuslims-demo"
primary_region = "iad"

[http_service]
  internal_port = 8000
  auto_stop_machines = false
  min_machines_running = 1

[[vm]]
  memory = "1gb"
  cpu_kind = "shared"
  cpus = 1
```

**Create** `fly-reset.toml` for scheduled reset machine:
```toml
app = "nexuslims-demo"
[experimental]
  cmd = ["/deployment/scripts/reset_demo.sh"]

[[schedule]]
  cron = "0 */2 * * *"  # every 2 hours
```

**Deployment steps** (documented in `deployment/DEMO_DEPLOY.md`):
1. `fly auth login`
2. `fly apps create nexuslims-demo` (main Django/Caddy app)
3. `fly apps create nexuslims-demo-db` (self-hosted Postgres)
4. `fly apps create nexuslims-demo-redis` (Redis)
5. `fly volumes create` for postgres data, redis data
6. `fly secrets set POSTGRES_PASS=... REDIS_PASS=... DJANGO_SECRET_KEY=...`
7. Deploy each service: `fly deploy --config fly-db.toml`, `fly deploy --config fly-redis.toml`, `fly deploy`
8. Add CNAME `nexuslims-demo.datasophos.co -> nexuslims-demo.fly.dev` in DNS
   Add CNAME `files.nexuslims-demo.datasophos.co -> nexuslims-demo-files.fly.dev` in DNS

---

## Critical Files

**Create:**
- `config/settings/demo_settings.py`
- `nexuslims_overrides/middleware.py`
- `nexuslims_overrides/templates/mdcs_home/tiles.html`
- `deployment/docker-compose.demo.yml`
- `deployment/docker-entrypoint.demo.sh`
- `deployment/demo-commands.sh`
- `deployment/.env.demo.example`
- `deployment/scripts/seed_demo_records.py`
- Fly.io scheduled reset script (small bash, runs in a scheduled machine)
- `deployment/fixtures/demo_records/*.xml` (30 files - after dataset sourcing)
- `deployment/fixtures/demo_data/` (after preview generation)
- `fly.toml`
- `deployment/DEMO_DEPLOY.md`

**Modify:**
- `nexuslims_overrides/settings.py` - add `IS_PUBLIC_DEMO = False`
- `nexuslims_overrides/context_processors.py` - expose `IS_PUBLIC_DEMO`
- `config/settings/demo_settings.py` - add middleware
- `deployment/scripts/init_environment.py` - demo user creation
- `templates/account/login.html` - demo credentials panel
- `nexuslims_overrides/templates/core_main_app/user/data/detail.html` - download warning

---

## Implementation Order

1. `IS_PUBLIC_DEMO` flag in settings + context processor
2. Auto-login middleware
3. Login page credentials panel
4. Homepage redesign template
5. Download warning in detail template
6. `init_environment.py` demo user creation
7. `seed_demo_records.py` scaffold (without records yet)
8. Docker infrastructure (compose, entrypoint, env, demo-commands.sh)
9. Fly.io config + deployment docs
10. **[Manual/parallel]** Source public datasets + run preview generator
11. Create 30 XML fixture records
12. Wire seed data into docker mounts
13. End-to-end local test, then deploy

---

## Verification

1. **Local**: `cd deployment && source demo-commands.sh && demo-up`
2. Visit `https://nexuslims-demo.localhost` - should be auto-logged in as `admin`
3. Browse to any record - verify download warning visible
4. Visit `/admin/` - verify full Django admin access
5. Log out, visit `/accounts/login/` - verify credentials panel with 3 accounts
6. Login as `readonly_user` - verify cannot create/edit records
7. Login as `project_lead` - verify can edit records
8. Run `demo-reset` - verify data fully restored, user-created data gone
9. Deploy to Fly.io, verify `nexuslims-demo.datasophos.co` resolves with TLS
10. Wait for scheduled reset - verify it fires correctly

---

## Open Questions / Notes

- **Dataset sourcing** is a manual prerequisite step. We'll document the search
  criteria and generate fixtures once files are found. This is the longest lead-time
  item and can be done in parallel with all code work.
- **Fly.io PostgreSQL**: Use a self-hosted Postgres container deployed as a separate
  Fly app (using the official `postgres:17` image + a persistent volume). This keeps
  the demo stack identical to the real deployment. Redis and Caddy follow the same
  pattern - each service gets its own Fly machine with a persistent volume where
  needed.
- **Reset timing**: 2 hours is conservative. Can be tuned in `fly-reset.toml` cron
  expression after initial deployment experience.
- **Caddy on Fly.io**: Fly handles TLS termination natively, so Caddy may be
  simplified or replaced by Fly's built-in proxy for the demo deployment.
