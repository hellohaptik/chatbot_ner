#!/bin/bash

until $(curl --output /dev/null --silent --head --fail http://localhost:9200); do
    echo "waiting for es.."
    sleep 2
done
python initial_setup_es.py