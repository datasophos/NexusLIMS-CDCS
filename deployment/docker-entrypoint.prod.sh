#!/bin/bash
set -e

echo "********* Production Mode - Waiting for Postgres *********"
until python -c "import socket; socket.create_connection(('${POSTGRES_HOST}', ${POSTGRES_PORT}), timeout=1)" 2>/dev/null; do
    sleep 1
done

echo "********* Running Migrations *********"
cd /srv/nexuslims
python manage.py migrate --noinput

echo "********* Collecting Static Files *********"
python manage.py collectstatic --noinput

echo "********* Starting Celery... *********"
celery -A mdcs worker -E -l info &
celery -A mdcs beat -l info &

echo "********* Starting Gunicorn Production Server *********"
echo "  Workers: ${GUNICORN_WORKERS:-4}, Threads: ${GUNICORN_THREADS:-2}, Timeout: ${GUNICORN_TIMEOUT:-120}s"
echo "********* NexusLIMS-CDCS available at ${SERVER_URI} *********"
exec gunicorn mdcs.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-4} \
    --threads ${GUNICORN_THREADS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --access-logfile - \
    --error-logfile - \
    --log-level info
