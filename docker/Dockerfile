# This is to automated chatbot_ner installation

FROM python:2.7.15

RUN apt-get update && apt-get install -y wget build-essential curl nginx supervisor

WORKDIR /app

COPY docker/install.sh nltk_setup.py datastore_setup.py /app/
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

# Important change this via .env (the file copied from config.example)
ENV SECRET_KEY=!yqqcz-v@(s@kpygpvomcuu3il0q1&qtpz)e_g0ulo-sdv%c0c

EXPOSE 8081

ADD . /app

# entrypoint/cmd script
CMD /app/docker/cmd.sh
