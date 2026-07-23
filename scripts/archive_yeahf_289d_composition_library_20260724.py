"""Archive the separate 289D composition-differentiation batch as a reusable asset library.

This batch is explicitly NOT the T1 writeback source for the YeahF 2000D workbook.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path


SOURCE = Path(r"D:\temu素材库\T首图候选暂存\YeahF_2000D_苍猿GPTImage2_构图差异化重做闭环_20260723")
TARGET = Path(r"D:\temu素材库\T首图已付费库\YeahF_289D_构图差异化素材库_20260724")
SOURCE_MANIFEST = SOURCE / "cangyuan_composition_manifest_20260723.json"
TARGET_MANIFEST = TARGET / "YeahF_289D_构图差异化素材库_归档清单_20260724.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    source_payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    records = source_payload["records"]
    if len(records) != 289 or any(record.get("status") != "validated" for record in records):
        raise RuntimeError("composition batch is not 289/289 validated")

    archive_records = []
    for record in records:
        source = Path(record["local_path"])
        if not source.is_file() or sha256(source) != record["output_sha256"]:
            raise RuntimeError(f"source asset changed or missing: {record['D']}")
        relative = Path("candidates") / record["L0xx"] / source.name
        target = TARGET / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file() and sha256(target) != record["output_sha256"]:
            raise RuntimeError(f"archive collision with different bytes: {target}")
        if not target.is_file():
            shutil.copy2(source, target)
        archive_records.append(
            {
                "D": record["D"],
                "L0xx": record["L0xx"],
                "source_path": str(source),
                "archive_path": str(target),
                "sha256": record["output_sha256"],
                "bytes": target.stat().st_size,
                "role": "REUSABLE_MATERIAL_LIBRARY_ONLY",
                "forbidden_writeback_batch": "YEAHF_2000D_INTERLEAVE_20260724",
            }
        )

    review_source = SOURCE / "review_289d_composition_20260723"
    review_target = TARGET / "review_289d_composition_20260723"
    if review_source.is_dir() and not review_target.exists():
        shutil.copytree(review_source, review_target)

    payload = {
        "schema": "yeahf-paid-t1-material-library/v1",
        "archived_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "count": len(archive_records),
        "source_batch": str(SOURCE),
        "source_manifest": str(SOURCE_MANIFEST),
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "library_role": "separate composition-differentiation material library",
        "workbook_writeback": "FORBIDDEN_FOR_YEAHF_2000D_INTERLEAVE_20260724",
        "authoritative_2000d_t1_source": str(
            Path(r"D:\temu素材库\T首图候选暂存\YeahF_2000D_苍猿GPTImage2_重新生成闭环_20260723")
        ),
        "records": archive_records,
    }
    TARGET.mkdir(parents=True, exist_ok=True)
    TARGET_MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if len(list((TARGET / "candidates").rglob("*.png"))) != 289:
        raise RuntimeError("archive PNG count is not 289")
    print(json.dumps({"status": "ARCHIVED", "count": 289, "target": str(TARGET), "manifest": str(TARGET_MANIFEST)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
