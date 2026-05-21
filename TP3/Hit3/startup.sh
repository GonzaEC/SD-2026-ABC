#!/bin/bash

apt-get update -y
apt-get install -y docker.io curl

systemctl start docker
systemctl enable docker

# Autenticar Docker contra GCR usando el token del metadata server
TOKEN=$(curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
echo "$TOKEN" | docker login -u oauth2accesstoken --password-stdin https://gcr.io

docker pull ${docker_image}

docker run -d \
  --restart unless-stopped \
  -p 8000:8000 \
  -e WORKER_ID=${worker_id} \
  -e RABBITMQ_HOST=${rabbitmq_host} \
  -e RABBITMQ_USER=${rabbitmq_user} \
  -e RABBITMQ_PASS=${rabbitmq_pass} \
  ${docker_image}
