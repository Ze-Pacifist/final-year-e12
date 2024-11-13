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
RUN cd /challenges/python_challenge && apt-get update && apt-get install -y --fix-missing python3-flask

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 3000
EXPOSE 5000

CMD ["/usr/bin/supervisord"]