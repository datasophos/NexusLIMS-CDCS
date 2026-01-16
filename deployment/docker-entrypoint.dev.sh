#!/bin/bash
set -e

echo "********* Development Mode - Waiting for Postgres *********"
until python -c "import socket; socket.create_connection(('${POSTGRES_HOST}', ${POSTGRES_PORT}), timeout=1)" 2>/dev/null; do
    sleep 1
done

echo "********* Running Migrations *********"
cd /srv/nexuslims
python manage.py migrate --noinput

echo "********* Collecting Static Files *********"
python manage.py collectstatic --noinput

echo "********* Initializing Development Environment *********"
python /srv/scripts/init_environment.py || true

echo "********* Starting Celery... *********"
celery -A mdcs worker -E -l info &
celery -A mdcs beat -l info &

echo "********* Starting Django Development Server with Auto-Reload *********"
echo "********* NexusLIMS-CDCS available at ${SERVER_URI} *********"
python manage.py runserver 0.0.0.0:8000
