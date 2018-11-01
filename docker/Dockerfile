# This is to automated chatbot_ner installation

FROM python:2.7.15

RUN apt-get update && apt-get install -y wget build-essential curl supervisor vim openjdk-8-jdk-headless sudo


# install ES
# https://www.elastic.co/guide/en/elasticsearch/reference/5.6/deb.html

RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -

RUN set -x \
	&& apt-get update && apt-get install -y --no-install-recommends apt-transport-https && rm -rf /var/lib/apt/lists/* \
	&& echo 'deb https://artifacts.elastic.co/packages/5.x/apt stable main' > /etc/apt/sources.list.d/elastic-5.x.list

ENV ELASTICSEARCH_VERSION 5.6.12
ENV ELASTICSEARCH_DEB_VERSION 5.6.12
ENV ES_JAVA_OPTS="-Djava.io.tmpdir=/var/lib/elasticsearch/tmp"

RUN set -x \
	\
# don't allow the package to install its sysctl file (causes the install to fail)
# Failed to write '262144' to '/proc/sys/vm/max_map_count': Read-only file system
	&& dpkg-divert --rename /usr/lib/sysctl.d/elasticsearch.conf \
	\
	&& apt-get update \
	&& apt-get install -y --no-install-recommends "elasticsearch=$ELASTICSEARCH_DEB_VERSION" \
	&& rm -rf /var/lib/apt/lists/*

ENV PATH /usr/share/elasticsearch/bin:$PATH

WORKDIR /usr/share/elasticsearch

RUN set -ex \
	&& for path in \
		./data \
		./logs \
		./config \
		./config/scripts \
	; do \
		mkdir -p "$path"; \
		chown -R elasticsearch:elasticsearch "$path"; \
	done

COPY log4j2.properties ./config

EXPOSE 9200 9300

WORKDIR /app


COPY docker/install.sh /app/
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p ~/model_lib && \
    mkdir -p /root/models && \
    /app/install.sh && \
    touch /app/config && \
    touch /app/model_config && \
    pip install --no-cache-dir -I uwsgi

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY initial_setup.py /app/initial_setup.py
RUN python /app/initial_setup.py

# From start_server.sh

ENV NAME="chatbot_ner"
ENV DJANGODIR=/app
ENV NUM_WORKERS=4
ENV DJANGO_SETTINGS_MODULE=chatbot_ner.settings
ENV PORT=8080
ENV TIMEOUT=600
ENV DEBIAN_FRONTEND=noninteractive

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
ENV ES_BULK_MSG_SIZE=10000
ENV ES_SEARCH_SIZE=10
ENV CITY_MODEL_TYPE=crf
ENV CITY_MODEL_PATH=
ENV GOOGLE_TRANSLATE_API_KEY=

#ENV DATE_MODEL_TYPE=crf
#ENV DATE_MODEL_PATH=/root/models/models_live/date/crf/model.crf

EXPOSE 8080

ADD . /app

# entrypoint/cmd script
# CMD /app/docker/cmd.sh
ENTRYPOINT ["/app/docker/cmd.sh"]