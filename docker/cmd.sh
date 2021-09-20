#!/bin/bash

cd $DJANGODIR

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Initial setup.py - Datastore lines need to be commented for using previously create data
# TODO: Bad design, should not need to comment
python /app/datastore_setup.py || { echo 'datastore setup failed'; exit 1; }
/usr/bin/supervisord
