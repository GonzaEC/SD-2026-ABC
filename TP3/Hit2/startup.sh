#!/bin/bash

apt update
apt install -y docker.io

systemctl start docker
systemctl enable docker

docker pull ${docker_image}

docker run -d \
  -p 8000:8000 \
  -e WORKER_ID=${worker_id} \
  -e RABBITMQ_HOST=${rabbitmq_host} \
  ${docker_image}