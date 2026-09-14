"""Run the authorized Agnes V2 product-only redo for all 23 rejected D values."""
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
OUT = ROOT / "human_redo23_agnes_v2_20260914"
PLAN = OUT / "agnes_v2_redo23_plan.json"
CANDIDATES = OUT / "candidates"
PROGRESS = OUT / "agnes_v2_redo23_progress.jsonl"
MANIFEST = OUT / "agnes_v2_redo23_manifest.json"
MAX_WORKERS = 8
EXPECTED_SIZE = (1024, 1024)
append_lock = threading.Lock()


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def append(record: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with append_lock, PROGRESS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def emit(record: dict) -> None:
    print(json.dumps(record, ensure_ascii=False), flush=True)


def load_records() -> list[dict]:
    payload = json.loads(PLAN.read_text(encoding="utf-8-sig"))
    records = payload["records"]
    if payload.get("record_count") != 23 or len(records) != 23:
        raise RuntimeError("V2 plan must contain exactly 23 records")
    if payload.get("all_old_T1_not_submitted") is not True:
        raise RuntimeError("Old T1 exclusion contract missing")
    if len({row["D"] for row in records}) != 23:
        raise RuntimeError("Duplicate D in V2 plan")
    for row in records:
        refs = row["submitted_images"]
        if len(refs) != 1 or refs[0]["role"] != "absolute_exact_D_product_identity":
            raise RuntimeError(f"V2 must submit exactly one product reference: {row['D']}")
        product = Path(refs[0]["path"])
        if not product.is_file() or sha256(product) != refs[0]["sha256"]:
            raise RuntimeError(f"Product reference missing/hash drift: {row['D']}")
        submitted = {product.resolve()}
        for evidence in row.get("planning_evidence_not_submitted", []):
            path = Path(evidence["path"])
            if not path.is_file() or sha256(path) != evidence["sha256"]:
                raise RuntimeError(f"Planning evidence missing/hash drift: {row['D']}")
            if path.resolve() in submitted:
                raise RuntimeError(f"Old T1 entered submitted images: {row['D']}")
        if len(row.get("negative_evidence_not_submitted", [])) != 2:
            raise RuntimeError(f"Two generations of negative evidence required: {row['D']}")
        for evidence in row["negative_evidence_not_submitted"]:
            path = Path(evidence["path"])
            if not path.is_file() or sha256(path) != evidence["sha256"]:
                raise RuntimeError(f"Negative evidence missing/hash drift: {row['D']}")
            if path.resolve() in submitted:
                raise RuntimeError(f"Rejected candidate entered request: {row['D']}")
    return records


def latest() -> dict[str, dict]:
    state: dict[str, dict] = {}
    if PROGRESS.is_file():
        for line in PROGRESS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("D"):
                    state[row["D"]] = row
    return state


def process_one(row: dict) -> dict:
    d_value = row["D"]
    target = CANDIDATES / row["L0xx"] / f"{d_value}.png"
    started = time.monotonic()
    append({
        "D": d_value,
        "L0xx": row["L0xx"],
        "status": "submitting",
        "provider": "Agnes AI",
        "model": DEFAULT_MODEL,
        "reference_count": 1,
        "old_T1_submitted": False,
        "negative_candidates_submitted": False,
        "updated_at": now(),
    })
    try:
        result = generate_edit(
            prompt=row["prompt"],
            image_paths=[Path(row["submitted_images"][0]["path"])],
        )
        with Image.open(io.BytesIO(result["image_bytes"])) as image:
            image.load()
            if image.size != EXPECTED_SIZE:
                raise RuntimeError(f"Unexpected Agnes output size: {image.size}")
            normalized = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".tmp")
            normalized.save(temporary, format="PNG", optimize=True)
            os.replace(temporary, target)
        with Image.open(target) as check:
            check.load()
            width, height = check.size
        record = {
            "D": d_value,
            "L0xx": row["L0xx"],
            "status": "validated",
            "provider": "Agnes AI",
            "model": DEFAULT_MODEL,
            "size": "1K",
            "ratio": "1:1",
            "reference_count": 1,
            "product_material": row["submitted_images"][0]["path"],
            "product_material_sha256": row["submitted_images"][0]["sha256"],
            "old_T1_submitted": False,
            "negative_candidates_submitted": False,
            "scene_recipe": row["scene_recipe"],
            "prompt": row["prompt"],
            "provider_created": result.get("created"),
            "provider_image_url": result.get("image_url") or "",
            "local_path": str(target),
            "bytes": target.stat().st_size,
            "width": width,
            "height": height,
            "output_sha256": sha256(target),
            "elapsed_sec": round(time.monotonic() - started, 2),
            "human_review_status": "pending",
            "eligible_for_badge_oss_writeback": False,
            "updated_at": now(),
        }
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        record = {
            "D": d_value,
            "L0xx": row["L0xx"],
            "status": "failed",
            "provider": "Agnes AI",
            "model": DEFAULT_MODEL,
            "systemic": any(token in message.lower() for token in ("http 401", "http 403", "missing or empty")),
            "error": message[:2000],
            "old_T1_submitted": False,
            "negative_candidates_submitted": False,
            "auto_resubmit": False,
            "updated_at": now(),
        }
    append(record)
    emit({k: record[k] for k in ("D", "status", "elapsed_sec", "local_path") if k in record})
    return record


def persist(records: list[dict], workers: int) -> dict:
    state = latest()
    values = [state.get(row["D"], {"D": row["D"], "status": "not_started"}) for row in records]
    payload = {
        "schema": "yeahf-1999d-agnes-v2-product-only-redo23-result/v1",
        "updated_at": now(),
        "provider": "Agnes AI",
        "model": DEFAULT_MODEL,
        "size": "1K",
        "ratio": "1:1",
        "workers": workers,
        "total": len(records),
        "status_counts": dict(Counter(row.get("status", "not_started") for row in values)),
        "all_old_T1_not_submitted": True,
        "all_prior_rejected_candidates_not_submitted": True,
        "returned_images_saved_immediately": True,
        "badge_applied": False,
        "oss_upload": False,
        "workbook_writeback": False,
        "records": values,
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--d", action="append", default=[])
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > MAX_WORKERS:
        raise RuntimeError(f"workers must be 1-{MAX_WORKERS}")
    records = load_records()
    if args.d:
        selected = set(args.d)
        records = [row for row in records if row["D"] in selected]
        if len(records) != len(selected):
            raise RuntimeError("Requested D is outside the V2 23-D plan")
    key_ready = True
    try:
        load_api_key()
    except RuntimeError:
        key_ready = False
    if args.preflight or not args.run:
        print(json.dumps({
            "preflight": "pass" if key_ready else "blocked_missing_key",
            "selected": len(records),
            "max_workers": MAX_WORKERS,
            "reference_count_each": 1,
            "all_old_T1_not_submitted": True,
            "all_negative_candidates_not_submitted": True,
        }, ensure_ascii=False))
        return
    if not key_ready:
        raise RuntimeError("Agnes key unavailable")
    prior = latest()
    todo = [row for row in records if (prior.get(row["D"]) or {}).get("status") != "validated"]
    emit({"run": "user_authorized_agnes_v2_redo23", "todo": len(todo), "workers": args.workers})
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process_one, row) for row in todo]
        for future in as_completed(futures):
            future.result()
    summary = persist(load_records(), args.workers)
    emit({"complete": True, "status_counts": summary["status_counts"], "manifest": str(MANIFEST)})


if __name__ == "__main__":
    main()

