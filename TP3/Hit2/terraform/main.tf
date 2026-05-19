resource "google_compute_instance" "worker" {

  count        = var.worker_count

  name         = "sobel-worker-${count.index}"
  machine_type = "e2-micro"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network = "default"

    access_config {}
  }

  metadata_startup_script = templatefile(
    "${path.module}/startup.sh",
    {
      rabbitmq_host = var.rabbitmq_host
      docker_image  = var.docker_image
      worker_id     = "worker-${count.index}"
    }
  )

  tags = ["http-server"]
}
resource "google_compute_firewall" "allow_health" {

  name    = "allow-health"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = ["0.0.0.0/0"]

  target_tags = ["http-server"]
}