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
ORIGINAL_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702")
REDO2_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_seedream_redo2_3_20260703")
FIXED_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_fixed_redo3_20260703")
OUT = Path(os.environ.get("OUT_DIR", r"D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo4_two_pngs_20260703"))
MODE = os.environ.get("MODE", "plan")
WORKERS = int(os.environ.get("WORKERS", "2") or "2")

PLAN_PATH = OUT / "l043060503_ai_redo4_two_pngs_plan.json"
RESULTS_PATH = OUT / "l043060503_ai_redo4_two_pngs_results.json"
PROGRESS_PATH = OUT / "l043060503_ai_redo4_two_pngs_progress.jsonl"
REVIEW_PATH = OUT / "l043060503_ai_redo4_two_pngs_review.html"
LOCK_PATH = OUT / "feedback_lock_l043060503_ai_redo4_two_pngs_20260703.json"

ORIGINAL_PLAN_PATH = ORIGINAL_OUT / "candidate_plan_197x3.json"
ORIGINAL_RESULTS_PATH = ORIGINAL_OUT / "candidate_results_197x3.json"
REDO2_RESULTS_PATH = REDO2_OUT / "image2_seedream_redo2_3_results.json"
FIXED_RESULTS_PATH = FIXED_OUT / "l043060503_redo3_fixed_results.json"

SOURCES = [
    {
        "candidate_id": "L043060503__set3__redo1__redo4_ai_a",
        "source_id": "L043_NEW_0038",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L043\kept_0035_0035_L043_NEW_0038_kept.png",
        "source_kind": "kept_cutout",
        "source_library_rel": "kept_plus_sku_variant_plus_retry_new_original_library/L043/kept_0035_0035_L043_NEW_0038_kept.png",
        "scene_lane": "open wardrobe shelf, folding board stack with clothes visible, realistic use context",
        "color_lane": "neutral warm wood closet daylight, avoid yellow cast",
        "composition_lane": "product large and inspectable, front/three-quarter view, no phone or tray reinterpretation",
    },
    {
        "candidate_id": "L043060503__set3__redo1__redo4_ai_b",
        "source_id": "L043_NEW_0043",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L043\kept_0036_0036_L043_NEW_0043_kept.png",
        "source_kind": "kept_cutout",
        "source_library_rel": "kept_plus_sku_variant_plus_retry_new_original_library/L043/kept_0036_0036_L043_NEW_0043_kept.png",
        "scene_lane": "bright bedroom closet organization scene, person holding folded clothes softly cropped",
        "color_lane": "cool white closet daylight with soft cream textile tones",
        "composition_lane": "product centered and large enough, preserve stack layers and side tabs",
    },
]


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


def source_base_item() -> dict:
    plan = {item.get("candidate_id"): item for item in load_json(ORIGINAL_PLAN_PATH, [])}
    base = dict(plan["L043060503__set3"])
    base["d"] = "L043060503"
    return base


def result_by_candidate(path: Path) -> dict[str, dict]:
    return {item.get("candidate_id"): item for item in load_json(path, []) if item.get("candidate_id")}


def build_plan() -> list[dict]:
    base = source_base_item()
    original_results = result_by_candidate(ORIGINAL_RESULTS_PATH)
    redo2_results = result_by_candidate(REDO2_RESULTS_PATH)
    fixed_results = result_by_candidate(FIXED_RESULTS_PATH)
    items = []
    for src in SOURCES:
        item = dict(base)
        item.update(src)
        item["d"] = src["candidate_id"]
        item["original_d"] = "L043060503"
        item["prefix"] = "L043"
        item["failed_original_candidate_id"] = "L043060503__set3"
        item["failed_redo2_candidate_id"] = "L043060503__set3__redo1__redo2_image2"
        item["user_rejected_fixed_method"] = True
        item["user_instruction_cn"] = "不要合成png和背景的图片，还是要ai做的，就拿这两个png去试一下"
        item["locked_bad_source_ids"] = ["L043_NEW_0008", "L043_NEW_0025"]
        item["redo_of_original_image2"] = original_results.get("L043060503__set3", {}).get("local_path")
        item["redo_of_redo2_image2"] = redo2_results.get("L043060503__set3__redo1__redo2_image2", {}).get("local_path")
        item["rejected_fixed_candidates"] = [
            fixed_results.get("L043060503__set3__redo1__redo3_fixed_a", {}).get("local_path"),
            fixed_results.get("L043060503__set3__redo1__redo3_fixed_b", {}).get("local_path"),
        ]
        item["run_type"] = "image2_ai_redo4_using_user_requested_two_pngs"
        item["source_selection_note"] = "user_rejected_fixed_composite_but_requested_these_two_pngs_for_ai"
        item["source_changed"] = True
        item["redo_prompt_append"] = (
            "User explicitly rejected the fixed PNG + background composite approach. This must be an AI-generated image2/APIMart scene using the assigned PNG as product reference. "
            "Use this source PNG only as the exact product/product-use reference; do not use the previous fixed composite output as input or style reference. "
            "Locked bad sources for this D: L043_NEW_0008 and L043_NEW_0025; do not imitate their failed outputs. "
            f"Assigned scene lane: {item['scene_lane']}. Color lane: {item['color_lane']}. Composition lane: {item['composition_lane']}. "
            "Preserve L043 folding board identity: stacked folding clothes boards, all visible holes, small center hole when visible, raised tabs/edges, panel seams, side tabs, clothing stack context, thin plastic material, realistic scale. "
            "Do not redraw it as a tray, phone holder, flat hole board, empty perforated shelf, generic plastic pad, drawer organizer, or product without stacked clothing context. "
            "Make the final image look like a realistic premium AI lifestyle photo, not a pasted composite."
        )
        items.append(item)
    save_json(PLAN_PATH, items)
    save_json(
        LOCK_PATH,
        {
            "review": "l043060503_redo3_fixed_review",
            "locked_at": datetime.now().isoformat(timespec="seconds"),
            "feedback": {
                "fixed_method": {
                    "decision": "redo",
                    "feedback": "不要合成png和背景的图片，还是要ai做的，就拿这两个png去试一下",
                    "ts": "2026-07-03",
                }
            },
            "locked_bad_source_ids": ["L043_NEW_0008", "L043_NEW_0025"],
            "next_action": "Run image2/APIMart AI with L043_NEW_0038 and L043_NEW_0043 only.",
        },
    )
    write_plan_md(items)
    return items


