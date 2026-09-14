"""Build the user-authorized Agnes V3 plan for four rejected V2 candidates."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(
    r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810"
    r"\t1_cangyuan_current_workbook_t1"
)
V2_DIR = ROOT / "human_redo23_agnes_v2_20260914"
V2_PLAN = V2_DIR / "agnes_v2_redo23_plan.json"
V2_MANIFEST = V2_DIR / "agnes_v2_redo23_manifest.json"
OUT = ROOT / "human_redo4_agnes_v3_20260914"
PLAN = OUT / "agnes_v3_redo4_plan.json"
LOCK = ROOT / "outcome_library" / "human_rejected" / "agnes_v2_20260914_redo4_human_rejection_lock.json"


CORRECTIONS = {
    "L077080826": {
        "reason": "产品比例不对",
        "scene": (
            "a bright contemporary living-room reading corner, eye-level three-quarter front camera, "
            "a young adult woman in her twenties sitting on a low cushion and playing with a cat beside the product, "
            "a soft rug edge in the foreground, exact cat house in the midground, slim bookcase and window depth behind"
        ),
        "lock": (
            "Preserve the exact reference body proportions instead of enlarging or stretching it: front body width-to-height "
            "about 1.45:1, original depth relationship, curved back panel, front opening, round hole, slots, fasteners and side "
            "scratching panels. It is a compact floor cat house, lower than an adult's knee when standing and only moderately "
            "larger than one normal cat. Keep it about 38-42 percent of the frame width and 28-34 percent of frame height."
        ),
    },
    "L081080846": {
        "reason": "多了脚架，且产品伸出桌外",
        "scene": (
            "a spacious modern co-working lounge coffee counter, eye-level three-quarter right camera, a thirty-something "
            "male barista in a denim apron placing coffee pods into the basket, ceramic cup foreground, exact organiser centered "
            "on a broad stone countertop, lounge seating and tall windows in the deep background"
        ),
        "lock": (
            "Preserve the exact short four-legged countertop organiser from the reference: one pale wood top, black rectangular "
            "frame, one pull-out wire basket and the original short legs only. All four original feet must be visibly planted on "
            "the same broad countertop with contact shadows. The entire product, including the extended basket, must stay inside "
            "the countertop boundary. No floor-length stand, no extra leg frame, no cart base, no casters and no supports below "
            "the countertop."
        ),
    },
    "L081080910": {
        "reason": "产品外观变更且疑似悬空",
        "scene": (
            "a warm architect-designed apartment breakfast bar, slightly high three-quarter left camera, a middle-aged woman "
            "in her forties arranging sealed coffee packets in the pulled-out basket, blurred fruit bowl foreground, exact "
            "organiser centered on a large oak island, pendant lights and dining area creating deep background layers"
        ),
        "lock": (
            "Copy the exact reference product geometry: pale rectangular wood top, black rectangular frame, four short straight "
            "legs, side rails and one pull-out black wire basket with the same proportions. All four feet must touch the same oak "
            "countertop and cast clear contact shadows; the frame cannot float, hang, bridge between furniture or extend to the "
            "floor. Keep the complete product inside the island edges. Do not redesign the frame, rails, basket, legs or top."
        ),
    },
    "L083080809": {
        "reason": "产品悬空",
        "scene": (
            "a refined home-office supply station, low three-quarter front-left camera, no person, a softly blurred notebook and "
            "pen in the foreground, the exact two-level organiser standing on a broad matte-white desk in the midground, wall art, "
            "plant and window forming a deep premium background"
        ),
        "lock": (
            "Preserve the exact freestanding desktop organiser: full flat rectangular bottom base and lower caddy resting directly "
            "on the desk, two rear vertical rods supporting the upper wire basket, exact side panels, handle slots, rails, connectors "
            "and proportions. The entire bottom base must visibly contact one continuous desk surface with a natural contact shadow. "
            "Do not mount it in cabinetry, do not pull it out, do not hang or float it, and add no hidden rails or supports."
        ),
    },
}


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    v2_plan = json.loads(V2_PLAN.read_text(encoding="utf-8-sig"))
    v2_manifest = json.loads(V2_MANIFEST.read_text(encoding="utf-8-sig"))
    plan_by_d = {row["D"]: row for row in v2_plan["records"]}
    result_by_d = {row["D"]: row for row in v2_manifest["records"]}
    created = now()
    lock_records = []
    records = []

    for d_value, correction in CORRECTIONS.items():
        old = plan_by_d[d_value]
        v2 = result_by_d[d_value]
        v2_path = Path(v2["local_path"])
        if not v2_path.is_file() or sha256(v2_path) != v2["output_sha256"]:
            raise RuntimeError(f"V2 negative evidence missing/hash drift: {d_value}")
        product = Path(old["submitted_images"][0]["path"])
        if not product.is_file() or sha256(product) != old["submitted_images"][0]["sha256"]:
            raise RuntimeError(f"Exact-D product evidence missing/hash drift: {d_value}")

        lock_records.append({
            "D": d_value,
            "candidate_path": str(v2_path),
            "candidate_sha256": sha256(v2_path),
            "human_status": "rejected",
            "reason": correction["reason"],
            "reuse_forbidden": True,
            "badge_forbidden": True,
            "oss_writeback_forbidden": True,
        })

        negative = list(old["negative_evidence_not_submitted"])
        negative.append({
            "role": "agnes_v2_human_rejected_not_submitted",
            "path": str(v2_path),
            "sha256": sha256(v2_path),
            "reason": correction["reason"],
        })
        prompt = (
            "MODE: product-only precision lifestyle reconstruction after a human rejection. The single input image is the "
            "absolute and only visual authority for the sale product. " + correction["lock"] + " Create " + correction["scene"] + ". "
            "Use the described age group exactly; do not substitute an elderly person. This must be a genuinely new photograph. "
            "Keep the product fully visible, physically supported, correctly scaled and structurally identical to the input. "
            "Exactly one sale-product set. No readable text, measurements, badges, inset circles, logos, watermarks, duplicated "
            "products, extra legs, extra supports, changed count, warped hardware, hovering, floating, impossible gravity or "
            "furniture-edge overhang. Square 1:1 polished realistic premium ecommerce photograph."
        )
        records.append({
            "D": d_value,
            "L0xx": old["L0xx"],
            "G": old["G"],
            "SKU": old["SKU"],
            "submitted_images": old["submitted_images"],
            "planning_evidence_not_submitted": old["planning_evidence_not_submitted"],
            "negative_evidence_not_submitted": negative,
            "human_rejection_reason": correction["reason"],
            "scene_recipe": correction["scene"],
            "product_lock": correction["lock"],
            "prompt": prompt,
            "status": "planned_user_authorized_redo_20260914",
            "review_status": "pending_generation",
            "writeback": "BLOCK_until_human_review_badge_OSS_release_gate",
        })

        v2["human_review_status"] = "rejected_user_20260914"
        v2["human_rejection_reason"] = correction["reason"]
        v2["eligible_for_badge_oss_writeback"] = False

    OUT.mkdir(parents=True, exist_ok=True)
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps({
        "schema": "temu-t1-human-rejection-lock/v1",
        "created_at": created,
        "source_batch": "agnes_v2_20260914",
        "record_count": len(lock_records),
        "records": lock_records,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    V2_MANIFEST.write_text(json.dumps(v2_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    PLAN.write_text(json.dumps({
        "schema": "yeahf-1999d-agnes-v3-product-only-redo4-plan/v1",
        "created_at": created,
        "record_count": len(records),
        "all_old_T1_not_submitted": True,
        "all_rejected_candidates_not_submitted": True,
        "age_mix": ["20s", "30s", "40s", "no_person"],
        "records": records,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"plan": str(PLAN), "lock": str(LOCK), "records": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
