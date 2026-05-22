#!/bin/bash

apt update
apt install -y docker.io

systemctl enable docker
systemctl start docker


docker pull ${docker_image}

docker run -d \
  --restart always \
  -p 8000:8000 \
  -e WORKER_ID=${worker_id} \
  -e RABBITMQ_HOST=${rabbitmq_host} \
  -e RABBITMQ_USER=${rabbitmq_user} \
  -e RABBITMQ_PASS=${rabbitmq_pass} \
  ${docker_image}