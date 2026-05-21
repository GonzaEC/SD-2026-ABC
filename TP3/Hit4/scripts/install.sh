#!/bin/bash
# Instala el stack de observabilidad (Hit #4) sobre el cluster GKE del Hit #3.
# Prerrequisito: cluster GKE corriendo y kubectl apuntando a él.
set -e

PROJECT="tp3-gcp-497003"
HIT4_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Hit #4 — Observabilidad: Prometheus + Grafana ==="

# ── 1. Helm repo ──────────────────────────────────────────────────────────────
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# ── 2. Namespace ──────────────────────────────────────────────────────────────
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# ── 3. kube-prometheus-stack ─────────────────────────────────────────────────
# install si no existe, upgrade si ya está
helm upgrade --install kps prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f "$HIT4_DIR/helm/values.yaml"

# ── 4. Firewall para acceder a Grafana (NodePort 30300) ──────────────────────
NODE_TAG=$(gcloud compute instances list --project "$PROJECT" \
  --filter="name~gke-sobel-cluster" --format="value(tags.items[0])" --limit=1)

gcloud compute firewall-rules create allow-grafana-nodeport \
  --project "$PROJECT" \
  --network default \
  --allow tcp:30300 \
  --source-ranges 0.0.0.0/0 \
  --target-tags "$NODE_TAG" \
  2>/dev/null || echo "Regla de firewall ya existe."

# ── 5. ServiceMonitors, dashboard y alertas ──────────────────────────────────
kubectl apply -f "$HIT4_DIR/k8s/servicemonitors.yaml"
kubectl apply -f "$HIT4_DIR/k8s/grafana-dashboard.yaml"
kubectl apply -f "$HIT4_DIR/k8s/alert-rules.yaml"

# ── Info de acceso ───────────────────────────────────────────────────────────
NODE_IP=$(gcloud compute instances list --project "$PROJECT" \
  --filter="name~gke-sobel-cluster" \
  --format="value(networkInterfaces[0].accessConfigs[0].natIP)" --limit=1)

echo ""
echo "=== Listo ==="
echo "Grafana: http://$NODE_IP:30300  (admin / sobel-admin)"
echo "Dashboard: 'Sobel — Plataforma Distribuida'"
