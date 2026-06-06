#!/usr/bin/env bash
# ChronoCanvas — VM Startup Script
# Runs on VM boot via GCE metadata startup-script.
# Syncs models from GCS, starts ComfyUI, connects Tailscale, installs idle watchdog.
#
# This script is idempotent — safe to run on first boot and subsequent reboots.

set -euo pipefail
exec > >(tee -a /var/log/startup-script.log) 2>&1
echo "━━━ ChronoCanvas startup script — $(date -u) ━━━"

# Reset idle watchdog timer on boot (prevents immediate shutdown from stale timer)
rm -f /tmp/gpu-idle-since

# ─── Read metadata ──────────────────────────────────────────
META_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
META_HEADER="Metadata-Flavor: Google"

GCS_MODELS_BUCKET=$(curl -sf -H "$META_HEADER" "$META_URL/GCS_MODELS_BUCKET")
GCS_OUTPUT_BUCKET=$(curl -sf -H "$META_HEADER" "$META_URL/GCS_OUTPUT_BUCKET")
IDLE_TIMEOUT_MIN=$(curl -sf -H "$META_HEADER" "$META_URL/IDLE_TIMEOUT_MIN" || echo "30")

echo "Models bucket:  $GCS_MODELS_BUCKET"
echo "Output bucket:  $GCS_OUTPUT_BUCKET"
echo "Idle timeout:   ${IDLE_TIMEOUT_MIN} min"

# ─── 1. Sync models from GCS ────────────────────────────────
echo ""
echo "◆ Syncing models from GCS (--no-clobber for fast subsequent boots)..."
SYNC_START=$(date +%s)

gcloud storage rsync -r \
  "$GCS_MODELS_BUCKET" /opt/ComfyUI/models/ \
  --no-clobber \
  2>&1 || echo "⚠ Model sync had warnings (may be partial)"

SYNC_END=$(date +%s)
SYNC_DURATION=$(( SYNC_END - SYNC_START ))
echo "✓ Model sync complete (${SYNC_DURATION}s)"

# ─── 2. Install ComfyUI if not present ──────────────────────
if [ ! -f /opt/ComfyUI/main.py ]; then
  echo ""
  echo "◆ Installing ComfyUI (first boot)..."

  # Ensure pip is available
  apt-get update -qq && apt-get install -y -qq python3-pip python3-venv > /dev/null 2>&1

  # Install ComfyUI via git (comfy-cli is unreliable on DLVM images)
  git clone https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI.tmp
  # Merge into existing dir (models already synced from GCS)
  rsync -a /opt/ComfyUI.tmp/ /opt/ComfyUI/ --ignore-existing
  rm -rf /opt/ComfyUI.tmp

  # Install Python dependencies in a venv
  python3 -m venv /opt/ComfyUI/venv
  /opt/ComfyUI/venv/bin/pip install --upgrade pip
  /opt/ComfyUI/venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu129
  /opt/ComfyUI/venv/bin/pip install -r /opt/ComfyUI/requirements.txt

  # Create comfyui system user if not exists
  if ! id -u comfyui &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false comfyui
  fi
  chown -R comfyui:comfyui /opt/ComfyUI

  # Install custom nodes via git clone
  echo "◆ Installing custom nodes..."
  NODES_DIR=/opt/ComfyUI/custom_nodes
  mkdir -p "$NODES_DIR"
  for repo in \
    "https://github.com/ByteDance/InfiniteYou.git ComfyUI_InfiniteYou" \
    "https://github.com/cubiq/ComfyUI_InstantID.git ComfyUI_InstantID" \
    "https://github.com/Fannovel16/comfyui_controlnet_aux.git comfyui_controlnet_aux"; do
    URL="${repo%% *}"
    DIR="${repo##* }"
    if [ ! -d "$NODES_DIR/$DIR" ]; then
      git clone "$URL" "$NODES_DIR/$DIR" 2>/dev/null || echo "⚠ Failed to clone $DIR"
      if [ -f "$NODES_DIR/$DIR/requirements.txt" ]; then
        /opt/ComfyUI/venv/bin/pip install -r "$NODES_DIR/$DIR/requirements.txt" 2>/dev/null || true
      fi
    fi
  done

  echo "✓ ComfyUI installed"
else
  echo "✓ ComfyUI already installed"
  # Ensure ownership is correct
  if ! id -u comfyui &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false comfyui
  fi
  chown -R comfyui:comfyui /opt/ComfyUI
fi

# ─── 3. Install and start ComfyUI service ───────────────────
cat > /etc/systemd/system/comfyui.service <<'UNIT'
[Unit]
Description=ComfyUI Server
After=network.target

