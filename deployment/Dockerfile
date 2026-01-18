# NexusLIMS-CDCS Development Dockerfile
# Based on MDCS 3.18.0

FROM astral/uv:python3.13-alpine3.23
# use 3.13 since lxml 5.4.0 does not have a binary for 3.14

# Create application directory
WORKDIR /srv/nexuslims

RUN apk add python3-dev build-base linux-headers gettext bash \
    && rm -rf /var/cache/apk/*

# Install additional python packages (needed before requirements)
RUN uv pip install --system setuptools wheel && \
    uv pip install --system psycopg2-binary uwsgi gunicorn[gthread]

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
# config is included in image for remote builds (Git URL context)
# For local dev, it can be overridden via bind mount in docker-compose.dev.yml
COPY config ./config
COPY nexuslims_overrides ./nexuslims_overrides
COPY xslt ./xslt

# Create necessary directories
RUN mkdir -p /srv/nexuslims/media /srv/nexuslims/static.prod

# Set up entrypoints and scripts
COPY deployment/docker-entrypoint.prod.sh /docker-entrypoint.prod.sh
COPY deployment/docker-entrypoint.dev.sh /docker-entrypoint.dev.sh
COPY deployment/scripts /srv/scripts
RUN chmod +x /docker-entrypoint.*.sh /srv/scripts/*.sh

ENTRYPOINT ["/docker-entrypoint.dev.sh"]
