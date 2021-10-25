#!/bin/bash
# startup script inside the container for tubearchivist

counter=0
until curl "$ES_URL" -fs; do
    echo "waiting for elastic search to start"
    counter=$((counter+1))
    if [[ $counter -eq 12 ]]; then
        # fail after 2 min
        echo "failed to connect to elastic search, exiting..."
        exit 1
    fi
    sleep 10
done

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser --noinput
python manage.py collectstatic --noinput -c
nginx &
celery -A home.tasks worker --loglevel=INFO &
uwsgi --ini uwsgi.ini
