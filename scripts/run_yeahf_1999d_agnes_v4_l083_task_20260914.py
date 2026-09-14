"""Build and run the authorized Agnes V4 task-scene redo for L083080809."""
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


D_VALUE = "L083080809"
ROOT = Path(
    r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810"
    r"\t1_cangyuan_current_workbook_t1"
)
V3 = ROOT / "human_redo4_agnes_v3_20260914"
V3_PLAN = V3 / "agnes_v3_redo4_plan.json"
V3_MANIFEST = V3 / "agnes_v3_redo4_manifest.json"
OUT = ROOT / "human_redo1_agnes_v4_l083_task_20260914"
PLAN = OUT / "agnes_v4_l083_task_plan.json"
MANIFEST = OUT / "agnes_v4_l083_task_manifest.json"
TARGET = OUT / "candidates" / "L083" / f"{D_VALUE}.png"
LOCK = ROOT / "outcome_library" / "human_rejected" / "agnes_v3_l083_no_task_human_rejection_lock.json"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_plan() -> dict:
    v3_plan = json.loads(V3_PLAN.read_text(encoding="utf-8-sig"))
    v3_manifest = json.loads(V3_MANIFEST.read_text(encoding="utf-8-sig"))
    source = next(row for row in v3_plan["records"] if row["D"] == D_VALUE)
    prior = next(row for row in v3_manifest["records"] if row["D"] == D_VALUE)
    prior_path = Path(prior["local_path"])
    if prior.get("status") != "validated" or not prior_path.is_file() or sha256(prior_path) != prior["output_sha256"]:
        raise RuntimeError("V3 L083 negative evidence missing/hash drift")
    product = Path(source["submitted_images"][0]["path"])
    if not product.is_file() or sha256(product) != source["submitted_images"][0]["sha256"]:
        raise RuntimeError("Exact-D product reference missing/hash drift")

    scene = (
        "a bright premium home-office worktable, eye-level three-quarter front-left camera, a young adult woman in her late "
        "twenties actively organizing work supplies: one hand places a notebook into the lower caddy while the other places "
        "pens into the upper wire basket, softly blurred laptop corner foreground, exact organiser and both hands clearly "
        "visible in the midground, bookcase, plant and window creating deep background layers"
    )
    product_lock = (
        "Preserve the exact freestanding desktop organiser from the input: one full flat rectangular bottom base, the lower "
        "solid caddy with both handle-slot side panels, front rail, two rear vertical rods, and one upper wire basket with the "
        "same dimensions, connectors and spacing. The entire bottom base must remain visibly planted on one continuous broad "
        "desk surface with realistic contact shadow throughout the task. The person may touch only the supplies; hands must "
        "not lift, pull, tilt, mount or cover the organiser. No cabinet installation, drawer rails, wall mounting or suspension."
    )
    prompt = (
        "MODE: product-only precision lifestyle reconstruction with a mandatory product-use task. The single input image is "
        "the absolute and only visual authority for the sale product. " + product_lock + " Create " + scene + ". The task must "
        "be obvious at first glance and physically believable. Keep the complete product unobstructed, correctly scaled and "
        "structurally identical to the input. Exactly one sale-product set. No readable text, measurements, badges, inset "
        "circles, logos, watermarks, duplicated products, extra legs, extra supports, changed count, warped hardware, hovering, "
        "floating, impossible gravity or furniture-edge overhang. Square 1:1 polished realistic premium ecommerce photograph."
    )
    negatives = list(source["negative_evidence_not_submitted"])
    negatives.append({
        "role": "agnes_v3_human_rejected_no_task_not_submitted",
        "path": str(prior_path),
        "sha256": sha256(prior_path),
        "reason": "产品支撑正确但缺少任务场景",
    })
    record = {
        "D": D_VALUE,
        "L0xx": "L083",
        "G": source.get("G", ""),
        "SKU": source.get("SKU", ""),
        "submitted_images": source["submitted_images"],
        "planning_evidence_not_submitted": source["planning_evidence_not_submitted"],
        "negative_evidence_not_submitted": negatives,
        "human_rejection_reason": "产品支撑正确但缺少任务场景",
        "scene_recipe": scene,
        "product_lock": product_lock,
        "prompt": prompt,
        "writeback": "BLOCK_until_human_review_badge_OSS_release_gate",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps({
        "schema": "yeahf-1999d-agnes-v4-l083-task-plan/v1",
        "created_at": now(),
        "record_count": 1,
        "all_rejected_candidates_not_submitted": True,
        "records": [record],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps({
        "schema": "temu-t1-human-rejection-lock/v1",
        "created_at": now(),
        "source_batch": "agnes_v3_20260914",
        "record_count": 1,
        "records": [{
            "D": D_VALUE,
            "candidate_path": str(prior_path),
            "candidate_sha256": sha256(prior_path),
            "human_status": "rejected",
            "reason": "产品支撑正确但缺少任务场景",
            "reuse_forbidden": True,
            "badge_forbidden": True,
            "oss_writeback_forbidden": True,
        }],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    prior["human_review_status"] = "rejected_user_20260914"
    prior["human_rejection_reason"] = "产品支撑正确但缺少任务场景"
    prior["eligible_for_badge_oss_writeback"] = False
    V3_MANIFEST.write_text(json.dumps(v3_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def validate_plan(record: dict) -> None:
    refs = record["submitted_images"]
    if len(refs) != 1 or refs[0]["role"] != "absolute_exact_D_product_identity":
        raise RuntimeError("V4 must submit exactly one exact-D product reference")
    product = Path(refs[0]["path"])
    if sha256(product) != refs[0]["sha256"]:
        raise RuntimeError("Product reference hash drift")
    if len(record["negative_evidence_not_submitted"]) != 4:
        raise RuntimeError("Four generations of negative evidence are required")
    for evidence in record["negative_evidence_not_submitted"]:
        path = Path(evidence["path"])
        if not path.is_file() or sha256(path) != evidence["sha256"]:
            raise RuntimeError("Negative evidence missing/hash drift")
        if path.resolve() == product.resolve():
            raise RuntimeError("Rejected evidence entered the submitted reference")


def run(record: dict) -> dict:
    started = time.monotonic()
    result = generate_edit(prompt=record["prompt"], image_paths=[Path(record["submitted_images"][0]["path"])])
    with Image.open(io.BytesIO(result["image_bytes"])) as image:
        image.load()
        if image.size != (1024, 1024):
            raise RuntimeError(f"Unexpected output size: {image.size}")
        normalized = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        temporary = TARGET.with_suffix(".tmp")
        normalized.save(temporary, format="PNG", optimize=True)
        os.replace(temporary, TARGET)
    payload = {
        "schema": "yeahf-1999d-agnes-v4-l083-task-result/v1",
        "updated_at": now(),
        "provider": "Agnes AI",
        "model": DEFAULT_MODEL,
        "status_counts": {"validated": 1},
        "returned_images_saved_immediately": True,
        "badge_applied": False,
        "oss_upload": False,
        "workbook_writeback": False,
        "records": [{
            "D": D_VALUE,
            "L0xx": "L083",
            "status": "validated",
            "provider": "Agnes AI",
            "model": DEFAULT_MODEL,
            "reference_count": 1,
            "product_material": record["submitted_images"][0]["path"],
            "product_material_sha256": record["submitted_images"][0]["sha256"],
            "all_negative_candidates_submitted": False,
            "scene_recipe": record["scene_recipe"],
            "prompt": record["prompt"],
            "local_path": str(TARGET),
            "bytes": TARGET.stat().st_size,
            "width": 1024,
            "height": 1024,
            "output_sha256": sha256(TARGET),
            "elapsed_sec": round(time.monotonic() - started, 2),
            "human_review_status": "pending",
            "eligible_for_badge_oss_writeback": False,
            "updated_at": now(),
        }],
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    record = build_plan()
    validate_plan(record)
    load_api_key()
    if args.preflight or not args.run:
        print(json.dumps({
            "preflight": "pass",
            "D": D_VALUE,
            "reference_count": 1,
            "negative_evidence_excluded": len(record["negative_evidence_not_submitted"]),
            "mandatory_task_scene": True,
        }, ensure_ascii=False))
        return
    if MANIFEST.is_file():
        existing = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
        rows = existing.get("records", [])
        if rows and rows[0].get("status") == "validated" and Path(rows[0]["local_path"]).is_file():
            print(json.dumps({"complete": True, "skipped_existing_validated": True, "manifest": str(MANIFEST)}, ensure_ascii=False))
            return
    payload = run(record)
    print(json.dumps({"complete": True, "status_counts": payload["status_counts"], "manifest": str(MANIFEST)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
