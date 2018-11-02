#!/bin/bash

cd $DJANGODIR

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Initial setup.py - Datastore lines need to be commented for using previously create data

# python /app/initial_setup.py

# Using supervisor as we want to use Nginx and Uwsgi both, Settings specified in supervisord.conf, any update to that will need build

sudo ES_JAVA_OPTS=$ES_JAVA_OPTS -u elasticsearch /usr/share/elasticsearch/bin/elasticsearch -d -p /usr/share/elasticsearch/logs/elasticsearch-pid
sh initial_setup_es.sh
kill -SIGTERM $(cat /usr/share/elasticsearch/logs/elasticsearch-pid)
/usr/bin/supervisord


# Below parameters can be changed as you wish, values fetched from env variables. You can only run UWSGI by uncommenting the next uwsgi line and commenting above supervisor line
#uwsgi --wsgi-file chatbot_ner/wsgi.py --http :$PORT --workers=$NUM_WORKERS --disable-logging --master --max-requests=$MAX_REQUESTS --harakiri=$TIMEOUT --reload-mercy=120 --worker-reload-mercy=120 --thunder-lock --http-auto-chunked --http-keepalive --vacuum && /usr/sbin/nginx -g 'daemon off;'
#/usr/sbin/nginx -g 'daemon off;'
