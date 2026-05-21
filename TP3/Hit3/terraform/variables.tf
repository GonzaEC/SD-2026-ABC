variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "worker_count" {
  description = "Number of Sobel worker VMs outside the cluster"
  type        = number
  default     = 3
}

variable "infra_pool_machine_type" {
  description = "Machine type for infra node pool (RabbitMQ, Redis)"
  type        = string
  default     = "e2-standard-2"
}

variable "apps_pool_machine_type" {
  description = "Machine type for apps node pool (frontend, backend, split, joiner)"
  type        = string
  default     = "e2-standard-2"
}

variable "worker_machine_type" {
  description = "Machine type for Sobel worker VMs"
  type        = string
  default     = "e2-standard-2"
}

variable "docker_image" {
  description = "Docker image URI for the Sobel worker"
  type        = string
}

variable "rabbitmq_host" {
  description = "RabbitMQ host reachable from worker VMs (internal LB IP)"
  type        = string
}

variable "rabbitmq_user" {
  description = "RabbitMQ username"
  type        = string
  default     = "user"
}

variable "rabbitmq_pass" {
  description = "RabbitMQ password"
  type        = string
  sensitive   = true
}
