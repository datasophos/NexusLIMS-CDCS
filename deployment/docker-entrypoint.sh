#!/bin/bash
set -e

# Docker entrypoint for NexusLIMS-CDCS

# Wait for PostgreSQL to be ready
if [ -n "$POSTGRES_HOST" ]; then
    echo "Waiting for PostgreSQL at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
    until python -c "import socket; socket.create_connection(('$POSTGRES_HOST', ${POSTGRES_PORT:-5432}), timeout=1)" 2>/dev/null; do
        sleep 1
    done
    echo "PostgreSQL is ready"
fi

# Wait for MongoDB to be ready
if [ -n "$MONGO_HOST" ]; then
    echo "Waiting for MongoDB at $MONGO_HOST:${MONGO_PORT:-27017}..."
    until python -c "import socket; socket.create_connection(('$MONGO_HOST', ${MONGO_PORT:-27017}), timeout=1)" 2>/dev/null; do
        sleep 1
    done
    echo "MongoDB is ready"
fi

# Execute the command
exec "$@"
