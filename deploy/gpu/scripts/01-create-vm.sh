#!/usr/bin/env bash
# ChronoCanvas — One-Time VM Creation Script
# Creates a GCP GPU VM (L4 or A100) using Deep Learning VM image.
# The VM is created in STOPPED state — use gpu-vm.sh to start it.
#
# Usage: ./01-create-vm.sh [l4|a100]
#
# Prerequisites:
#   - GCP_PROJECT_ID set in environment
#   - GPU quota requested for the target tier in us-central1
#   - GCS buckets created (gs://chronocanvas-models, gs://chronocanvas-outputs)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../config.env"

# ─── Argument Parsing ───────────────────────────────────────
TIER="${1:-}"
if [[ -z "$TIER" ]] || [[ "$TIER" != "l4" && "$TIER" != "a100" ]]; then
  echo "Usage: $0 [l4|a100]"
  echo ""
  echo "  l4   — g2-standard-8, NVIDIA L4 24GB, SPOT (~\$${L4_HOURLY_RATE}/hr)"
  echo "  a100 — a2-highgpu-1g, NVIDIA A100 40GB, STANDARD (~\$${A100_HOURLY_RATE}/hr)"
  exit 1
fi

# ─── Set Tier-Specific Variables ─────────────────────────────
if [[ "$TIER" == "l4" ]]; then
  INSTANCE_NAME="$L4_INSTANCE_NAME"
  MACHINE_TYPE="$L4_MACHINE_TYPE"
  ACCELERATOR="$L4_ACCELERATOR"
  BOOT_DISK_SIZE="$L4_BOOT_DISK_SIZE"
  BOOT_DISK_TYPE="$L4_BOOT_DISK_TYPE"
  PROVISIONING="$L4_PROVISIONING"
  IDLE_TIMEOUT_MIN="$L4_IDLE_TIMEOUT_MIN"
  HOURLY_RATE="$L4_HOURLY_RATE"
else
  INSTANCE_NAME="$A100_INSTANCE_NAME"
  MACHINE_TYPE="$A100_MACHINE_TYPE"
  ACCELERATOR="$A100_ACCELERATOR"
  BOOT_DISK_SIZE="$A100_BOOT_DISK_SIZE"
  BOOT_DISK_TYPE="$A100_BOOT_DISK_TYPE"
  PROVISIONING="$A100_PROVISIONING"
  IDLE_TIMEOUT_MIN="$A100_IDLE_TIMEOUT_MIN"
  HOURLY_RATE="$A100_HOURLY_RATE"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Creating $TIER VM: $INSTANCE_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Machine type:  $MACHINE_TYPE"
echo "  GPU:           $ACCELERATOR"
echo "  Disk:          $BOOT_DISK_SIZE ($BOOT_DISK_TYPE)"
echo "  Provisioning:  $PROVISIONING"
echo "  Zone:          $GCP_ZONE"
echo "  Hourly rate:   ~\$$HOURLY_RATE/hr"
echo ""

# ─── Create VM ──────────────────────────────────────────────
CREATE_ARGS=(
  --project="$GCP_PROJECT_ID"
  --zone="$GCP_ZONE"
  --machine-type="$MACHINE_TYPE"
  --accelerator="$ACCELERATOR"
  --image-family="$VM_IMAGE_FAMILY"
  --image-project="$VM_IMAGE_PROJECT"
  --boot-disk-size="$BOOT_DISK_SIZE"
  --boot-disk-type="$BOOT_DISK_TYPE"
  --maintenance-policy=TERMINATE
  --provisioning-model="$PROVISIONING"
  --scopes=cloud-platform
  --metadata-from-file=startup-script="$SCRIPT_DIR/02-startup.sh",shutdown-script="$SCRIPT_DIR/03-shutdown.sh"
  --metadata="GCS_MODELS_BUCKET=$GCS_MODELS_BUCKET,GCS_OUTPUT_BUCKET=$GCS_OUTPUT_BUCKET,IDLE_TIMEOUT_MIN=$IDLE_TIMEOUT_MIN"
  --tags="$VM_TAGS"
)

# SPOT VMs: preserve disk on preemption
if [[ "$PROVISIONING" == "SPOT" ]]; then
  CREATE_ARGS+=(--instance-termination-action=STOP)
fi

gcloud compute instances create "$INSTANCE_NAME" "${CREATE_ARGS[@]}"

echo ""
echo "✓ VM created: $INSTANCE_NAME"
echo ""

# ─── Stop VM (created but not running) ──────────────────────
echo "Stopping VM (will be started on-demand via gpu-vm.sh)..."
gcloud compute instances stop "$INSTANCE_NAME" \
  --project="$GCP_PROJECT_ID" \
  --zone="$GCP_ZONE" \
  --quiet

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✓ $TIER VM created and stopped: $INSTANCE_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Start the VM:  ./gpu-vm.sh start $TIER"
echo "  2. Check status:  ./gpu-vm.sh status $TIER"
echo ""
if [[ "$PROVISIONING" == "SPOT" ]]; then
  echo "⚠ This is a SPOT VM — it may be preempted by GCP."
  echo "  The boot disk is preserved on preemption (--instance-termination-action=STOP)."
  echo ""
fi
