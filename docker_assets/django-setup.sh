#!/command/with-contenv bash
. $(dirname "$0")/base.sh

python manage.py migrate
python manage.py collectstatic --noinput -c
