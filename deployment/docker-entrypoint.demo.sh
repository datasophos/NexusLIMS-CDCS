#!/bin/bash
set -e

echo "********* Demo Mode - Waiting for Postgres *********"
until python -c "import socket; socket.create_connection(('${POSTGRES_HOST}', ${POSTGRES_PORT}), timeout=1)" 2>/dev/null; do
    sleep 1
done

echo "********* Running Migrations *********"
cd /srv/nexuslims
python manage.py migrate --noinput

echo "********* Collecting Static Files *********"
python manage.py collectstatic --noinput

echo "********* Checking Demo Fixture Data *********"
FIXTURES_DATA_DIR="/srv/nexuslims/deployment/fixtures/demo_data"
FIXTURES_REPO="${DEMO_FIXTURES_REPO:-datasophos/NexusLIMS-CDCS}"
FIXTURES_TAG="${DEMO_FIXTURES_TAG:-demo-fixtures-latest}"
FIXTURES_ASSET="demo_data.tar.gz"
FIXTURES_URL="https://github.com/${FIXTURES_REPO}/releases/download/${FIXTURES_TAG}/${FIXTURES_ASSET}"

if [ -z "$(ls -A "${FIXTURES_DATA_DIR}/nx-data" 2>/dev/null)" ]; then
    echo "  demo_data not found - downloading from GitHub Release (${FIXTURES_TAG})..."
    TARBALL="/tmp/${FIXTURES_ASSET}"
    if curl -fL --progress-bar -o "${TARBALL}" "${FIXTURES_URL}"; then
        mkdir -p "$(dirname "${FIXTURES_DATA_DIR}")"
        tar -xzf "${TARBALL}" -C "$(dirname "${FIXTURES_DATA_DIR}")"
        rm -f "${TARBALL}"
        echo "  Fixtures downloaded successfully."
    else
        echo "  Warning: Could not download demo fixtures from ${FIXTURES_URL}" >&2
        echo "  Preview images will not be available." >&2
    fi
else
    echo "  demo_data already present, skipping download."
fi

echo "********* Initializing Demo Environment *********"
python /srv/scripts/init_environment.py || true

echo "********* Seeding Demo Records *********"
python /srv/scripts/seed_demo_records.py || true

echo "********* Starting Celery... *********"
celery -A mdcs worker -E -l info &
celery -A mdcs beat -l info &

GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
GUNICORN_EXTRA_ARGS=""
if [ "${DJANGO_DEBUG}" = "True" ]; then
    GUNICORN_WORKERS=1
    GUNICORN_EXTRA_ARGS="--reload"
fi

echo "********* Starting Gunicorn Demo Server *********"
echo "  Workers: ${GUNICORN_WORKERS}, Threads: ${GUNICORN_THREADS:-2}, Timeout: ${GUNICORN_TIMEOUT:-120}s, Reload: ${DJANGO_DEBUG}"
echo "********* NexusLIMS-CDCS Demo available at ${SERVER_URI} *********"
exec gunicorn mdcs.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS} \
    --threads ${GUNICORN_THREADS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    ${GUNICORN_EXTRA_ARGS}
