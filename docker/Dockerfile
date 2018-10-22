# This is to automated chatbot_ner installation

FROM python:2.7.15

RUN apt-get update && apt-get install -y wget build-essential curl nginx supervisor
RUN apt-get install -y software-properties-common

#--- SM image -----

# Java installation for elasticsearch
RUN \
  echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
  add-apt-repository -y ppa:webupd8team/java && \
  apt-get update && \
  apt-get install -y --allow-unauthenticated oracle-java8-installer && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer

# Define commonly used JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

#---- / SM image ---

WORKDIR /app


COPY install.sh initial_setup.py /app/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p ~/model_lib && \
    mkdir -p /root/models && \
    /app/install.sh && \
    touch /app/config && \
    touch /app/model_config && \
    pip install --no-cache-dir -I uwsgi

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# From start_server.sh

ENV NAME="chatbot_ner"
ENV DJANGODIR=/app
ENV NUM_WORKERS=4
ENV DJANGO_SETTINGS_MODULE=chatbot_ner.settings
ENV PORT=8081
ENV TIMEOUT=600
ENV DEBIAN_FRONTEND=noninteractive

#--- SM image --

# Setting env variables
# ENV vars defined in Dockerfile can be overwritten here before docker-compose up
ENV NUM_WORKERS=1
ENV MAX_REQUESTS=1000
ENV DJANGO_WSGI_MODULE=chatbot_ner/wsgi.py
ENV DJANGO_LOG_LEVEL=debug
ENV DJANGO_DEBUG=False
ENV ENGINE=elasticsearch

# ES_HOST is host for ES that comes up with compose
ENV ES_HOST=localhost
ENV ES_PORT=9200
ENV ES_INDEX_NAME=entity_data
ENV ES_DOC_TYPE=data_dictionary
ENV ES_BULK_MSG_SIZE=1000
ENV ES_SEARCH_SIZE=10
ENV CITY_MODEL_TYPE=crf
ENV CITY_MODEL_PATH=
ENV GOOGLE_TRANSLATE_API_KEY=

# --- / SM image --


#ENV DATE_MODEL_TYPE=crf
#ENV DATE_MODEL_PATH=/root/models/models_live/date/crf/model.crf

EXPOSE 8081

ADD . /app

# entrypoint/cmd script
CMD /app/docker/cmd.sh
