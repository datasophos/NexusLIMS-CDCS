# Architecture and Directory Structure

## Architecture

The development stack uses Docker Compose with two configuration layers:

```
docker-compose.base.yml    # Shared configuration (services, networks, volumes)
docker-compose.dev.yml     # Development overrides (ports, mounts, commands)
```

```{mermaid}
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#e3f2fd', 'primaryTextColor': '#000', 'primaryBorderColor': '#1976d2', 'lineColor': '#1976d2'}}}%%
flowchart TB
    Browser([Browser]) -->|HTTPS :443| Caddy

    subgraph Docker["Docker Compose"]
        Caddy[Caddy<br/>Local CA Certs<br/>File Server]
        Django[Django runserver<br/>Hot Reload]
        Postgres[(PostgreSQL<br/>:5532)]
        Redis[(Redis<br/>:6479)]

        Caddy -->|:8000| Django
        Django --> Postgres
        Django --> Redis
    end

    subgraph Mounts["Mounted Directories"]
        Code[Source Code<br/>./]
        XSLT[XSLT Files<br/>xslt/]
        TestData[Test Data<br/>test-data/]
    end

    Django -.- Code
    Django -.- XSLT
    Caddy -.- TestData

    classDef browser fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef service fill:#e1f5ff,stroke:#1976d2,stroke-width:2px
    classDef mount fill:#e8f5e9,stroke:#388e3c,stroke-width:2px

    class Browser browser
    class Caddy,Django,Postgres,Redis service
    class Code,XSLT,TestData mount
```

---

## Directory Structure

```text
deployment/
├── docker-compose.base.yml    # Shared configuration
├── docker-compose.dev.yml     # Development overrides
├── Dockerfile                 # Application image
├── docker-entrypoint.sh       # Container startup script
│
├── .env                       # Active environment (copy from .env.dev)
├── .env.dev                   # Development defaults
│
├── caddy/
│   ├── Dockerfile             # Custom Caddy with plugins
│   ├── Caddyfile.dev          # Development reverse proxy
│   └── certs/                 # CA certificate for HTTPS
│
├── scripts/
│   ├── init_environment.py    # Superuser + schema + XSLT setup
│   ├── update-xslt.sh         # Update XSLT in database
│   └── setup-test-data.sh     # Extract test data
│
├── test-data/                 # Test data (extracted, gitignored)
│
└── dev-commands.sh            # Development helper aliases
```
