#!/bin/bash
# Get sample Nginx file for routing and GUI
cd /tmp
wget "https://s3-us-west-2.amazonaws.com/chatbotner/chatbot_ner_nginx/default"
bash -c "cat /tmp/default > /etc/nginx/sites-available/default"
rm -rf /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
sed -i 's/www-data/root/g' /etc/nginx/nginx.conf