def write_plan_md(items: list[dict]) -> None:
    lines = [
        "# L043060503 redo4 AI from two PNGs plan",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- output: `{OUT}`",
        "- user instruction: `不要合成png和背景的图片，还是要ai做的，就拿这两个png去试一下`",
        "- method: APIMart / GPT-Image-2 AI generation, not fixed compositing.",
        "- locked bad sources: `L043_NEW_0008`, `L043_NEW_0025`.",
        "- no Excel writeback; no final product upload.",
        "",
        "| candidate | source | scene lane |",
        "|---|---|---|",
    ]
    for item in items:
        lines.append(f"| {item['candidate_id']} | {item['source_id']} | {item['scene_lane']} |")
    (OUT / "l043060503_ai_redo4_two_pngs_plan.md").write_text("\n".join(lines), encoding="utf-8")


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
    queue = [(item, idx, prefix_totals[item["prefix"]]) for idx, item in enumerate(items) if item["candidate_id"] not in done]
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
                "failed_original_candidate_id",
                "failed_redo2_candidate_id",
                "user_instruction_cn",
                "user_rejected_fixed_method",
                "locked_bad_source_ids",
                "run_type",
                "scene_lane",
                "color_lane",
                "composition_lane",
                "source_selection_note",
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
        (REDO2_OUT.resolve(), f"/outputs/{REDO2_OUT.name}"),
        (FIXED_OUT.resolve(), f"/outputs/{FIXED_OUT.name}"),
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


def build_review() -> None:
    plan = load_json(PLAN_PATH, [])
    results = load_success_results()
    cards = []
    for item in plan:
        result = results.get(item["candidate_id"], {})
        cards.append(
            f"""
<article class="card">
  <h3>{esc(item['candidate_id'])}</h3>
  <p>source {esc(item['source_id'])} · AI image2 · locked bad {esc(','.join(item['locked_bad_source_ids']))}</p>
  <div class="grid">
    <figure><img src="{esc(url_for(item.get('redo_of_redo2_image2')))}" loading="lazy"><figcaption>failed image2 redo2</figcaption></figure>
    <figure><img src="{esc(url_for(item.get('source_png')))}" loading="lazy"><figcaption>source PNG for AI</figcaption></figure>
    <figure><img src="{esc(url_for(result.get('local_path')))}" loading="lazy"><figcaption>new AI image2 result</figcaption></figure>
  </div>
  <p class="note">用户要求：不要合成 PNG 和背景，还是要 AI 做；只拿这两个 PNG 去试。</p>
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
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>L043060503 AI redo4 two PNGs</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f6f4ef;margin:0;color:#1f2937}}header{{position:sticky;top:0;background:#fff;padding:12px 18px;border-bottom:1px solid #ddd;z-index:2}}
.wrap{{padding:16px;max-width:1500px;margin:auto}}.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin-bottom:18px;padding:12px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
figure{{margin:0;border:1px solid #e5e7eb;background:#fafafa;padding:6px;text-align:center}}img{{max-width:100%;height:320px;object-fit:contain;background:#fff}}figcaption{{font-size:12px;color:#555;word-break:break-all}}
.note{{background:#eef2ff;border:1px solid #c7d2fe;padding:8px;border-radius:6px}}button{{border:0;border-radius:6px;padding:6px 10px;background:#7c3aed;color:#fff}}button:nth-child(2){{background:#f59e0b}}button:nth-child(3){{background:#ef4444}}
input{{min-width:260px;padding:6px}}#exportBox{{width:100%;height:130px}}pre{{white-space:pre-wrap;font-size:11px;max-height:180px;overflow:auto;background:#111827;color:#fff;padding:8px}}@media(max-width:1100px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><header><h2>L043060503 AI redo4 two PNGs</h2><p>这页是 AI/image2 结果，不是固定合成。左：之前失败图；中：本次 PNG；右：新 AI 图。</p><button onclick="exportFeedback()">导出筛选JSON</button><textarea id="exportBox"></textarea></header><main class="wrap">{''.join(cards)}</main>
<script>
const REVIEW='l043060503_ai_redo4_two_pngs_review';let feedback={{}};
function mark(id,decision){{feedback[id]={{decision,feedback:document.getElementById('fb-'+id)?.value||'',ts:new Date().toISOString()}};document.getElementById('st-'+id).textContent=decision;}}
function exportFeedback(){{for(const id of Object.keys(feedback))feedback[id].feedback=document.getElementById('fb-'+id)?.value||feedback[id].feedback||'';const data={{review:REVIEW,exported_at:new Date().toISOString(),feedback}};document.getElementById('exportBox').value=JSON.stringify(data,null,2);navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('exportBox').value).catch(()=>{{}});}}
</script></body></html>"""
    REVIEW_PATH.write_text(page, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    module = load_base_module()
    wrap_prompt_builder(module)
    plan = build_plan()
    if MODE == "run":
        run_items(module, plan)
    build_review()
    print(json.dumps({"mode": MODE, "out": str(OUT), "count": len(plan), "review": str(REVIEW_PATH)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
