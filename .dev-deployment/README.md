# NexusLIMS-CDCS Development Deployment

This directory contains Docker Compose configuration for local development of NexusLIMS-CDCS.

## Quick Start

1. **Load development helper commands:**
   ```bash
   cd .dev-deployment
   source dev-commands.sh
   ```
   This loads convenient aliases for common development tasks.

2. **Build the Docker image** (first time only):
   ```bash
   docker compose build
   ```

3. **Start the development environment:**
   ```bash
   dev-up
   # Or without aliases:
   # docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

4. **Trust the development certificate** (one-time setup):
   
   The development environment uses a persistent self-signed certificate. To avoid browser warnings, import the CA certificate as a trusted authority:
   
   **On macOS:**
   ```bash
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain caddy/certs/ca.crt
   ```
   
   **Or import manually:**
   1. Open Keychain Access
   2. File → Import Items
   3. Select `caddy/certs/ca.crt`
   4. Double-click the imported cert and set "When using this certificate" to "Always Trust"
   5. Close and re-open your browser
   
   **Or trust directly in your browser:**
   Most browsers allow you to import the CA certificate directly through their settings:
   - **Chrome/Edge**: Settings → Privacy and security → Security → Manage certificates → Import `caddy/certs/ca.crt`
   - **Firefox**: Preferences → Privacy & Security → Certificates → View Certificates → Import `caddy/certs/ca.crt`
   - **Safari**: Open `caddy/certs/ca.crt` with Safari, then follow prompts to add to keychain

5. **Access the application:**
   - URL: https://nexuslims-dev.localhost
   - After importing the certificate, the connection will be trusted with no browser warnings

6. **Create a superuser:**
   ```bash
   dev-superuser
   # Or without aliases:
   # docker compose exec cdcs python manage.py createsuperuser
   ```

7. **Initialize NexusLIMS schema** (optional, but recommended):
   ```bash
   dev-init-schema
   # This registers the Nexus Experiment XSD template and XSLT stylesheets
   # Use --force to re-initialize: docker exec nexuslims_dev_cdcs python manage.py init_nexus_schema --force
   ```

## Configuration

### Ports
**Inside Docker Network** (standard ports):
- Caddy: 80 (HTTP) and 443 (HTTPS)
- Django: 8000
- PostgreSQL: 5432
- MongoDB: 27017
- Redis: 6379

**Exposed to Host** (non-standard ports to avoid conflicts):
- **Application**: https://nexuslims-dev.localhost (Caddy on 443)
- **PostgreSQL**: localhost:5532
- **MongoDB**: localhost:27117
- **Redis**: localhost:6479

### Environment Variables
Edit `.env` to configure:
- Database credentials
- Django secret key
- Server settings

### Development Settings
The `cdcs/dev_settings.py` file extends the main `mdcs/settings.py` with development-specific configurations.

## Live Development

The development setup mounts your local source code at `..` (parent directory) into the container, enabling:
- **Live code reload** - Django runserver automatically detects changes
- **No rebuild needed** - Edit code locally, see changes immediately
- **Full debugging** - Django debug mode enabled

## Services

- **curator_caddy**: Reverse proxy with automatic HTTPS
- **curator_postgres**: PostgreSQL database
- **curator_mongo**: MongoDB database
- **curator_redis**: Redis cache
- **cdcs**: Django application (NexusLIMS-CDCS)
- **celery_worker**: Celery worker for async tasks (MongoDB document creation, etc.)
- **celery_beat**: Celery beat scheduler for periodic tasks

## Development Helper Commands

The `dev-commands.sh` script provides convenient aliases. Load it with:
```bash
source dev-commands.sh
```

### Lifecycle Commands
```bash
dev-up              # Start development environment
dev-down            # Stop development environment  
dev-restart         # Restart CDCS app only
dev-restart-all     # Restart all services
```

### Viewing Logs
```bash
dev-logs            # View all logs (follow mode)
dev-logs-app        # View CDCS app logs only
dev-logs-caddy      # View Caddy proxy logs
```

### Shell Access
```bash
dev-shell           # Open bash shell in CDCS container
dev-manage          # Run Django management commands (e.g., dev-manage migrate)
dev-djshell         # Open Django shell (Python REPL)
```

### Database Operations
```bash
dev-migrate         # Run database migrations
dev-makemigrations  # Create new migrations
dev-dbshell         # Open PostgreSQL shell
```

### User Management
```bash
dev-superuser       # Create superuser
```

### Static Files
```bash
dev-collectstatic   # Collect static files
```

### Without Aliases
If you prefer not to use aliases or need more control:

```bash
# View logs
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f cdcs

# Run migrations
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec cdcs python manage.py migrate

# Collect static files
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec cdcs python manage.py collectstatic --noinput

# Access Django shell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec cdcs python manage.py shell

# Stop all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

## Troubleshooting

### Certificate warnings
If you see browser certificate warnings, you haven't imported the CA certificate yet. Follow the "Trust the development certificate" instructions in the Quick Start section above. After importing `caddy/certs/ca.crt`, the connection will be fully trusted.

### Database connection errors
Ensure the containers are fully started. The Django container waits for PostgreSQL to be ready before starting.

### Port conflicts
If you encounter port conflicts on the host, edit the port mappings in `.env`:
```
POSTGRES_HOST_PORT=5532
MONGO_HOST_PORT=27117
REDIS_HOST_PORT=6479
```
Note: These only affect host-exposed ports, not internal Docker networking.

## Architecture

```
Browser → Caddy (HTTPS :443) → Django runserver (:8000) → Application
                                       ↓
                            ┌──────────┼──────────┐
                            ↓          ↓          ↓
                       PostgreSQL  MongoDB    Redis
                        (:5432)   (:27017)   (:6379)

Host Access (optional):
  PostgreSQL: localhost:5532 → Container:5432
  MongoDB:    localhost:27117 → Container:27017
  Redis:      localhost:6479 → Container:6379
```

## Next Steps

After the upgrade is complete:
1. Test all functionality through the web interface
2. Run automated tests: `docker compose exec cdcs python manage.py test`
3. Verify XSLT rendering of records
4. Test download functionality
5. Check search and filtering
