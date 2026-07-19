"""Freeze user-approved 398-D T1/J assets, upload durable assets, and emit URL maps.

This script does not mutate any workbook. Spreadsheet writeback is handled separately
through artifact-tool after the upload maps and approval evidence are frozen.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path


ROOT = Path(r"C:\Users\Administrator\Documents\temu自动化")
OUT = ROOT / r"outputs\yeahf_title_dedup_20260709\yeahf_400d_refill_20260718"
GUARD = OUT / r"release_candidates\YF398-20260719-SORTED-JT1-V1"
EVIDENCE = GUARD / "evidence"
SOURCE = OUT / "YeahF_398D_按L0xx顺位归组_待J_T1回填_20260719.xlsx"
T_MANIFEST = OUT / r"t1_badged_local_review_20260719\YeahF_398D_T1_角标本地候选_manifest_20260719.json"
J_MANIFEST = OUT / r"j_full_candidate_review_20260719\YeahF_398D_J_702行候选_manifest_20260719.json"
T_DECISIONS = EVIDENCE / "t1_user_approved_20260719.json"
J_DECISIONS = EVIDENCE / "j_user_approved_20260719.json"
T_APPROVAL = EVIDENCE / "t1_approval.json"
BADGE_APPROVAL = EVIDENCE / "badge_approval.json"
J_APPROVED_MANIFEST = EVIDENCE / "j_manifest.json"
T_URLS = EVIDENCE / "t1_oss_urls.json"
J_URLS = EVIDENCE / "j_oss_urls.json"
BATCH_ID = "YF398-20260719-SORTED-JT1-V1"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import finalize_yeahf_398d_after_review_20260719 as finalizer

    t_manifest, j_manifest = finalizer.validate_manifests()
    workbook_sha = sha256(SOURCE)
    old_approval = read_json(EVIDENCE / "badge_approval_pending.json")
    policy_sha = old_approval["policy_sha256"]
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    t_decisions = {
        record["D"]: {
            "decision": "approve",
            "approver": "User",
            "approved_at": now,
            "asset_path": record["rendered_path"],
            "asset_sha256": record["rendered_sha256"],
            "basis": "User instruction: ok，t1，j，oss回填，然后启动审查机制",
        }
        for record in t_manifest["records"]
    }
    j_decisions = {
        record["decision_key"]: {
            "decision": "approve",
            "approver": "User",
            "approved_at": now,
            "row": int(record["row"]),
            "D": record["D"],
            "G": record["G"],
            "SKU": record["SKU"],
            "source_path": record["source_path"],
            "candidate_J": record["candidate_J"],
            "match_mode": record["match_mode"],
            "warning": record.get("warning", ""),
            "basis": "User instruction: ok，t1，j，oss回填，然后启动审查机制",
        }
        for record in j_manifest["records"]
    }
    write_json(T_DECISIONS, {"batch_id": BATCH_ID, "decisions": t_decisions})
    write_json(J_DECISIONS, {"batch_id": BATCH_ID, "decisions": j_decisions})

    base_assets = {record["base_path"]: record["base_sha256"] for record in t_manifest["records"]}
    badge_assets = {record["rendered_path"]: record["rendered_sha256"] for record in t_manifest["records"]}
    approval_common = {
        "schema": "temu-release-human-approval/v1",
        "batch_id": BATCH_ID,
        "decision": "APPROVED",
        "approver": "User",
        "approved_at": now,
        "workbook_sha256": workbook_sha,
        "policy_sha256": policy_sha,
        "approval_basis": "Explicit user approval in current task after focused T1 redo review; user requested T1/J OSS writeback and guard execution.",
    }
    write_json(T_APPROVAL, {**approval_common, "asset_paths": base_assets})
    write_json(BADGE_APPROVAL, {**approval_common, "asset_paths": badge_assets})

    t_urls = finalizer.upload_t1(t_manifest["records"])
    j_urls = finalizer.final_j_map(j_manifest)
    write_json(T_URLS, {"batch_id": BATCH_ID, "count": len(t_urls), "items": t_urls})
    write_json(J_URLS, {"batch_id": BATCH_ID, "count": len(j_urls), "items": {str(k): v for k, v in j_urls.items()}})

    pending = read_json(EVIDENCE / "j_manifest_pending_human_review.json")
    by_row = {int(item["row"]): item for item in pending["rows"]}
    approved_rows = []
    for record in j_manifest["records"]:
        row_number = int(record["row"])
        detail = dict(by_row[row_number])
        detail["oss_url"] = j_urls[row_number]
        detail["AC_previewImgUrls"] = j_urls[row_number]
        detail["visual_decision"] = "APPROVED"
        detail["visual_approver"] = "User"
        detail["approved_at"] = now
        approved_rows.append(detail)
    write_json(J_APPROVED_MANIFEST, {
        "schema": "temu-release-j-manifest/v1",
        "batch_id": BATCH_ID,
        "workbook_sha256": workbook_sha,
        "physical_rows": [{"row": x["row"], "D": x["D"], "G": x["G"], "SKU": x["SKU"]} for x in approved_rows],
        "rows": approved_rows,
        "summary": {
            "physical_rows": len(approved_rows),
            "approved": len(approved_rows),
            "pending": 0,
            "t1_uploaded": len(t_urls),
            "j_urls": len(j_urls),
        },
    })
    print(json.dumps({
        "status": "complete",
        "t1_approved": len(t_decisions),
        "j_approved": len(j_decisions),
        "t1_urls": len(t_urls),
        "j_urls": len(j_urls),
        "t1_approval": str(T_APPROVAL),
        "badge_approval": str(BADGE_APPROVAL),
        "j_manifest": str(J_APPROVED_MANIFEST),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
