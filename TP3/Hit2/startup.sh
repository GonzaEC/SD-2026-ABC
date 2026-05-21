#!/bin/bash

apt update
apt install -y docker.io

systemctl start docker
systemctl enable docker

docker pull ${docker_image}

docker run -d \
  --restart unless-stopped \
  -p 8000:8000 \
  -e WORKER_ID=${worker_id} \
  -e RABBITMQ_HOST=${rabbitmq_host} \
  -e RABBITMQ_USER=${rabbitmq_user} \
  -e RABBITMQ_PASS=${rabbitmq_pass} \
  ${docker_image}