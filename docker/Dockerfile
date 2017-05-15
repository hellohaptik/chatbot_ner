FROM ubuntu:latest
RUN apt-get update && apt-get install -y python-dev python-pip build-essential curl python-pip vim git

RUN pip install --upgrade pip
#######If you want to run with virtualenv uncomment below line
#RUN /bin/bash -c "source /usr/local/bin/virtualenvwrapper.sh && mkvirtualenv chatbotnervenv && workon chatbotnervenv"
RUN cd ~/ &&  git clone https://github.com/hellohaptik/chatbot_ner.git ; cd ~/chatbot_ner && pip install -r requirements.txt
COPY java.sh elasticsearch.sh /root/
RUN /root/java.sh && /root/elasticsearch.sh
RUN cp /root/chatbot_ner/config.example /root/chatbot_ner/config ; ~/chatbot_ner_elasticsearch/elasticsearch-2.4.4/bin/elasticsearch -Des.insecure.allow.root=true -d && sleep 10 && python ~/chatbot_ner/initial_setup.py
###WONT LET YOU RUN IT AS ROOT ~/chatbot_ner_elasticsearch/elasticsearch-2.4.4/bin/elasticsearch -d

##FOR Non virtualenv 
ADD start.sh /root/start.sh
CMD bash /root/start.sh

#FOR virtual env, comment above 2 lines and uncomment below line

#ADD start-env.sh /root/start-env.sh
#CMD bash /root/start-env.sh
