#!/bin/bash
# startup script inside the container for tubearchivist

set -e

# replace environment variables in nginx site configuration
if [ -n "${BASE_URL}" ]; then
    if [[ ${BASE_URL:0:1} == "/" ]]; then
        BASE_URL=${BASE_URL:1}
    fi
    if [[ ${BASE_URL: -1} != "/" ]]; then
        BASE_URL="$BASE_URL/"
    fi
fi
envsubst < /etc/nginx/sites-available/default.template > /etc/nginx/sites-available/default

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
celery -A home.celery worker --loglevel=INFO --max-tasks-per-child 10 &
celery -A home beat --loglevel=INFO \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler &
uwsgi --ini uwsgi.ini
