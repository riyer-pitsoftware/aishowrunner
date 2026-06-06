# ChronoCanvas GPU Infrastructure

Two-tier ephemeral GPU VMs for image (L4) and video (A100) generation via ComfyUI, accessed through Tailscale VPN.

## Prerequisites

- **GCP project** with billing enabled
- **gcloud CLI** authenticated (`gcloud auth login`)
- **Tailscale account** (free tier is fine)
- **jq** for status output parsing (`brew install jq` on macOS)
- *(Optional)* **runpodctl** for RunPod fallback

## Quick Start (First Time)

### 1. Set your GCP project

```bash
export GCP_PROJECT_ID=your-project-id
```

### 2. Request GPU quota

Go to [GCP Console → IAM & Admin → Quotas](https://console.cloud.google.com/iam-admin/quotas) and request:
- `NVIDIA_L4_GPUS` in `us-central1` (at least 1)
- `NVIDIA_A100_GPUS` in `us-central1` (at least 1)

> GPU quota requests can take 24-48 hours. If denied, use the [RunPod fallback](#runpod-fallback).

### 3. Create GCS buckets

```bash
gcloud storage buckets create gs://chronocanvas-models --location=us-central1
gcloud storage buckets create gs://chronocanvas-outputs --location=us-central1
```

### 4. Upload models

Download models listed in `models/model-manifest.json` and upload to GCS:

```bash
# Example for one model — repeat for all models in manifest
wget https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8-e4m3fn.safetensors
gcloud storage cp flux1-dev-fp8-e4m3fn.safetensors gs://chronocanvas-models/diffusion_models/

# See model-manifest.json for the full list (8 L4 models + 4 A100 models)
```

**Total model sizes:** L4 ~30.5 GB | A100 ~24.2 GB | Combined ~54.7 GB

### 5. Create Tailscale auth key

1. Go to [Tailscale Admin → Auth Keys](https://login.tailscale.com/admin/settings/authkeys)
2. Generate a **reusable, ephemeral** key
3. Store in GCP Secret Manager:

```bash
echo -n "tskey-auth-xxxxxxxxxxxx" | gcloud secrets create ts-authkey --data-file=-
```

### 6. Create VMs

```bash
./gpu-vm.sh create l4
./gpu-vm.sh create a100
```

### 7. Start a VM

```bash
./gpu-vm.sh start l4
```

### 8. Access ComfyUI

Once the startup script completes:

```
http://cc-gpu-l4:8188     (via Tailscale VPN)
```

> **First boot:** ~15-20 min (model sync from GCS). **Subsequent boots:** ~30 seconds (--no-clobber skips existing files).

## Daily Operations

```bash
# Start an image generation session
./gpu-vm.sh start l4

# Start a video generation session
./gpu-vm.sh start a100

# Check status (state, uptime, estimated cost)
./gpu-vm.sh status l4

# Stop when done
./gpu-vm.sh stop l4

# SSH for debugging
./gpu-vm.sh ssh l4
```

## Cost Control

| Tier | Provisioning | Rate | Auto-Shutdown |
|------|-------------|------|---------------|
| L4 | SPOT | ~$0.34/hr | 30 min idle |
| A100 | ON-DEMAND | ~$3.67/hr | 30 min idle |

**Key safeguards:**
- **Auto-shutdown:** VM stops after 30 min of < 5% GPU utilization (configurable in `config.env`)
- **Always stop when done** — don't rely solely on auto-shutdown
- **Check status before leaving:** `./gpu-vm.sh status l4`
- **SPOT preemption:** L4 may be preempted by GCP. Boot disk is preserved (stops, doesn't delete). Restart with `./gpu-vm.sh start l4`.

**Edit idle timeout:**
```bash
# In config.env
L4_IDLE_TIMEOUT_MIN=30    # Change this value
A100_IDLE_TIMEOUT_MIN=30
```

## RunPod Fallback

Use when GCP GPU quota is denied or pool is exhausted.

| | GCP L4 | RunPod L4 | GCP A100 | RunPod A100 |
|---|--------|-----------|----------|-------------|
| VRAM | 24 GB | 24 GB | 40 GB | **80 GB** |
| Rate | ~$0.34/hr | ~$0.24/hr | ~$3.67/hr | ~$1.19-1.39/hr |
| Access | Tailscale VPN | Public URL | Tailscale VPN | Public URL |

```bash
# Start a RunPod pod
./runpod/runpod-start.sh l4

# Sync models to pod
./runpod/runpod-sync.sh <pod-id> upload

# Download outputs
./runpod/runpod-sync.sh <pod-id> download

# Stop pod (syncs outputs first)
./runpod/runpod-stop.sh <pod-id>
```

> **RunPod A100 is 80GB** (vs GCP 40GB) and cheaper ($1.19-1.39/hr vs $3.67/hr). If GCP quota is denied, RunPod is actually a better option for video generation.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| VM won't start | Check GPU quota: `gcloud compute regions describe us-central1 --format="value(quotas)"` |
| Can't reach ComfyUI | Check Tailscale: `tailscale status`. Verify VM is RUNNING: `./gpu-vm.sh status l4` |
| Models not loading | SSH in and check startup logs: `./gpu-vm.sh ssh l4` then `journalctl -u comfyui` |
| Slow boot (15-20 min) | First boot syncs all models from GCS. Subsequent boots < 1 min with `--no-clobber`. |
| SPOT preemption | L4 was preempted. Restart: `./gpu-vm.sh start l4`. Boot disk is preserved. |
| Outputs missing | Check shutdown log: `journalctl -u google-shutdown-scripts.service`. Manual sync: `gcloud storage rsync -r /opt/ComfyUI/output/ gs://chronocanvas-outputs/$(date +%Y%m%d)/` |

## File Structure

```
deploy/gpu/
├── config.env                    # Shared two-tier config (GCP settings, costs, timeouts)
├── gpu-vm.sh                     # Main entrypoint: start/stop/status/create/ssh
├── models/
│   └── model-manifest.json       # Declarative model list (8 L4 + 4 A100 models)
├── scripts/
│   ├── 00-config.sh              # Config sourcing + prerequisite validation
│   ├── 01-create-vm.sh           # One-time VM creation (L4 or A100)
│   ├── 02-startup.sh             # VM boot: model sync, ComfyUI, Tailscale, watchdog
│   ├── 03-shutdown.sh            # VM shutdown: output sync, Tailscale disconnect
│   ├── 04-idle-watchdog.sh       # Cron: GPU idle detection → auto-shutdown
│   └── comfyui.service           # systemd unit for ComfyUI (port 8188)
└── runpod/
    ├── runpod-start.sh           # Fallback: create RunPod pod
    ├── runpod-stop.sh            # Fallback: stop pod (syncs outputs first)
    └── runpod-sync.sh            # Fallback: upload models / download outputs
```
