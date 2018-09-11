#!/bin/bash

cd $DJANGODIR

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Initial setup.py - Datastore lines need to be commented for using previously create data

python /app/initial_setup.py

/usr/sbin/nginx -g 'daemon off;'

# Below parameters can be changed as you wish, values fetched from env variables
uwsgi --wsgi-file ../chatbot_ner/wsgi.py --http :$PORT --workers=$NUM_WORKERS --disable-logging --master --max-requests=$MAX_REQUESTS --harakiri=$TIMEOUT --reload-mercy=120 --worker-reload-mercy=120 --thunder-lock --http-auto-chunked --http-keepalive --vacuum
