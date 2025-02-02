#!/bin/bash
# startup script inside the container for tubearchivist

set -e

# stop on pending manual migration
python manage.py ta_stop_on_error

# django setup
python manage.py migrate

if [[ -z "$DJANGO_DEBUG" ]]; then
    python manage.py collectstatic --noinput -c
fi

# ta setup
python manage.py ta_envcheck
python manage.py ta_connection
python manage.py ta_startup

# start all tasks
nginx &
celery -A task.celery worker \
    --loglevel=INFO \
    --concurrency 4 \
    --max-tasks-per-child 5 \
    --max-memory-per-child 150000 &
celery -A task beat --loglevel=INFO \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler &
python backend_start.py
