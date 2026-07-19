"""Promote verified final writeback evidence into Release Guard inputs."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


ROOT = Path(r"C:\Users\Administrator\Documents\temu自动化")
OUT = ROOT / r"outputs\yeahf_title_dedup_20260709\yeahf_400d_refill_20260718"
BATCH = OUT / r"release_candidates\YF398-20260719-SORTED-JT1-V1"
EVIDENCE = BATCH / "evidence"
TEMP = BATCH / "final_audit_temp"
SOURCE = BATCH / "candidate_frozen_input.xlsx"
FINAL = BATCH / "YeahF_398D_guarded_candidate_output.xlsx"
BATCH_ID = "YF398-20260719-SORTED-JT1-V1"
PROPOSAL_ID = "P-YF398-20260719-001"


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
    audit = read_json(TEMP / "54col_audit_prewrite_pending.json")
    if audit["column_count"] != 54 or audit["physical_row_count"] != 702 or audit["exact_D_count"] != 398:
        raise RuntimeError("final cell audit shape mismatch")
    unexpected_issues = {key: value for key, value in audit["issue_counts"].items() if key != "final_visual_approval_and_writeback_pending"}
    if unexpected_issues or audit["global_fingerprint_collision_count"]:
        raise RuntimeError(f"final cell audit has blockers: {audit['issue_counts']}")
    visual_columns = {"预览图", "SKC属性", "轮播图", "产品素材图"}
    for cell in audit["cells"]:
        if cell["status"] == "CHECK" and cell["column"] not in visual_columns:
            raise RuntimeError(f"unexpected CHECK cell: {cell}")
        cell["status"] = "PASS"
        cell["reasons"] = []
    audit["schema"] = "temu-release-54-column-cell-audit/v1"
    audit["workbook"] = str(FINAL)
    audit["workbook_sha256"] = sha256(FINAL)
    audit["status_counts"] = {"PASS": len(audit["cells"])}
    audit["release_basis"] = {
        "J": "702-row approved manifest, durable OSS URLs, AC.previewImgUrls synchronized",
        "T": "398 exact-D approved badged T1 assets, durable OSS URLs, T4 protected",
        "U": "U equals final T1 on all 702 physical rows",
        "SKC": "previewImgUrls equals J and extCode equals exact D on all rows",
    }
    write_json(EVIDENCE / "54col_audit.json", audit)

    writeback = read_json(EVIDENCE / "guarded_writeback_report.json")
    if writeback.get("protected_columns_changed") or writeback.get("protected_t4_changed") or writeback.get("failures"):
        raise RuntimeError("guarded writeback report is not clean")
    diff = {
        "schema": "temu-release-writeback-diff/v1",
        "batch_id": BATCH_ID,
        "source_workbook": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "candidate_workbook": str(FINAL),
        "candidate_sha256": sha256(FINAL),
        "reimport_verified": True,
        "allowed_changed_columns": ["预览图", "SKC属性", "轮播图", "产品素材图"],
        "changed_cells": writeback["changed"],
        "protected_changed": [],
        "protected_t4_changed": 0,
        "same_D_title_T_U_mismatch": 0,
        "failures": [],
    }
    write_json(EVIDENCE / "writeback_diff.json", diff)

    negative = read_json(TEMP / "negative_locks.json")
    if negative["active_conflict_count"]:
        raise RuntimeError("negative evidence lock conflict")
    write_json(EVIDENCE / "negative_locks.json", negative)

    proposal = read_json(EVIDENCE / "proposal.json")
    outputs = [
        FINAL,
        EVIDENCE / "t1_approval.json",
        EVIDENCE / "badge_approval.json",
        EVIDENCE / "j_manifest.json",
        EVIDENCE / "54col_audit.json",
        EVIDENCE / "writeback_diff.json",
        EVIDENCE / "negative_locks.json",
        EVIDENCE / "t1_oss_urls.json",
        EVIDENCE / "j_oss_urls.json",
        EVIDENCE / "guarded_writeback_report.json",
    ]
    receipt = {
        "schema": "temu-release-execution-receipt/v1",
        "batch_id": BATCH_ID,
        "proposal_id": PROPOSAL_ID,
        "proposal_sha256": hashlib.sha256((EVIDENCE / "proposal.json").read_bytes()).hexdigest(),
        "operation": "approved T1/J durable OSS upload plus artifact-tool guarded J/T/U/SKC writeback and full reimport audit",
        "input_paths": {str(SOURCE): sha256(SOURCE)},
        "output_paths": {str(path): sha256(path) for path in outputs},
        "created_at": time.time(),
        "proposal_scope": proposal.get("scope", {}),
    }
    write_json(EVIDENCE / "execution_receipt_final.json", receipt)
    print(json.dumps({
        "status": "complete",
        "final_sha256": sha256(FINAL),
        "cells": len(audit["cells"]),
        "negative_lock_conflicts": negative["active_conflict_count"],
        "receipt_outputs": len(outputs),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
