#!/bin/bash

if [ "$1" == "--html" ]; then
    docker exec -it docker_chatbot-ner_1 python postman_tests/run_tests.py --html
else
    docker exec -it docker_chatbot-ner_1 python postman_tests/run_tests.py
fi
