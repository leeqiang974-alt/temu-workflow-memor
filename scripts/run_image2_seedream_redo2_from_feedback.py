from __future__ import annotations

import html
import importlib.util
import json
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


BASE_SCRIPT = Path(
    os.environ.get(
        "BASE_IMAGE2_SCRIPT",
        r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\run_0616_2_low_cost_t_candidates.py",
    )
)
ORIGINAL_OUT = Path(
    os.environ.get(
        "ORIGINAL_OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702",
    )
)
SEEDREAM_OUT = Path(
    os.environ.get(
        "SEEDREAM_OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_197x3_redo_feedback_20260703",
    )
)
OUT = Path(
    os.environ.get(
        "OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_seedream_redo2_3_20260703",
    )
)
MODE = os.environ.get("MODE", "plan")
WORKERS = int(os.environ.get("WORKERS", "2") or "2")

ORIGINAL_PLAN_PATH = ORIGINAL_OUT / "candidate_plan_197x3.json"
ORIGINAL_RESULTS_PATH = ORIGINAL_OUT / "candidate_results_197x3.json"
SEEDREAM_RESULTS_PATH = SEEDREAM_OUT / "seedream_fallback_results.json"
PLAN_PATH = OUT / "image2_seedream_redo2_3_plan.json"
RESULTS_PATH = OUT / "image2_seedream_redo2_3_results.json"
PROGRESS_PATH = OUT / "image2_seedream_redo2_3_progress.jsonl"
REVIEW_PATH = OUT / "0616_2_image2_seedream_redo2_3_review.html"
RAW_FEEDBACK_PATH = OUT / "seedream_16_review_feedback_redo2_raw_20260703.json"
LOCK_PATH = OUT / "feedback_lock_seedream_16_review_redo2_20260703.json"


RAW_FEEDBACK = {
    "review": "0616_2_seedream_from_redo_61_feedback_16_review",
    "exported_at": "2026-07-03T04:28:11.281Z",
    "feedback": {
        "L043060503__set1__redo1": {
            "decision": "redo",
            "feedback": "这个png废掉，用其他png用image2，换进来。",
            "ts": "2026-07-03T04:27:51.903Z",
        },
        "L043060503__set3__redo1": {
            "decision": "redo",
            "feedback": "这个png废掉，用其他png用image2，换进来",
            "ts": "2026-07-03T04:27:54.305Z",
        },
        "L091060506__set2__redo1": {
            "decision": "redo",
            "feedback": "不要做这种带顶部的图片，image2",
            "ts": "2026-07-03T04:28:04.320Z",
        },
    },
}

SOURCE_OVERRIDES = {
    "L043060503__set1__redo1__redo2_image2": {
        "source_id": "L043_NEW_0001",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L043\kept_0021_0021_L043_NEW_0001_kept.png",
        "source_kind": "kept_cutout",
        "source_library_rel": "kept_plus_sku_variant_plus_retry_new_original_library/L043/kept_0021_0021_L043_NEW_0001_kept.png",
    },
    "L043060503__set3__redo1__redo2_image2": {
        "source_id": "L043_NEW_0025",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L043\kept_0030_0030_L043_NEW_0025_kept.png",
        "source_kind": "kept_cutout",
        "source_library_rel": "kept_plus_sku_variant_plus_retry_new_original_library/L043/kept_0030_0030_L043_NEW_0025_kept.png",
    },
    "L091060506__set2__redo1__redo2_image2": {
        "source_id": "L091_T_0030",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L091\kept_0187_0187_L091_T_0030_kept.png",
        "source_kind": "kept_cutout",
        "source_library_rel": "kept_plus_sku_variant_plus_retry_new_original_library/L091/kept_0187_0187_L091_T_0030_kept.png",
    },
}


