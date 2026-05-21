output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster API endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "worker_ips" {
  description = "Internal IPs of Sobel worker VMs"
  value       = [for w in google_compute_instance.worker : w.network_interface[0].network_ip]
}

output "get_credentials_cmd" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --zone ${var.zone} --project ${var.project_id}"
}
