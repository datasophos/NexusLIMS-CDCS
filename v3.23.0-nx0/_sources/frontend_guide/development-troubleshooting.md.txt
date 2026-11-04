# Development Troubleshooting

## Certificate Warnings

Trust the CA certificate as described in {doc}`development setup <development>`.

## Port Conflicts

Edit port mappings in `.env`:
```bash
POSTGRES_HOST_PORT=5532  # Change if 5532 is in use
REDIS_HOST_PORT=6479     # Change if 6479 is in use
```

## Permission Errors

Ensure scripts are executable:
```bash
chmod +x dev-commands.sh
chmod +x scripts/*.sh scripts/*.py
```

## Test Data Not Loading

Run extraction manually:
```bash
bash scripts/setup-test-data.sh
```

## XSLT Changes Not Appearing

Update the database and refresh:
```bash
dev-update-xslt
```

## Database Connection Errors

Wait for services to fully start. The Django container waits for PostgreSQL to be ready, but this can take a few seconds on first startup.
