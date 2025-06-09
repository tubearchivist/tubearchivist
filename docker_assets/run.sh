#!/bin/bash
# startup script inside the container for tubearchivist

set -e

if [[ -n "$DJANGO_DEBUG" ]]; then
  LOGLEVEL="DEBUG"
else
  LOGLEVEL="INFO"
fi

if [ "${TA_AUTO_UPDATE_YTDLP,,}" = "true" ]; then
    echo "Updating yt-dlp..."
    python -m pip install -U yt-dlp
fi

# stop on pending manual migration
python manage.py ta_stop_on_error

# django setup
python manage.py migrate
python manage.py collectstatic --noinput -c

# ta setup
python manage.py ta_envcheck
python manage.py ta_connection
python manage.py ta_startup

# start all tasks
nginx &
celery -A task.celery worker \
    --loglevel=$LOGLEVEL \
    --concurrency 4 \
    --max-tasks-per-child 5 \
    --max-memory-per-child 150000 &

./beat_auto_spawn.sh &

python backend_start.py
