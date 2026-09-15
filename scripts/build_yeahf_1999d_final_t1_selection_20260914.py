"""Resolve one current final unbadged T1 candidate for every 1999 exact D."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


BASE = Path(r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810")
ROOT = BASE / "t1_cangyuan_current_workbook_t1"
REVIEW = Path(r"D:\Desktop\jit\HJXYmall\YeahF_1999D_T1审核结果.json")
REDO105 = ROOT / "human_redo105_20260813" / "cangyuan_human_redo105_manifest.json"
V2 = ROOT / "human_redo23_agnes_v2_20260914" / "agnes_v2_redo23_manifest.json"
V3 = ROOT / "human_redo4_agnes_v3_20260914" / "agnes_v3_redo4_manifest.json"
V4 = ROOT / "human_redo1_agnes_v4_l083_task_20260914" / "agnes_v4_l083_task_manifest.json"
OUT_DIR = ROOT / "finalization_20260914"
OUTPUT = OUT_DIR / "YeahF_1999D_final_unbadged_T1_selection_manifest.json"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def records(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return {str(row["D"]): row for row in payload["records"]}


def main() -> None:
    decisions = json.loads(REVIEW.read_text(encoding="utf-8-sig"))
    decision_by_d = {str(row["D"]): str(row["decision"]) for row in decisions}
    if len(decision_by_d) != 1999 or Counter(decision_by_d.values()) != {"approved": 1894, "rejected": 105}:
        raise RuntimeError("Expected the immutable 1894-approved/105-rejected first review")
    redo105 = records(REDO105)
    v2 = records(V2)
    v3 = records(V3)
    v4 = records(V4)
    if Counter(row.get("status") for row in redo105.values()) != {"validated": 82, "failed": 23}:
        raise RuntimeError("Redo105 reconciliation changed")

    v3_override = {"L077080826", "L081080846", "L081080910"}
    v4_override = {"L083080809"}
    selected = []
    for d_value in sorted(decision_by_d):
        if decision_by_d[d_value] == "approved":
            path = ROOT / "candidates" / d_value[:4] / f"{d_value}.png"
            source = "original_1999_human_approved"
            approval = "YeahF_1999D_T1审核结果.json:approved"
            provider = "Cangyuan"
        elif redo105[d_value].get("status") == "validated":
            path = Path(redo105[d_value]["local_path"])
            source = "redo105_cangyuan_validated"
            approval = "user_global_writeback_authorization_20260914"
            provider = "Cangyuan"
        elif d_value in v4_override:
            path = Path(v4[d_value]["local_path"])
            source = "agnes_v4_task_scene_user_approved"
            approval = "user_said_挺好的_then_全部回填_20260914"
            provider = "Agnes AI"
        elif d_value in v3_override:
            path = Path(v3[d_value]["local_path"])
            source = "agnes_v3_support_scale_fix_user_approved"
            approval = "user_said_挺好的_then_全部回填_20260914"
            provider = "Agnes AI"
        else:
            row = v2.get(d_value)
            if not row or row.get("status") != "validated":
                raise RuntimeError(f"No validated final candidate for rejected D: {d_value}")
            path = Path(row["local_path"])
            source = "agnes_v2_product_only_user_approved"
            approval = "user_said_其他整体非常好_then_全部回填_20260914"
            provider = "Agnes AI"
        if not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError(f"Selected file missing: {d_value}: {path}")
        selected.append({
            "D": d_value,
            "L0xx": d_value[:4],
            "source_kind": source,
            "provider": provider,
            "local_path": str(path),
            "sha256": sha256(path),
            "human_approval_evidence": approval,
            "badge_status": "not_applied",
            "oss_status": "not_uploaded",
            "workbook_writeback": False,
        })

    if len(selected) != 1999 or len({row["D"] for row in selected}) != 1999:
        raise RuntimeError("Final selection coverage/uniqueness failure")
    counts = Counter(row["source_kind"] for row in selected)
    expected = {
        "original_1999_human_approved": 1894,
        "redo105_cangyuan_validated": 82,
        "agnes_v2_product_only_user_approved": 19,
        "agnes_v3_support_scale_fix_user_approved": 3,
        "agnes_v4_task_scene_user_approved": 1,
    }
    if dict(counts) != expected:
        raise RuntimeError(f"Unexpected final source counts: {dict(counts)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "yeahf-1999d-final-unbadged-t1-selection/v1",
        "created_at": now(),
        "record_count": len(selected),
        "source_counts": dict(counts),
        "all_local_files_present": True,
        "all_hashes_recorded": True,
        "badge_applied": False,
        "oss_upload": False,
        "workbook_writeback": False,
        "release_status": "BLOCK_pending_badge_review_OSS_writeback_and_release_gate",
        "records": selected,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "records": len(selected), "source_counts": dict(counts)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
