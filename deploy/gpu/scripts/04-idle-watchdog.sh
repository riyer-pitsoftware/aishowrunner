#!/usr/bin/env bash
# ChronoCanvas — GPU Idle Watchdog
# Runs every 5 minutes via cron. Shuts down VM after configurable idle period.
# Checks GPU utilization via nvidia-smi; if < 5% for IDLE_TIMEOUT_MIN minutes, triggers shutdown.

set -euo pipefail

IDLE_TIMER_FILE="/tmp/gpu-idle-since"
LOG_PREFIX="[idle-watchdog $(date -u +%H:%M:%S)]"

# ─── Read idle timeout from metadata ────────────────────────
META_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
META_HEADER="Metadata-Flavor: Google"
IDLE_TIMEOUT_MIN=$(curl -sf -H "$META_HEADER" "$META_URL/IDLE_TIMEOUT_MIN" 2>/dev/null || echo "30")

# ─── Check GPU utilization ──────────────────────────────────
GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d '[:space:]')

if [ -z "$GPU_UTIL" ]; then
  echo "$LOG_PREFIX ERROR: Could not read GPU utilization from nvidia-smi"
  exit 1
fi

echo "$LOG_PREFIX GPU utilization: ${GPU_UTIL}%"

# ─── Idle detection logic ───────────────────────────────────
if [ "$GPU_UTIL" -lt 5 ]; then
  # GPU is idle
  if [ ! -f "$IDLE_TIMER_FILE" ]; then
    # Start idle timer
    date +%s > "$IDLE_TIMER_FILE"
    echo "$LOG_PREFIX GPU idle — timer started (timeout: ${IDLE_TIMEOUT_MIN} min)"
  else
    # Check how long we've been idle
    IDLE_SINCE=$(cat "$IDLE_TIMER_FILE")
    NOW=$(date +%s)
    IDLE_SEC=$(( NOW - IDLE_SINCE ))
    IDLE_MIN=$(( IDLE_SEC / 60 ))

    echo "$LOG_PREFIX GPU idle for ${IDLE_MIN} min (timeout: ${IDLE_TIMEOUT_MIN} min)"

    if [ "$IDLE_MIN" -ge "$IDLE_TIMEOUT_MIN" ]; then
      echo "$LOG_PREFIX ⚠ IDLE TIMEOUT REACHED — initiating shutdown"

      # Sync outputs to GCS before shutdown
      META_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
      GCS_OUTPUT_BUCKET=$(curl -sf -H "$META_HEADER" "$META_URL/GCS_OUTPUT_BUCKET" 2>/dev/null || echo "")

      if [ -n "$GCS_OUTPUT_BUCKET" ] && [ -d /opt/ComfyUI/output ]; then
        DATE_DIR=$(date +%Y%m%d)
        echo "$LOG_PREFIX Syncing outputs to ${GCS_OUTPUT_BUCKET}/${DATE_DIR}/..."
        gcloud storage rsync -r /opt/ComfyUI/output/ "${GCS_OUTPUT_BUCKET}/${DATE_DIR}/" 2>&1 || true
        echo "$LOG_PREFIX Output sync complete"
      fi

      # Disconnect Tailscale
      if command -v tailscale &>/dev/null; then
        tailscale logout 2>/dev/null || true
        echo "$LOG_PREFIX Tailscale disconnected"
      fi

      # Clean up timer
      rm -f "$IDLE_TIMER_FILE"

      # Shutdown
      echo "$LOG_PREFIX Shutting down NOW"
      shutdown -h now
    fi
  fi
else
  # GPU is active — reset timer
  if [ -f "$IDLE_TIMER_FILE" ]; then
    echo "$LOG_PREFIX GPU active (${GPU_UTIL}%) — idle timer reset"
    rm -f "$IDLE_TIMER_FILE"
  else
    echo "$LOG_PREFIX GPU active (${GPU_UTIL}%)"
  fi
fi
