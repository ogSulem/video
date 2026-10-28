#!/usr/bin/env python3
"""Generate the four hero clips on NVIDIA's hosted video models (run locally).

This script is deliberately built to be run by a human with an NVIDIA API key,
because the agent sandbox cannot reach integrate.api.nvidia.com (egress is
restricted to GitHub/PyPI). Nothing here needs the repository's venv: only
`requests` is required.

Quick start
-----------
    export NVIDIA_API_KEY=nvapi-...
    python video/nvidia_i2v.py --list-models

That prints every model id your key can see. Pick the image-to-video one
(names differ by account and change over time), then:

    python video/nvidia_i2v.py --clip A --model <MODEL_ID> --dry-run
    python video/nvidia_i2v.py --clip A --model <MODEL_ID>
    python video/nvidia_i2v.py --all --model <MODEL_ID> --duration 10

Generated files land in video/shots/ai_hero_clips/clipA.mp4 ... clipD.mp4,
which is exactly where video/tools/assemble_hero_clips.py looks for them.

Prompts are read from prompts_export.json (generated alongside the plan), so
the wording stays identical to production/video_generation_pack/02_promty_*.md.

The endpoint shapes of NVIDIA-hosted video models differ (sync asset response,
async NVCF request id + polling, multipart vs JSON base64 image). This script
therefore auto-detects: it sends the configured shape, prints the server's own
error verbatim if it does not match, and lets you switch shape with --shape.
Paste that error back into the agent session and the call can be pinned exactly.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("pip install requests")

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "production" / "video_generation_pack"
PROMPTS = PACK / "prompts_export.json"
REFS = PACK / "references"
CLIP_DIR = ROOT / "video" / "shots" / "ai_hero_clips"

HOST = "https://integrate.api.nvidia.com/v1"
NVCF = "https://api.nvcf.nvidia.com/v2/nvcf"


def b64(path: Path) -> tuple[str, str]:
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return base64.b64encode(path.read_bytes()).decode("ascii"), mime


def load_prompts() -> dict:
    if not PROMPTS.exists():
        sys.exit(f"missing {PROMPTS} (run the pack build step first)")
    return json.loads(PROMPTS.read_text())


def list_models(key: str) -> int:
    r = requests.get(f"{HOST}/models", headers={"Authorization": f"Bearer {key}"},
                     timeout=60)
    if r.status_code != 200:
        print(f"HTTP {r.status_code}\n{r.text[:2000]}")
        return 1
    data = r.json().get("data", [])
    print(f"{len(data)} models visible to this key:\n")
    for m in sorted(data, key=lambda x: x.get("id", "")):
        mid = m.get("id", "?")
        if any(k in mid.lower() for k in ("video", "i2v", "t2v", "wan", "cosmos",
                                          "ltx", "svd", "stable-video", "motion")):
            print(f"  * {mid}   <- looks like a video model")
        else:
            print(f"    {mid}")
    return 0


def post_json(url: str, key: str, payload: dict, timeout: int):
    return requests.post(url, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }, json=payload, timeout=timeout)


def post_multipart(url: str, key: str, prompt: str, image: Path, extra: dict,
                   timeout: int):
    with image.open("rb") as fh:
        files = {"image": (image.name, fh, mimetypes.guess_type(str(image))[0] or "image/png")}
        return requests.post(url, headers={"Authorization": f"Bearer {key}"},
                             data={"prompt": prompt, **{k: str(v) for k, v in extra.items()}},
                             files=files, timeout=timeout)


def poll_nvcf(key: str, req_id: str, timeout: int = 900) -> requests.Response:
    url = f"{NVCF}/pexec/status/{req_id}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=60)
        if r.status_code == 202:
            print("  ...still rendering")
            time.sleep(10)
            continue
        return r
    raise TimeoutError("NVCF job did not finish in time")


def save_video(r: requests.Response, out: Path) -> bool:
    ctype = r.headers.get("Content-Type", "")
    if ctype.startswith("video/") or ctype == "application/octet-stream":
        out.write_bytes(r.content)
        return True
    try:
        body = r.json()
    except ValueError:
        return False
    # common shapes: {"video": "<url>"} | {"assets": [{"url": ...}]} | {"artifacts":[{"base64": ...}]}
    for v in body.get("videos", []) if isinstance(body.get("videos"), list) else []:
        if isinstance(v, str) and v.startswith("http"):
            out.write_bytes(requests.get(v, timeout=300).content)
            return True
    for key in ("video", "video_url", "url", "output"):
        val = body.get(key)
        if isinstance(val, str) and val.startswith("http"):
            out.write_bytes(requests.get(val, timeout=300).content)
            return True
        if isinstance(val, str) and len(val) > 4096:
            out.write_bytes(base64.b64decode(val))
            return True
    for coll in ("assets", "artifacts", "outputs"):
        for item in body.get(coll, []) or []:
            if not isinstance(item, dict):
                continue
            if item.get("url"):
                out.write_bytes(requests.get(item["url"], timeout=300).content)
                return True
            if item.get("base64"):
                out.write_bytes(base64.b64decode(item["base64"]))
                return True
    print("unrecognised response shape:")
    print(json.dumps(body, indent=2)[:3000])
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clip", choices=list("ABCD"))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--model", default=os.environ.get("NVIDIA_VIDEO_MODEL", ""))
    ap.add_argument("--list-models", action="store_true")
    ap.add_argument("--shape", choices=["json_b64", "multipart", "json_seedance"],
                    default="json_b64",
                    help="request shape; try another if the server rejects the payload")
    ap.add_argument("--asset-endpoint", default=os.environ.get("NVIDIA_ASSET_ENDPOINT", ""),
                    help="pre-uploaded asset id/url for the reference image, if the model needs one")
    ap.add_argument("--duration", type=int, default=10, help="seconds to request")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--dry-run", action="store_true", help="print the request, send nothing")
    ap.add_argument("--out-dir", default=str(CLIP_DIR))
    args = ap.parse_args()

    key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not key:
        sys.exit("set NVIDIA_API_KEY first (never commit it)")

    if args.list_models:
        return list_models(key)

    if not args.clip and not args.all:
        sys.exit("choose --clip A|B|C|D or --all (or --list-models)")

    prompts = load_prompts()
    tags = list("ABCD") if args.all else [args.clip]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.model:
        sys.exit("pass --model <id> (run --list-models to find it)")

    for tag in tags:
        spec = prompts[tag]
        image = REFS / spec["reference"]
        out = out_dir / f"clip{tag}.mp4"
        if out.exists():
            print(f"clip{tag}: {out} exists, skipping (delete it to regenerate)")
            continue
        if not image.exists():
            sys.exit(f"clip{tag}: missing reference {image}")

        print(f"\n=== clip{tag}: {image.name} -> {out.name}")
        if args.shape == "multipart":
            payload_desc = {"prompt": spec["prompt"][:120] + "...", "data": {"image": str(image)}}
        else:
            img_b64, mime = b64(image)
            payload = {
                "prompt": spec["prompt"],
                "negative_prompt": spec.get("negative_prompt", ""),
                "image": args.asset_endpoint or f"data:{mime};base64,{img_b64}",
                "duration": args.duration,
                "fps": args.fps,
                "size": args.size,
                "seed": 0,
                "steps": 30,
                "cfg_scale": 5.0,
            }
            payload_desc = {k: (v[:80] + "..." if isinstance(v, str) and len(v) > 120 else v)
                            for k, v in payload.items() if k != "image"}

        url = f"{HOST}/video/{args.model}" if not args.model.startswith("http") else args.model
        print(f"POST {url}  shape={args.shape}")
        if args.dry_run:
            print(json.dumps(payload_desc, indent=2))
            continue

        if args.shape == "multipart":
            r = post_multipart(url, key, spec["prompt"], image,
                               {"duration": args.duration, "fps": args.fps,
                                "size": args.size}, timeout=900)
        else:
            r = post_json(url, key, payload, timeout=900)

        if r.status_code == 202:
            req_id = r.json().get("reqId") or r.headers.get("NVCF-REQID", "")
            print(f"  async job {req_id}; polling")
            r = poll_nvcf(key, req_id)

        if r.status_code >= 300:
            print(f"  HTTP {r.status_code}\n  {r.text[:2500]}")
            print("  -> try a different --shape, or check the model id/size limits, "
                  "then paste this error back into the session so the call can be pinned.")
            continue

        if save_video(r, out):
            print(f"  saved {out} ({out.stat().st_size / 1e6:.1f} MB)")
        else:
            print("  could not extract video from the response")

    print("\nnext: .venv/bin/python video/tools/assemble_hero_clips.py --force")
    return 0


if __name__ == "__main__":
    sys.exit(main())
