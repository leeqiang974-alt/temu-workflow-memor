from __future__ import annotations

import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


BASE_SCRIPT = Path(
    os.environ.get(
        "BASE_IMAGE2_SCRIPT",
        r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\run_0616_2_low_cost_t_candidates.py",
    )
)
OUT = Path(
    os.environ.get(
        "OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702",
    )
)
WORKBOOK = Path(
    os.environ.get(
        "WORKBOOK",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702\0616-2_197_最终回传_硬校验修复_L051060505_C列删第1图_20260702.xlsx",
    )
)
SETS = int(os.environ.get("SETS", "3"))
WORKERS = int(os.environ.get("WORKERS", "3"))
LIMIT = int(os.environ.get("LIMIT", "0"))
MODE = os.environ.get("MODE", "plan")

PLAN_PATH = OUT / "candidate_plan_197x3.json"
RESULTS_PATH = OUT / "candidate_results_197x3.json"
PROGRESS_PATH = OUT / "candidate_progress_197x3.jsonl"


def load_base_module():
    os.environ["WORKBOOK"] = str(WORKBOOK)
    os.environ["OUT_DIR"] = str(OUT)
    spec = importlib.util.spec_from_file_location("image2_base_0616_2", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base image2 script: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["image2_base_0616_2"] = module
    spec.loader.exec_module(module)
    module.OUT = OUT
    module.GENERATED = OUT / "generated"
    module.PLAN_PATH = OUT / "base_candidate_plan.json"
    module.RESULTS_PATH = OUT / "base_candidate_results.json"
    module.PROGRESS_PATH = OUT / "base_candidate_progress.jsonl"
    return module


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def build_expanded_plan(module) -> list[dict]:
    by_set: dict[int, list[dict]] = {}
    original_shift = os.environ.get("SOURCE_SHIFT")
    for set_no in range(1, SETS + 1):
        os.environ["SOURCE_SHIFT"] = str(set_no - 1)
        by_set[set_no] = module.build_plan()
    if original_shift is None:
        os.environ.pop("SOURCE_SHIFT", None)
    else:
        os.environ["SOURCE_SHIFT"] = original_shift

    expanded: list[dict] = []
    for set_no, plan in by_set.items():
        for item in plan:
            original_d = item["d"]
            candidate_id = f"{original_d}__set{set_no}"
            item = dict(item)
            item["original_d"] = original_d
            item["candidate_id"] = candidate_id
            item["d"] = candidate_id
            item["set_no"] = set_no
            item["run_type"] = "image2_197x3_candidate_pool"
            item["scene_lane"] = f"set_{set_no}_scene_lane"
            item["color_lane"] = f"set_{set_no}_color_lane"
            item["composition_lane"] = f"set_{set_no}_composition_lane"
            item["prompt_append"] = (
                f"This is candidate set {set_no} of {SETS} for exact D {original_d}. "
                "It is a spare candidate pool for future replacement, not an immediate workbook writeback. "
                "Make this set visibly different from other sets for the same exact D: different source PNG where available, "
                "different scene mood, color palette, product scale, placement and prop arrangement. "
                "Do not reuse any deleted/rejected/wrong-color image and do not imitate old all_sku_tfirst or Ali single-SKU outputs."
            )
            expanded.append(item)

    save_json(PLAN_PATH, expanded)
    write_plan_summary(expanded)
    return expanded


def write_plan_summary(items: list[dict]) -> None:
    prefix_counts = Counter(item["prefix"] for item in items)
    source_counts = Counter((item["prefix"], item.get("source_id") or "") for item in items)
    rows = [
        "# 197 D x 3 image2 candidate plan",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- workbook: `{WORKBOOK}`",
        f"- output: `{OUT}`",
        f"- target_candidates: {len(items)}",
        f"- unique_original_d: {len(set(item['original_d'] for item in items))}",
        f"- sets: {SETS}",
        f"- provider/model: APIMart / gpt-image-2",
        f"- purpose: spare T-first candidate pool for future replacement, no workbook writeback",
        "",
        "## Prefix Counts",
        "",
        "| prefix | candidates |",
        "|---|---:|",
    ]
    for prefix in sorted(prefix_counts):
        rows.append(f"| {prefix} | {prefix_counts[prefix]} |")
    rows.extend(["", "## Source Rotation Sample", "", "| prefix | source_id | uses |", "|---|---|---:|"])
    for (prefix, source_id), count in sorted(source_counts.items())[:200]:
        rows.append(f"| {prefix} | {str(source_id).replace('|','/')} | {count} |")
    (OUT / "candidate_plan_197x3.md").write_text("\n".join(rows), encoding="utf-8")


def wrap_prompt_builder(module):
    original_build_prompt = module.build_prompt

    def build_prompt(item: dict, index_in_prefix: int, prefix_total: int) -> str:
        prompt = original_build_prompt(item, index_in_prefix, prefix_total)
        append = item.get("prompt_append")
        if append:
            prompt = f"{prompt} {append}"
        return prompt

    module.build_prompt = build_prompt


def existing_candidates() -> set[str]:
    done = set()
    for item in load_json(RESULTS_PATH, []):
        if item.get("candidate_id") and item.get("local_path") and Path(item["local_path"]).exists():
            done.add(item["candidate_id"])
    return done


def run_candidates(module, items: list[dict]) -> list[dict]:
    prefix_totals = Counter(item["prefix"] for item in items)
    prefix_seen = defaultdict(int)
    done = existing_candidates()
    queue = []
    for item in items:
        index = prefix_seen[item["prefix"]]
        prefix_seen[item["prefix"]] += 1
        if item["candidate_id"] in done:
            continue
        if not item.get("source_png"):
            continue
        queue.append((item, index, prefix_totals[item["prefix"]]))
    if LIMIT > 0:
        queue = queue[:LIMIT]

    results = load_json(RESULTS_PATH, [])
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(module.apimart_submit, item, index, total): item for item, index, total in queue}
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                result["status"] = result.get("status") or "ok"
            except Exception as error:
                result = {
                    "provider": "APIMart",
                    "model": "gpt-image-2",
                    "status": "error",
                    "error": str(error),
                    "d": item["candidate_id"],
                    "prefix": item["prefix"],
                    "rows": item.get("rows", []),
                    "source_png": item.get("source_png"),
                    "cost_usd_est": 0,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            result["candidate_id"] = item["candidate_id"]
            result["original_d"] = item["original_d"]
            result["set_no"] = item["set_no"]
            result["run_type"] = "image2_197x3_candidate_pool"
            result["scene_lane"] = item.get("scene_lane")
            result["color_lane"] = item.get("color_lane")
            result["composition_lane"] = item.get("composition_lane")
            results.append(result)
            with PROGRESS_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            save_json(RESULTS_PATH, results)
            print(
                f"{result.get('status')} {item['candidate_id']} {result.get('elapsed_sec','-')}s {result.get('error','')[:160]}",
                flush=True,
            )
    return results


def build_review(module) -> Path:
    module.PLAN_PATH = PLAN_PATH
    module.RESULTS_PATH = RESULTS_PATH
    module.PROGRESS_PATH = PROGRESS_PATH
    # The base review groups by d, and here d is candidate_id, which is exactly what we need.
    review = module.build_review()
    target = OUT / "0616_2_image2_197x3_t_candidates_review.html"
    if review != target:
        target.write_text(review.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    module = load_base_module()
    wrap_prompt_builder(module)
    items = build_expanded_plan(module)
    missing_source = sum(1 for item in items if not item.get("source_png"))
    summary = {
        "mode": MODE,
        "workbook": str(WORKBOOK),
        "out": str(OUT),
        "sets": SETS,
        "target_candidates": len(items),
        "unique_original_d": len(set(item["original_d"] for item in items)),
        "missing_source": missing_source,
        "workers": WORKERS,
        "limit": LIMIT,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    if MODE == "run":
        run_candidates(module, items)
    review = build_review(module)
    print(f"REVIEW={review}", flush=True)


if __name__ == "__main__":
    main()
