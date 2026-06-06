#!/usr/bin/env bash
# ChronoCanvas — RunPod Fallback: Model/Output Sync
# Syncs models to RunPod or downloads outputs from RunPod.
#
# Usage: ./runpod-sync.sh <pod-id> <upload|download>
#
# upload:   Send models from GCS to RunPod pod volume
# download: Pull outputs from RunPod pod to GCS output bucket

set -euo pipefail

POD_ID="${1:-}"
DIRECTION="${2:-}"

if [[ -z "$POD_ID" ]] || [[ -z "$DIRECTION" ]]; then
  echo "Usage: $0 <pod-id> <upload|download>"
  echo ""
  echo "  upload   — Sync models from GCS to RunPod volume"
  echo "  download — Sync outputs from RunPod to GCS"
  exit 1
fi

if [[ "$DIRECTION" != "upload" && "$DIRECTION" != "download" ]]; then
  echo "ERROR: Direction must be 'upload' or 'download'"
  exit 1
fi

if ! command -v runpodctl &>/dev/null; then
  echo "ERROR: runpodctl not installed"
  exit 1
fi

# Read GCS config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../config.env" ]; then
  source "$SCRIPT_DIR/../config.env"
fi

GCS_MODELS_BUCKET="${GCS_MODELS_BUCKET:-gs://chronocanvas-models}"
GCS_OUTPUT_BUCKET="${GCS_OUTPUT_BUCKET:-gs://chronocanvas-outputs}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " RunPod Sync: $DIRECTION (pod: $POD_ID)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

case "$DIRECTION" in
  upload)
    echo ""
    echo "◆ Syncing models from GCS to RunPod..."
    echo "  Source: $GCS_MODELS_BUCKET"
    echo "  Dest:   /workspace/ComfyUI/models/ (on pod)"
    echo ""

    # Create temp directory for download
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    # Download from GCS locally first
    echo "  Step 1/2: Downloading from GCS..."
    gcloud storage rsync -r "$GCS_MODELS_BUCKET" "$TEMP_DIR/" --no-clobber

    # Upload to RunPod via runpodctl
    echo "  Step 2/2: Uploading to RunPod pod..."
    runpodctl send "$TEMP_DIR" --podId "$POD_ID"

    echo ""
    echo "✓ Model sync complete"
    echo ""
    echo "NOTE: You may need to move files to the correct ComfyUI model directories"
    echo "      on the pod. SSH in with: runpodctl exec $POD_ID bash"
    ;;

  download)
    echo ""
    echo "◆ Syncing outputs from RunPod to GCS..."
    echo "  Source: /workspace/ComfyUI/output/ (on pod)"
    echo "  Dest:   $GCS_OUTPUT_BUCKET/$(date +%Y%m%d)/"
    echo ""

    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    # Download from RunPod
    echo "  Step 1/2: Downloading from RunPod..."
    runpodctl receive --podId "$POD_ID" "$TEMP_DIR"

    # Upload to GCS
    DATE_DIR=$(date +%Y%m%d)
    echo "  Step 2/2: Uploading to GCS..."
    gcloud storage rsync -r "$TEMP_DIR/" "${GCS_OUTPUT_BUCKET}/${DATE_DIR}/"

    echo ""
    echo "✓ Output sync complete"
    ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✓ Sync $DIRECTION complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
