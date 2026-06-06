#!/usr/bin/env bash
# ChronoCanvas — Config Helper
# Sourced by gpu-vm.sh and other lifecycle scripts.
# Validates prerequisites, sources config.env, provides helper functions.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Source project .env (for GCP_PROJECT_ID, HF_TOKEN, etc.) ──
PROJECT_ENV="$SCRIPT_DIR/../../../.env"
if [ -f "$PROJECT_ENV" ]; then
  set -a; source "$PROJECT_ENV"; set +a
fi

# ─── Source config ──────────────────────────────────────────
if [ ! -f "$SCRIPT_DIR/../config.env" ]; then
  echo "ERROR: config.env not found at $SCRIPT_DIR/../config.env"
  exit 1
fi
source "$SCRIPT_DIR/../config.env"

# ─── Validate prerequisites ─────────────────────────────────
_check_prereqs() {
  local missing=0

  if ! command -v gcloud &>/dev/null; then
    echo "ERROR: gcloud CLI not installed. Install: https://cloud.google.com/sdk/docs/install"
    missing=1
  fi

  if ! command -v jq &>/dev/null; then
    echo "ERROR: jq not installed. Install: brew install jq (macOS) or apt-get install jq (Linux)"
    missing=1
  fi

  if [ -z "${GCP_PROJECT_ID:-}" ]; then
    echo "ERROR: GCP_PROJECT_ID not set. Run: export GCP_PROJECT_ID=your-project-id"
    missing=1
  fi

  if [ "$missing" -eq 1 ]; then
    exit 1
  fi
}

# ─── Helper functions ───────────────────────────────────────

# Get tier-specific variable value
# Usage: get_tier_var l4 MACHINE_TYPE → returns value of L4_MACHINE_TYPE
get_tier_var() {
  local tier="$(echo "$1" | tr '[:lower:]' '[:upper:]')"
  local suffix="$2"
  local var_name="${tier}_${suffix}"
  echo "${!var_name}"
}

# Get instance name for tier
# Usage: get_instance_name l4 → cc-gpu-l4
get_instance_name() {
  local tier="$(echo "$1" | tr '[:upper:]' '[:lower:]')"
  get_tier_var "$tier" INSTANCE_NAME
}

# Colored output helpers
log_info() {
  echo -e "\033[0;32m✓\033[0m $*"
}

log_error() {
  echo -e "\033[0;31m✗\033[0m $*" >&2
}

log_warn() {
  echo -e "\033[0;33m⚠\033[0m $*"
}

# Confirmation prompt (skipped with --yes flag)
confirm_action() {
  local msg="$1"
  if [[ "${SKIP_CONFIRM:-}" == "true" ]]; then
    return 0
  fi
  echo -n "$msg [y/N] "
  read -r response
  [[ "$response" =~ ^[Yy] ]]
}

# Run prerequisite check on source
_check_prereqs
