#!/command/with-contenv bash
. $(dirname "$0")/base.sh
set -x
python manage.py ta_envcheck
python manage.py ta_connection
python manage.py ta_startup
