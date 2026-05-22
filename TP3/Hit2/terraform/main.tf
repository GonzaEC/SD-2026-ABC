resource "google_compute_instance" "worker" {

  count        = var.worker_count

  depends_on = [
    google_compute_instance.rabbitmq,
    google_compute_firewall.allow_rabbitmq
  ]

  name         = "sobel-worker-${count.index}"
  machine_type = "e2-micro"
  zone         = var.zone

  tags = ["worker", "http-server"]

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
      rabbitmq_host = google_compute_instance.rabbitmq.network_interface[0].access_config[0].nat_ip
      rabbitmq_user = var.rabbitmq_user
      rabbitmq_pass = var.rabbitmq_pass
      docker_image  = var.docker_image
      worker_id     = "worker-${count.index}"
    }
  )
}

resource "google_compute_firewall" "allow_health" {

  name    = "allow-health"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = ["0.0.0.0/0"]

  target_tags = ["worker"]
}

resource "google_compute_instance" "rabbitmq" {

  name         = "rabbitmq-server"
  machine_type = "e2-micro"
  zone         = var.zone

  tags = ["rabbitmq"]

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
    "${path.module}/rabbitmq-startup.sh",
    {
      rabbitmq_user = var.rabbitmq_user
      rabbitmq_pass = var.rabbitmq_pass
    }
  )
}

resource "google_compute_firewall" "allow_rabbitmq" {

  name    = "allow-rabbitmq"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5672", "15672"]
  }

  source_ranges = ["0.0.0.0/0"]

  target_tags = ["rabbitmq"]
}