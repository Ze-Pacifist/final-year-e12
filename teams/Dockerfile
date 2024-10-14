FROM ubuntu

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    supervisor \
    python3 \
    python3-pip \
    nodejs \
    npm
WORKDIR /challenges
COPY challenges/ /challenges/
RUN cd /challenges/node_challenge && npm install
RUN cd /challenges/python_challenge && apt install python3-flask -y

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 3000
EXPOSE 5000

CMD ["/usr/bin/supervisord"]