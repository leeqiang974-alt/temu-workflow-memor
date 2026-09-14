"""Run only the two user-authorized Agnes v2 diagnostic images.

This script is intentionally separate from the failed-23 runner. It supports the
product-first two-reference test and the L082 product-only fusion-control test.
It never submits prior rejected candidates or writes to the workbook.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

from agnes_image_client import DEFAULT_MODEL, generate_edit, load_api_key


ROOT = Path(
    r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810"
    r"\t1_cangyuan_current_workbook_t1"
)
PLAN = ROOT / "diagnostics" / "agnes_prompt_v2_two_image_ab_plan_20260914.json"
OUT = ROOT / "diagnostics" / "agnes_prompt_v2_results_20260914"
PROGRESS = OUT / "progress.jsonl"
MANIFEST = OUT / "manifest.json"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_records() -> list[dict]:
    payload = json.loads(PLAN.read_text(encoding="utf-8-sig"))
    records = payload["records"]
    if len(records) != 2:
        raise RuntimeError("Diagnostic plan must contain exactly two records")
    for row in records:
        for ref in row["submitted_images"]:
            path = Path(ref["path"])
            if not path.is_file() or sha256(path) != ref["sha256"]:
                raise RuntimeError(f"Reference missing/hash drift: {row['D']} {ref['role']}")
        negative = Path(row["negative_candidate"]["path"])
        if not negative.is_file() or sha256(negative) != row["negative_candidate"]["sha256"]:
            raise RuntimeError(f"Negative evidence missing/hash drift: {row['D']}")
        if row["negative_candidate"].get("submitted") is not False:
            raise RuntimeError(f"Rejected image entered request: {row['D']}")
        submitted = {Path(ref["path"]).resolve() for ref in row["submitted_images"]}
        if negative.resolve() in submitted:
            raise RuntimeError(f"Rejected image path collision: {row['D']}")
        for ref in row.get("planning_evidence_not_submitted", []):
            if Path(ref["path"]).resolve() in submitted:
                raise RuntimeError(f"Planning-only conflicting scene entered request: {row['D']}")
    return records


def append(row: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()


def latest() -> dict[str, dict]:
    result = {}
    if PROGRESS.is_file():
        for line in PROGRESS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                result[row["D"]] = row
    return result


def run_one(row: dict) -> dict:
    d_value = row["D"]
    target = OUT / "candidates" / d_value[:4] / f"{d_value}.png"
    append({"D": d_value, "status": "submitting", "updated_at": now()})
    started = time.monotonic()
    try:
        refs = [Path(ref["path"]) for ref in row["submitted_images"]]
        result = generate_edit(prompt=row["prompt"], image_paths=refs)
        with Image.open(io.BytesIO(result["image_bytes"])) as image:
            image.load()
            if image.size != (1024, 1024):
                raise RuntimeError(f"Unexpected output dimensions: {image.size}")
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".tmp")
            image.save(temporary, format="PNG", optimize=True)
            os.replace(temporary, target)
        record = {
            "D": d_value,
            "status": "validated",
            "provider": "Agnes AI",
            "model": DEFAULT_MODEL,
            "reference_count": len(refs),
            "reference_roles": [ref["role"] for ref in row["submitted_images"]],
            "negative_candidate_submitted": False,
            "local_path": str(target),
            "output_sha256": sha256(target),
            "width": 1024,
            "height": 1024,
            "elapsed_sec": round(time.monotonic() - started, 2),
            "human_review_status": "pending",
            "eligible_for_writeback": False,
            "updated_at": now(),
        }
    except Exception as exc:  # noqa: BLE001
        record = {
            "D": d_value,
            "status": "failed",
            "error": str(exc)[:2000],
            "negative_candidate_submitted": False,
            "auto_resubmit": False,
            "updated_at": now(),
        }
    append(record)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    return record


def persist(records: list[dict]) -> None:
    state = latest()
    payload = {
        "schema": "yeahf-1999d-agnes-v2-diagnostics/v1",
        "updated_at": now(),
        "provider": "Agnes AI",
        "model": DEFAULT_MODEL,
        "records": [state.get(row["D"], {"D": row["D"], "status": "not_started"}) for row in records],
        "human_review_required": True,
        "badge_applied": False,
        "oss_upload": False,
        "workbook_writeback": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--d", action="append", default=[])
    args = parser.parse_args()
    records = load_records()
    if args.d:
        selected = set(args.d)
        records = [row for row in records if row["D"] in selected]
        if len(records) != len(selected):
            raise RuntimeError("Requested D is outside the two-record diagnostic plan")
    key_ready = True
    try:
        load_api_key()
    except RuntimeError:
        key_ready = False
    if args.preflight or not args.run:
        print(json.dumps({
            "preflight": "pass" if key_ready else "blocked_missing_key",
            "selected": [row["D"] for row in records],
            "reference_counts": {row["D"]: len(row["submitted_images"]) for row in records},
            "negative_candidates_submitted": False,
            "bulk_run": False,
        }, ensure_ascii=False))
        return
    if not key_ready:
        raise RuntimeError("Agnes key unavailable")
    prior = latest()
    for row in records:
        if (prior.get(row["D"]) or {}).get("status") != "validated":
            run_one(row)
    persist(load_records())


if __name__ == "__main__":
    main()

