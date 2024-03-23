#!/bin/bash
# startup script inside the container for tubearchivist

set -e

cd /app || exit 1

# django setup
python manage.py migrate

if [[ -z "$DJANGO_DEBUG" ]]; then
    python manage.py collectstatic --noinput -c
fi

# ta setup
python manage.py ta_envcheck
python manage.py ta_connection
python manage.py ta_startup
python manage.py ta_migpath

#export PYTHONWARNINGS=error

pip install watchdog -U
watchmedo shell-command --patterns="*.html;*.css;*.js" --recursive --command='kill -HUP `cat /tmp/project-master.pid`' . &
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A home.tasks worker --loglevel=INFO --max-tasks-per-child 10 &

# start all tasks
nginx &
celery -A home.tasks worker --loglevel=INFO --max-tasks-per-child 10 &
celery -A home beat --loglevel=INFO \
    -s "${BEAT_SCHEDULE_PATH:-${cachedir}/celerybeat-schedule}" &
uwsgi --ini /uwsgi-dev.ini
