#!/usr/bin/env bash
# ChronoCanvas — Upload Models to GCS via Ephemeral CPU VM
# Spins up a cheap VM inside GCP, downloads models from HuggingFace,
# uploads to GCS (intra-Google network), then deletes the VM.
#
# Usage: ./06-upload-models.sh [--tier l4|a100|all] [--yes]
#   or via entrypoint: ./gpu-vm.sh upload-models [l4|a100|all]
#
# Default tier: l4

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-config.sh"

TIER="${1:-l4}"
if [[ "$TIER" != "l4" && "$TIER" != "a100" && "$TIER" != "all" ]]; then
  echo "Usage: $0 [l4|a100|all]"
  exit 1
fi

MANIFEST="$SCRIPT_DIR/../models/model-manifest.json"
if [ ! -f "$MANIFEST" ]; then
  log_error "Model manifest not found: $MANIFEST"
  exit 1
fi

UPLOAD_VM="cc-model-uploader"
UPLOAD_MACHINE="e2-standard-4"
UPLOAD_DISK="200GB"

# HF_TOKEN loaded from .env via 00-config.sh
if [ -z "${HF_TOKEN:-}" ]; then
  log_warn "HF_TOKEN not set in .env. Gated models (FLUX.1-dev) will fail."
fi

# ─── Parse manifest ────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ChronoCanvas — Upload Models to GCS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build list of tiers to process
if [[ "$TIER" == "all" ]]; then
  TIERS=("l4" "a100")
else
  TIERS=("$TIER")
fi

# Count models and total size
TOTAL_MODELS=0
TOTAL_SIZE="0"
for T in "${TIERS[@]}"; do
  COUNT=$(jq -r ".models.$T | length" "$MANIFEST")
  SIZE=$(jq -r ".total_size_gb.$T" "$MANIFEST")
  TOTAL_MODELS=$((TOTAL_MODELS + COUNT))
  TOTAL_SIZE=$(echo "$TOTAL_SIZE + $SIZE" | bc)
done

echo "  Tier(s):    ${TIERS[*]}"
echo "  Models:     $TOTAL_MODELS files"
echo "  Total size: ~${TOTAL_SIZE} GB"
echo "  Upload VM:  $UPLOAD_VM ($UPLOAD_MACHINE, ~\$0.13/hr)"
echo "  GCS bucket: $GCS_MODELS_BUCKET"
echo ""

# ─── Check which models already exist in GCS ──────────────────
echo "◆ Checking existing models in GCS..."
SKIP_COUNT=0
UPLOAD_ENTRIES=()

for T in "${TIERS[@]}"; do
  MODEL_COUNT=$(jq -r ".models.$T | length" "$MANIFEST")
  for i in $(seq 0 $((MODEL_COUNT - 1))); do
    DEST=$(jq -r ".models.$T[$i].dest" "$MANIFEST")
    NAME=$(jq -r ".models.$T[$i].name" "$MANIFEST")
    SOURCE=$(jq -r ".models.$T[$i].source" "$MANIFEST")
    SIZE_GB=$(jq -r ".models.$T[$i].size_gb" "$MANIFEST")

    if gcloud storage ls "$GCS_MODELS_BUCKET/$DEST" &>/dev/null; then
      log_info "Already in GCS: $NAME ($DEST)"
      SKIP_COUNT=$((SKIP_COUNT + 1))
    else
      echo "  ○ Needs upload: $NAME (~${SIZE_GB}GB)"
      UPLOAD_ENTRIES+=("$T|$i|$NAME|$SOURCE|$DEST|$SIZE_GB")
    fi
  done
done

