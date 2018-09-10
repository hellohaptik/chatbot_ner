# This is to automated chatbot_ner installation

FROM python:2.7.15

RUN apt-get update && apt-get install -y wget build-essential curl nginx

WORKDIR /app


COPY install.sh nginx.sh /app

RUN mkdir -p ~/model_lib && \
    mkdir -p /root/models && \
    /app/install_CRF.sh && \
    /app/nginx.sh && \
    touch /app/config && \
    touch /app/model_config

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

RUN chmod +x /app/entrypoint.sh

CMD /app/entrypoint.sh
