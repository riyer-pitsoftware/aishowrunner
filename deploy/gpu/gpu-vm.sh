#!/usr/bin/env bash
# ChronoCanvas — GPU VM Lifecycle Entrypoint
# Single command for all VM operations across both tiers.
#
# Usage: ./gpu-vm.sh <command> [tier] [--yes]
#
# Commands:
#   setup          — First-time GCP setup (buckets, Tailscale secret)
#   upload-models  — Upload models to GCS via ephemeral CPU VM [l4|a100|all]
#   create <tier>  — One-time VM creation (calls 01-create-vm.sh)
#   start  <tier>  — Start a stopped VM
#   stop   <tier>  — Stop a running VM
#   status <tier>  — Show VM state, uptime, cost
#   ssh    <tier>  — SSH into VM via IAP tunnel
#
# Tiers: l4, a100

set -euo pipefail

GPU_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─── Parse arguments ────────────────────────────────────────
COMMAND="${1:-}"
TIER="${2:-}"
SKIP_CONFIRM="false"

for arg in "$@"; do
  if [[ "$arg" == "--yes" ]]; then
    SKIP_CONFIRM="true"
  fi
done
export SKIP_CONFIRM

# ─── Validate arguments ─────────────────────────────────────
if [[ -z "$COMMAND" ]]; then
  echo "Usage: $0 <command> [tier] [--yes]"
  echo ""
  echo "Commands:"
  echo "  setup          — First-time GCP setup (buckets, Tailscale secret)"
  echo "  upload-models  — Upload models to GCS via ephemeral CPU VM [l4|a100|all]"
  echo "  create <tier>  — One-time VM creation"
  echo "  start <tier>   — Start a stopped VM"
  echo "  stop <tier>    — Stop a running VM"
  echo "  status <tier>  — Show VM state, uptime, and cost"
  echo "  ssh <tier>     — SSH into VM via IAP tunnel"
  echo ""
  echo "Tiers: l4, a100"
  exit 1
fi

# Commands that don't require a tier
if [[ "$COMMAND" == "setup" ]]; then
  "$GPU_DIR/scripts/05-setup-gcp.sh"
  exit $?
fi

if [[ "$COMMAND" == "upload-models" ]]; then
  UPLOAD_TIER="${TIER:-l4}"
  "$GPU_DIR/scripts/06-upload-models.sh" "$UPLOAD_TIER"
  exit $?
fi

# All other commands require a tier
if [[ -z "$TIER" ]]; then
  echo "Usage: $0 $COMMAND <l4|a100> [--yes]"
  exit 1
fi

if [[ "$TIER" != "l4" && "$TIER" != "a100" ]]; then
  echo "ERROR: Invalid tier '$TIER'. Use 'l4' or 'a100'."
  exit 1
fi

# ─── Source config helper ───────────────────────────────────
source "$GPU_DIR/scripts/00-config.sh"

INSTANCE=$(get_instance_name "$TIER")
MACHINE_TYPE=$(get_tier_var "$TIER" MACHINE_TYPE)
PROVISIONING=$(get_tier_var "$TIER" PROVISIONING)
HOURLY_RATE=$(get_tier_var "$TIER" HOURLY_RATE)

# ─── Helper: check if VM exists ─────────────────────────────
vm_exists() {
  gcloud compute instances describe "$INSTANCE" \
    --project="$GCP_PROJECT_ID" \
    --zone="$GCP_ZONE" \
    --format="value(name)" 2>/dev/null && return 0 || return 1
}

# ─── Helper: get VM state ───────────────────────────────────
vm_state() {
  gcloud compute instances describe "$INSTANCE" \
    --project="$GCP_PROJECT_ID" \
    --zone="$GCP_ZONE" \
    --format="value(status)" 2>/dev/null || echo "NOT_FOUND"
}

# ─── Commands ───────────────────────────────────────────────

