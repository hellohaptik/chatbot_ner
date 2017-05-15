#!/bin/bash
mkdir -p ~/chatbot_ner_elasticsearch
cd /tmp/
curl -O https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.4.4/elasticsearch-2.4.4.tar.gz
tar -xzf elasticsearch-2.4.4.tar.gz -C ~/chatbot_ner_elasticsearch/
~/chatbot_ner_elasticsearch/elasticsearch-2.4.4/bin/elasticsearch -d
