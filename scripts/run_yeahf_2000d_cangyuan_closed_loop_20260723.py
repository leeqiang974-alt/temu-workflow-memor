"""Regenerate the 289 YeahF expansion T1 images with a zero-loss Cangyuan loop.

The runner submits at most one task per worker, waits for that exact task, downloads
its temporary result immediately, validates the image, and only then accepts another
item. It never uploads OSS or writes a workbook.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import mimetypes
import os
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from PIL import Image


WORKSPACE = Path(r"C:\Users\Administrator\Documents\temu自动化")
BACKEND = Path(r"D:\JackWPP\smartphoto_backend")
PLAN = (
    WORKSPACE
    / "outputs"
    / "yeahf_merged_d_0721"
    / "YeahF_2000D_苍猿T1原稿参考任务清单_20260723.json"
)
OUT = Path(r"D:\temu素材库\T首图候选暂存\YeahF_2000D_苍猿GPTImage2_重新生成闭环_20260723")
CANDIDATES = OUT / "candidates"
PROGRESS = OUT / "cangyuan_closed_loop_progress_20260723.jsonl"
MANIFEST = OUT / "cangyuan_closed_loop_manifest_20260723.json"
ERROR_KEY = "yeahf2000_cangyuan_closed_loop_20260723"
MAX_IN_FLIGHT = 8
# Cangyuan accepts the 1024x1024 request but its established successful YeahF
# pipeline returns 1254x1254 PNG assets. The historical approved 144-D candidates
# were verified at this exact size.
EXPECTED_SIZE = (1254, 1254)

os.chdir(BACKEND)
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.reference_images import LoadedReferenceImage  # noqa: E402
from app.services.upstream import WhataiClient  # noqa: E402


append_lock = threading.Lock()
circuit_lock = threading.Lock()
circuit_open = threading.Event()
systemic_failures: Counter[str] = Counter()


def timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def append(record: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with append_lock:
        with PROGRESS.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()


def load_progress() -> dict[str, dict]:
    latest: dict[str, dict] = {}
    if not PROGRESS.is_file():
        return latest
    for line in PROGRESS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("D"):
            latest[str(record["D"])] = record
    return latest


def load_plan() -> list[dict]:
    records = json.loads(PLAN.read_text(encoding="utf-8"))["records"]
    if len(records) != 289 or len({r["target_D"] for r in records}) != 289:
        raise RuntimeError("289-D plan count/uniqueness check failed")
    for record in records:
        reference = Path(record["reference_image"])
        if not reference.is_file():
            raise RuntimeError(f"missing original reference: {record['target_D']} -> {reference}")
        lowered = str(reference).lower()
        if "candidates" in lowered or "outputs" in lowered:
            raise RuntimeError(f"generated/output reference is forbidden: {record['target_D']} -> {reference}")
        if record["target_D"].startswith("L047"):
            prompt = record["prompt"].lower()
            required = ("insert directly into", "circular", "square", "cross", "pedestal", "freestanding")
            if not all(term in prompt for term in required):
                raise RuntimeError(f"L047 ground/base prompt lock missing: {record['target_D']}")
    return records


def make_reference(record: dict) -> LoadedReferenceImage:
    path = Path(record["reference_image"])
    content = path.read_bytes()
    with Image.open(io.BytesIO(content)) as image:
        image.load()
        width, height = image.size
    return LoadedReferenceImage(
        image_id=f"yeahf2000-closed-{record['target_D']}",
        slot_type="front",
        display_order=1,
        source_url=str(path),
        width=width,
        height=height,
        mime_type=mimetypes.guess_type(path.name)[0] or "image/jpeg",
        file_size=len(content),
        file_name=path.name,
        path=path,
        content=content,
    )


def submission_from_task(record: dict, task_id: str) -> dict:
    return {
        "submission_id": record["target_D"],
        "task_id": task_id,
        "upstream_endpoint": "/v1/images/edits",
        "task_path": "/images/edits",
        "prompt": record["prompt"],
        "size": "1024x1024",
        "aspect_ratio": "1:1",
    }


def validate_image(content: bytes) -> tuple[int, int, str]:
    with Image.open(io.BytesIO(content)) as image:
        image.load()
        width, height = image.size
        mode = image.mode
    if (width, height) != EXPECTED_SIZE:
        raise RuntimeError(f"unexpected image size: {(width, height)} != {EXPECTED_SIZE}")
    return width, height, mode


def classify_failure(exc: Exception) -> tuple[str, bool]:
    message = str(exc)
    lowered = message.lower()
    if any(term in lowered for term in ("insufficient", "balance", "payment", "余额", "欠费")):
        return "payment_or_balance", True
    if any(term in lowered for term in ("401", "403", "unauthorized", "forbidden", "authentication")):
        return "authentication", True
    if any(term in lowered for term in ("no space left", "disk full", "permission denied")):
        return "local_storage", True
    if "404" in lowered and ("tmp.cangyuansuanli.cn" in lowered or "gen-images" in lowered):
        with circuit_lock:
            systemic_failures["completed_download_404"] += 1
            repeated = systemic_failures["completed_download_404"] >= 3
        return "completed_download_404", repeated
    if "image task failed" in lowered or "upstream failure" in lowered:
        return "provider_generation_failed", False
    if "429" in lowered or "rate limit" in lowered:
        return "rate_limit_exhausted", False
    return "isolated_or_unknown", False


def process_one(record: dict, prior: dict | None = None) -> dict:
    d_value = record["target_D"]
    target = CANDIDATES / d_value[:4] / f"{d_value}.png"
    if prior and prior.get("status") == "validated" and target.is_file():
        return prior

    existing_task = ""
    if (
        prior
        and prior.get("task_id")
        and prior.get("status") != "validated"
        and prior.get("failure_category") != "provider_generation_failed"
    ):
        existing_task = str(prior.get("task_id") or "")
    if circuit_open.is_set() and not existing_task:
        paused = {
            "D": d_value,
            "L0xx": d_value[:4],
            "status": "paused_before_submit",
            "reason": "systemic circuit breaker is open",
            "updated_at": timestamp(),
        }
        append(paused)
        return paused

    client = WhataiClient()
    if not client._image_api_key_value() or not client._is_cangyuan_image_base():
        raise RuntimeError("Cangyuan configuration unavailable; fake fallback forbidden")
    reference = make_reference(record)
    source_sha = sha256_file(reference.path)

    try:
        if existing_task:
            submission = submission_from_task(record, existing_task)
        else:
            submitted_at = time.monotonic()
            submission = client.submit_image_request(
                prompt=record["prompt"],
                size="1024x1024",
                aspect_ratio="1:1",
                reference_images=[reference],
                error_key=ERROR_KEY,
            )
            if submission.get("upstream_endpoint") == "/local/fake-image" or not submission.get("task_id"):
                raise RuntimeError("fake/taskless provider response rejected")
            submitted = {
                "D": d_value,
                "L0xx": d_value[:4],
                "status": "submitted",
                "provider": "Cangyuan",
                "model": "gpt-image-2",
                "mode": "reference_edit",
                "task_id": str(submission["task_id"]),
                "source_original": str(reference.path),
                "source_sha256": source_sha,
                "prompt": record["prompt"],
                "submit_elapsed_sec": round(time.monotonic() - submitted_at, 2),
                "updated_at": timestamp(),
                "writeback": "blocked_until_user_visual_approval",
            }
            append(submitted)
            print(json.dumps({"submitted": d_value, "task_id": submitted["task_id"]}, ensure_ascii=False), flush=True)

        task_id = str(submission["task_id"])
        completed = client.poll_image_tasks([submission], ERROR_KEY, initial_delay_seconds=3)
        image_result = completed.get(task_id) or completed.get(d_value)
        if not image_result:
            raise RuntimeError(f"missing completed result for task={task_id}")
        append(
            {
                "D": d_value,
                "L0xx": d_value[:4],
                "status": "provider_completed",
                "task_id": task_id,
                "updated_at": timestamp(),
            }
        )
        content = client.download_image_bytes(submission, image_result, ERROR_KEY)
        width, height, mode = validate_image(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, target)
        output_sha = sha256_bytes(content)
        validated = {
            "D": d_value,
            "L0xx": d_value[:4],
            "status": "validated",
            "provider": "Cangyuan",
            "model": "gpt-image-2",
            "mode": "reference_edit",
            "task_id": task_id,
            "source_original": str(reference.path),
            "source_sha256": source_sha,
            "image_url": str(image_result.get("url") or ""),
            "local_path": str(target),
            "bytes": len(content),
            "width": width,
            "height": height,
            "mode_name": mode,
            "output_sha256": output_sha,
            "updated_at": timestamp(),
            "writeback": "blocked_until_user_visual_approval",
        }
        append(validated)
        print(json.dumps({"validated": d_value, "bytes": len(content), "local_path": str(target)}, ensure_ascii=False), flush=True)
        return validated
    except Exception as exc:
        category, systemic = classify_failure(exc)
        if systemic:
            circuit_open.set()
        failed = {
            "D": d_value,
            "L0xx": d_value[:4],
            "status": "failed",
            "failure_category": category,
            "systemic": systemic,
            "task_id": str((locals().get("submission") or {}).get("task_id") or existing_task),
            "source_original": str(reference.path),
            "source_sha256": source_sha,
            "error": str(exc),
            "updated_at": timestamp(),
            "auto_resubmit": False,
        }
        append(failed)
        print(json.dumps({"failed": d_value, "category": category, "systemic": systemic}, ensure_ascii=False), flush=True)
        return failed


def write_manifest(plan: list[dict]) -> dict:
    latest = load_progress()
    records = [latest.get(row["target_D"], {"D": row["target_D"], "status": "not_started"}) for row in plan]
    counts = Counter(str(record.get("status") or "unknown") for record in records)
    payload = {
        "generated_at": timestamp(),
        "provider": "Cangyuan",
        "model": "gpt-image-2",
        "scope": "YeahF 2000-D expansion: 289 regenerated T1 local candidates",
        "closed_loop": True,
        "max_in_flight": MAX_IN_FLIGHT,
        "oss_upload": False,
        "workbook_writeback": False,
        "counts": dict(counts),
        "records": records,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Explicitly resubmit only provider_generation_failed D values after user approval.",
    )
    parser.add_argument("--workers", type=int, default=MAX_IN_FLIGHT)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > MAX_IN_FLIGHT:
        raise RuntimeError(f"workers must be between 1 and {MAX_IN_FLIGHT}")

    plan = load_plan()
    prior = load_progress()
    if args.smoke_only:
        first = plan[0]
        result = process_one(first, prior.get(first["target_D"]))
        payload = write_manifest(plan)
        if result.get("status") != "validated":
            raise RuntimeError(f"smoke task did not validate locally: {result}")
        print(
            json.dumps(
                {
                    "smoke": "passed",
                    "D": first["target_D"],
                    "local_path": result["local_path"],
                    "manifest": str(MANIFEST),
                    "counts": payload["counts"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return

    smoke = prior.get(plan[0]["target_D"])
    smoke_path = Path(str((smoke or {}).get("local_path") or ""))
    if not smoke or smoke.get("status") != "validated" or not smoke_path.is_file():
        raise RuntimeError("bulk run blocked: execute --smoke-only and validate local download first")

    if args.retry_failed:
        todo = [
            row
            for row in plan
            if (prior.get(row["target_D"]) or {}).get("status") == "failed"
            and (prior.get(row["target_D"]) or {}).get("failure_category")
            == "provider_generation_failed"
        ]
        append(
            {
                "status": "retry_batch_authorized",
                "retry_count": len(todo),
                "retry_D": [row["target_D"] for row in todo],
                "authorization": "explicit_user_request",
                "updated_at": timestamp(),
            }
        )
    else:
        terminal = {"validated", "failed"}
        todo = [
            row
            for row in plan
            if (prior.get(row["target_D"]) or {}).get("status") not in terminal
        ]
    print(
        json.dumps(
            {
                "run": "bulk",
                "planned": len(plan),
                "already_terminal": len(plan) - len(todo),
                "todo": len(todo),
                "workers": args.workers,
                "retry_failed": args.retry_failed,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(process_one, row, prior.get(row["target_D"])): row["target_D"]
            for row in todo
        }
        for future in as_completed(futures):
            future.result()
    payload = write_manifest(plan)
    print(
        json.dumps(
            {
                "run": "finished",
                "counts": payload["counts"],
                "circuit_open": circuit_open.is_set(),
                "manifest": str(MANIFEST),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
