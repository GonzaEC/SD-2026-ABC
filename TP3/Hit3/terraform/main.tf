# ── GKE Cluster ───────────────────────────────────────────────────────────────
# remove_default_node_pool=true para crear node pools dedicados con labels/taints
resource "google_container_cluster" "primary" {
  name                     = "sobel-cluster"
  location                 = var.zone
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = "default"
  subnetwork = "default"

  deletion_protection = false
}

# ── Nodegroup: Infraestructura (RabbitMQ, Redis, Prometheus, Grafana) ─────────
resource "google_container_node_pool" "infra" {
  name       = "infra-pool"
  location   = var.zone
  cluster    = google_container_cluster.primary.name
  node_count = 1

  node_config {
    machine_type = var.infra_pool_machine_type
    disk_size_gb = 30

    labels = {
      nodegroup = "infra"
    }

    taint {
      key    = "nodegroup"
      value  = "infra"
      effect = "NO_SCHEDULE"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# ── Nodegroup: Aplicaciones (frontend, backend, split, joiner) ────────────────
resource "google_container_node_pool" "apps" {
  name       = "apps-pool"
  location   = var.zone
  cluster    = google_container_cluster.primary.name
  node_count = 2

  node_config {
    machine_type = var.apps_pool_machine_type
    disk_size_gb = 30

    labels = {
      nodegroup = "apps"
    }

    taint {
      key    = "nodegroup"
      value  = "apps"
      effect = "NO_SCHEDULE"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# ── Worker VMs (Compute Engine, fuera del cluster GKE) ────────────────────────
# Mantenerlas fuera del cluster permite escalarlas independientemente y usar
# tipos de instancia distintos sin cambiar los node pools de GKE.
resource "google_compute_instance" "worker" {
  count        = var.worker_count
  name         = "sobel-worker-${count.index}"
  machine_type = var.worker_machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network = "default"
    # Sin external IP para no consumir cuota IN_USE_ADDRESSES; Cloud NAT da salida
  }

  metadata_startup_script = templatefile(
    "${path.module}/../startup.sh",
    {
      rabbitmq_host = var.rabbitmq_host
      rabbitmq_user = var.rabbitmq_user
      rabbitmq_pass = var.rabbitmq_pass
      docker_image  = var.docker_image
      worker_id     = "worker-${count.index}"
    }
  )

  tags = ["sobel-worker"]

  service_account {
    email  = "${data.google_project.project.number}-compute@developer.gserviceaccount.com"
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

data "google_project" "project" {
  project_id = var.project_id
}

# ── Cloud NAT — salida a internet para workers sin external IP ─────────────────
resource "google_compute_router" "nat_router" {
  name    = "sobel-nat-router"
  network = "default"
  region  = var.region
}

resource "google_compute_router_nat" "nat" {
  name                               = "sobel-nat"
  router                             = google_compute_router.nat_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# ── Firewall: health check de workers ─────────────────────────────────────────
resource "google_compute_firewall" "allow_worker_health" {
  name    = "allow-worker-health"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["sobel-worker"]
}

# ── Firewall: RabbitMQ accesible desde las worker VMs ─────────────────────────
resource "google_compute_firewall" "allow_rabbitmq" {
  name    = "allow-rabbitmq-from-workers"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5672"]
  }

  source_tags = ["sobel-worker"]
  target_tags = ["gke-sobel-cluster"]
}
