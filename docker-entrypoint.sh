#!/bin/sh
set -e
flask db upgrade
exec gunicorn \
    --bind "0.0.0.0:${PORT:-5050}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --access-logfile - \
    --no-control-socket \
    application.wsgi:app
