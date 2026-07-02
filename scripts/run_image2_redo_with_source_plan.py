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
OUT = Path(os.environ["OUT_DIR"])
SOURCE_PLAN_PATH = Path(os.environ["SOURCE_PLAN_PATH"])
FEEDBACK_LOCK_PATH = Path(os.environ["FEEDBACK_LOCK_PATH"])
ONLY_D_VALUES = [value.strip() for value in os.environ.get("ONLY_D_VALUES", "").split(",") if value.strip()]
WORKERS = int(os.environ.get("WORKERS", "1") or "1")
MODE = os.environ.get("MODE", "plan")


def load_base_module():
    spec = importlib.util.spec_from_file_location("base_image2_candidates", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base image2 script: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["base_image2_candidates"] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_source_plan(plan: list[dict], source_plan: dict, feedback_lock: dict) -> list[dict]:
    by_d = source_plan.get("items", {})
    feedback_by_d = feedback_lock.get("feedback", {})
    selected = []
    for item in plan:
        d = item["d"]
        if ONLY_D_VALUES and d not in ONLY_D_VALUES:
            continue
        override = by_d.get(d)
        if not override:
            continue
        item = dict(item)
        item["source_png"] = override["source_png"]
        item["source_kind"] = override.get("source_kind")
        item["source_id"] = override.get("source_id")
        item["source_library_rel"] = override.get("source_library_rel")
        item["redo_of"] = override.get("redo_of")
        item["redo_reason_cn"] = feedback_by_d.get(d, {}).get("feedback", "")
        item["scene_lane"] = override.get("scene_lane", "")
        item["color_lane"] = override.get("color_lane", "")
        item["composition_lane"] = override.get("composition_lane", "")
        item["product_lock"] = override.get("product_lock", "")
        item["redo_prompt_append"] = build_prompt_append(item)
        selected.append(item)
    return selected


def build_prompt_append(item: dict) -> str:
    chunks = [
        "This is an image2 redo after human review failed the previous output.",
        f"Human review feedback in Chinese: {item.get('redo_reason_cn') or 'redo requested by reviewer'}.",
        f"Assigned color palette lane: {item.get('color_lane')}.",
        f"Assigned scene lane: {item.get('scene_lane')}.",
        f"Assigned composition lane: {item.get('composition_lane')}.",
    ]
    if item.get("product_lock"):
        chunks.append(f"Extra product-specific lock: {item['product_lock']}.")
    chunks.append(
        "Do not repeat the previous failed image. The source PNG was deliberately changed for material differentiation; "
        "also make the scene, color palette, product scale, placement, and composition visibly different from sibling images."
    )
    return " ".join(chunks)


def wrap_prompt_builder(module):
    original = module.build_prompt

    def build_prompt(item: dict, index_in_prefix: int, prefix_total: int) -> str:
        prompt = original(item, index_in_prefix, prefix_total)
        append = item.get("redo_prompt_append")
        if append:
            prompt = f"{prompt} {append}"
        return prompt

    module.build_prompt = build_prompt


def write_allocation_artifacts(items: list[dict], feedback_lock: dict, source_plan: dict) -> None:
    rows = []
    for item in items:
        rows.append(
            {
                "d": item["d"],
                "prefix": item["prefix"],
                "rows": item.get("rows", []),
                "source_png": item.get("source_png"),
                "source_kind": item.get("source_kind"),
                "source_id": item.get("source_id"),
                "redo_reason_cn": item.get("redo_reason_cn"),
                "scene_lane": item.get("scene_lane"),
                "color_lane": item.get("color_lane"),
                "composition_lane": item.get("composition_lane"),
                "product_lock": item.get("product_lock"),
            }
        )
    save_json(OUT / "redo_source_allocation_plan.json", {"items": rows})

    md = [
        "# image2 redo source allocation plan",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- target_count: {len(items)}",
        f"- source_plan: `{SOURCE_PLAN_PATH}`",
        f"- feedback_lock: `{FEEDBACK_LOCK_PATH}`",
        "",
        "| D | source_id | scene lane | color lane | composition | feedback |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        md.append(
            "| {d} | {source_id} | {scene_lane} | {color_lane} | {composition_lane} | {redo_reason_cn} |".format(
                **{key: str(value or "").replace("|", "/") for key, value in row.items()}
            )
        )
    (OUT / "redo_source_allocation_plan.md").write_text("\n".join(md), encoding="utf-8")


def run_items(module, items: list[dict]) -> list[dict]:
    prefix_totals = Counter(item["prefix"] for item in items)
    prefix_seen = defaultdict(int)
    queue = []
    for item in items:
        index = prefix_seen[item["prefix"]]
        prefix_seen[item["prefix"]] += 1
        queue.append((item, index, prefix_totals[item["prefix"]]))

    results_path = OUT / "candidate_results.json"
    progress_path = OUT / "candidate_progress.jsonl"
    results = load_json(results_path) if results_path.exists() else []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(module.apimart_submit, item, index, total): item for item, index, total in queue}
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                result["run_type"] = "image2_redo_after_review"
                result["redo_of"] = item.get("redo_of")
                result["redo_reason_cn"] = item.get("redo_reason_cn")
                result["scene_lane"] = item.get("scene_lane")
                result["color_lane"] = item.get("color_lane")
                result["composition_lane"] = item.get("composition_lane")
            except Exception as error:
                result = {
                    "provider": "APIMart",
                    "model": "gpt-image-2",
                    "run_type": "image2_redo_after_review",
                    "d": item["d"],
                    "prefix": item["prefix"],
                    "rows": item.get("rows", []),
                    "source_png": item.get("source_png"),
                    "source_kind": item.get("source_kind"),
                    "source_id": item.get("source_id"),
                    "redo_of": item.get("redo_of"),
                    "redo_reason_cn": item.get("redo_reason_cn"),
                    "scene_lane": item.get("scene_lane"),
                    "color_lane": item.get("color_lane"),
                    "composition_lane": item.get("composition_lane"),
                    "status": "error",
                    "error": str(error),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "cost_usd_est": 0,
                }
            results.append(result)
            with progress_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            save_json(results_path, results)
            print(f"{result.get('status','ok')} {result['d']} {result.get('elapsed_sec','-')}s {result.get('error','')[:120]}", flush=True)
    return results


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    module = load_base_module()
    wrap_prompt_builder(module)
    source_plan = load_json(SOURCE_PLAN_PATH)
    feedback_lock = load_json(FEEDBACK_LOCK_PATH)
    full_plan = module.build_plan()
    items = apply_source_plan(full_plan, source_plan, feedback_lock)
    write_allocation_artifacts(items, feedback_lock, source_plan)
    print(json.dumps({"mode": MODE, "out": str(OUT), "items": len(items), "workers": WORKERS}, ensure_ascii=False, indent=2))
    if MODE == "run":
        run_items(module, items)


if __name__ == "__main__":
    main()
