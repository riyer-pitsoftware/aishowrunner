#!/usr/bin/env bash
# Shut down ChronoCanvas Cloud Run services.
#
# Usage:
#   cd /path/to/chrono-canvas
#   export GCP_PROJECT_ID=gen-lang-client-0925647028
#
#   bash deploy/cloudrun/shutdown.sh              # Scale to zero (cheap sleep)
#   bash deploy/cloudrun/shutdown.sh --delete     # Delete services entirely
#   bash deploy/cloudrun/shutdown.sh --nuke       # Delete services + infra (DB, Redis, VPC)
#   bash deploy/cloudrun/shutdown.sh --dry-run    # Print what would happen
set -euo pipefail
source "$(dirname "$0")/scripts/00-env.sh"

MODE="scale-zero"
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --delete)  MODE="delete" ;;
    --nuke)    MODE="nuke" ;;
    --dry-run) DRY_RUN=true ;;
  esac
done

SERVICES=(chronocanvas-api chronocanvas-worker chronocanvas-frontend)

log()  { echo "$(date '+%H:%M:%S') | $*"; }
ok()   { echo "$(date '+%H:%M:%S') | ✅ $*"; }
warn() { echo "$(date '+%H:%M:%S') | ⚠️  $*"; }
fail() { echo "$(date '+%H:%M:%S') | ❌ $*"; }

run() {
  if [ "$DRY_RUN" = true ]; then
    log "[dry-run] $*"
  else
    "$@"
  fi
}

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ChronoCanvas Shutdown                              ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Mode:    ${MODE}                                   "
echo "║  Project: ${GCP_PROJECT_ID}                         "
echo "║  Region:  ${GCP_REGION}                             "
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Scale to zero ──────────────────────────────────────────────────
if [ "$MODE" = "scale-zero" ]; then
  log "Scaling all services to 0 instances (no traffic = no cost)..."
  for svc in "${SERVICES[@]}"; do
    if gcloud run services describe "$svc" --region="${GCP_REGION}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
      run gcloud run services update "$svc" \
        --region="${GCP_REGION}" \
        --project="${GCP_PROJECT_ID}" \
        --min-instances=0 \
        --max-instances=0
      ok "$svc → scaled to zero"
    else
      warn "$svc not found, skipping"
    fi
  done
  echo ""
  log "Services are dormant. To bring them back:"
  log "  bash deploy/cloudrun/redeploy.sh"
  exit 0
fi

# ── Delete services ────────────────────────────────────────────────
if [ "$MODE" = "delete" ] || [ "$MODE" = "nuke" ]; then
  log "Deleting Cloud Run services..."
  for svc in "${SERVICES[@]}"; do
    if gcloud run services describe "$svc" --region="${GCP_REGION}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
      run gcloud run services delete "$svc" \
        --region="${GCP_REGION}" \
        --project="${GCP_PROJECT_ID}" \
        --quiet
      ok "$svc deleted"
    else
      warn "$svc not found, skipping"
    fi
  done
fi

# ── Nuke infrastructure ───────────────────────────────────────────
if [ "$MODE" = "nuke" ]; then
  echo ""
  warn "Deleting infrastructure (DB, Redis, VPC connector)..."
  warn "This is IRREVERSIBLE. Data in Cloud SQL will be lost."

  if [ "$DRY_RUN" = false ]; then
    read -r -p "Type 'yes' to confirm infrastructure deletion: " confirm
    if [ "$confirm" != "yes" ]; then
      fail "Aborted."
      exit 1
    fi
  fi

  # Delete VPC connector
  if gcloud compute networks vpc-access connectors describe "$VPC_CONNECTOR" \
       --region="${GCP_REGION}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    run gcloud compute networks vpc-access connectors delete "$VPC_CONNECTOR" \
      --region="${GCP_REGION}" --project="${GCP_PROJECT_ID}" --quiet
    ok "VPC connector deleted"
  else
    warn "VPC connector $VPC_CONNECTOR not found"
  fi

  # Delete Redis
  if gcloud redis instances describe "$REDIS_INSTANCE" \
       --region="${GCP_REGION}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    run gcloud redis instances delete "$REDIS_INSTANCE" \
      --region="${GCP_REGION}" --project="${GCP_PROJECT_ID}" --quiet
    ok "Redis instance deleted"
  else
    warn "Redis instance $REDIS_INSTANCE not found"
  fi

  # Delete Cloud SQL (protection: requires explicit flag)
  if gcloud sql instances describe "$DB_INSTANCE" --project="${GCP_PROJECT_ID}" &>/dev/null; then
    run gcloud sql instances delete "$DB_INSTANCE" \
      --project="${GCP_PROJECT_ID}" --quiet
    ok "Cloud SQL instance deleted"
  else
    warn "Cloud SQL instance $DB_INSTANCE not found"
  fi

  # Delete Artifact Registry images (optional cleanup)
  log "Artifact Registry images left in place. Clean up manually if needed:"
  log "  gcloud artifacts docker images delete ${IMAGE_BASE}/api --delete-tags --quiet"
  log "  gcloud artifacts docker images delete ${IMAGE_BASE}/frontend --delete-tags --quiet"
fi

echo ""
ok "Shutdown complete (mode: ${MODE})"
