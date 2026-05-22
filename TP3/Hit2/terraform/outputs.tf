output "worker_ips" {
  value = [
    for instance in google_compute_instance.worker :
    instance.network_interface[0].access_config[0].nat_ip
  ]
}

output "rabbitmq_ip" {
  value = google_compute_instance.rabbitmq.network_interface[0].access_config[0].nat_ip
}