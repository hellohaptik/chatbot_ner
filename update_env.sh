#!/bin/bash

# SERVER_ENV=development
# REGION=us-west-2
# rm -f /tmp/chatbot_ner.env
# aws s3 cp s3://haptik-env-configuration/$SERVER_ENV/$REGION/chatbot_ner.env /tmp/chatbot_ner.env --region ap-south-1
az storage blob download --container-name  devserver-env --name chatbot_ner.env --account-name haptikdevelopment  -f /tmp/chatbot_ner.env
cp /tmp/chatbot_ner.env ~/chatbot_ner/.env

