# AI Showrunner — Alibaba Cloud Deployment (bead asr-av5.3, TRD §14)

Run the AI Showrunner backend on **Alibaba Cloud**, with the **skill plane
routed to Qwen Cloud** (`qwen-cloud/*` via DashScope, OpenAI-compatible). This
reuses the repo's existing `docker/Dockerfile.api` + `docker/Dockerfile.frontend`
and mirrors the structure of `deploy/cloudrun/`.

Target: a single **ECS** instance running the full `docker compose` stack
(api + worker + frontend + Postgres/pgvector + Redis). For a hackathon/demo
this is the pragmatic choice — one box, one command, no managed-service sprawl.

```
                         ECS instance (Ubuntu + Docker)
   Internet ─:80─▶  frontend (nginx SPA)  ──/api/──▶  api (FastAPI :8000)
                                                          │
                                                          ├─▶ db (pgvector :5432)
                                                          ├─▶ redis (:6379)
                                                          └─▶ worker (arq jobs)
                                                          │
                                       skill plane ───────┘
                                       Qwen Cloud (DashScope, qwen-cloud/*)
```

---

## ⚠️ Why `DEPLOYMENT_MODE` must NOT be `gcp`

`backend/src/chronocanvas/config.py` has a deliberate coupling: when
`DEPLOYMENT_MODE=gcp`, `Settings._unify_gcp_and_hackathon()` **auto-forces**
`hackathon_mode = True` and `hackathon_strict_gemini = True` — i.e. **Gemini-only
routing**. That is correct for the GCP/Cloud Run target, but **wrong for a
Qwen/Alibaba deployment**: it would bypass the Qwen Cloud skill plane entirely.

This deployment therefore runs with **`DEPLOYMENT_MODE=hybrid`** (hardcoded in
`docker-compose.alibaba.yml`, and `deploy.sh` refuses to proceed if you override
it back to `gcp`). The skill plane is flipped to Qwen Cloud **purely** via:

```
HARNESS_MODELS_PATH=/app/.harness/models.cloud.yaml
```

`models.cloud.yaml` maps every skill tier to `qwen-cloud/*` (turbo/plus/max).
litellm resolves those against DashScope using `DASHSCOPE_API_KEY`. We do **not**
edit `config.py` — we configure around the coupling.

---

## Prerequisites

**Alibaba Cloud account (International / Singapore region `ap-southeast-1`):**

1. **DashScope API key** — Model Studio → API-KEY. This is the Qwen Cloud
   credential (`DASHSCOPE_API_KEY`). The international compatible-mode endpoint
   is `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`.
2. **ECS instance** — Ubuntu 22.04, ≥ 2 vCPU / 8 GB RAM (sentence-transformers
   + builds need headroom), ≥ 40 GB disk. Note its **public IP**.
3. **Security group** — inbound allow **80** (and **443** if you add TLS).
   You do **not** need to expose 5432/6379/8000 — only the frontend (`:80`) is
   published; everything else stays on the internal compose network.
4. **SSH key** — added to the ECS instance; private key path on your workstation.
5. *(Optional)* **ACR** (Alibaba Container Registry) namespace + login
   credentials, if you want to build locally and have the host pull images
   rather than build on the host. Endpoint looks like
   `registry-intl.ap-southeast-1.aliyuncs.com`.
6. *(Optional)* **`aliyun` CLI** authenticated (`aliyun configure`) if you script
   ECS/ACR provisioning — not required by `deploy.sh`, which uses SSH + docker.

**Workstation:** `docker` (with buildx), `git`, `curl`, `ssh`/`scp`, and `rsync`
(only for on-host build mode).

---

## Quick start

```bash
# 1. From the repo root, create your env file and fill in REAL values.
cp deploy/alibaba/.env.alibaba.example deploy/alibaba/.env.alibaba
$EDITOR deploy/alibaba/.env.alibaba

# 2. Generate the required secrets:
openssl rand -hex 32   # → SECRET_KEY
openssl rand -hex 16   # → POSTGRES_PASSWORD
#   pick an APP_PASSWORD; paste your DashScope key into DASHSCOPE_API_KEY
#   set ECS_HOST / ECS_SSH_KEY (and ACR_* if using a registry)
#   set CORS_ORIGINS to include http://<ECS_HOST>

# 3. Deploy (build → ship → up → migrate → health-check).
bash deploy/alibaba/deploy.sh

# Dry-run first if you want to see every action without executing:
bash deploy/alibaba/deploy.sh --dry-run
```

`deploy.sh` auto-selects between two modes from your env:

| Mode | Trigger | What happens |
|---|---|---|
| **On-host build** | `ACR_REGISTRY` empty | `rsync` repo to ECS, `docker compose build` on the host, `up -d`. Simplest single-box path. |
| **ACR push** | `ACR_REGISTRY` set | Build locally, push to ACR, host pulls tagged images, `up -d`. Faster host start, repeatable. |

Migrations run automatically: the api service starts with `RUN_MIGRATIONS=true`,
so the entrypoint runs `alembic upgrade head` before uvicorn.

