# This is to automated chatbot_ner installation

FROM python:2.7.15

RUN apt-get update && apt-get install -y wget build-essential curl nginx supervisor

WORKDIR /app


COPY docker/install.sh initial_setup.py /app/
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

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


#ENV DATE_MODEL_TYPE=crf
#ENV DATE_MODEL_PATH=/root/models/models_live/date/crf/model.crf

EXPOSE 8081

ADD . /app

# entrypoint/cmd script
CMD /app/docker/cmd.sh
