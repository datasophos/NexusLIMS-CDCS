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
WORKDIR /srv/curator

# Install additional python packages (needed before requirements)
RUN pip install --upgrade pip setuptools wheel && \
    pip install psycopg2 uwsgi gunicorn[gthread]

# Copy requirements and install Python dependencies
# Note: In dev mode, source code is mounted as a volume
COPY requirements.txt requirements.core.txt ./
RUN pip install -r requirements.txt && \
    pip install -r requirements.core.txt

# Create necessary directories
RUN mkdir -p /srv/curator/media /srv/curator/static.prod

# Set up entrypoint
COPY .dev-deployment/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["mdcs", "runserver"]
