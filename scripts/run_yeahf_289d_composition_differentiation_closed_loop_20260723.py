"""Run the approved 289-D composition-differentiation plan in a new asset root.

The mature Cangyuan submit/poll/download/validate loop is reused without splitting
its lifecycle. Existing first-pass candidates are never overwritten.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


WORKSPACE = Path(r"C:\Users\Administrator\Documents\temu自动化")
BASE_RUNNER = (
    WORKSPACE / "scripts" / "run_yeahf_2000d_cangyuan_closed_loop_20260723.py"
)
PLAN = (
    WORKSPACE
    / "outputs"
    / "yeahf_merged_d_0721"
    / "YeahF_2000D_289D_按L0xx构图差异化重做任务清单_20260723.json"
)
OUT = Path(
    r"D:\temu素材库\T首图候选暂存"
    r"\YeahF_2000D_苍猿GPTImage2_构图差异化重做闭环_20260723"
)


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "yeahf_2000d_cangyuan_base_runner", BASE_RUNNER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base runner: {BASE_RUNNER}")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    runner.PLAN = PLAN
    runner.OUT = OUT
    runner.CANDIDATES = OUT / "candidates"
    runner.PROGRESS = OUT / "cangyuan_composition_progress_20260723.jsonl"
    runner.MANIFEST = OUT / "cangyuan_composition_manifest_20260723.json"
    runner.ERROR_KEY = "yeahf2000_cangyuan_composition_differentiation_20260723"
    runner.main()


if __name__ == "__main__":
    main()
