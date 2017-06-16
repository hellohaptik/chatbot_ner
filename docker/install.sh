#!/bin/bash
pip install pip --upgrade
pip install -U virtualenvwrapper
/bin/bash -c "source /usr/local/bin/virtualenvwrapper.sh;  mkvirtualenv chatbotnervenv ;  workon chatbotnervenv"
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
echo "workon chatbotnervenv" >> ~/.bashrc
source ~/.bashrc
cd ~/ &&  git clone https://github.com/hellohaptik/chatbot_ner.git --branch docker
cd ~/chatbot_ner && pip install -r requirements.txt
cp /root/chatbot_ner/config.example /root/chatbot_ner/config
~/chatbot_ner_elasticsearch/elasticsearch-2.4.4/bin/elasticsearch -Des.insecure.allow.root=true -d && sleep 10 && python ~/chatbot_ner/initial_setup.py
touch /usr/bin/killgun; echo "ps -aef | grep gunicorn | grep -v grep | cut -d ' ' -f8 | xargs kill -9" > /usr/bin/killgun ; chmod +x /usr/bin/killgun

cd /tmp
wget "https://s3-us-west-2.amazonaws.com/chatbotner/chatbot_ner_nginx/default"
bash -c "/tmp/default > /etc/nginx/sites-available/default"
rm -rf /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
