FROM ubuntu

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    supervisor \
    python3 \
    python3-pip \
    nodejs \
    npm \
    openssh-server

RUN mkdir /var/run/sshd && \
echo 'root:root' | chpasswd && \
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

WORKDIR /challenges
COPY challenges/ /challenges/
RUN cd /challenges/node_challenge && npm install
RUN cd /challenges/python_challenge && apt-get update && apt-get install -y --fix-missing python3-flask

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 3000
EXPOSE 5000

CMD ["/usr/bin/supervisord"]