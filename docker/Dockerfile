FROM ubuntu

RUN apt-get update && apt-get install -y nginx python-dev python-pip build-essential curl python-pip vim git

COPY install_CRF.sh install.sh java.sh elasticsearch.sh /root/
RUN /root/java.sh && /root/elasticsearch.sh
RUN /root/install.sh
RUN bash /root/install_CRF.sh

ADD start.sh /root/start.sh
CMD bash /root/start.sh

# ADD start-env.sh /root/start-env.sh
# CMD bash /root/start-env.sh
