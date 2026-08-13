"""Build an immutable preflight ledger from the 1999-D human T1 review.

This is deliberately not a paid generation plan.  It records rejected candidates,
their original current-workbook T1 anchors, human reason categories, and whether an
exact-D product-material authority is still required before a redo may be submitted.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(
    r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810"
    r"\t1_cangyuan_current_workbook_t1"
)
REVIEW = Path(r"D:\Desktop\jit\HJXYmall\YeahF_1999D_T1审核结果.json")
PLAN = ROOT / "YeahF_1999D_当前表T1参考_Cangyuan闭环任务计划.json"
OUTPUT = ROOT / "YeahF_1999D_T1人工驳回_重做前置清单_20260813.json"

APPROVED_OVERRIDES = {"L042080933", "L042080944"}
HIGH_RISK_REASONS = {
    "L081": "wrong_product_appearance_inheritance",
    "L043": "product_appearance_changed",
    "L072": "product_appearance_hallucinated",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    review_rows = json.loads(REVIEW.read_text(encoding="utf-8-sig"))
    plan_rows = json.loads(PLAN.read_text(encoding="utf-8-sig"))["records"]
    by_d = {str(row["target_D"]): row for row in plan_rows}
    rejected = [row for row in review_rows if row.get("decision") == "rejected"]

    if len(review_rows) != 1999 or len({row.get("D") for row in review_rows}) != 1999:
        raise RuntimeError("review must contain exactly 1999 unique D records")
    if any(row.get("decision") == "pending" for row in review_rows):
        raise RuntimeError("review still contains pending decisions")
    if any(
        next(row for row in review_rows if row.get("D") == d).get("decision") != "approved"
        for d in APPROVED_OVERRIDES
    ):
        raise RuntimeError("explicitly approved L042 overrides are not approved")

    records: list[dict] = []
    for decision in rejected:
        d = str(decision["D"])
        source = by_d[d]
        l0xx = str(decision["L0xx"])
        anchor = Path(str(source["reference_image"]))
        candidate = ROOT / "candidates" / l0xx / f"{d}.png"
        if not anchor.is_file() or not candidate.is_file():
            raise RuntimeError(f"missing anchor/candidate for {d}")
        reason = HIGH_RISK_REASONS.get(l0xx, "human_rejected_reason_not_yet_classified")
        product_required = l0xx in HIGH_RISK_REASONS
        records.append(
            {
                "D": d,
                "L0xx": l0xx,
                "decision": "rejected",
                "rejection_reason": reason,
                "negative_evidence_candidate": str(candidate),
                "negative_evidence_sha256": sha256(candidate),
                "scene_anchor": str(anchor),
                "scene_anchor_sha256": sha256(anchor),
                "scene_anchor_role": "current_workbook_T1_scene_composition_only",
                "verified_product_material_required": product_required,
                "verified_product_material": None,
                "verified_product_material_sha256": None,
                "product_material_status": (
                    "BLOCK_unresolved_exact_D_G_SKU_visual_authority"
                    if product_required
                    else "BLOCK_reason_and_product_authority_not_yet_classified"
                ),
                "reuse_rejected_candidate_forbidden": True,
                "paid_submission_status": "BLOCK",
            }
        )

    payload = {
        "schema": "yeahf-1999d-t1-human-rejection-preflight/v1",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "review_file": str(REVIEW),
        "review_sha256": sha256(REVIEW),
        "review_counts": dict(Counter(row.get("decision") for row in review_rows)),
        "explicit_approved_overrides": sorted(APPROVED_OVERRIDES),
        "rejected_count": len(records),
        "rejected_by_L0xx": dict(sorted(Counter(row["L0xx"] for row in records).items())),
        "rejected_by_reason": dict(
            sorted(Counter(row["rejection_reason"] for row in records).items())
        ),
        "policy": {
            "human_rejected_candidate_is_negative_evidence": True,
            "rejected_candidate_may_not_be_reused": True,
            "L081_same_L0xx_or_sibling_D_product_inheritance_forbidden": True,
            "L043_L072_product_appearance_locked": True,
            "paid_retry_requires_user_authorization": True,
            "workbook_writeback": "BLOCK_until_redo_approval_badge_OSS_and_release_gate",
        },
        "paid_submission_status": "BLOCK",
        "records": records,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "review_counts": payload["review_counts"],
                "rejected_count": len(records),
                "rejected_by_reason": payload["rejected_by_reason"],
                "paid_submission_status": "BLOCK",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