case "$COMMAND" in
  create)
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Creating $TIER VM"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    "$GPU_DIR/scripts/01-create-vm.sh" "$TIER"
    ;;

  start)
    if ! vm_exists; then
      log_error "VM '$INSTANCE' does not exist. Run: $0 create $TIER"
      exit 1
    fi

    STATE=$(vm_state)
    if [[ "$STATE" == "RUNNING" ]]; then
      log_warn "VM '$INSTANCE' is already running"
      exit 0
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Starting $TIER VM: $INSTANCE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  Machine type:  $MACHINE_TYPE"
    echo "  Hourly rate:   ~\$$HOURLY_RATE/hr"
    echo ""

    if [[ "$PROVISIONING" == "SPOT" ]]; then
      log_warn "SPOT instance — may be preempted by GCP at any time"
    fi

    gcloud compute instances start "$INSTANCE" \
      --project="$GCP_PROJECT_ID" \
      --zone="$GCP_ZONE"

    echo ""
    echo "◆ Waiting for VM to reach RUNNING state..."
    gcloud compute instances tail-serial-port-output "$INSTANCE" \
      --project="$GCP_PROJECT_ID" \
      --zone="$GCP_ZONE" \
      --port=1 2>/dev/null &
    TAIL_PID=$!

    # Wait for RUNNING state (max 120s)
    for i in $(seq 1 24); do
      STATE=$(vm_state)
      if [[ "$STATE" == "RUNNING" ]]; then
        break
      fi
      sleep 5
    done

    kill "$TAIL_PID" 2>/dev/null || true

    if [[ "$(vm_state)" == "RUNNING" ]]; then
      echo ""
      log_info "VM '$INSTANCE' is RUNNING"
      echo ""
      echo "  ComfyUI will be available after startup script completes (~1 min for warm boot, ~20 min for cold boot)"
      echo "  Access: http://cc-gpu-${TIER}:8188  (via Tailscale)"
      echo ""
      echo "  💰 Cost reminder: ~\$$HOURLY_RATE/hr. Auto-shutdown after $(get_tier_var "$TIER" IDLE_TIMEOUT_MIN) min idle."
    else
      log_error "VM did not reach RUNNING state. Current state: $(vm_state)"
      exit 1
    fi
    ;;

  stop)
    if ! vm_exists; then
      log_error "VM '$INSTANCE' does not exist."
      exit 1
    fi

    STATE=$(vm_state)
    if [[ "$STATE" == "TERMINATED" ]] || [[ "$STATE" == "STOPPED" ]]; then
      log_warn "VM '$INSTANCE' is already stopped ($STATE)"
      exit 0
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Stopping $TIER VM: $INSTANCE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    gcloud compute instances stop "$INSTANCE" \
      --project="$GCP_PROJECT_ID" \
      --zone="$GCP_ZONE"

    echo ""
    log_info "VM '$INSTANCE' stopped (shutdown script will sync outputs)"
    ;;

  status)
    if ! vm_exists; then
      echo "VM '$INSTANCE' does not exist."
      echo "  Create it: $0 create $TIER"
      exit 0
    fi

    VM_JSON=$(gcloud compute instances describe "$INSTANCE" \
      --project="$GCP_PROJECT_ID" \
      --zone="$GCP_ZONE" \
      --format=json 2>/dev/null)

    STATE=$(echo "$VM_JSON" | jq -r '.status')
    MACHINE=$(echo "$VM_JSON" | jq -r '.machineType' | rev | cut -d'/' -f1 | rev)
    PROV=$(echo "$VM_JSON" | jq -r '.scheduling.provisioningModel // "STANDARD"')

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " $TIER VM Status: $INSTANCE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  State:         $STATE"
    echo "  Machine type:  $MACHINE"
    echo "  Provisioning:  $PROV"

    if [[ "$STATE" == "RUNNING" ]]; then
      # Calculate uptime
      LAST_START=$(echo "$VM_JSON" | jq -r '.lastStartTimestamp // empty')
      if [ -n "$LAST_START" ]; then
        START_EPOCH=$(date -jf "%Y-%m-%dT%H:%M:%S" "$(echo "$LAST_START" | cut -d. -f1)" +%s 2>/dev/null || date -d "$LAST_START" +%s 2>/dev/null || echo "0")
        NOW_EPOCH=$(date +%s)
        if [ "$START_EPOCH" -gt 0 ]; then
          UPTIME_MIN=$(( (NOW_EPOCH - START_EPOCH) / 60 ))
          UPTIME_HRS=$(echo "scale=1; $UPTIME_MIN / 60" | bc)
          COST=$(echo "scale=2; $UPTIME_HRS * $HOURLY_RATE" | bc)
          echo "  Uptime:        ${UPTIME_MIN} min (~${UPTIME_HRS} hrs)"
          echo "  Est. cost:     ~\$$COST (at \$$HOURLY_RATE/hr)"
        fi
      fi
    fi

    echo ""
    ;;

  ssh)
    if ! vm_exists; then
      log_error "VM '$INSTANCE' does not exist."
      exit 1
    fi

    if [[ "$(vm_state)" != "RUNNING" ]]; then
      log_error "VM '$INSTANCE' is not running. Start it first: $0 start $TIER"
      exit 1
    fi

    echo "Connecting to $INSTANCE via IAP tunnel..."
    gcloud compute ssh "$INSTANCE" \
      --project="$GCP_PROJECT_ID" \
      --zone="$GCP_ZONE" \
      --tunnel-through-iap
    ;;

  *)
    echo "ERROR: Unknown command '$COMMAND'"
    echo "Usage: $0 <start|stop|status|create|ssh> <l4|a100> [--yes]"
    exit 1
    ;;
esac
