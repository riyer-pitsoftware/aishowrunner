#!/usr/bin/env bash
# ChronoCanvas — VM Shutdown Script
# Runs on VM shutdown via GCE metadata shutdown-script.
# Syncs ComfyUI outputs to GCS and disconnects Tailscale.

set -euo pipefail
exec > >(tee -a /var/log/shutdown-script.log) 2>&1
echo "━━━ ChronoCanvas shutdown script — $(date -u) ━━━"

# ─── Read metadata ──────────────────────────────────────────
META_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
META_HEADER="Metadata-Flavor: Google"

GCS_OUTPUT_BUCKET=$(curl -sf -H "$META_HEADER" "$META_URL/GCS_OUTPUT_BUCKET" || echo "")

# ─── 1. Sync outputs to GCS ─────────────────────────────────
if [ -n "$GCS_OUTPUT_BUCKET" ] && [ -d /opt/ComfyUI/output ]; then
  DATE_DIR=$(date +%Y%m%d)
  echo "◆ Syncing outputs to ${GCS_OUTPUT_BUCKET}/${DATE_DIR}/..."

  gcloud storage rsync -r \
    /opt/ComfyUI/output/ \
    "${GCS_OUTPUT_BUCKET}/${DATE_DIR}/" \
    2>&1 || echo "⚠ Output sync had warnings"

  echo "✓ Output sync complete"
else
  echo "⚠ Skipping output sync (bucket or output dir missing)"
fi

# ─── 2. Disconnect Tailscale ────────────────────────────────
if command -v tailscale &>/dev/null; then
  echo "◆ Disconnecting Tailscale..."
  tailscale logout 2>/dev/null || echo "⚠ Tailscale logout had issues"
  echo "✓ Tailscale disconnected (ephemeral node removed)"
else
  echo "⚠ Tailscale not installed, skipping logout"
fi

# ─── Done ───────────────────────────────────────────────────
echo ""
echo "━━━ ChronoCanvas shutdown complete — $(date -u) ━━━"
