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
nginx &
celery -A home.tasks worker --loglevel=INFO --max-tasks-per-child 10 &
celery -A home beat --loglevel=INFO \
    -s "${BEAT_SCHEDULE_PATH:-${cachedir}/celerybeat-schedule}" &
uwsgi --ini uwsgi.ini
