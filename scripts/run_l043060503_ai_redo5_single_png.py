from __future__ import annotations

import html
import importlib.util
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


BASE_SCRIPT = Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\run_0616_2_low_cost_t_candidates.py")
ORIGINAL_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702")
REDO4_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo4_two_pngs_20260703")
OUT = Path(os.environ.get("OUT_DIR", r"D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo5_single_png_20260703"))
MODE = os.environ.get("MODE", "plan")

PLAN_PATH = OUT / "l043060503_ai_redo5_single_png_plan.json"
RESULTS_PATH = OUT / "l043060503_ai_redo5_single_png_results.json"
PROGRESS_PATH = OUT / "l043060503_ai_redo5_single_png_progress.jsonl"
REVIEW_PATH = OUT / "l043060503_ai_redo5_single_png_review.html"
LOCK_PATH = OUT / "feedback_lock_l043060503_ai_redo5_single_png_20260703.json"

ORIGINAL_PLAN_PATH = ORIGINAL_OUT / "candidate_plan_197x3.json"
REDO4_RESULTS_PATH = REDO4_OUT / "l043060503_ai_redo4_two_pngs_results.json"


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


def result_by_candidate(path: Path) -> dict[str, dict]:
    return {item.get("candidate_id"): item for item in load_json(path, []) if item.get("candidate_id")}


def build_plan() -> list[dict]:
    original_plan = {item.get("candidate_id"): item for item in load_json(ORIGINAL_PLAN_PATH, []) if item.get("candidate_id")}
    redo4_results = result_by_candidate(REDO4_RESULTS_PATH)
    base = dict(original_plan["L043060503__set3"])
    item = dict(base)
    item.update(
        {
            "d": "L043060503__set3__redo1__redo5_ai_single",
            "candidate_id": "L043060503__set3__redo1__redo5_ai_single",
            "original_d": "L043060503",
            "prefix": "L043",
            "source_id": "L043_NEW_0034",
            "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L043\kept_0033_0033_L043_NEW_0034_kept.png",
            "source_kind": "kept_cutout",
            "source_library_rel": "kept_plus_sku_variant_plus_retry_new_original_library/L043/kept_0033_0033_L043_NEW_0034_kept.png",
            "run_type": "image2_ai_redo5_single_supplement",
            "user_feedback_cn": "png的一致性太差了，换个png，做个图，补充进来，不要反复试了",
            "keep_candidate_id": "L043060503__set3__redo1__redo4_ai_b",
            "keep_candidate_path": redo4_results.get("L043060503__set3__redo1__redo4_ai_b", {}).get("local_path"),
            "failed_candidate_id": "L043060503__set3__redo1__redo4_ai_a",
            "failed_candidate_path": redo4_results.get("L043060503__set3__redo1__redo4_ai_a", {}).get("local_path"),
            "locked_bad_source_ids": ["L043_NEW_0008", "L043_NEW_0025", "L043_NEW_0038", "L043_NEW_0035"],
            "scene_lane": "bright closet folding workflow scene, hand placing folded clothes on stacked folding boards",
            "color_lane": "soft cool white daylight with clean textile tones",
            "composition_lane": "large product, stack layers visible, hand context allowed, no scattered multi-product layout",
            "source_selection_note": "single supplemental PNG chosen for consistency with passed L043_NEW_0043; no repeated batch retry",
        }
    )
    source_path = Path(item["source_png"])
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    item["redo_prompt_append"] = (
        "Single supplemental image2/APIMart AI generation. The user said not to repeatedly try; make one replacement using a new, more consistent PNG. "
        "Use source_id L043_NEW_0034 only. Do not use or imitate failed/bad sources L043_NEW_0008, L043_NEW_0025, L043_NEW_0038, or L043_NEW_0035. "
        "The previous passed reference for consistency is L043_NEW_0043; keep a similar product-use identity: stacked folding clothes boards, folded clothes, side tabs, raised board edges and realistic hand/closet context. "
        "Preserve L043 folding board identity: all visible holes, small center hole when visible, raised tabs/edges, panel seams, side tabs, thin plastic material, stacked board layers and realistic scale. "
        "Do not redraw it as a tray, phone holder, empty perforated shelf, drawer organizer, scattered unrelated products, or generic plastic pad. "
        f"Scene lane: {item['scene_lane']}. Color lane: {item['color_lane']}. Composition lane: {item['composition_lane']}."
    )
    plan = [item]
    save_json(PLAN_PATH, plan)
    save_json(
        LOCK_PATH,
        {
            "review": "l043060503_ai_redo4_two_pngs_review",
            "locked_at": datetime.now().isoformat(timespec="seconds"),
            "feedback": {
                "L043060503__set3__redo1__redo4_ai_b": {
                    "decision": "keep",
                    "feedback": "通过",
                    "ts": "2026-07-03T05:03:23.184Z",
                },
                "L043060503__set3__redo1__redo4_ai_a": {
                    "decision": "redo",
                    "feedback": "png的一致性太差了，换个png，做个图，补充进来，不要反复试了",
                    "ts": "2026-07-03T05:03:56.217Z",
                },
            },
            "keep": ["L043060503__set3__redo1__redo4_ai_b"],
            "locked_bad_source_ids": ["L043_NEW_0008", "L043_NEW_0025", "L043_NEW_0038", "L043_NEW_0035"],
            "source_used": "L043_NEW_0034",
            "claude_code_reviewed": True,
            "nvidia_validated": True,
            "validation_gate": "claude_nvidia_l043060503_ai_redo5_final_gate_20260703.md",
            "next_action": "Run exactly one supplemental image2 candidate using L043_NEW_0034.",
        },
    )
    write_plan_md(plan)
    return plan


