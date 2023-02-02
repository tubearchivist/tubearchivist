#!/bin/bash
# startup script inside the container for tubearchivist

set -e

# check environment
python manage.py ta_envcheck
python manage.py ta_connection
python manage.py ta_startup

# start python application
python manage.py makemigrations
python manage.py migrate
# python manage.py collectstatic --noinput -c

nginx &
celery -A home.tasks worker --loglevel=INFO &
celery -A home beat --loglevel=INFO \
    -s "${BEAT_SCHEDULE_PATH:-${cachedir}/celerybeat-schedule}" &
uwsgi --ini uwsgi.ini
