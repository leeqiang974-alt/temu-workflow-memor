"""Small secret-safe client for Agnes image generation/editing.

The API key is read from a local file or environment variable and is never
included in returned records, logs, manifests, or exceptions.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_ENDPOINT = "https://apihub.agnes-ai.com/v1/images/generations"
DEFAULT_MODEL = "agnes-image-2.5-flash"
DEFAULT_KEY_PATHS = (
    Path(r"D:\Desktop\api\agnes爱思.txt"),
    Path(r"D:\Desktop\api\agnesapi.txt"),
)


def load_api_key() -> tuple[str, Path | None]:
    value = os.environ.get("AGNES_API_KEY", "").strip()
    if value:
        return value, None
    configured = os.environ.get("AGNES_API_KEY_PATH", "").strip()
    paths = (Path(configured),) if configured else DEFAULT_KEY_PATHS
    for path in paths:
        if path.is_file():
            value = path.read_text(encoding="utf-8-sig").strip()
            if value:
                return value, path
    raise RuntimeError(
        "Agnes API key file is missing or empty; expected "
        + " or ".join(str(path) for path in paths)
    )


def _redact(text: str, key: str = "") -> str:
    if key:
        text = text.replace(key, "[REDACTED]")
    return re.sub(r"cpk-[A-Za-z0-9_-]{12,}", "[REDACTED]", text)


def image_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def generate_edit(
    *,
    prompt: str,
    image_paths: list[Path],
    model: str = DEFAULT_MODEL,
    size: str = "1K",
    ratio: str = "1:1",
    timeout_seconds: int = 360,
) -> dict[str, Any]:
    if model != DEFAULT_MODEL:
        raise RuntimeError(f"Unexpected Agnes model: {model}")
    if size != "1K" or ratio != "1:1":
        raise RuntimeError("This Temu runner permits only Agnes 1K square output")
    if len(image_paths) != 2:
        raise RuntimeError("The 1999D redo contract requires exactly two references")
    for path in image_paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    key, key_path = load_api_key()
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "ratio": ratio,
        "extra_body": {
            "image": [image_data_uri(path) for path in image_paths],
            "response_format": "b64_json",
        },
    }
    request = urllib.request.Request(
        DEFAULT_ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "temu-1999d-agnes-runner/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"Agnes HTTP {exc.code}: {_redact(detail, key)}") from None
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(_redact(f"Agnes request failed: {exc}", key)) from None

    try:
        result = json.loads(body.decode("utf-8"))
        item = result["data"][0]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Invalid Agnes response schema: {exc}") from None

    image_bytes: bytes | None = None
    image_url = item.get("url") if isinstance(item, dict) else None
    b64_json = item.get("b64_json") if isinstance(item, dict) else None
    if b64_json:
        try:
            image_bytes = base64.b64decode(b64_json, validate=True)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Invalid Agnes image Base64: {exc}") from None
    elif image_url:
        try:
            with urllib.request.urlopen(str(image_url), timeout=120) as response:
                image_bytes = response.read()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Agnes result download failed: {_redact(str(exc), key)}") from None
    if not image_bytes:
        raise RuntimeError("Agnes response contained neither image bytes nor URL")

    return {
        "image_bytes": image_bytes,
        "image_url": str(image_url or ""),
        "created": result.get("created"),
        "model": model,
        "size": size,
        "ratio": ratio,
        "key_path": str(key_path) if key_path else "AGNES_API_KEY",
    }

