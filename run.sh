#!/bin/bash
# startup script inside the container for tubearchivist

counter=0
until curl "$ES_URL" -fs; do
    echo "waiting for elastic search to start"
    counter=$((counter+1))
    if [[ $counter -eq 12 ]]; then
        # fail after 1 min
        echo "failed to connect to elastic search, exiting..."
        exit 1
    fi
    sleep 5
done

python manage.py migrate
python manage.py collectstatic
nginx &
celery -A home.tasks worker --loglevel=INFO --detach
uwsgi --ini uwsgi.ini
