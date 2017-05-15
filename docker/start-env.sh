#!/bin/bash
/root/chatbot_ner_elasticsearch/elasticsearch-2.4.4/bin/elasticsearch -Des.insecure.allow.root=true -d && /root/chatbot_ner/docker/start_server_docker.sh
