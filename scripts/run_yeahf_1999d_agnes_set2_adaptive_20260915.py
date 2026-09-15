"""Run the second full Agnes set with adaptive concurrency and immediate local saves."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import threading
import time
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from PIL import Image

from agnes_image_client import DEFAULT_MODEL, generate_edit, load_api_key


ROOT = Path(
    r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810"
    r"\t1_cangyuan_current_workbook_t1\agnes_set2_full1999_20260915"
)
PLAN = ROOT / "YeahF_1999D_Agnes第二套1999计划_20260915.json"
CANDIDATES = ROOT / "candidates"
PROGRESS = ROOT / "agnes_set2_progress.jsonl"
MANIFEST = ROOT / "agnes_set2_manifest.json"
ADAPTIVE_STATE = ROOT / "agnes_set2_adaptive_concurrency.json"
EXPECTED_SIZE = (1024, 1024)
MAX_PROBE_WORKERS = 8
REQUEST_TIMEOUT = 150
COOLDOWN_SECONDS = 90
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
    ROOT.mkdir(parents=True, exist_ok=True)
    with append_lock, PROGRESS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def emit(value: dict) -> None:
    print(json.dumps(value, ensure_ascii=False), flush=True)


def load_records() -> list[dict]:
    payload = json.loads(PLAN.read_text(encoding="utf-8-sig"))
    rows = payload["records"]
    if payload.get("record_count") != 1999 or len(rows) != 1999 or len({row["D"] for row in rows}) != 1999:
        raise RuntimeError("Agnes set2 plan must contain 1999 unique D records")
    for row in rows:
        refs = row["submitted_images"]
        if len(refs) != 1 or refs[0]["role"] != "absolute_exact_D_product_identity":
            raise RuntimeError(f"Invalid product-only reference contract: {row['D']}")
        product = Path(refs[0]["path"])
        if not product.is_file() or sha256(product) != refs[0]["sha256"]:
            raise RuntimeError(f"Product material missing/hash drift: {row['D']}")
        prior = row["prior_final_candidate_not_submitted"]
        prior_path = Path(prior["path"])
        if not prior_path.is_file() or sha256(prior_path) != prior["sha256"]:
            raise RuntimeError(f"Prior final candidate missing/hash drift: {row['D']}")
        if product.resolve() == prior_path.resolve():
            raise RuntimeError(f"Prior generated T1 entered product reference: {row['D']}")
    return rows


def latest() -> dict[str, dict]:
    state = {}
    if PROGRESS.is_file():
        for line in PROGRESS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("D"):
                    state[row["D"]] = row
    return state


def process_one(row: dict, phase: str, workers: int) -> dict:
    d_value = row["D"]
    target = CANDIDATES / row["L0xx"] / f"{d_value}.png"
    started = time.monotonic()
    append({"D": d_value, "L0xx": row["L0xx"], "status": "submitting", "phase": phase, "workers": workers, "updated_at": now()})
    try:
        result = generate_edit(
            prompt=row["prompt"],
            image_paths=[Path(row["submitted_images"][0]["path"])],
            timeout_seconds=REQUEST_TIMEOUT,
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
            "phase": phase,
            "workers": workers,
            "provider": "Agnes AI",
            "model": DEFAULT_MODEL,
            "reference_count": 1,
            "product_material": row["submitted_images"][0]["path"],
            "product_material_sha256": row["submitted_images"][0]["sha256"],
            "old_T1_submitted": False,
            "prior_generated_T1_submitted": False,
            "scene_recipe": row["scene_recipe"],
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
        lower = message.lower()
        record = {
            "D": d_value,
            "L0xx": row["L0xx"],
            "status": "failed",
            "phase": phase,
            "workers": workers,
            "provider": "Agnes AI",
            "model": DEFAULT_MODEL,
            "error": message[:2000],
            "error_kind": "queue_full" if "queue is full" in lower else "timeout" if "timed out" in lower else "systemic" if any(x in lower for x in ("http 401", "http 403", "missing or empty")) else "other",
            "auto_retry_after_cooldown": True,
            "updated_at": now(),
        }
    append(record)
    emit({k: record[k] for k in ("D", "status", "phase", "workers", "elapsed_sec", "error_kind", "local_path") if k in record})
    return record


def persist(records: list[dict], adaptive: dict) -> dict:
    state = latest()
    values = [state.get(row["D"], {"D": row["D"], "status": "not_started"}) for row in records]
    payload = {
        "schema": "yeahf-1999d-agnes-second-full-set-result/v1",
        "updated_at": now(),
        "provider": "Agnes AI",
        "model": DEFAULT_MODEL,
        "total": 1999,
        "status_counts": dict(Counter(row.get("status", "not_started") for row in values)),
        "adaptive_concurrency": adaptive,
        "all_old_and_prior_generated_T1_not_submitted": True,
        "returned_images_saved_immediately": True,
        "badge_applied": False,
        "oss_upload": False,
        "workbook_writeback": False,
        "records": values,
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ADAPTIVE_STATE.write_text(json.dumps(adaptive, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def run_batch(rows: list[dict], workers: int, phase: str) -> list[dict]:
    outputs = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(process_one, row, phase, workers) for row in rows]
        for future in as_completed(futures):
            outputs.append(future.result())
    return outputs


def probe_order(records: list[dict]) -> list[dict]:
    by_family = defaultdict(deque)
    for row in records:
        by_family[row["L0xx"]].append(row)
    output = []
    families = sorted(by_family)
    while any(by_family.values()) and len(output) < sum(range(1, MAX_PROBE_WORKERS + 1)) + 10:
        for family in families:
            if by_family[family]:
                output.append(by_family[family].popleft())
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--max-probe-workers", type=int, default=MAX_PROBE_WORKERS)
    parser.add_argument("--cooldown", type=int, default=COOLDOWN_SECONDS)
    parser.add_argument("--resume-workers", type=int, default=0)
    args = parser.parse_args()
    if not 1 <= args.max_probe_workers <= MAX_PROBE_WORKERS:
        raise RuntimeError("max probe workers must be 1-8")
    if args.resume_workers and not 1 <= args.resume_workers <= MAX_PROBE_WORKERS:
        raise RuntimeError("resume workers must be 1-8")
    records = load_records()
    load_api_key()
    if args.preflight or not args.run:
        print(json.dumps({
            "preflight": "pass",
            "records": len(records),
            "probe_levels": list(range(1, args.max_probe_workers + 1)),
            "request_timeout_seconds": REQUEST_TIMEOUT,
            "cooldown_seconds": args.cooldown,
            "one_exact_D_product_reference_each": True,
            "all_prior_T1_excluded": True,
        }, ensure_ascii=False))
        return

    adaptive = {
        "started_at": now(),
        "probe_levels": [],
        "stable_workers": 0,
        "ramp_stopped_on_first_error": False,
        "cooldown_seconds": args.cooldown,
        "current_phase": "probe",
    }
    state = latest()
    if args.resume_workers:
        adaptive["stable_workers"] = args.resume_workers
        adaptive["resumed_from_existing_progress"] = True
        adaptive["resume_workers"] = args.resume_workers
        probes = []
    else:
        probes = [row for row in probe_order(records) if (state.get(row["D"]) or {}).get("status") != "validated"]
    cursor = 0
    level = args.max_probe_workers + 1 if args.resume_workers else 1
    while level <= args.max_probe_workers:
        batch = probes[cursor : cursor + level]
        if len(batch) < level:
            break
        emit({"probe_level": level, "batch": len(batch)})
        outputs = run_batch(batch, level, f"probe_{level}")
        success = sum(row["status"] == "validated" for row in outputs)
        failures = [row for row in outputs if row["status"] != "validated"]
        adaptive["probe_levels"].append({
            "workers": level,
            "submitted": len(outputs),
            "validated": success,
            "failed": len(failures),
            "error_kinds": dict(Counter(row.get("error_kind", "") for row in failures)),
            "completed_at": now(),
        })
        if failures:
            if any(row.get("error_kind") == "systemic" for row in failures):
                adaptive["current_phase"] = "blocked_systemic"
                persist(records, adaptive)
                raise RuntimeError("Systemic Agnes error during concurrency probe")
            adaptive["ramp_stopped_on_first_error"] = True
            adaptive["stable_workers"] = max(1, level - 1)
            persist(records, adaptive)
            emit({"ramp_stopped": True, "failed_level": level, "stable_workers": adaptive["stable_workers"], "cooldown_seconds": args.cooldown})
            time.sleep(args.cooldown)
            break
        adaptive["stable_workers"] = level
        persist(records, adaptive)
        cursor += level
        level += 1

    stable = max(1, int(adaptive["stable_workers"]))
    adaptive["current_phase"] = "production"
    adaptive["production_started_at"] = now()
    persist(records, adaptive)
    round_number = 0
    while True:
        state = latest()
        todo = [row for row in records if (state.get(row["D"]) or {}).get("status") != "validated"]
        if not todo:
            break
        round_number += 1
        batch = todo[:stable]
        emit({"production_round": round_number, "workers": stable, "todo_before": len(todo), "batch": len(batch)})
        outputs = run_batch(batch, stable, "production")
        failures = [row for row in outputs if row["status"] != "validated"]
        adaptive["production_rounds"] = round_number
        adaptive["last_round"] = {
            "submitted": len(outputs),
            "validated": len(outputs) - len(failures),
            "failed": len(failures),
            "completed_at": now(),
        }
        persist(records, adaptive)
        if failures:
            if any(row.get("error_kind") == "systemic" for row in failures):
                adaptive["current_phase"] = "blocked_systemic"
                persist(records, adaptive)
                raise RuntimeError("Systemic Agnes error during production")
            previous = stable
            stable = max(1, stable - 1)
            adaptive["stable_workers"] = stable
            adaptive.setdefault("production_backoffs", []).append({"from": previous, "to": stable, "failures": len(failures), "at": now()})
            persist(records, adaptive)
            emit({"production_pause": True, "workers_previous": previous, "workers_after_cooldown": stable, "cooldown_seconds": args.cooldown, "failures": len(failures)})
            time.sleep(args.cooldown)

    adaptive["current_phase"] = "complete"
    adaptive["completed_at"] = now()
    summary = persist(records, adaptive)
    emit({"complete": True, "status_counts": summary["status_counts"], "stable_workers": stable, "manifest": str(MANIFEST)})


if __name__ == "__main__":
    main()
