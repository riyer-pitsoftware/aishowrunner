#!/usr/bin/env bash
# ChronoCanvas — RunPod Fallback: Start Pod
# Use when GCP GPU quota is denied. Creates a RunPod pod with ComfyUI.
#
# NOTE: This is a FALLBACK — GCP is the primary infrastructure.
# RunPod pods get public URLs (less secure than Tailscale VPN).
#
# Usage: ./runpod-start.sh <l4|a100>
#
# Prerequisites:
#   - runpodctl installed: https://github.com/runpod/runpodctl
#   - RUNPOD_API_KEY set in environment

set -euo pipefail

TIER="${1:-}"

if [[ -z "$TIER" ]] || [[ "$TIER" != "l4" && "$TIER" != "a100" ]]; then
  echo "Usage: $0 <l4|a100>"
  echo ""
  echo "  l4   — NVIDIA L4, 1 GPU (~\$0.24/hr)"
  echo "  a100 — NVIDIA A100 80GB PCIe, 1 GPU (~\$1.19-1.39/hr)"
  echo ""
  echo "  NOTE: RunPod A100 is 80GB (vs GCP 40GB) — better for Wan 14B at 720p"
  exit 1
fi

# Validate runpodctl
if ! command -v runpodctl &>/dev/null; then
  echo "ERROR: runpodctl not installed"
  echo ""
  echo "Install:"
  echo "  macOS: brew install runpod/runpodctl/runpodctl"
  echo "  Linux: wget -qO- cli.runpod.net | sudo bash"
  echo ""
  echo "Then: runpodctl config --apiKey YOUR_API_KEY"
  exit 1
fi

# Set GPU type based on tier
if [[ "$TIER" == "l4" ]]; then
  GPU_TYPE="NVIDIA L4"
  GPU_COUNT=1
  VOLUME_SIZE=100
elif [[ "$TIER" == "a100" ]]; then
  GPU_TYPE="NVIDIA A100 80GB PCIe"
  GPU_COUNT=1
  VOLUME_SIZE=100
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " RunPod Fallback: Creating $TIER pod"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  GPU:     $GPU_TYPE (x$GPU_COUNT)"
echo "  Volume:  ${VOLUME_SIZE}GB"
echo "  Image:   comfyanonymous/comfyui:latest"
echo "  Port:    8188/http"
echo ""

runpodctl create pod \
  --name "cc-gpu-${TIER}" \
  --gpuType "$GPU_TYPE" \
  --gpuCount "$GPU_COUNT" \
  --volumeSize "$VOLUME_SIZE" \
  --imageName "comfyanonymous/comfyui:latest" \
  --ports "8188/http" \
  --env "COMFYUI_PORT=8188"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✓ RunPod pod created"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Check pod status: runpodctl get pod"
echo "  2. Sync models:      ./runpod-sync.sh <pod-id> upload"
echo "  3. Access ComfyUI:   See pod URL in RunPod dashboard"
echo ""
echo "⚠ RunPod pods have public URLs — less secure than Tailscale VPN."
echo "  Stop the pod when done: ./runpod-stop.sh <pod-id>"