if [ ${#UPLOAD_ENTRIES[@]} -eq 0 ]; then
  echo ""
  log_info "All models already in GCS. Nothing to upload."
  exit 0
fi

echo ""
echo "  Skipped: $SKIP_COUNT (already in GCS)"
echo "  To upload: ${#UPLOAD_ENTRIES[@]} models"
echo ""

if [[ "${SKIP_CONFIRM:-}" != "true" ]]; then
  echo -n "Proceed? This will create a temporary VM (~\$0.13/hr). [y/N] "
  read -r response
  if [[ ! "$response" =~ ^[Yy] ]]; then
    echo "Aborted."
    exit 0
  fi
fi

# ─── Build the download+upload script for the VM ──────────────
REMOTE_SCRIPT=$(mktemp)
cat > "$REMOTE_SCRIPT" <<SCRIPT_HEADER
#!/usr/bin/env bash
set -euo pipefail
echo "━━━ Model download+upload started: \$(date -u) ━━━"

HF_TOKEN="${HF_TOKEN:-}"

# Install unzip (needed for InsightFace AntelopeV2)
sudo apt-get update -qq && sudo apt-get install -y -qq unzip > /dev/null 2>&1

WORKDIR="/tmp/models"
mkdir -p "\$WORKDIR"
cd "\$WORKDIR"

FAILED=0
SCRIPT_HEADER

# Append download+upload commands for each model
for ENTRY in "${UPLOAD_ENTRIES[@]}"; do
  IFS='|' read -r T IDX NAME SOURCE DEST SIZE_GB <<< "$ENTRY"

  # Handle the InsightFace zip specially (needs unzip)
  POST_INSTALL=$(jq -r ".models.$T[$IDX].post_install // empty" "$MANIFEST")

  cat >> "$REMOTE_SCRIPT" <<EOF

echo ""
echo "◆ [$NAME] Downloading (~${SIZE_GB}GB)..."
FILENAME=\$(basename "$SOURCE")
WGET_ARGS=(-O "\$FILENAME" --progress=dot:giga)
if [ -n "\$HF_TOKEN" ]; then
  WGET_ARGS+=(--header "Authorization: Bearer \$HF_TOKEN")
fi
if wget "\${WGET_ARGS[@]}" "$SOURCE" 2>&1; then
  echo "  ✓ Downloaded \$FILENAME"
EOF

  if [[ -n "$POST_INSTALL" && "$POST_INSTALL" == *"unzip"* ]]; then
    # Extract unzip target from post_install hint
    UNZIP_DIR=$(echo "$POST_INSTALL" | sed 's/unzip to //')
    cat >> "$REMOTE_SCRIPT" <<EOF
  echo "  Unzipping..."
  mkdir -p unzipped
  unzip -o "\$FILENAME" -d unzipped/
  gcloud storage cp -r unzipped/* "$GCS_MODELS_BUCKET/$UNZIP_DIR/"
  echo "  ✓ Uploaded to $GCS_MODELS_BUCKET/$UNZIP_DIR/"
  # Also upload the zip itself
  gcloud storage cp "\$FILENAME" "$GCS_MODELS_BUCKET/$DEST"
  echo "  ✓ Uploaded zip to $GCS_MODELS_BUCKET/$DEST"
  rm -rf unzipped "\$FILENAME"
EOF
  else
    cat >> "$REMOTE_SCRIPT" <<EOF
  echo "  Uploading to GCS..."
  gcloud storage cp "\$FILENAME" "$GCS_MODELS_BUCKET/$DEST"
  echo "  ✓ Uploaded to $GCS_MODELS_BUCKET/$DEST"
  rm -f "\$FILENAME"
EOF
  fi

  cat >> "$REMOTE_SCRIPT" <<EOF
else
  echo "  ✗ FAILED to download $NAME"
  FAILED=\$((FAILED + 1))
fi
EOF
done

cat >> "$REMOTE_SCRIPT" <<'SCRIPT_FOOTER'

echo ""
echo "━━━ Model upload complete: $(date -u) ━━━"
if [ "$FAILED" -gt 0 ]; then
  echo "⚠ $FAILED model(s) failed to download"
  exit 1
fi
SCRIPT_FOOTER

# ─── Create ephemeral VM ──────────────────────────────────────
echo ""
echo "◆ Creating upload VM: $UPLOAD_VM..."

# Check if VM already exists (from a previous failed run)
if gcloud compute instances describe "$UPLOAD_VM" \
  --project="$GCP_PROJECT_ID" --zone="$GCP_ZONE" &>/dev/null; then
  log_warn "Upload VM already exists (previous run?). Deleting it first..."
  gcloud compute instances delete "$UPLOAD_VM" \
    --project="$GCP_PROJECT_ID" --zone="$GCP_ZONE" --quiet
fi

gcloud compute instances create "$UPLOAD_VM" \
  --project="$GCP_PROJECT_ID" \
  --zone="$GCP_ZONE" \
  --machine-type="$UPLOAD_MACHINE" \
  --boot-disk-size="$UPLOAD_DISK" \
  --boot-disk-type=pd-ssd \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --scopes=cloud-platform \
  --quiet

log_info "Upload VM created"

# Wait for SSH to be ready
echo "◆ Waiting for VM to accept SSH..."
for i in $(seq 1 30); do
  if gcloud compute ssh "$UPLOAD_VM" \
    --project="$GCP_PROJECT_ID" --zone="$GCP_ZONE" \
    --tunnel-through-iap --command="echo ready" &>/dev/null; then
    break
  fi
  sleep 5
done

# ─── Run download+upload on VM ─────────────────────────────────
echo ""
echo "◆ Running model downloads on VM (this will take a while)..."
echo ""

gcloud compute scp "$REMOTE_SCRIPT" "$UPLOAD_VM:/tmp/upload-models.sh" \
  --project="$GCP_PROJECT_ID" --zone="$GCP_ZONE" \
  --tunnel-through-iap --quiet

UPLOAD_EXIT=0
gcloud compute ssh "$UPLOAD_VM" \
  --project="$GCP_PROJECT_ID" --zone="$GCP_ZONE" \
  --tunnel-through-iap \
  --command="chmod +x /tmp/upload-models.sh && /tmp/upload-models.sh" || UPLOAD_EXIT=$?

# ─── Cleanup ──────────────────────────────────────────────────
rm -f "$REMOTE_SCRIPT"

echo ""
echo "◆ Deleting upload VM..."
gcloud compute instances delete "$UPLOAD_VM" \
  --project="$GCP_PROJECT_ID" --zone="$GCP_ZONE" --quiet
log_info "Upload VM deleted"

# ─── Summary ──────────────────────────────────────────────────
echo ""
if [ "$UPLOAD_EXIT" -eq 0 ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo " ✓ All models uploaded to $GCS_MODELS_BUCKET"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Next steps:"
  echo "  1. Create GPU VM:  ./gpu-vm.sh create l4"
  echo "  2. Start GPU VM:   ./gpu-vm.sh start l4"
  echo ""
else
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log_error "Some models failed to upload. Re-run to retry (skips existing)."
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
fi
