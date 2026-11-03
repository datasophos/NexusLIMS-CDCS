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

---

## Gallery administration implementation

The gallery admin feature adds a **site-wide policy for selecting images** and a staff-only page that shows which images can currently appear. It does not maintain a separate list of gallery images: it derives candidates from the XML in publicly accessible records each time the admin page or gallery API is requested.

```{mermaid}
flowchart LR
    A[Staff member] -->|saves mode and rating| B[Gallery admin]
    B --> C[(GallerySettings<br/>single site-wide policy)]
    B --> D[Selectable images table]
    E[Global workspace<br/>records] --> F[Parse record XML<br/>and select candidates]
    C --> F
    F --> D
    F --> G[Public next-slide API]
    G -->|random record, then random candidate| H[Gallery slideshow]
```

### Admin page and settings

When the gallery app is installed and `NX_ENABLE_GALLERY` is enabled, the **Visual Gallery** admin menu item and the `/admin/gallery/` route are available. Django's `staff_member_required` protects the view. The public gallery and its API remain accessible without authentication. The route is registered in `mdcs/urls.py`, and the menu item is registered in `nexuslims_overrides/menus.py`.

The form saves two values in `GallerySettings` (`nexuslims_gallery/models.py`):

- **Selection mode:** all previewable records, featured or rated records, or featured only.
- **Minimum rating:** an integer from 1 to 5, used by the featured-or-rated mode.

The view treats the row with primary key `1` as the site-wide settings record. If it does not exist yet, an unsaved model instance supplies the defaults: **all previewable records** and minimum rating **1**. A valid POST creates or updates that row, then redirects back to the page. The singleton convention is implemented by the view; the model itself does not prevent other rows from being created. The settings and admin view are implemented in `nexuslims_gallery/views.py`.

### How an image becomes selectable

Both the admin page and the public API call the same selection functions. They retrieve records from the **global workspace as an anonymous user**, parse each record's NexusLIMS XML, and inspect datasets within its acquisition activities. A dataset needs a nonempty preview path; the code joins that path to `XSLT_PREVIEW_BASE_URL`. Malformed XML contributes no candidates.

The decision is made **within each record**:

```{mermaid}
flowchart TD
    A[Previewable datasets in one record] --> B{Any featured?}
    B -->|Yes| C[All featured datasets<br/>are candidates]
    B -->|No| D{Mode?}
    D -->|Featured only| E[Record excluded]
    D -->|Featured or rated| F[Keep ratings at or above minimum]
    D -->|All previewable| G[Consider all rated datasets]
    F --> H{Any qualifying rated datasets?}
    G --> H
    H -->|Yes| I[Highest-rated datasets<br/>are candidates; ties retained]
    H -->|No, all previewable mode| J[First previewable dataset<br/>is the candidate]
    H -->|No, featured or rated mode| E
```

Featured datasets take precedence over ratings in **every mode**. For example, if a record has one featured image and another image rated 5, only the featured image is selectable. If there are several featured images—or a tie for the highest qualifying rating—all are candidates.

The minimum rating affects only **featured or rated** mode. Featured datasets qualify regardless of their rating. In all-previewable mode, the highest rated dataset wins if there is one; otherwise the first previewable dataset is used.

### What the admin table represents

The table lists **every candidate that could win** under the *saved* policy, with its preview, experimenter, file name, selection reason, and record link. Thus, a record can produce multiple rows when candidates tie. The table is informational: individual images are curated through the metadata in their records, not toggled directly in this table.

Search is case-insensitive and matches dataset name, experimenter, or record title. Filtering happens before pagination, with 20 rows per page. The page builds the full candidate list in memory on each request; pagination limits what is displayed rather than how many records are fetched or parsed. The table is rendered by `nexuslims_gallery/templates/nexuslims_gallery/admin.html`.

### How the public slideshow uses it

For each request to `/gallery/api/next/`, the server reads the current policy and rebuilds the eligible record list. It then chooses **a record at random**, followed by **a candidate within that record at random**. Consequently, records have equal selection probability, but individual images do not necessarily have equal probability across the entire gallery: an image in a record with several candidates shares that record's chance with its peers.

The JSON includes the preview and record URLs, title, featured flag, and available descriptive metadata. If there are no eligible records, the API returns 404; a failure fetching records or settings returns 500. The gallery JavaScript (`nexuslims_gallery/static/nexuslims_gallery/gallery.js`) requests and displays these slides.
