#!/bin/bash
# auto restart beat scheduler
# https://github.com/celery/django-celery-beat/issues/894

if [[ -n "$DJANGO_DEBUG" ]]; then
  LOGLEVEL="DEBUG"
else
  LOGLEVEL="INFO"
fi

COMMAND="celery -A task beat --loglevel=$LOGLEVEL --scheduler django_celery_beat.schedulers:DatabaseScheduler"
TIMEOUT=3600

while true; do
    echo "Starting process beat scheduler"

    $COMMAND &
    PID=$!

    sleep $TIMEOUT

    # Kill the process if still running
    if kill -0 $PID 2>/dev/null; then
        echo "Killing beat process after $TIMEOUT seconds"
        kill $PID
        # Wait a bit to allow graceful shutdown, then force kill if needed
        sleep 10
        kill -9 $PID 2>/dev/null
    fi

    echo "Restarting beat..."
done
