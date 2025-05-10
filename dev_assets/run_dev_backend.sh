#!/usr/bin/env bash
# startup script for development

set -e

# if the static/db.sqlite3 file does not exist, very likely the app hasn't been initialized yet
if [[ ! -f static/db.sqlite3 ]]; then
  python3 manage.py ta_startup || :
fi

# stop on pending manual migration
python3 manage.py ta_stop_on_error || :

# django setup
python3 manage.py migrate || :
python3 manage.py collectstatic --noinput -c || :

# ta setup
python3 manage.py ta_envcheck || :
python3 manage.py ta_connection || :
python3 manage.py ta_startup || :

# launch the backend
python3 manage.py runserver
