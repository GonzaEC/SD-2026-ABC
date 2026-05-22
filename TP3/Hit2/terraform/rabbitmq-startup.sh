#!/bin/bash

exec > /var/log/startup-script.log 2>&1
set -eux

apt-get update
apt-get install -y docker.io

systemctl enable docker
systemctl start docker

docker pull rabbitmq:3-management

docker run -d \
  --hostname rabbitmq \
  --restart always \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=${rabbitmq_user} \
  -e RABBITMQ_DEFAULT_PASS=${rabbitmq_pass} \
  rabbitmq:3-management