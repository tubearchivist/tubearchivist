#!/bin/bash
# startup script inside the container for tubearchivist

set -e

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
exec nginx &
exec celery -A home.celery worker --loglevel=INFO --max-tasks-per-child 10 &
exec celery -A home beat --loglevel=INFO \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler &
exec uwsgi --hook-master-start "unix_signal:15 gracefully_kill_them_all" --ini uwsgi.ini
