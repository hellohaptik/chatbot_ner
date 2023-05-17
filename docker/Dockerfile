FROM python:3.6.15
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y wget build-essential curl nginx supervisor

WORKDIR /app

COPY requirements.txt nltk_setup.py /app/

RUN touch /app/config && \
    pip install --no-cache-dir -U pip &&  \
    pip install --no-cache-dir -r /app/requirements.txt && \
    pip check && \
    python /app/nltk_setup.py

COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/default.site.conf /etc/nginx/sites-available/default

# TODO: Separate this out to a dev/test docker image
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash && \
    apt-get install nodejs && \
    npm install -g newman && \
    npm install -g newman-reporter-htmlextra && \
    rm -rf /tmp/* ~/.cache/pip /var/lib/apt/lists/*


ENV NAME="chatbot_ner"
ENV DJANGODIR=/app
ENV NUM_WORKERS=4
ENV DJANGO_SETTINGS_MODULE=chatbot_ner.settings
ENV PORT=8081
ENV TIMEOUT=600
# Important change this via .env (the file copied from .env.example)
ENV SECRET_KEY=!yqqcz-v@(s@kpygpvomcuu3il0q1&qtpz)e_g0ulo-sdv%c0c

ADD . /app
EXPOSE 8081
# entrypoint/cmd script
CMD /app/docker/cmd.sh
