# NexusLIMS-CDCS Development Dockerfile
# Based on MDCS 3.18.0

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get --no-install-recommends install -y \
    gcc \
    g++ \
    python3-dev \
    gettext \
    libpq-dev \
    postgresql-client \
    libxml2-dev \
    libxslt1-dev \
    libxslt-dev \
    zlib1g \
    zlib1g-dev \
    libssl-dev \
    xmlsec1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /srv/nexuslims

# Install uv for faster package installation
RUN pip install --upgrade pip && pip install uv

# Install additional python packages (needed before requirements)
RUN uv pip install --system setuptools wheel && \
    uv pip install --system psycopg2 uwsgi gunicorn[gthread]

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.core.txt ./
RUN uv pip install --system -r requirements.txt && \
    uv pip install --system -r requirements.core.txt

# Copy application source code and configuration
COPY manage.py ./
COPY mdcs ./mdcs
COPY mdcs_home ./mdcs_home
COPY locale ./locale
COPY templates ./templates
COPY static ./static
COPY config ./config
COPY nexuslims_overrides ./nexuslims_overrides
COPY xslt ./xslt

# Create necessary directories
RUN mkdir -p /srv/nexuslims/media /srv/nexuslims/static.prod

# Set up entrypoints and scripts
COPY deployment/docker-entrypoint.sh /docker-entrypoint.sh
COPY deployment/scripts /srv/scripts
RUN chmod +x /docker-entrypoint.sh /srv/scripts/*.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["mdcs", "runserver"]
