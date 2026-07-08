#!/usr/bin/env python3
"""Guarded APIMart GPT-Image-2 client for Temu image generation."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ALLOWED_MODEL = "gpt-image-2"
ALLOWED_RESOLUTION = "1k"
ALLOWED_QUALITY = "standard"
DEFAULT_KEY_PATH = Path(r"D:\Desktop\api\apid-api.txt")
SUBMIT_URL = "https://api.apimart.ai/v1/images/generations"
TASK_URL_TEMPLATE = "https://api.apimart.ai/v1/tasks/{task_id}"
FAILED_STATUSES = {"failed", "error", "canceled", "cancelled"}


def read_key() -> str:
    env_key = os.environ.get("APIMART_KEY", "").strip()
    if env_key:
        return env_key
    key_path = Path(os.environ.get("APIMART_KEY_PATH", str(DEFAULT_KEY_PATH)))
    key = key_path.read_text(encoding="utf-8").strip()
    if not key:
        raise RuntimeError(f"APIMart key file is empty: {key_path}")
    return key


def guard_low_cost(model: str, resolution: str, quality: str) -> None:
    if model != ALLOWED_MODEL:
        raise RuntimeError(f"Refusing expensive/nonstandard image2 model: {model}")
    if resolution != ALLOWED_RESOLUTION:
        raise RuntimeError(f"Refusing non-low-cost image2 resolution without explicit approval: {resolution}")
    if quality != ALLOWED_QUALITY:
        raise RuntimeError(f"Refusing nonstandard image2 quality without explicit approval: {quality}")


def image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def request_json(method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None = None, timeout: int = 240) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"APIMart HTTP {exc.code}: {error_text[:1000]}") from exc
    return json.loads(text)


def find_urls(obj: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in {"url", "image_url", "output_url"} and isinstance(value, str) and value.startswith(("http://", "https://")):
                urls.append(value)
            else:
                urls.extend(find_urls(value))
    elif isinstance(obj, list):
        for item in obj:
            urls.extend(find_urls(item))
    return urls


def extract_task_id(data: dict[str, Any]) -> str | None:
    task_id = data.get("task_id") or data.get("id")
    initial_data = data.get("data")
    if not task_id and isinstance(initial_data, dict):
        task_id = initial_data.get("task_id") or initial_data.get("id")
    if not task_id and isinstance(initial_data, list):
        for entry in initial_data:
            if isinstance(entry, dict) and (entry.get("task_id") or entry.get("id")):
                return entry.get("task_id") or entry.get("id")
    return task_id


def download(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=240) as resp:
        output_path.write_bytes(resp.read())


def generate_image2(
    prompt: str,
    image_paths: list[Path],
    output_path: Path,
    *,
    model: str = ALLOWED_MODEL,
    resolution: str = ALLOWED_RESOLUTION,
    quality: str = ALLOWED_QUALITY,
    poll_interval_sec: int = 3,
    max_polls: int = 120,
) -> dict[str, Any]:
    guard_low_cost(model, resolution, quality)
    key = read_key()
    payload = {
        "model": model,
        "prompt": prompt,
        "size": "1:1",
        "resolution": resolution,
        "quality": quality,
        "response_format": "url",
        "image_urls": [image_to_data_url(path) for path in image_paths],
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    started = time.time()
    data = request_json("POST", SUBMIT_URL, headers, payload, timeout=240)
    task_id = extract_task_id(data)
    image_url = None
    raw_final = data
    urls = find_urls(data)
    if urls:
        image_url = urls[0]
    if not image_url and task_id:
        for _ in range(max_polls):
            time.sleep(poll_interval_sec)
            raw_final = request_json("GET", TASK_URL_TEMPLATE.format(task_id=task_id), {"Authorization": f"Bearer {key}"}, timeout=120)
            urls = find_urls(raw_final)
            if urls:
                image_url = urls[0]
            raw_data = raw_final.get("data")
            data_status = raw_data.get("status") if isinstance(raw_data, dict) else ""
            status = str(raw_final.get("status") or raw_final.get("task_status") or data_status or "").lower()
            if image_url or status in FAILED_STATUSES:
                break
    if not image_url:
        raise RuntimeError(f"APIMart no image url: {json.dumps(raw_final, ensure_ascii=False)[:1000]}")
    download(image_url, output_path)
    return {
        "status": "ok",
        "provider": "APIMart",
        "model": model,
        "apimart_resolution": resolution,
        "apimart_quality": quality,
        "prompt": prompt,
        "source_pngs": [str(path) for path in image_paths],
        "image_url": image_url,
        "local_path": str(output_path),
        "cost_credits_est": 0.06,
        "elapsed_sec": round(time.time() - started, 2),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "raw_task": raw_final,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded APIMart gpt-image-2 client.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--image", action="append", required=True, help="Reference image path. Repeat for multiple images.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = generate_image2(args.prompt, [Path(p) for p in args.image], Path(args.output))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
