"""Apply the 18 local T1 redos to review artifacts only."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(r"C:\Users\Administrator\Documents\temu自动化")
REDO = Path(r"D:\temu素材库\T首图候选暂存\YeahF_398D_用户重做_20260719\cangyuan_user_redo_manifest_20260719.json")
sys.path.insert(0, str(ROOT / "scripts"))
import build_yeahf_398d_t1_badged_local_review_20260719 as review  # noqa: E402


def main() -> None:
    manifest = json.loads(review.MANIFEST.read_text(encoding="utf-8"))
    records = {str(row["D"]): row for row in manifest["records"]}
    redos = json.loads(REDO.read_text(encoding="utf-8"))["records"]
    replaced = []
    for redo in redos:
        if redo.get("status") != "completed":
            continue
        d_value = str(redo["D"])
        base = Path(redo["local_path"])
        inset = review.choose_inset(d_value)
        rendered, corner = review.render(d_value, base, inset)
        old = records[d_value]
        previous_base = old.get("base_path")
        old.update({
            "provider": "苍猿 gpt-image-2 用户重做",
            "base_path": str(base),
            "base_sha256": review.sha256(base),
            "inset_path": str(inset),
            "inset_sha256": review.sha256(inset),
            "corner": corner,
            "rendered_path": str(rendered),
            "rendered_sha256": review.sha256(rendered),
            "status": "local-user-redo-review-only",
            "redo_manifest": str(REDO),
            "redo_task_id": redo.get("task_id"),
            "previous_base_path": previous_base,
        })
        replaced.append(d_value)
    ordered = [records[str(row["D"])] for row in manifest["records"]]
    manifest["records"] = ordered
    manifest["user_redo_20260719"] = {
        "count": len(replaced), "D": replaced, "source_manifest": str(REDO),
        "oss_upload": False, "writeback": False,
    }
    review.MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    review.build_review(ordered)
    print(json.dumps({"replaced": len(replaced), "D": replaced, "review": str(review.REVIEW)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
