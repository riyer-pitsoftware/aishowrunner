#!/usr/bin/env python3
"""Submit a FLUX generation prompt to ComfyUI and poll until complete.

Usage:
    python3 scripts/comfyui-submit.py --prompt "your prompt" --negative "negative" \
        --prefix ep01_scene05 --width 832 --height 1216 --steps 30 --cfg 3.5 \
        --lora-strength 0.8 --seed 12345 --download output/episodes/ep01/images/

If --download is specified, the finished image is fetched and saved locally.
If --seed is omitted, a random seed is used.
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.request

COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "http://cc-gpu-l4:8188")


def build_workflow(prompt, negative, prefix, width, height, steps, cfg,
                   sampler, scheduler, lora_strength, seed):
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "flux1-dev-fp8.safetensors",
                "weight_dtype": "fp8_e4m3fn"
            }
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "clip_l.safetensors",
                "clip_name2": "t5xxl_fp8_e4m3fn.safetensors",
                "type": "flux"
            }
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "flux-ae.safetensors"}
        },
        "4": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["2", 0],
                "lora_name": "flux-RealismLora.safetensors",
                "strength_model": lora_strength,
                "strength_clip": lora_strength
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["4", 1]}
        },
        "6": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1}
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["4", 0],
                "positive": ["5", 0],
                "negative": ["9", 0],
                "latent_image": ["6", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1.0
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["7", 0], "vae": ["3", 0]}
        },
        "9": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]}
        },
        "10": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": prefix}
        }
    }


def submit(workflow):
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_HOST}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["prompt_id"]


def poll(prompt_id, timeout=600):
    url = f"{COMFYUI_HOST}/history/{prompt_id}"
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(5)
        try:
            resp = urllib.request.urlopen(url)
            data = json.loads(resp.read())
            if not data:
                continue
            d = list(data.values())[0]
            status = d.get("status", {})
            if status.get("status_str") == "error":
                print(f"ERROR: {json.dumps(status, indent=2)}", file=sys.stderr)
                return None
            outputs = d.get("outputs", {})
            for node_id, out in outputs.items():
                if "images" in out:
                    return out["images"]
        except Exception:
            continue
    print("TIMEOUT", file=sys.stderr)
    return None


def download_image(image_info, dest_dir):
    filename = image_info["filename"]
    subfolder = image_info.get("subfolder", "")
    img_type = image_info.get("type", "output")
    url = f"{COMFYUI_HOST}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, filename)
    urllib.request.urlretrieve(url, dest)
    return dest


def main():
    p = argparse.ArgumentParser(description="Submit prompt to ComfyUI")
    p.add_argument("--prompt", required=True)
    p.add_argument("--negative", default="")
    p.add_argument("--prefix", default="comfyui_output")
    p.add_argument("--width", type=int, default=832)
    p.add_argument("--height", type=int, default=1216)
    p.add_argument("--steps", type=int, default=30)
    p.add_argument("--cfg", type=float, default=3.5)
    p.add_argument("--sampler", default="euler")
    p.add_argument("--scheduler", default="simple")
    p.add_argument("--lora-strength", type=float, default=0.8)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--download", default=None, help="Local dir to download result")
    p.add_argument("--no-wait", action="store_true", help="Submit and exit immediately")
    args = p.parse_args()

    seed = args.seed if args.seed is not None else random.randint(1, 2**32)
    print(f"Seed: {seed}")

    workflow = build_workflow(
        args.prompt, args.negative, args.prefix,
        args.width, args.height, args.steps, args.cfg,
        args.sampler, args.scheduler, args.lora_strength, seed
    )

    prompt_id = submit(workflow)
    print(f"Queued: {prompt_id}")

    if args.no_wait:
        return

    print("Waiting for completion...")
    images = poll(prompt_id)
    if not images:
        sys.exit(1)

    for img in images:
        print(f"Generated: {img['filename']}")
        if args.download:
            dest = download_image(img, args.download)
            print(f"Downloaded: {dest}")


if __name__ == "__main__":
    main()
