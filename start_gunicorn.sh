#!/bin/bash

NAME="chatbot_ner"                                 # Name of the application
DJANGODIR=/home/ubuntu/chatbot_ner                 # Django project directory
SOCKFILE=/home/ubuntu/run/gunicorn.sock           # we will communicate using this unix socket
USER=ubuntu                                       # the user to run as
GROUP=ubuntu                                     # the group to run as
NUM_WORKERS=2                                     # how many worker processes should Gunicorn spawn
PORT=8081
TIMEOUT=600

DJANGO_SETTINGS_MODULE=chatbot_ner.settings # which settings file should Django use
DJANGO_WSGI_MODULE=chatbot_ner.wsgi                    # WSGI module name

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source ~/Envs/vchatbotner/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR


# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  -b 0.0.0.0:$PORT \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --log-level=debug \
  --bind=unix:$SOCKFILE \
  --timeout $TIMEOUT \
  --backlog=2048
#  --threads=2