[Service]
Type=simple
User=comfyui
WorkingDirectory=/opt/ComfyUI
ExecStart=/opt/ComfyUI/venv/bin/python main.py --listen 0.0.0.0 --port 8188
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable comfyui.service
systemctl start comfyui.service
echo "✓ ComfyUI service started (port 8188)"

# ─── 4. Connect Tailscale ───────────────────────────────────
echo ""
echo "◆ Setting up Tailscale..."

# Install Tailscale if not present
if ! command -v tailscale &>/dev/null; then
  echo "  Installing Tailscale..."
  curl -fsSL https://tailscale.com/install.sh | sh
fi

# Retrieve auth key from GCP Secret Manager
TS_AUTHKEY=$(gcloud secrets versions access latest --secret=ts-authkey 2>/dev/null || true)

if [ -n "$TS_AUTHKEY" ]; then
  HOSTNAME_TAG="cc-gpu-$(hostname)"
  tailscale up --auth-key="$TS_AUTHKEY" --hostname="$HOSTNAME_TAG" --accept-routes
  echo "✓ Tailscale connected as $HOSTNAME_TAG"
else
  echo "⚠ No Tailscale auth key found in Secret Manager (secret: ts-authkey)"
  echo "  ComfyUI will not be accessible via VPN until Tailscale is configured."
fi

# ─── 5. Install idle watchdog cron ──────────────────────────
echo ""
echo "◆ Installing idle watchdog..."

WATCHDOG_SCRIPT="/opt/ComfyUI/idle-watchdog.sh"
# Download watchdog from the startup script's companion (baked into metadata won't work,
# so we write it inline). The watchdog is self-contained.
cat > "$WATCHDOG_SCRIPT" <<'WATCHDOG'
#!/usr/bin/env bash
set -euo pipefail
IDLE_TIMER_FILE="/tmp/gpu-idle-since"
LOG_PREFIX="[idle-watchdog $(date -u +%H:%M:%S)]"
META_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
META_HEADER="Metadata-Flavor: Google"
IDLE_TIMEOUT_MIN=$(curl -sf -H "$META_HEADER" "$META_URL/IDLE_TIMEOUT_MIN" 2>/dev/null || echo "30")
GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d '[:space:]')
if [ -z "$GPU_UTIL" ]; then echo "$LOG_PREFIX ERROR: no GPU data"; exit 1; fi
echo "$LOG_PREFIX GPU utilization: ${GPU_UTIL}%"
if [ "$GPU_UTIL" -lt 5 ]; then
  if [ ! -f "$IDLE_TIMER_FILE" ]; then
    date +%s > "$IDLE_TIMER_FILE"
    echo "$LOG_PREFIX idle timer started (timeout: ${IDLE_TIMEOUT_MIN} min)"
  else
    IDLE_SINCE=$(cat "$IDLE_TIMER_FILE"); NOW=$(date +%s)
    IDLE_MIN=$(( (NOW - IDLE_SINCE) / 60 ))
    echo "$LOG_PREFIX idle for ${IDLE_MIN} min (timeout: ${IDLE_TIMEOUT_MIN} min)"
    if [ "$IDLE_MIN" -ge "$IDLE_TIMEOUT_MIN" ]; then
      echo "$LOG_PREFIX TIMEOUT — shutting down"
      GCS_OUTPUT_BUCKET=$(curl -sf -H "$META_HEADER" "$META_URL/GCS_OUTPUT_BUCKET" 2>/dev/null || echo "")
      if [ -n "$GCS_OUTPUT_BUCKET" ] && [ -d /opt/ComfyUI/output ]; then
        gcloud storage rsync -r /opt/ComfyUI/output/ "${GCS_OUTPUT_BUCKET}/$(date +%Y%m%d)/" 2>&1 || true
      fi
      rm -f "$IDLE_TIMER_FILE"
      shutdown -h now
    fi
  fi
else
  [ -f "$IDLE_TIMER_FILE" ] && rm -f "$IDLE_TIMER_FILE" && echo "$LOG_PREFIX active — timer reset"
fi
WATCHDOG
chmod +x "$WATCHDOG_SCRIPT"

cat > /etc/cron.d/gpu-idle-watchdog <<EOF
# ChronoCanvas — GPU idle watchdog (runs every 5 minutes)
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
*/5 * * * * root $WATCHDOG_SCRIPT >> /var/log/idle-watchdog.log 2>&1
EOF
echo "✓ Idle watchdog installed (every 5 min, timeout: ${IDLE_TIMEOUT_MIN} min)"

# ─── Done ───────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✓ ChronoCanvas startup complete — $(date -u)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Print access info
TS_IP=$(tailscale ip -4 2>/dev/null || echo "unknown")
echo ""
echo "  ComfyUI:  http://$(hostname):8188"
echo "  Tailscale IP: $TS_IP"
echo ""
