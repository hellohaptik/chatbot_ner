#!/bin/bash

CONTAINER = $(docker ps -q -f name=chatbot-ner)

if [ "$1" == "--html" ]; then
    docker exec -it $CONTAINER python postman_tests/run_postman_tests.py --html
else
    docker exec -it $CONTAINER python postman_tests/run_postman_tests.py
fi
