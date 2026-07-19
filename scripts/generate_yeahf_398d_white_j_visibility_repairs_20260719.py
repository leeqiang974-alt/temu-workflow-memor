"""Generate local-only J repairs for white variants whose old RGB trim erased product pixels."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(r"C:\Users\Administrator\Documents\temu自动化")
OUT = ROOT / r"outputs\yeahf_title_dedup_20260709\yeahf_400d_refill_20260718"
SOURCE_MANIFEST = OUT / r"j_full_candidate_review_20260719\YeahF_398D_J_702行候选_manifest_20260719.json"
TARGET = OUT / "j_white_visibility_repair_20260719"
IMAGES = TARGET / "images"
MANIFEST = TARGET / "YeahF_398D_J_白色变体156行修复_manifest_20260719.json"

sys.path.insert(0, str(ROOT / "scripts"))
from generate_yeahf_400d_j_candidates import make_preview  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    records = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))["records"]
    selected = [
        row for row in records
        if row["L0xx"] != "L043" and "\\白\\白.png" in row["source_path"]
    ]
    if len(selected) != 156:
        raise RuntimeError(f"expected 156 confirmed white-source rows, got {len(selected)}")
    output = []
    for position, row in enumerate(selected, 1):
        source = Path(row["source_path"])
        target = IMAGES / row["L0xx"] / f"r{int(row['row']):04d}_{row['D']}_{row['SKU']}_white_visibility.jpg"
        info = make_preview(source, {key: str(row[key]) for key in ("row", "D", "G", "L0xx", "SKU")}, target)
        output.append({
            "row": row["row"],
            "D": row["D"],
            "G": row["G"],
            "SKU": row["SKU"],
            "source_path": str(source),
            "source_sha256": sha256(source),
            "local_candidate": str(target),
            "candidate_sha256": sha256(target),
            "bytes": info["bytes"],
            "status": "local-human-review-required",
            "reason": "preserve-authoritative-alpha + visible-two-color-macaron-gradient + subtle-perimeter + full-cell-fit",
        })
        if position % 20 == 0:
            print(json.dumps({"processed": position, "total": len(selected)}, ensure_ascii=False), flush=True)
    payload = {"count": len(output), "upload_performed": False, "writeback_performed": False, "records": output}
    TARGET.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"count": len(output), "manifest": str(MANIFEST)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
