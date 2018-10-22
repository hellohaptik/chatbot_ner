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

# install ES

RUN addgroup -S elasticsearch && adduser -S -G elasticsearch elasticsearch

# grab su-exec for easy step-down from root
# and bash for "bin/elasticsearch" among others
RUN apk add --no-cache 'su-exec>=0.2' bash

# https://artifacts.elastic.co/GPG-KEY-elasticsearch
ENV GPG_KEY 46095ACC8548582C1A2699A9D27D666CD88E42B4

WORKDIR /usr/share/elasticsearch
ENV PATH /usr/share/elasticsearch/bin:$PATH

ENV ELASTICSEARCH_VERSION 5.6.12
ENV ELASTICSEARCH_TARBALL="https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.6.12.tar.gz" \
	ELASTICSEARCH_TARBALL_ASC="https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.6.12.tar.gz.asc" \
	ELASTICSEARCH_TARBALL_SHA1="bc57fb5f089d7859ad2db5b10dc7561c711fd419"

RUN set -ex; \
	\
	apk add --no-cache --virtual .fetch-deps \
		ca-certificates \
		gnupg \
		openssl \
		tar \
	; \
	\
	wget -O elasticsearch.tar.gz "$ELASTICSEARCH_TARBALL"; \
	\
	if [ "$ELASTICSEARCH_TARBALL_SHA1" ]; then \
		echo "$ELASTICSEARCH_TARBALL_SHA1 *elasticsearch.tar.gz" | sha1sum -c -; \
	fi; \
	\
	if [ "$ELASTICSEARCH_TARBALL_ASC" ]; then \
		wget -O elasticsearch.tar.gz.asc "$ELASTICSEARCH_TARBALL_ASC"; \
		export GNUPGHOME="$(mktemp -d)"; \
		gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEY"; \
		gpg --batch --verify elasticsearch.tar.gz.asc elasticsearch.tar.gz; \
		rm -rf "$GNUPGHOME" elasticsearch.tar.gz.asc; \
	fi; \
	\
	tar -xf elasticsearch.tar.gz --strip-components=1; \
	rm elasticsearch.tar.gz; \
	\
	apk del .fetch-deps; \
	\
	mkdir -p ./plugins; \
	for path in \
		./data \
		./logs \
		./config \
		./config/scripts \
	; do \
		mkdir -p "$path"; \
		chown -R elasticsearch:elasticsearch "$path"; \
	done; \
	\
# we shouldn't need much RAM to test --version (default is 2gb, which gets Jenkins in trouble sometimes)
	export ES_JAVA_OPTS='-Xms32m -Xmx32m'; \
	if [ "${ELASTICSEARCH_VERSION%%.*}" -gt 1 ]; then \
		elasticsearch --version; \
	else \
# elasticsearch 1.x doesn't support --version
# but in 5.x, "-v" is verbose (and "-V" is --version)
		elasticsearch -v; \
	fi

#COPY config ./config

VOLUME /usr/share/elasticsearch/data

#COPY docker-entrypoint.sh /

EXPOSE 9200 9300


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