def write_plan_md(plan: list[dict]) -> None:
    item = plan[0]
    lines = [
        "# L043060503 redo5 single PNG AI supplement plan",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- output: `{OUT}`",
        "- user keep: `L043060503__set3__redo1__redo4_ai_b` passed.",
        "- user redo: `L043060503__set3__redo1__redo4_ai_a` failed because PNG consistency was poor.",
        "- instruction: `换个png，做个图，补充进来，不要反复试了`",
        "- method: exactly one APIMart / GPT-Image-2 AI generation.",
        "- no Excel writeback; no final upload.",
        "",
        "| candidate | source | locked bad sources |",
        "|---|---|---|",
        f"| {item['candidate_id']} | {item['source_id']} | {', '.join(item['locked_bad_source_ids'])} |",
    ]
    (OUT / "l043060503_ai_redo5_single_png_plan.md").write_text("\n".join(lines), encoding="utf-8")


def load_success_results() -> dict[str, dict]:
    return {
        item.get("candidate_id"): item
        for item in load_json(RESULTS_PATH, [])
        if item.get("status") == "ok" and item.get("candidate_id") and item.get("local_path") and Path(item["local_path"]).exists()
    }


def run_items(module, plan: list[dict]) -> None:
    results = load_json(RESULTS_PATH, [])
    if plan[0]["candidate_id"] in load_success_results():
        return
    with ThreadPoolExecutor(max_workers=1) as pool:
        futures = {pool.submit(module.apimart_submit, plan[0], 0, 1): plan[0]}
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
                "user_feedback_cn",
                "keep_candidate_id",
                "failed_candidate_id",
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
        (Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo4_two_pngs_20260703").resolve(), "/outputs/store_newskill_l043060503_ai_redo4_two_pngs_20260703"),
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
    item = plan[0]
    result = results.get(item["candidate_id"], {})
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>L043060503 redo5 single PNG</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f6f4ef;margin:0;color:#1f2937}}header{{position:sticky;top:0;background:#fff;padding:12px 18px;border-bottom:1px solid #ddd;z-index:2}}
.wrap{{padding:16px;max-width:1500px;margin:auto}}.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin-bottom:18px;padding:12px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
figure{{margin:0;border:1px solid #e5e7eb;background:#fafafa;padding:6px;text-align:center}}img{{max-width:100%;height:300px;object-fit:contain;background:#fff}}figcaption{{font-size:12px;color:#555;word-break:break-all}}
.note{{background:#eef2ff;border:1px solid #c7d2fe;padding:8px;border-radius:6px}}button{{border:0;border-radius:6px;padding:6px 10px;background:#7c3aed;color:#fff}}button:nth-child(2){{background:#f59e0b}}button:nth-child(3){{background:#ef4444}}
input{{min-width:260px;padding:6px}}#exportBox{{width:100%;height:130px}}pre{{white-space:pre-wrap;font-size:11px;max-height:180px;overflow:auto;background:#111827;color:#fff;padding:8px}}@media(max-width:1100px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><header><h2>L043060503 redo5 single PNG supplement</h2><p>补充 1 张，不反复试。左起：通过图、失败图、新 PNG、新 AI 图。</p><button onclick="exportFeedback()">导出筛选JSON</button><textarea id="exportBox"></textarea></header><main class="wrap">
<article class="card">
  <h3>{esc(item['candidate_id'])}</h3>
  <p>source {esc(item['source_id'])} · keep {esc(item['keep_candidate_id'])} · locked bad {esc(','.join(item['locked_bad_source_ids']))}</p>
  <div class="grid">
    <figure><img src="{esc(url_for(item.get('keep_candidate_path')))}" loading="lazy"><figcaption>passed redo4 B</figcaption></figure>
    <figure><img src="{esc(url_for(item.get('failed_candidate_path')))}" loading="lazy"><figcaption>failed redo4 A</figcaption></figure>
    <figure><img src="{esc(url_for(item.get('source_png')))}" loading="lazy"><figcaption>new source PNG</figcaption></figure>
    <figure><img src="{esc(url_for(result.get('local_path')))}" loading="lazy"><figcaption>new AI image2 supplement</figcaption></figure>
  </div>
  <p class="note">用户要求：png的一致性太差，换个 PNG 做 1 张补充，不反复试。</p>
  <div class="actions">
    <button onclick="mark('{esc(item['candidate_id'])}','keep')">保留</button>
    <button onclick="mark('{esc(item['candidate_id'])}','redo')">重做</button>
    <button onclick="mark('{esc(item['candidate_id'])}','reject')">不要</button>
    <input id="fb-{esc(item['candidate_id'])}" placeholder="反馈">
    <span id="st-{esc(item['candidate_id'])}">未筛选</span>
  </div>
  <details><summary>prompt</summary><pre>{esc(result.get('prompt') or item.get('redo_prompt_append'))}</pre></details>
</article></main>
<script>
const REVIEW='l043060503_ai_redo5_single_png_review';let feedback={{}};
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
