#!/usr/bin/env bash
# AI Showrunner — Alibaba Cloud ECS deploy (bead asr-av5.3, TRD §14)
#
# Mirrors deploy/cloudrun/redeploy.sh in spirit: build images, optionally push
# to Alibaba Container Registry (ACR), bring the compose stack up on the ECS
# host, run migrations (via the api entrypoint RUN_MIGRATIONS=true), and
# health-check /api/health.
#
# Two modes, auto-selected from env:
#   • ACR push mode   — when ACR_REGISTRY is set: build locally, push to ACR,
#                       the ECS host pulls and runs the images.
#   • On-host build   — when ACR_REGISTRY is unset: ship the repo to the ECS
#                       host and build there (simplest single-box demo path).
#
# Everything is driven by deploy/alibaba/.env.alibaba (copy from the .example).
# No secrets are hardcoded. Fails fast with a clear message on missing vars.
#
# Usage:
#   cp deploy/alibaba/.env.alibaba.example deploy/alibaba/.env.alibaba   # then edit
#   bash deploy/alibaba/deploy.sh                 # full deploy
#   bash deploy/alibaba/deploy.sh --build-only    # build (+push) images, no remote up
#   bash deploy/alibaba/deploy.sh --no-build      # skip build, just (re)up + verify
#   bash deploy/alibaba/deploy.sh --dry-run       # print actions, run nothing
set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.alibaba.yml"
ENV_FILE="${SCRIPT_DIR}/.env.alibaba"

# ── Logging helpers ──────────────────────────────────────────────────────
log()  { echo "$(date '+%H:%M:%S') | $*"; }
ok()   { echo "$(date '+%H:%M:%S') | OK   $*"; }
info() { echo "$(date '+%H:%M:%S') | ..   $*"; }
fail() { echo "$(date '+%H:%M:%S') | FAIL $*" >&2; }
die()  { fail "$*"; exit 1; }

# ── Flags ────────────────────────────────────────────────────────────────
DO_BUILD=true
DO_REMOTE=true
DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --build-only) DO_REMOTE=false ;;
    --no-build)   DO_BUILD=false ;;
    --dry-run)    DRY_RUN=true ;;
    -h|--help)    grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "Unknown argument: $arg (try --help)" ;;
  esac
done

run() {
  if [ "$DRY_RUN" = true ]; then
    info "[dry-run] $*"
  else
    "$@"
  fi
}

# ── Load env ─────────────────────────────────────────────────────────────
[ -f "$ENV_FILE" ] || die "Missing $ENV_FILE. Copy .env.alibaba.example to it and fill in values."
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

# ── Require helper ───────────────────────────────────────────────────────
require() {
  local name="$1"
  local val="${!name:-}"
  [ -n "$val" ] || die "Required env var '$name' is not set in $ENV_FILE"
}

# Runtime secrets needed for the stack to start at all.
require DASHSCOPE_API_KEY
require POSTGRES_PASSWORD
require SECRET_KEY
require APP_PASSWORD

# Guard rail: a Qwen/Alibaba deployment must NOT run in gcp mode (that forces
# Gemini-only routing). compose hardcodes hybrid, but catch an override here.
if [ "${DEPLOYMENT_MODE:-hybrid}" = "gcp" ]; then
  die "DEPLOYMENT_MODE=gcp forces Gemini-only routing — wrong for Qwen Cloud. Use hybrid. See README."
fi

# ── Image tag resolution ─────────────────────────────────────────────────
TAG="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo latest)"
USE_ACR=false
if [ -n "${ACR_REGISTRY:-}" ]; then
  USE_ACR=true
  require ACR_NAMESPACE
  export API_IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/ai-showrunner-api:${TAG}"
  export FRONTEND_IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/ai-showrunner-frontend:${TAG}"
else
  export API_IMAGE="ai-showrunner-api:${TAG}"
  export FRONTEND_IMAGE="ai-showrunner-frontend:${TAG}"
fi

