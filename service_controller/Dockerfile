FROM python:3.9-alpine
WORKDIR /app

COPY service_controller/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service_controller/src/ .
COPY service_controller/checkers/ .
COPY service_controller/entrypoint.sh .

RUN chmod +x entrypoint.sh

RUN apk add --no-cache \
	findutils openresolv iptables ip6tables iproute2 wireguard-tools
    
CMD ["/app/entrypoint.sh"]