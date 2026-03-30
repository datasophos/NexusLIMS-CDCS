# NexusLIMS Public Demo - Deployment Guide

Deployment target: `nexuslims-demo.datasophos.co` on an Oracle Cloud Infrastructure
(OCI) free-tier Ampere A1 ARM VM.

The demo stack is deployed via Docker Compose and consists of:
- **cdcs** - Django/Gunicorn/Celery app
- **caddy** - Reverse proxy + file server (automatic Let's Encrypt TLS)
- **postgres** - PostgreSQL 17
- **redis** - Redis 8

Data resets every 2 hours via a system cron job that wipes the database and Redis
volumes and restarts the stack. The entrypoint re-initializes everything from scratch
on each start (migrate -> init users/schema/XSLT -> seed records).

---

## Prerequisites

- DNS access for `datasophos.co` to add A records (everything else is set up below)

---

## OCI Account Setup

### 1. Create an Oracle Cloud account

### 2. Create the ARM VM instance

Navigate to **Compute > Instances > Create Instance**.

- **Name**: `nexuslims-cdcs-demo`

**Shape** (click **Edit > Change shape**):
- Shape series: **Ampere**
- Shape: **VM.Standard.A1.Flex**
- OCPUs: `2`, Memory: `12 GB`

**Image** (click **Change image**): Canonical Ubuntu 24.04

**Networking**: create new VCN and public subnet

**SSH key**: paste your public key or generate a new key pair and download it immediately

Click **Create** and wait for the instance to reach **Running** state. Note the
**Public IP address** shown in the instance details.

### 3. Configure public IP

```
oci network public-ip create \
  --compartment-id "ocid1.tenancy.oc1........." \
  --lifetime RESERVED \
  --private-ip-id "ocid1.privateip........" \
  --display-name "nexuslims-demo-ip" \
  --profile DEMO
```

### 4. Configure the cloud firewall (Security List)

Navigate to **Networking > Virtual Cloud Networks > [your VCN] > Security Lists >
Default Security List**.

Click **Add Ingress Rules** and add:

| Source CIDR | Protocol | Dest. Port | Description |
|---|---|---|---|
| `0.0.0.0/0` | TCP | `80` | HTTP |
| `0.0.0.0/0` | TCP | `443` | HTTPS |

You can also restrict SSH access to known IPs on this screen.

### 5. Open ports in the OS firewall

OCI Ubuntu images ship with an iptables ruleset that blocks all inbound traffic except
SSH, **regardless of what the cloud Security List permits**. SSH into the instance and
run:

```bash
ssh -i /path/to/your.key ubuntu@<PUBLIC_IP>
```

```bash
# Open ports 80 and 443
# -I INPUT inserts at the top of the chain, before the default REJECT rule
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT

# Persist across reboots
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

> **Do not enable UFW** on OCI Ubuntu instances. OCI's iptables setup and Docker's
> own iptables manipulation both conflict with UFW.

---

## Server Setup

### 6. Install Docker

```bash
# Add Docker's official GPG key:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker ubuntu
newgrp docker
```

Verify:
```bash
docker run hello-world
docker compose version
```

### 7. Configure unattended upgrades

```
sudo apt install -y unattended-upgrades update-notifier-common

# Enable automatic updates
sudo dpkg-reconfigure -plow unattended-upgrades
# (select "Yes" at the prompt)

# Optional: auto-reboot at 3am if a kernel update requires it
sudo tee -a /etc/apt/apt.conf.d/50unattended-upgrades <<'EOF'
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
EOF
```

### 8. Clone the repo and configure

```bash
sudo mkdir -p /opt/nexuslims-cdcs
sudo chown ubuntu:ubuntu /opt/nexuslims-cdcs
git clone https://github.com/datasophos/NexusLIMS-CDCS.git /opt/nexuslims-cdcs
cd /opt/nexuslims-cdcs

cd deployment
cp .env.demo.example .env
```

Edit `.env` and fill in the required values:

| Variable | Value |
|---|---|
| `DJANGO_SECRET_KEY` | `python3 -c "from secrets import token_urlsafe; print(token_urlsafe(50))"` |
| `POSTGRES_PASS` | `python3 -c "from secrets import token_urlsafe; print(token_urlsafe(32))"` |
| `REDIS_PASS` | `python3 -c "from secrets import token_urlsafe; print(token_urlsafe(32))"` |
| `CADDY_ACME_EMAIL` | your email address (for Let's Encrypt expiry notifications) |

The remaining `.env` defaults (`DOMAIN`, `FILES_DOMAIN`, `CADDYFILE`, `REQUESTS_CA_BUNDLE`, etc.)
are already set correctly for OCI production deployment.

### 9. Download fixture data

```bash
./scripts/manage-demo-fixtures.sh download
```

This downloads ~195 MB of preview images from the `demo-fixtures-latest` GitHub
Release into `deployment/fixtures/demo_data/`. The data lives in the bind-mounted
repo directory (not a Docker volume), so it persists across demo resets.

After the initial setup, the GitHub Actions deploy workflow checks for fixture data
automatically and downloads it if absent -- no manual re-run needed after re-provisioning.

### 10. Set up the GitHub Actions self-hosted runner

The deploy workflow (`.github/workflows/deploy-demo.yml`) runs directly on the OCI
instance via a self-hosted runner. This avoids the need to allow inbound SSH from
GitHub's IP ranges (which number in the thousands and change over time).

The runner makes only **outbound HTTPS (port 443)** connections to GitHub -- no
additional firewall rules are needed.

Get a registration token (run locally, requires `gh` authenticated to the repo):

```bash
gh api repos/datasophos/NexusLIMS-CDCS/actions/runners/registration-token \
  --method POST --jq '.token'
```

On the OCI instance:

```bash
mkdir -p /opt/actions-runner && cd /opt/actions-runner

# Download the ARM64 runner binary
curl -o actions-runner-linux-arm64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.323.0/actions-runner-linux-arm64-2.323.0.tar.gz
tar xzf actions-runner-linux-arm64.tar.gz

# Register with the repo (accept all defaults)
./config.sh --url https://github.com/datasophos/NexusLIMS-CDCS --token <TOKEN>

# Install and start as a systemd service (auto-starts on reboot)
sudo ./svc.sh install
sudo ./svc.sh start
```

Verify the runner is online at **GitHub repo > Settings > Actions > Runners** -- it
should appear as `Idle`.

### 11. Build and deploy the stack

```bash
source demo-commands.sh
demo-build   # first build takes ~5-10 minutes (compiles custom Caddy + installs Python deps)
demo-up
```

Watch the startup logs until the app is ready:
```bash
demo-logs-cdcs
```

Look for `NexusLIMS-CDCS Demo available at https://nexuslims-demo.datasophos.co`. The
first startup takes 2-4 minutes as it runs migrations, initializes the environment, and
seeds demo records.

---

## Configure DNS

Add these A records in your DNS provider:

| Name | Type | Value |
|---|---|---|
| `nexuslims-demo` | A | `<VM public IP>` |
| `files.nexuslims-demo` | A | `<VM public IP>` |

Caddy automatically obtains Let's Encrypt certificates for both domains on first HTTPS
request (once DNS has propagated). Watch cert issuance in the Caddy logs:

```bash
demo-logs-caddy
```

---

## Scheduled Reset (every 2 hours)

The reset script at `deployment/scripts/reset_demo.sh`:
1. Stops all containers
2. Removes the PostgreSQL, Redis, and app media/static volumes
3. Restarts the stack -- the entrypoint re-runs migrations, `init_environment.py`, and
   `seed_demo_records.py` on the fresh database

Caddy's `caddy_data` and `caddy_config` volumes are **not** removed, which preserves
the Let's Encrypt certificates across resets and avoids rate limit exhaustion
(Let's Encrypt allows 5 certificate requests per domain per hour, 50 per week).

### Set up the cron job

```bash
crontab -e
```

Add this line:

```
0 */2 * * * /opt/nexuslims-cdcs/deployment/scripts/reset_demo.sh >> /var/log/nexuslims-demo-reset.log 2>&1
```

```bash
touch /var/log/nexuslims-demo-reset.log
```

### Manually trigger a reset

```bash
/opt/nexuslims-cdcs/deployment/scripts/reset_demo.sh
```

---

## Local Demo Testing

```bash
cd deployment
cp .env.demo.example .env
```

Edit `.env` and make these changes for local testing:

| Variable | `.env.demo.example` default (OCI) | Local value |
|---|---|---|
| `DOMAIN` | `nexuslims-demo.datasophos.co` | `nexuslims-demo.localhost` |
| `FILES_DOMAIN` | `files.nexuslims-demo.datasophos.co` | `files.nexuslims-demo.localhost` |
| `CADDYFILE` | `Caddyfile.prod` | `Caddyfile.dev` |
| `REQUESTS_CA_BUNDLE` | `/etc/ssl/certs/ca-certificates.crt` | `/etc/ssl/certs/caddy-root-ca.crt` |
| `CURL_CA_BUNDLE` | `/etc/ssl/certs/ca-certificates.crt` | `/etc/ssl/certs/caddy-root-ca.crt` |

Also fill in `DJANGO_SECRET_KEY`, `POSTGRES_PASS`, and `REDIS_PASS` with generated values.

```bash
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
8. Wait for scheduled reset on OCI - verify it fires at the 2-hour mark

---

## Managing Demo Fixture Data

`deployment/fixtures/demo_data/` (~195 MB of preview images) is not stored in git.
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

On OCI, fixture data is downloaded to `deployment/fixtures/demo_data/` inside the
bind-mounted repo directory at startup (if absent). Because this path is on the host
filesystem rather than a Docker volume, it persists across demo resets. The release tag
never moves -- only its attached assets are replaced -- so no code changes are needed
when fixture content is updated.

---

## Updating the Deployment

Deploys are automated via GitHub Actions (`.github/workflows/deploy-demo.yml`). Every
push to `main` triggers the self-hosted runner on the OCI instance, which pulls the
latest code, rebuilds the CDCS container, restarts the stack, and downloads fixture
data if absent.

To trigger a deploy manually, push to `main` or re-run the workflow in the GitHub
Actions UI.

To update manually on the server (e.g. after re-provisioning):

```bash
cd /opt/nexuslims-cdcs
git pull
cd deployment
source demo-commands.sh
demo-build        # rebuild if Dockerfile or Python dependencies changed
demo-restart-all  # restart all services with updated code
```

---

## Troubleshooting

**App not starting / checking startup progress:**
```bash
demo-logs-cdcs
```

**Certificate not being issued:**
```bash
demo-logs-caddy
# Verify DNS is propagated:
dig nexuslims-demo.datasophos.co
# Verify ports 80/443 are reachable from the internet:
curl -v http://nexuslims-demo.datasophos.co
```

**Ports unreachable despite correct Security List:**
The OS-level iptables is likely blocking traffic. Re-run the iptables commands from
step 5 and verify with:
```bash
sudo iptables -L INPUT --line-numbers
# ACCEPT rules for ports 80 and 443 must appear before any REJECT/DROP rule
```

**Out of Host Capacity on A1 instance:**
Try different Availability Domains in the OCI Console. If capacity is persistently
unavailable, use the automated retry script at
https://github.com/hitrov/oci-arm-host-capacity

**Re-run initialization manually:**
```bash
demo-shell
python /srv/scripts/init_environment.py
python /srv/scripts/seed_demo_records.py
```

**Check reset cron logs:**
```bash
tail -f /var/log/nexuslims-demo-reset.log
```
