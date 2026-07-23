"""Bind the user's explicit approval of last night's original 289D batch to Release Guard."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


ROOT = Path(r"C:\Users\Administrator\Documents\temu自动化")
BATCH_ID = "YEAHF-2000D-INTERLEAVE-WRITEBACK-20260724"
STATE = ROOT / r"outputs\yeahf_merged_d_0721\release_guard_state_2000d_writeback_20260724"
FREEZE = STATE / "batches" / BATCH_ID / "freeze.json"
SOURCE_MANIFEST = Path(
    r"D:\temu素材库\T首图候选暂存\YeahF_2000D_苍猿GPTImage2_重新生成闭环_20260723"
    r"\cangyuan_closed_loop_manifest_20260723.json"
)
OUT = ROOT / r"outputs\yeahf_merged_d_0721\release_guard_2000d_writeback_20260724\t1_approval.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    records = manifest["records"]
    if len(records) != 289 or any(record.get("status") != "validated" for record in records):
        raise RuntimeError("approved source batch is not 289/289 validated")
    assets = {}
    for record in records:
        local = Path(record["local_path"]).resolve()
        digest = record["output_sha256"]
        if not local.is_file() or sha256(local) != digest:
            raise RuntimeError(f"approved asset changed: {record['D']}")
        assets[str(local)] = digest
    payload = {
        "schema": "temu-release-human-approval/v1",
        "batch_id": BATCH_ID,
        "decision": "APPROVED",
        "approver": "User",
        "approval_basis": "User correction: 昨晚已经通过了一批289的图，并且让你把289的表行穿插填入2000总表。",
        "approved_batch": str(SOURCE_MANIFEST.parent),
        "workbook_sha256": freeze["workbook_sha256"],
        "policy_sha256": freeze["policy_sha256"],
        "asset_paths": assets,
        "created_at": time.time(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "APPROVED", "assets": len(assets), "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
