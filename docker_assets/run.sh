#!/bin/bash
# startup script inside the container for tubearchivist


# check environment
python manage.py ta_envcheck
python manage.py ta_connection

# wait for elasticsearch
# counter=0
# until curl -u "$ELASTIC_USER":"$ELASTIC_PASSWORD" "$ES_URL" -fs; do
#     echo "waiting for elastic search to start"
#     counter=$((counter+1))
#     if [[ $counter -eq 12 ]]; then
#         # fail after 2 min
#         echo "failed to connect to elastic search, exiting..."
#         curl -v -u "$ELASTIC_USER":"$ELASTIC_PASSWORD" "$ES_URL"?pretty
#         exit 1
#     fi
#     sleep 10
# done

# start python application
python manage.py makemigrations
python manage.py migrate
# python manage.py collectstatic --noinput -c

nginx &
celery -A home.tasks worker --loglevel=INFO &
celery -A home beat --loglevel=INFO \
    -s "${BEAT_SCHEDULE_PATH:-${cachedir}/celerybeat-schedule}" &
uwsgi --ini uwsgi.ini
