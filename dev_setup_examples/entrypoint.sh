#!/bin/bash

export $(envkey-source -f | sed -e 's/\<export\>//g' | sed -e 's/\s\+/\n/g' | xargs) > /dev/null
export ENVKEY=""

cd $DJANGODIR

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
# RUNDIR=$(dirname $SOCKFILE)
# test -d $RUNDIR || mkdir -p $RUNDIR


if [ "$NEWRELIC" == "true" ]; then

        # Define app_name based on the environment to be deployed on.
        if [ "$HAPTIK_ENV" == "staging" ]; then
                sed -i "s/chatbot_ner/chatbot_ner_staging/g" newrelic.ini
        fi

        # Update the license key
        sed -i "s/license_value/$NEWRELIC_LICENSE_KEY/g" newrelic.ini

        # Start uwsgi with newrelic agent
        export NEW_RELIC_CONFIG_FILE=newrelic.ini
        newrelic-admin run-program uwsgi --wsgi-file chatbot_ner/wsgi.py --http :$PORT --strict --need-app --master --workers=$NUM_WORKERS --threads 5 --enable-threads --disable-logging --log-5xx --log-prefix=uwsgi --log-slow=3000 --logto=/app/logs/ner_log.log --logfile-chmod=644 --max-requests=$MAX_REQUESTS --harakiri=$TIMEOUT --reload-mercy=60 --worker-reload-mercy=60 --thunder-lock --http-auto-chunked --http-keepalive --vacuum --single-interpreter --buffer-size=15000

else

    uwsgi --wsgi-file chatbot_ner/wsgi.py --http :$PORT --strict --need-app --master --workers=$NUM_WORKERS --threads 5 --enable-threads --disable-logging --log-5xx --log-prefix=uwsgi --log-slow=3000 --logto=/app/logs/ner_log.log --logfile-chmod=644 --max-requests=$MAX_REQUESTS --harakiri=$TIMEOUT --reload-mercy=60 --worker-reload-mercy=60 --thunder-lock --http-auto-chunked --vacuum --single-interpreter --buffer-size=15000 --http-keepalive=1 --http-timeout=600

fi
