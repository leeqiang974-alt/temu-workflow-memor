"""Redo the remaining 23 failed YeahF 1999D T1 items with Agnes Image 2.5.

This runner consumes the already audited two-reference plan. It never submits
the human-rejected candidate. Every successful response is decoded, validated,
normalized to PNG, hashed, and saved before the record is marked validated.
No badge, OSS upload, or workbook writeback occurs in this stage.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from PIL import Image

from agnes_image_client import DEFAULT_MODEL, generate_edit, load_api_key


ROOT = Path(
    r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810"
    r"\t1_cangyuan_current_workbook_t1"
)
PLAN = ROOT / "YeahF_1999D_T1人工驳回105D_双参考重做计划_20260813.json"
PRIOR = ROOT / "human_redo105_20260813" / "cangyuan_human_redo105_manifest.json"
OUT = ROOT / "human_redo23_agnes_20260914"
CANDIDATES = OUT / "candidates"
PROGRESS = OUT / "agnes_failed23_progress.jsonl"
MANIFEST = OUT / "agnes_failed23_manifest.json"
MAX_WORKERS = 4
EXPECTED_SIZE = (1024, 1024)


append_lock = threading.Lock()


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def append(record: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with append_lock, PROGRESS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def emit(record: dict) -> None:
    print(json.dumps(record, ensure_ascii=False), flush=True)


def load_records() -> list[dict]:
    plan = json.loads(PLAN.read_text(encoding="utf-8-sig"))
    prior = json.loads(PRIOR.read_text(encoding="utf-8-sig"))
    failed = {row["D"] for row in prior["records"] if row.get("status") == "failed"}
    records = [row for row in plan["records"] if row.get("target_D") in failed]
    if len(failed) != 23 or len(records) != 23:
        raise RuntimeError(f"Expected 23 exact failed D values, got failed={len(failed)} plan={len(records)}")
    if len({row["target_D"] for row in records}) != 23:
        raise RuntimeError("Duplicate D in Agnes redo plan")
    for row in records:
        scene = Path(row["scene_anchor"])
        product = Path(row["product_material"])
        negative = Path(row["negative_candidate"])
        if not scene.is_file() or sha256_file(scene) != row["scene_anchor_sha256"]:
            raise RuntimeError(f"Scene anchor missing/hash drift: {row['target_D']}")
        if not product.is_file() or sha256_file(product) != row["product_material_sha256"]:
            raise RuntimeError(f"Product material missing/hash drift: {row['target_D']}")
        if not negative.is_file() or sha256_file(negative) != row["negative_candidate_sha256"]:
            raise RuntimeError(f"Negative evidence missing/hash drift: {row['target_D']}")
        if row.get("negative_candidate_submitted") is not False:
            raise RuntimeError(f"Negative candidate exclusion missing: {row['target_D']}")
        if negative.resolve() in {scene.resolve(), product.resolve()}:
            raise RuntimeError(f"Rejected candidate entered reference chain: {row['target_D']}")
    return records


def latest() -> dict[str, dict]:
    state: dict[str, dict] = {}
    if PROGRESS.is_file():
        for line in PROGRESS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("D"):
                    state[str(row["D"])] = row
    return state


def persist(records: list[dict]) -> dict:
    state = latest()
    values = [state.get(row["target_D"], {"D": row["target_D"], "status": "not_started"}) for row in records]
    payload = {
        "schema": "yeahf-1999d-t1-failed23-agnes/v1",
        "updated_at": now(),
        "provider": "Agnes AI",
        "endpoint": "https://apihub.agnes-ai.com/v1/images/generations",
        "model": DEFAULT_MODEL,
        "size": "1K",
        "ratio": "1:1",
        "reference_count": 2,
        "total": len(records),
        "status_counts": dict(Counter(str(row.get("status") or "not_started") for row in values)),
        "returned_images_saved_immediately": True,
        "negative_candidates_submitted": False,
        "badge_applied": False,
        "oss_upload": False,
        "workbook_writeback": False,
        "records": values,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def process_one(row: dict) -> dict:
    d_value = row["target_D"]
    target = CANDIDATES / row["l0xx"] / f"{d_value}.png"
    prior = latest().get(d_value)
    if prior and prior.get("status") == "validated" and target.is_file():
        return prior

    append({
        "D": d_value,
        "L0xx": row["l0xx"],
        "status": "submitting",
        "provider": "Agnes AI",
        "model": DEFAULT_MODEL,
        "scene_anchor_sha256": row["scene_anchor_sha256"],
        "product_material_sha256": row["product_material_sha256"],
        "negative_candidate_sha256": row["negative_candidate_sha256"],
        "negative_candidate_submitted": False,
        "updated_at": now(),
    })
    started = time.monotonic()
    try:
        result = generate_edit(
            prompt=row["prompt"],
            image_paths=[Path(row["scene_anchor"]), Path(row["product_material"])],
        )
        with Image.open(io.BytesIO(result["image_bytes"])) as image:
            image.load()
            if image.size != EXPECTED_SIZE:
                raise RuntimeError(f"Unexpected Agnes output size: {image.size}")
            normalized = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            buffer = io.BytesIO()
            normalized.save(buffer, format="PNG", optimize=True)
            content = buffer.getvalue()
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, target)
        with Image.open(target) as check:
            check.load()
            width, height = check.size
        record = {
            "D": d_value,
            "L0xx": row["l0xx"],
            "status": "validated",
            "provider": "Agnes AI",
            "model": DEFAULT_MODEL,
            "size": "1K",
            "ratio": "1:1",
            "reference_count": 2,
            "scene_anchor": row["scene_anchor"],
            "scene_anchor_sha256": row["scene_anchor_sha256"],
            "product_material": row["product_material"],
            "product_material_sha256": row["product_material_sha256"],
            "negative_candidate_sha256": row["negative_candidate_sha256"],
            "negative_candidate_submitted": False,
            "prompt": row["prompt"],
            "provider_created": result.get("created"),
            "provider_image_url": result.get("image_url") or "",
            "local_path": str(target),
            "bytes": len(content),
            "width": width,
            "height": height,
            "output_sha256": sha256_file(target),
            "elapsed_sec": round(time.monotonic() - started, 2),
            "review_status": "pending_human_review",
            "writeback": "BLOCK_until_human_review_badge_OSS_release_gate",
            "updated_at": now(),
        }
        append(record)
        emit({"validated": d_value, "seconds": record["elapsed_sec"], "local_path": str(target)})
        return record
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        systemic = any(token in message.lower() for token in ("http 401", "http 403", "missing or empty"))
        record = {
            "D": d_value,
            "L0xx": row["l0xx"],
            "status": "failed",
            "provider": "Agnes AI",
            "model": DEFAULT_MODEL,
            "systemic": systemic,
            "error": message[:2000],
            "negative_candidate_submitted": False,
            "auto_resubmit": False,
            "updated_at": now(),
        }
        append(record)
        emit({"failed": d_value, "systemic": systemic, "error": message[:300]})
        return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--d", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > MAX_WORKERS:
        raise RuntimeError(f"workers must be 1-{MAX_WORKERS}")
    records = load_records()
    if args.d:
        selected = set(args.d)
        records = [row for row in records if row["target_D"] in selected]
        missing = selected - {row["target_D"] for row in records}
        if missing:
            raise RuntimeError(f"Requested D is not in the failed-23 set: {sorted(missing)}")
    if args.limit:
        records = records[: args.limit]
    key_ready = True
    key_path = ""
    try:
        _, path = load_api_key()
        key_path = str(path or "AGNES_API_KEY")
    except RuntimeError:
        key_ready = False
    if args.preflight or not args.run:
        summary = persist(load_records())
        print(json.dumps({
            "preflight": "pass" if key_ready else "blocked_missing_key",
            "key_ready": key_ready,
            "key_path": key_path or str(Path(r"D:\Desktop\api\agnes爱思.txt")),
            "provider": "Agnes AI",
            "model": DEFAULT_MODEL,
            "size": "1K",
            "ratio": "1:1",
            "failed_set": 23,
            "selected": len(records),
            "all_two_reference_hashes_verified": True,
            "all_negative_candidates_excluded": True,
            "status_counts": summary["status_counts"],
        }, ensure_ascii=False))
        return
    if not key_ready:
        raise RuntimeError(r"Agnes key file is empty: D:\Desktop\api\agnes爱思.txt")

    prior = latest()
    todo = [row for row in records if (prior.get(row["target_D"]) or {}).get("status") != "validated"]
    emit({"run": "user_authorized_agnes_failed23", "selected": len(records), "todo": len(todo), "workers": args.workers})
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process_one, row) for row in todo]
        for future in as_completed(futures):
            future.result()
    summary = persist(load_records())
    emit({"complete": True, "status_counts": summary["status_counts"], "manifest": str(MANIFEST)})


if __name__ == "__main__":
    main()