def load_json(path: Path, default=None):
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_base_module():
    os.environ["OUT_DIR"] = str(OUT)
    spec = importlib.util.spec_from_file_location("base_image2_0616_2", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base image2 script: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["base_image2_0616_2"] = module
    spec.loader.exec_module(module)
    module.OUT = OUT
    module.GENERATED = OUT / "generated"
    return module


def wrap_prompt_builder(module):
    original = module.build_prompt

    def build_prompt(item: dict, index_in_prefix: int, prefix_total: int) -> str:
        prompt = original(item, index_in_prefix, prefix_total)
        append = item.get("redo_prompt_append")
        return f"{prompt} {append}" if append else prompt

    module.build_prompt = build_prompt


def seedream_records_by_d() -> dict[str, dict]:
    return {item.get("d"): item for item in load_json(SEEDREAM_RESULTS_PATH, []) if item.get("d")}


def original_plan_by_candidate() -> dict[str, dict]:
    return {item.get("candidate_id"): item for item in load_json(ORIGINAL_PLAN_PATH, []) if item.get("candidate_id")}


def original_results_by_candidate() -> dict[str, dict]:
    return {item.get("candidate_id"): item for item in load_json(ORIGINAL_RESULTS_PATH, []) if item.get("candidate_id")}


def original_candidate_id(seedream_id: str) -> str:
    return seedream_id.replace("__redo1", "")


def prompt_append(item: dict) -> str:
    if item["prefix"] == "L043":
        return (
            "Targeted redo after Seedream failed human review. The reviewer said the previous PNG is废掉 and must be locked out. "
            "Do not use or imitate source_id L043_NEW_0008. Use the newly assigned PNG only. "
            "Freeze the folding board outline, all circular holes, the small center hole, rear raised detail, front raised detail, panel seams, thin plastic thickness, material and scale. "
            "Do not turn it into a tray, pad, phone holder, flat board without holes, or generic clothing stack. "
            "Image2/APIMart is explicitly requested for this replacement."
        )
    return (
        "Targeted redo after Seedream failed human review. The reviewer said: 不要做这种带顶部的图片，image2. "
        "Create a strict front-facing product view in a closet/wardrobe scene. Do not use overhead, top-down, high-angle, or prominent top-display composition. "
        "Keep the front drawer surface, transparent front door, black handle, white frame and stack structure visible. "
        "The top edge may be minimally visible only as the natural upper border; do not highlight, enlarge, invent, or display a top lid/platform/groove as the main feature. "
        "Image2/APIMart is explicitly requested for this replacement."
    )


def build_plan() -> list[dict]:
    original_plan = original_plan_by_candidate()
    original_results = original_results_by_candidate()
    seedream_results = seedream_records_by_d()
    items = []
    for seedream_id, fb in RAW_FEEDBACK["feedback"].items():
        redo_id = f"{seedream_id}__redo2_image2"
        base_id = original_candidate_id(seedream_id)
        base = dict(original_plan[base_id])
        override = SOURCE_OVERRIDES[redo_id]
        base.update(override)
        base["d"] = redo_id
        base["candidate_id"] = redo_id
        base["original_d"] = seedream_results.get(seedream_id, {}).get("d", seedream_id).split("__")[0]
        base["failed_seedream_id"] = seedream_id
        base["failed_original_candidate_id"] = base_id
        base["redo_reason_cn"] = fb["feedback"]
        base["redo_of_seedream"] = seedream_results.get(seedream_id, {}).get("local_image")
        base["redo_of_image2"] = original_results.get(base_id, {}).get("local_path")
        base["old_seedream_source_id"] = seedream_results.get(seedream_id, {}).get("source_id")
        base["locked_bad_source_ids"] = ["L043_NEW_0008"] if base["prefix"] == "L043" else []
        base["source_selection_note"] = "manual_override_from_seedream_review_feedback"
        base["source_changed"] = True
        base["run_type"] = "image2_redo2_after_seedream_review_feedback"
        base["scene_lane"] = "closet/laundry folding-board scene with holes clear" if base["prefix"] == "L043" else "strict front-facing closet drawer organizer scene, no top-down view"
        base["color_lane"] = "neutral daylight, realistic closet/laundry colors" if base["prefix"] == "L043" else "cool white closet daylight, low angle front view"
        base["composition_lane"] = "product large enough to inspect holes and panel detail" if base["prefix"] == "L043" else "front-only catalog lifestyle composition, product about 34 percent of image height"
        base["redo_prompt_append"] = prompt_append(base)
        items.append(base)
    save_json(RAW_FEEDBACK_PATH, RAW_FEEDBACK)
    save_json(
        LOCK_PATH,
        {
            "review": RAW_FEEDBACK["review"],
            "locked_at": datetime.now().isoformat(timespec="seconds"),
            "rule": "Only these three Seedream fallback failures are reworked. L043_NEW_0008 is locked out for L043060503 redo2.",
            "counts": {"total": 3, "redo": 3},
            "feedback": RAW_FEEDBACK["feedback"],
            "locked_bad_sources": {"L043": ["L043_NEW_0008"]},
        },
    )
    save_json(PLAN_PATH, items)
    write_plan_md(items)
    return items


def write_plan_md(items: list[dict]) -> None:
    rows = [
        "# image2 redo2 from Seedream review feedback",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- output: `{OUT}`",
        f"- provider/model: APIMart / gpt-image-2",
        f"- count: {len(items)}",
        "- no Excel writeback, no final product upload",
        "",
        "| redo2 id | original D | prefix | failed Seedream | locked bad source | new source | feedback |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in items:
        locked = ",".join(item.get("locked_bad_source_ids") or [])
        rows.append(
            f"| {item['candidate_id']} | {item['original_d']} | {item['prefix']} | {item['failed_seedream_id']} | {locked} | {item.get('source_id')} | {item.get('redo_reason_cn','').replace('|','/')} |"
        )
    (OUT / "image2_seedream_redo2_3_plan.md").write_text("\n".join(rows), encoding="utf-8")


def load_success_results() -> dict[str, dict]:
    return {
        item.get("candidate_id"): item
        for item in load_json(RESULTS_PATH, [])
        if item.get("status") == "ok" and item.get("candidate_id") and item.get("local_path") and Path(item["local_path"]).exists()
    }


def run_items(module, items: list[dict]) -> None:
    results = load_json(RESULTS_PATH, [])
    done = set(load_success_results())
    prefix_totals = Counter(item["prefix"] for item in items)
    prefix_seen = Counter()
    queue = []
    for item in items:
        if item["candidate_id"] in done:
            continue
        idx = prefix_seen[item["prefix"]]
        prefix_seen[item["prefix"]] += 1
        queue.append((item, idx, prefix_totals[item["prefix"]]))
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(module.apimart_submit, item, idx, total): item for item, idx, total in queue}
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
                    "source_png": item.get("source_png"),
                    "cost_usd_est": 0,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            for key in [
                "candidate_id",
                "original_d",
                "failed_seedream_id",
                "failed_original_candidate_id",
                "redo_reason_cn",
                "redo_of_seedream",
                "redo_of_image2",
                "old_seedream_source_id",
                "locked_bad_source_ids",
                "source_selection_note",
                "source_changed",
                "run_type",
                "scene_lane",
                "color_lane",
                "composition_lane",
            ]:
                result[key] = item.get(key)
            results.append(result)
            save_json(RESULTS_PATH, results)
            with PROGRESS_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(f"{result.get('status')} {item['candidate_id']} {result.get('elapsed_sec','-')}s {result.get('error','')[:120]}", flush=True)


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def url_for(value: str | None) -> str:
    if not value:
        return ""
    path = Path(value).resolve()
    roots = [
        (OUT.resolve(), f"/outputs/{OUT.name}"),
        (SEEDREAM_OUT.resolve(), f"/outputs/{SEEDREAM_OUT.name}"),
        (ORIGINAL_OUT.resolve(), f"/outputs/{ORIGINAL_OUT.name}"),
        (Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs").resolve(), "/outputs"),
    ]
    for root, prefix in roots:
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        return prefix + "/" + quote(rel.as_posix(), safe="/")
    return ""


def build_review() -> Path:
    plan = load_json(PLAN_PATH, [])
    results = load_success_results()
    cards = []
    for item in plan:
        result = results.get(item["candidate_id"], {})
        cards.append(
            f"""
<article class="card" data-id="{esc(item['candidate_id'])}">
  <h3>{esc(item['candidate_id'])}</h3>
  <p>{esc(item['original_d'])} · {esc(item['prefix'])} · new source {esc(item.get('source_id'))} · locked bad {esc(','.join(item.get('locked_bad_source_ids') or []))}</p>
  <div class="grid">
    <figure><img src="{esc(url_for(item.get('redo_of_image2')))}" loading="lazy"><figcaption>original image2 failed</figcaption></figure>
    <figure><img src="{esc(url_for(item.get('redo_of_seedream')))}" loading="lazy"><figcaption>Seedream failed</figcaption></figure>
    <figure><img src="{esc(url_for(item.get('source_png')))}" loading="lazy"><figcaption>new source PNG</figcaption></figure>
    <figure><img src="{esc(url_for(result.get('local_path')))}" loading="lazy"><figcaption>new image2 redo2</figcaption></figure>
  </div>
  <p class="fb">用户反馈：{esc(item.get('redo_reason_cn'))}</p>
  <div class="actions">
    <button onclick="mark('{esc(item['candidate_id'])}','keep')">保留</button>
    <button onclick="mark('{esc(item['candidate_id'])}','redo')">重做</button>
    <button onclick="mark('{esc(item['candidate_id'])}','reject')">不要</button>
    <input id="fb-{esc(item['candidate_id'])}" placeholder="反馈">
    <span id="st-{esc(item['candidate_id'])}">未筛选</span>
  </div>
  <details><summary>prompt</summary><pre>{esc(result.get('prompt') or item.get('redo_prompt_append'))}</pre></details>
</article>"""
        )
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>image2 redo2 3 review</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f6f4ef;margin:0;color:#1f2937}}
header{{position:sticky;top:0;background:#fff;padding:12px 18px;border-bottom:1px solid #ddd;z-index:2}}
.wrap{{padding:16px;max-width:1700px;margin:auto}}.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin-bottom:18px;padding:12px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}figure{{margin:0;border:1px solid #e5e7eb;background:#fafafa;padding:6px;text-align:center}}
img{{max-width:100%;height:250px;object-fit:contain;background:#fff}}figcaption{{font-size:12px;color:#555;word-break:break-all}}.fb{{background:#fff7ed;border:1px solid #fed7aa;padding:8px;border-radius:6px}}
button{{border:0;border-radius:6px;padding:6px 10px;background:#7c3aed;color:#fff}}button:nth-child(2){{background:#f59e0b}}button:nth-child(3){{background:#ef4444}}
input{{min-width:260px;padding:6px}}#exportBox{{width:100%;height:140px}}pre{{white-space:pre-wrap;font-size:11px;max-height:180px;overflow:auto;background:#111827;color:#fff;padding:8px}}
@media(max-width:1100px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><header><h2>0616-2 image2 redo2 3 review</h2><p>3 张 Seedream 失败项改回 image2。左起：原 image2 失败、Seedream 失败、新 PNG、新 image2。</p><button onclick="exportFeedback()">导出筛选JSON</button><textarea id="exportBox"></textarea></header><main class="wrap">{''.join(cards)}</main>
<script>
const REVIEW='0616_2_image2_seedream_redo2_3_review';let feedback={{}};
function mark(id,decision){{const fb=document.getElementById('fb-'+id)?.value||'';feedback[id]={{decision,feedback:fb,ts:new Date().toISOString()}};document.getElementById('st-'+id).textContent=decision;}}
function exportFeedback(){{for(const id of Object.keys(feedback))feedback[id].feedback=document.getElementById('fb-'+id)?.value||feedback[id].feedback||'';const data={{review:REVIEW,exported_at:new Date().toISOString(),feedback}};document.getElementById('exportBox').value=JSON.stringify(data,null,2);navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('exportBox').value).catch(()=>{{}});}}
</script></body></html>"""
    REVIEW_PATH.write_text(page, encoding="utf-8")
    return REVIEW_PATH


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    module = load_base_module()
    wrap_prompt_builder(module)
    plan = build_plan()
    print(json.dumps({"mode": MODE, "out": str(OUT), "count": len(plan), "workers": WORKERS}, ensure_ascii=False, indent=2), flush=True)
    if MODE == "run":
        run_items(module, plan)
    review = build_review()
    print(f"REVIEW={review}", flush=True)


if __name__ == "__main__":
    main()
