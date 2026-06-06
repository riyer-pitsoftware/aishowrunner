#!/usr/bin/env bash
# ChronoCanvas — RunPod Fallback: Stop Pod
# Syncs outputs before stopping the pod.
#
# Usage: ./runpod-stop.sh <pod-id>

set -euo pipefail

POD_ID="${1:-}"

if [[ -z "$POD_ID" ]]; then
  echo "Usage: $0 <pod-id>"
  echo ""
  echo "Find pod ID: runpodctl get pod"
  exit 1
fi

if ! command -v runpodctl &>/dev/null; then
  echo "ERROR: runpodctl not installed"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " RunPod Fallback: Stopping pod $POD_ID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Sync outputs before stopping
echo ""
echo "◆ Syncing outputs before stop..."
"$SCRIPT_DIR/runpod-sync.sh" "$POD_ID" download 2>/dev/null || echo "⚠ Output sync had issues (pod may be already stopping)"

# Stop the pod
echo ""
echo "◆ Stopping pod..."
runpodctl stop pod "$POD_ID"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✓ Pod $POD_ID stopped"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To remove pod entirely: runpodctl remove pod $POD_ID"