---

## What the files are

| File | Purpose |
|---|---|
| `docker-compose.alibaba.yml` | The ECS stack. Reuses `docker/Dockerfile.api` + `docker/Dockerfile.frontend`. Sets `DEPLOYMENT_MODE=hybrid`, `HARNESS_MODELS_PATH=/app/.harness/models.cloud.yaml`, Qwen keys, `RUN_MIGRATIONS=true`, persistent volumes, and the security hardening (`no-new-privileges`, `cap_drop: ALL`, `tmpfs`). |
| `deploy.sh` | Build → (push) → remote up → migrate → health-check `/api/health`. Fails fast on missing env. Idempotent (`up -d` reconciles). |
| `.env.alibaba.example` | Every var the operator sets — DB, Redis (internal), DashScope/Qwen keys, `SECRET_KEY`, `APP_PASSWORD`, ACR, ECS/SSH, region. |
| `README.md` | This runbook. |

---

## Verify

1. **Health:**
   ```bash
   curl http://<ECS_HOST>/api/health     # expect HTTP 200
   ```
   `deploy.sh` already polls this and fails the deploy if it never goes green.

2. **App loads:** open `http://<ECS_HOST>/` in a browser. You'll hit the
   `APP_PASSWORD` gate — enter the password you set.

3. **Skill plane is Qwen Cloud (the real check):** run a produce/episode flow
   from the UI, then confirm the skill invocations were billed to Qwen:
   ```bash
   ssh <user>@<ECS_HOST> "cd /opt/ai-showrunner && \
     docker compose -f docker-compose.alibaba.yml exec -T db \
     psql -U chronocanvas -d chronocanvas \
     -c \"select provider, count(*) from skill_invocations group by provider;\""
   ```
   You should see `provider = qwen-cloud`. If you instead see Gemini/local, the
   harness map didn't take effect — check `HARNESS_MODELS_PATH` and that
   `.harness/models.cloud.yaml` is mounted into the api/worker containers.

4. **Confirm mode (sanity):**
   ```bash
   ssh <user>@<ECS_HOST> "cd /opt/ai-showrunner && \
     docker compose -f docker-compose.alibaba.yml exec -T api \
     env | grep -E 'DEPLOYMENT_MODE|HARNESS_MODELS_PATH'"
   ```
   Expect `DEPLOYMENT_MODE=hybrid` and the cloud harness path. If you see
   `gcp`, stop — routing is Gemini-only (see the warning section above).

---

## Logs & operations

```bash
ssh <user>@<ECS_HOST>
cd /opt/ai-showrunner

docker compose -f docker-compose.alibaba.yml ps
docker compose -f docker-compose.alibaba.yml logs -f --tail=100 api
docker compose -f docker-compose.alibaba.yml logs -f --tail=100 worker
```

Redeploy after a code change: just re-run `bash deploy/alibaba/deploy.sh` from
your workstation. It rebuilds, re-ships, and `up -d` reconciles in place.

---

## Rollback

- **ACR push mode** — images are tagged with the git short SHA. Roll back by
  re-running with a known-good checkout:
  ```bash
  git checkout <good-sha>
  bash deploy/alibaba/deploy.sh
  ```
  or on the host, pin the old tag and re-up:
  ```bash
  ssh <user>@<ECS_HOST> "cd /opt/ai-showrunner && \
    API_IMAGE=<acr>/<ns>/ai-showrunner-api:<old-sha> \
    FRONTEND_IMAGE=<acr>/<ns>/ai-showrunner-frontend:<old-sha> \
    docker compose -f docker-compose.alibaba.yml --env-file .env up -d"
  ```
- **On-host build mode** — `git checkout <good-sha>` on your workstation and
  re-run `deploy.sh` (it rsyncs the checkout and rebuilds).
- **Data:** Postgres lives in the `pgdata` named volume and survives `up`/`down`.
  A schema rollback needs a matching Alembic downgrade — coordinate before
  rolling back across a migration boundary.
- **Full stop:**
  ```bash
  ssh <user>@<ECS_HOST> "cd /opt/ai-showrunner && \
    docker compose -f docker-compose.alibaba.yml down"      # add -v to wipe data
  ```

---

## Notes & alternatives

- **Managed data services:** to use **RDS for PostgreSQL (pgvector)** and
  **ApsaraDB for Redis** instead of containers, drop the `db`/`redis` services
  and point `DATABASE_URL`/`REDIS_URL` at the managed endpoints (keep the
  pgvector extension enabled on RDS). The app code is unchanged.
- **ACK / Function Compute:** ACK (Kubernetes) is the scale-out path; Function
  Compute doesn't fit the always-on worker + stateful Postgres/Redis stack well.
  For the demo, ECS + compose is the right altitude.
- **TLS:** for HTTPS, front the instance with Alibaba SLB/ALB or add a Caddy/Traefik
  sidecar terminating 443 → frontend `:8080`, and open 443 in the security group.
