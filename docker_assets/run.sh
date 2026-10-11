#!/bin/bash
# startup script inside the container for tubearchivist

set -e

if [[ -n "$DJANGO_DEBUG" ]]; then
  LOGLEVEL="DEBUG"
else
  LOGLEVEL="INFO"
fi

# update yt-dlp if needed
YTDLP_UPDATE_DIR=/tmp/ta-yt-dlp
if [[ "${TA_AUTO_UPDATE_YTDLP,,}" =~ ^(release|nightly)$ ]]; then
  echo "Updating yt-dlp..."
  preflag=""
  if [[ "${TA_AUTO_UPDATE_YTDLP,,}" == "nightly" ]]; then
    preflag="--pre"
  fi

  if python -m pip install \
    --no-cache-dir \
    --target="$YTDLP_UPDATE_DIR" \
    --upgrade \
    $preflag \
    "yt-dlp[default]"
  then
    export PYTHONPATH="$YTDLP_UPDATE_DIR${PYTHONPATH:+:$PYTHONPATH}"
  else
    echo "yt-dlp update failed, using bundled version"
  fi
fi

# stop on pending manual migration
python manage.py ta_stop_on_error

# django setup
python manage.py migrate

# ta setup
python manage.py ta_envcheck
python manage.py ta_connection
python manage.py ta_startup

# start all tasks
celery -A task.celery worker \
    --loglevel=$LOGLEVEL \
    --concurrency 4 \
    --max-tasks-per-child 5 \
    --max-memory-per-child 150000 &

./beat_auto_spawn.sh &

python backend_start.py
