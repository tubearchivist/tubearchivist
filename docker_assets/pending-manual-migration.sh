#!/command/with-contenv bash
. $(dirname "$0")/base.sh

python manage.py ta_stop_on_error
