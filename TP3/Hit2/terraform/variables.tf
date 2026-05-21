variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "zone" {
  type = string
}

variable "worker_count" {
  type = number
}

variable "rabbitmq_host" {
  type = string
}

variable "rabbitmq_user" {
  type    = string
  default = "user"
}

variable "rabbitmq_pass" {
  type      = string
  sensitive = true
}

variable "docker_image" {
  type = string
}