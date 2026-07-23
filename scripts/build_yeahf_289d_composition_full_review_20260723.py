"""Build the full original-vs-redo review page for the 289-D composition batch."""
from __future__ import annotations

import importlib.util
from pathlib import Path


WORKSPACE = Path(r"C:\Users\Administrator\Documents\temu自动化")
BASE_BUILDER = WORKSPACE / "scripts" / "build_yeahf_289d_cangyuan_full_review_20260723.py"
LIBRARY_ROOT = Path(r"D:\temu素材库\T首图候选暂存")
BATCH_ROOT = LIBRARY_ROOT / "YeahF_2000D_苍猿GPTImage2_构图差异化重做闭环_20260723"
PLAN = (
    WORKSPACE
    / "outputs"
    / "yeahf_merged_d_0721"
    / "YeahF_2000D_289D_按L0xx构图差异化重做任务清单_20260723.json"
)
REVIEW_DIR = BATCH_ROOT / "review_289d_composition_20260723"


def main() -> None:
    spec = importlib.util.spec_from_file_location("yeahf_289d_base_review", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load review builder: {BASE_BUILDER}")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    builder.LIBRARY_ROOT = LIBRARY_ROOT
    builder.BATCH_ROOT = BATCH_ROOT
    builder.CANDIDATES = BATCH_ROOT / "candidates"
    builder.PLAN = PLAN
    builder.PROGRESS = BATCH_ROOT / "cangyuan_composition_progress_20260723.jsonl"
    builder.REVIEW_DIR = REVIEW_DIR
    builder.REVIEW_HTML = REVIEW_DIR / "YeahF_2000D_新增289D_构图差异化T1_原稿对照全量审核.html"
    builder.REVIEW_MANIFEST = REVIEW_DIR / "YeahF_2000D_新增289D_构图差异化T1_全量审核清单.json"
    builder.main()


if __name__ == "__main__":
    main()
