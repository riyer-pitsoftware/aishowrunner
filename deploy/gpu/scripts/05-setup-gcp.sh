#!/usr/bin/env bash
# ChronoCanvas — First-Time GCP Setup
# Creates GCS buckets and stores Tailscale auth key in Secret Manager.
# Idempotent — safe to run multiple times.
#
# Usage: ./05-setup-gcp.sh
#   or via entrypoint: ./gpu-vm.sh setup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-config.sh"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ChronoCanvas — GCP Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Project:  $GCP_PROJECT_ID"
echo "  Region:   $GCP_REGION"
echo ""

# ─── 1. Enable required APIs ──────────────────────────────────
echo "◆ Enabling required APIs..."
gcloud services enable \
  compute.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  --project="$GCP_PROJECT_ID" \
  --quiet
log_info "APIs enabled"

# ─── 2. Create GCS buckets ────────────────────────────────────
echo ""
echo "◆ Creating GCS buckets..."

for BUCKET in "$GCS_MODELS_BUCKET" "$GCS_OUTPUT_BUCKET"; do
  BUCKET_NAME="${BUCKET#gs://}"
  if gcloud storage buckets describe "$BUCKET" --project="$GCP_PROJECT_ID" &>/dev/null; then
    log_info "Bucket already exists: $BUCKET"
  else
    gcloud storage buckets create "$BUCKET" \
      --project="$GCP_PROJECT_ID" \
      --location="$GCP_REGION" \
      --uniform-bucket-level-access
    log_info "Created bucket: $BUCKET"
  fi
done

# ─── 3. Tailscale auth key ────────────────────────────────────
echo ""
echo "◆ Tailscale auth key setup..."

TS_SECRET_NAME="ts-authkey"
if gcloud secrets describe "$TS_SECRET_NAME" --project="$GCP_PROJECT_ID" &>/dev/null; then
  log_info "Tailscale secret already exists in Secret Manager"
  echo "  To update: gcloud secrets versions add $TS_SECRET_NAME --project=$GCP_PROJECT_ID --data-file=-"
else
  echo ""
  echo "  Tailscale auth key needed for VPN access to ComfyUI."
  echo "  Generate one at: https://login.tailscale.com/admin/settings/keys"
  echo "  Settings: Reusable=yes, Ephemeral=yes"
  echo ""
  echo -n "  Paste your Tailscale auth key (tskey-auth-...): "
  read -r TS_KEY

  if [[ -z "$TS_KEY" ]]; then
    log_warn "No key provided — skipping Tailscale setup"
    echo "  You can add it later:"
    echo "  echo -n 'tskey-auth-...' | gcloud secrets create $TS_SECRET_NAME --project=$GCP_PROJECT_ID --data-file=-"
  elif [[ "$TS_KEY" != tskey-auth-* ]]; then
    log_error "Key doesn't start with 'tskey-auth-'. Skipping."
    echo "  You can add it later:"
    echo "  echo -n 'tskey-auth-...' | gcloud secrets create $TS_SECRET_NAME --project=$GCP_PROJECT_ID --data-file=-"
  else
    echo -n "$TS_KEY" | gcloud secrets create "$TS_SECRET_NAME" \
      --project="$GCP_PROJECT_ID" \
      --data-file=-
    log_info "Tailscale auth key stored in Secret Manager"
  fi
fi

# ─── Summary ──────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✓ GCP setup complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Upload models:  ./gpu-vm.sh upload-models"
echo "  2. Create VM:      ./gpu-vm.sh create l4"
echo "  3. Start VM:       ./gpu-vm.sh start l4"
echo ""