echo ""
echo "=============================================================="
echo "  AI Showrunner — Alibaba Cloud ECS deploy"
echo "  Repo:      ${REPO_ROOT}"
echo "  Tag:       ${TAG}"
echo "  ACR push:  ${USE_ACR}  ${ACR_REGISTRY:+(${ACR_REGISTRY})}"
echo "  ECS host:  ${ECS_HOST:-<on-host steps skipped>}"
echo "  Skill map: /app/.harness/models.cloud.yaml  (Qwen Cloud)"
echo "  Mode:      DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-hybrid}"
[ "$DRY_RUN" = true ] && echo "  DRY RUN — nothing will be executed"
echo "=============================================================="
echo ""

vendor_wheel() {
  # The Dockerfile.api COPY vendor/*.whl needs at least one wheel present.
  if ! ls "${REPO_ROOT}"/vendor/*.whl >/dev/null 2>&1; then
    if [ -f "${REPO_ROOT}/scripts/build-vendor-wheels.sh" ]; then
      info "Building vendor wheels (no *.whl found in vendor/)"
      run bash "${REPO_ROOT}/scripts/build-vendor-wheels.sh"
    else
      die "No vendor/*.whl present and scripts/build-vendor-wheels.sh is missing."
    fi
  fi
}

# ── Step 1: build images ─────────────────────────────────────────────────
if [ "$DO_BUILD" = true ]; then
  command -v docker >/dev/null 2>&1 || die "docker not found on PATH"
  docker info >/dev/null 2>&1 || die "Docker daemon is not running"
  vendor_wheel

  info "Building images (context=repo root)"
  run docker compose --project-directory "$REPO_ROOT" -f "$COMPOSE_FILE" build

  if [ "$USE_ACR" = true ]; then
    require ACR_USERNAME
    require ACR_PASSWORD
    info "Logging in to ACR ${ACR_REGISTRY}"
    if [ "$DRY_RUN" = false ]; then
      echo "$ACR_PASSWORD" | docker login --username "$ACR_USERNAME" --password-stdin "$ACR_REGISTRY"
    fi
    info "Pushing images to ACR"
    run docker push "$API_IMAGE"
    run docker push "$FRONTEND_IMAGE"
    ok "Images pushed: ${API_IMAGE} , ${FRONTEND_IMAGE}"
  else
    ok "Images built locally (no ACR push): ${API_IMAGE}"
  fi
else
  info "Skipping build (--no-build)"
fi

[ "$DO_REMOTE" = true ] || { ok "Build-only complete."; exit 0; }

# ── Remote target required from here on ──────────────────────────────────
require ECS_HOST
require ECS_REMOTE_DIR
SSH_USER="${ECS_SSH_USER:-root}"
SSH_PORT="${ECS_SSH_PORT:-22}"
SSH_KEY="${ECS_SSH_KEY:-$HOME/.ssh/id_rsa}"
SSH_KEY="${SSH_KEY/#\~/$HOME}"
[ -f "$SSH_KEY" ] || die "SSH key not found: $SSH_KEY (set ECS_SSH_KEY)"

SSH=(ssh -i "$SSH_KEY" -p "$SSH_PORT" -o StrictHostKeyChecking=accept-new "${SSH_USER}@${ECS_HOST}")
remote() {
  if [ "$DRY_RUN" = true ]; then
    info "[dry-run] ssh ${SSH_USER}@${ECS_HOST}: $*"
  else
    "${SSH[@]}" "$@"
  fi
}

# ── Step 2: ship compose + env (+ source when building on-host) ──────────
info "Preparing remote dir ${ECS_REMOTE_DIR} on ${ECS_HOST}"
remote "mkdir -p '${ECS_REMOTE_DIR}'"

SCP=(scp -i "$SSH_KEY" -P "$SSH_PORT" -o StrictHostKeyChecking=accept-new)
copy() {
  if [ "$DRY_RUN" = true ]; then
    info "[dry-run] scp $1 -> ${ECS_HOST}:$2"
  else
    "${SCP[@]}" "$1" "${SSH_USER}@${ECS_HOST}:$2"
  fi
}

if [ "$USE_ACR" = true ]; then
  # Only compose + env + harness map needed on the host; images come from ACR.
  copy "$COMPOSE_FILE" "${ECS_REMOTE_DIR}/docker-compose.alibaba.yml"
  copy "$ENV_FILE"     "${ECS_REMOTE_DIR}/.env"
  info "Syncing harness model maps to host"
  remote "mkdir -p '${ECS_REMOTE_DIR}/.harness'"
  copy "${REPO_ROOT}/.harness/models.cloud.yaml" "${ECS_REMOTE_DIR}/.harness/models.cloud.yaml"
  copy "${REPO_ROOT}/.harness/models.yaml"       "${ECS_REMOTE_DIR}/.harness/models.yaml"
  info "Logging the ECS host in to ACR"
  remote "echo '${ACR_PASSWORD}' | docker login --username '${ACR_USERNAME}' --password-stdin '${ACR_REGISTRY}'"
  info "Pulling images on host"
  remote "cd '${ECS_REMOTE_DIR}' && API_IMAGE='${API_IMAGE}' FRONTEND_IMAGE='${FRONTEND_IMAGE}' docker compose -f docker-compose.alibaba.yml --env-file .env pull"
else
  # On-host build: rsync the whole repo (respecting .gitignore via git archive).
  command -v rsync >/dev/null 2>&1 || die "rsync needed for on-host build mode (or set ACR_REGISTRY to push)"
  info "Syncing repo to host (on-host build mode)"
  if [ "$DRY_RUN" = false ]; then
    rsync -az --delete \
      --exclude '.git' --exclude 'node_modules' --exclude '__pycache__' \
      -e "ssh -i '$SSH_KEY' -p '$SSH_PORT' -o StrictHostKeyChecking=accept-new" \
      "${REPO_ROOT}/" "${SSH_USER}@${ECS_HOST}:${ECS_REMOTE_DIR}/"
  else
    info "[dry-run] rsync repo -> ${ECS_HOST}:${ECS_REMOTE_DIR}"
  fi
  copy "$ENV_FILE" "${ECS_REMOTE_DIR}/.env"
  info "Building images on host"
  remote "cd '${ECS_REMOTE_DIR}' && docker compose --project-directory . -f deploy/alibaba/docker-compose.alibaba.yml --env-file .env build"
fi

# ── Step 3: bring the stack up ───────────────────────────────────────────
info "Starting the stack on ${ECS_HOST}"
if [ "$USE_ACR" = true ]; then
  remote "cd '${ECS_REMOTE_DIR}' && API_IMAGE='${API_IMAGE}' FRONTEND_IMAGE='${FRONTEND_IMAGE}' docker compose -f docker-compose.alibaba.yml --env-file .env up -d"
else
  remote "cd '${ECS_REMOTE_DIR}' && docker compose --project-directory . -f deploy/alibaba/docker-compose.alibaba.yml --env-file .env up -d --build"
fi
ok "Stack started. Migrations run automatically via the api entrypoint (RUN_MIGRATIONS=true)."

# ── Step 4: health check /api/health ─────────────────────────────────────
HTTP_PORT="${HTTP_PORT:-80}"
HEALTH_URL="http://${ECS_HOST}:${HTTP_PORT}/api/health"
info "Health-checking ${HEALTH_URL}"
if [ "$DRY_RUN" = true ]; then
  info "[dry-run] would poll ${HEALTH_URL} until 200"
  ok "Dry run complete."
  exit 0
fi

attempts=30
for i in $(seq 1 "$attempts"); do
  code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 "$HEALTH_URL" 2>/dev/null || true)"
  if [ "$code" = "200" ]; then
    ok "Health check passed (HTTP 200) after ${i} attempt(s)."
    echo ""
    ok "Deploy complete → http://${ECS_HOST}:${HTTP_PORT}/"
    exit 0
  fi
  info "Attempt ${i}/${attempts}: got '${code:-no-response}', retrying in 5s..."
  sleep 5
done

fail "Health check did not pass after ${attempts} attempts."
fail "Inspect logs on the host:"
fail "  ssh ${SSH_USER}@${ECS_HOST} \"cd ${ECS_REMOTE_DIR} && docker compose -f docker-compose.alibaba.yml logs --tail=100 api\""
exit 1
