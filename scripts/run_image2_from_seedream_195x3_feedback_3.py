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


BASE_SCRIPT = Path(
    os.environ.get(
        "BASE_IMAGE2_SCRIPT",
        r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\run_0616_2_low_cost_t_candidates.py",
    )
)
SEEDREAM_OUT = Path(
    os.environ.get(
        "SEEDREAM_OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_195x3_redo_json45_feedback_20260706",
    )
)
OUT = Path(
    os.environ.get(
        "OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_from_seedream_feedback_3_20260706",
    )
)
MODE = os.environ.get("MODE", "plan")
WORKERS = int(os.environ.get("WORKERS", "1") or "1")

SEEDREAM_PLAN_PATH = SEEDREAM_OUT / "source_plan_seedream_from_redo_json45_feedback_20260706.json"
SEEDREAM_RESULTS_PATH = SEEDREAM_OUT / "seedream_fallback_results.json"
PLAN_PATH = OUT / "image2_from_seedream_feedback_3_plan.json"
RESULTS_PATH = OUT / "image2_from_seedream_feedback_3_results.json"
PROGRESS_PATH = OUT / "image2_from_seedream_feedback_3_progress.jsonl"
RAW_FEEDBACK_PATH = OUT / "seedream_13_review_feedback_raw_20260706.json"
LOCK_PATH = OUT / "feedback_lock_seedream_13_review_image2_3_20260706.json"
REVIEW_PATH = OUT / "0616_2_image2_from_seedream_feedback_3_review.html"

RAW_FEEDBACK = {
    "review": "0616_2_seedream_from_195x3_redo_json45_feedback_13_review",
    "exported_at": "2026-07-06T06:16:59.821Z",
    "feedback": {
        "L042060505__set1__redo1": {
            "decision": "redo",
            "feedback": "太失败了。找image2，重做一个安全的。",
            "ts": "2026-07-06T06:15:25.151Z",
        },
        "L043060502__set3__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:15:43.471Z"},
        "L043060503__set2__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:15:47.639Z"},
        "L043060504__set1__redo1": {
            "decision": "redo",
            "feedback": "image2，重做一个安全的",
            "ts": "2026-07-06T06:15:55.185Z",
        },
        "L043060504__set3__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:16:09.109Z"},
        "L043060505__set2__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:16:12.876Z"},
        "L043060507__set1__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:16:15.313Z"},
        "L043060507__set2__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:16:19.400Z"},
        "L043060507__set3__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:16:23.727Z"},
        "L043060508__set3__redo1": {
            "decision": "redo",
            "feedback": "image2，重做一个安全的",
            "ts": "2026-07-06T06:16:28.153Z",
        },
        "L081060501__set3__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:16:48.999Z"},
        "L082060509__set2__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:16:52.479Z"},
        "L091060505__set3__redo1": {"decision": "keep", "feedback": "", "ts": "2026-07-06T06:16:55.748Z"},
    },
}

SOURCE_OVERRIDES = {
    "L042060505__set1__redo1__redo2_image2_safe": {
        "source_id": "L042_NEW_0030",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L042\kept_0016_0016_L042_NEW_0030_kept.png",
        "source_kind": "kept_cutout",
        "source_library_rel": "kept_plus_sku_variant_plus_retry_new_original_library/L042/kept_0016_0016_L042_NEW_0030_kept.png",
    },
    "L043060504__set1__redo1__redo2_image2_safe": {
        "source_id": "L043_NEW_0006",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L043\kept_0025_0025_L043_NEW_0006_kept.png",
        "source_kind": "kept_cutout",
        "source_library_rel": "kept_plus_sku_variant_plus_retry_new_original_library/L043/kept_0025_0025_L043_NEW_0006_kept.png",
    },
    "L043060508__set3__redo1__redo2_image2_safe": {
        "source_id": "L043_NEW_0001",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L043\kept_0021_0021_L043_NEW_0001_kept.png",
        "source_kind": "kept_cutout",
        "source_library_rel": "kept_plus_sku_variant_plus_retry_new_original_library/L043/kept_0021_0021_L043_NEW_0001_kept.png",
    },
}

PRODUCT_LOCKS = {
    "L042": (
        "Use the input PNG as a fixed product reference. Preserve the black garden edging roll, perforated fixing tabs, hole pattern, roll geometry, and the fan of short black spiral stakes exactly. "
        "The safety goal is correct product shape, not creative scene complexity. Do not create long straight pins, fence rods, loose black sticks, outward spikes, decorative bars, extra nail bundles, or a separate fence-like row of stakes."
    ),
    "L043": (
        "Use the input PNG as a fixed folding-board hardware reference. Preserve board outline, all circular holes, small center hole, rear raised support detail, front lip/detail, panel seams, thickness, material and realistic scale. "
        "Do not turn it into a tray, mat, tablet stand, generic board, laundry basket, or clothing stack. Do not remove or move holes."
    ),
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
        base = original(item, index_in_prefix, prefix_total)
        return f"{base} {item.get('redo_prompt_append', '')}".strip()

    module.build_prompt = build_prompt


def seedream_plan() -> dict[str, dict]:
    return load_json(SEEDREAM_PLAN_PATH)["items"]


def seedream_results() -> dict[str, dict]:
    rows = {}
    for item in load_json(SEEDREAM_RESULTS_PATH, []):
        cid = item.get("candidate_id") or item.get("d")
        if cid:
            rows[cid] = item
    return rows


def prompt_append(item: dict) -> str:
    if item["prefix"] == "L042":
        return (
            "Targeted SAFE image2/APIMart redo after Seedream failed human review. User said: 太失败了。找image2，重做一个安全的。 "
            "Do not imitate the failed Seedream output or any failed image2 output. Use this newly assigned clearer PNG source only. "
            f"Extra product lock: {PRODUCT_LOCKS['L042']} "
            "Create a conservative safe garden-border ecommerce image: clean lawn edge or stone path border, pulled back enough to feel real but with the product still large enough to inspect. "
            "Product about 24-30 percent of image height. Simple natural daylight, no text, no labels, no measurement marks, no tools, no hands, no people."
        )
    return (
        "Targeted SAFE image2/APIMart redo after Seedream failed human review. User said: image2，重做一个安全的. "
        "Do not imitate failed Seedream output. Use this newly assigned clean board PNG only; do not use locked or discarded L043 sources L043_NEW_0004, L043_NEW_0008, or L043_NEW_0025. "
        f"Extra product lock: {PRODUCT_LOCKS['L043']} "
        "Create a conservative safe laundry/closet shelf scene with product on a flat folding table or shelf. Keep the product front/near-front view; avoid dramatic perspective, hands, phones, or clothes covering holes. "
        "Product about 28-34 percent of image height for inspection. Natural daylight, realistic contact shadow, no text, no logos, no electronic screens."
    )


def build_plan() -> list[dict]:
    seed_plan = seedream_plan()
    seed_results = seedream_results()
    redo_ids = [cid for cid, value in RAW_FEEDBACK["feedback"].items() if value.get("decision") == "redo"]
    keep_ids = [cid for cid, value in RAW_FEEDBACK["feedback"].items() if value.get("decision") == "keep"]
    rows = []
    for failed_seedream_id in redo_ids:
        base = dict(seed_plan[failed_seedream_id])
        redo_id = f"{failed_seedream_id}__redo2_image2_safe"
        base.update(SOURCE_OVERRIDES[redo_id])
        base["d"] = redo_id
        base["candidate_id"] = redo_id
        base["original_d"] = base.get("original_d") or failed_seedream_id.split("__")[0]
        base["failed_seedream_id"] = failed_seedream_id
        base["failed_seedream_path"] = seed_results.get(failed_seedream_id, {}).get("local_path") or seed_results.get(failed_seedream_id, {}).get("local_image")
        base["failed_seedream_source_id"] = seed_results.get(failed_seedream_id, {}).get("source_id")
        base["redo_reason_cn"] = RAW_FEEDBACK["feedback"][failed_seedream_id].get("feedback", "")
        base["locked_bad_source_ids"] = ["L043_NEW_0004", "L043_NEW_0008", "L043_NEW_0025"] if base["prefix"] == "L043" else []
        base["source_selection_note"] = "manual_safe_image2_source_after_seedream_failure"
        base["source_changed"] = True
        base["run_type"] = "image2_safe_redo_after_seedream_195x3_feedback"
        base["scene_lane"] = "safe garden border scene, product 24-30 percent height" if base["prefix"] == "L042" else "safe laundry/closet folding-board scene, product 28-34 percent height"
        base["color_lane"] = "natural daylight, realistic outdoor greens and stone" if base["prefix"] == "L042" else "neutral daylight, clean closet/laundry colors"
        base["composition_lane"] = "conservative product-inspection composition, no creative close-up drift"
        base["product_lock"] = PRODUCT_LOCKS[base["prefix"]]
        base["redo_prompt_append"] = prompt_append(base)
        base.setdefault("rows", [])
        rows.append(base)

    save_json(RAW_FEEDBACK_PATH, RAW_FEEDBACK)
    save_json(
        LOCK_PATH,
        {
            "review": RAW_FEEDBACK["review"],
            "exported_at": RAW_FEEDBACK["exported_at"],
            "locked_at": datetime.now().isoformat(timespec="seconds"),
            "rule": "Only three explicit redo items from Seedream 13 review go to image2 safe redo. Ten explicit keep items remain keep.",
            "counts": {"explicit_feedback": len(RAW_FEEDBACK["feedback"]), "redo": len(redo_ids), "keep": len(keep_ids)},
            "redo_ids": redo_ids,
            "keep_ids": keep_ids,
            "feedback": RAW_FEEDBACK["feedback"],
            "locked_bad_sources": {"L043": ["L043_NEW_0004", "L043_NEW_0008", "L043_NEW_0025"]},
        },
    )
    save_json(PLAN_PATH, rows)
    write_plan_md(rows, keep_ids)
    return rows


def write_plan_md(rows: list[dict], keep_ids: list[str]) -> None:
    lines = [
        "# image2 safe redo from Seedream 13 feedback",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- output: `{OUT}`",
        "- provider/model: APIMart / gpt-image-2",
        f"- redo_count: {len(rows)}",
        f"- keep_count: {len(keep_ids)}",
        "- no Excel writeback, no final product upload",
        "",
        "| redo id | original D | prefix | failed Seedream | failed source | new source | feedback |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| {item['candidate_id']} | {item['original_d']} | {item['prefix']} | {item['failed_seedream_id']} | {item.get('failed_seedream_source_id')} | {item.get('source_id')} | {item.get('redo_reason_cn','').replace('|','/')} |"
        )
    (OUT / "image2_from_seedream_feedback_3_plan.md").write_text("\n".join(lines), encoding="utf-8")


def load_success_results() -> dict[str, dict]:
    return {
        item.get("candidate_id"): item
        for item in load_json(RESULTS_PATH, [])
        if item.get("status") == "ok" and item.get("candidate_id") and item.get("local_path") and Path(item["local_path"]).exists()
    }


def run_items(module, rows: list[dict]) -> None:
    results = load_json(RESULTS_PATH, [])
    done = set(load_success_results())
    prefix_totals = Counter(item["prefix"] for item in rows)
    prefix_seen = Counter()
    queue = []
    for item in rows:
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
                "failed_seedream_path",
                "failed_seedream_source_id",
                "redo_reason_cn",
                "locked_bad_source_ids",
                "source_selection_note",
                "source_changed",
                "run_type",
                "scene_lane",
                "color_lane",
                "composition_lane",
                "product_lock",
            ]:
                result[key] = item.get(key)
            results.append(result)
            save_json(RESULTS_PATH, results)
            with PROGRESS_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(f"{result.get('status')} {item['candidate_id']} {result.get('elapsed_sec','-')}s {result.get('error','')[:120]}", flush=True)


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def file_url(value: str | None) -> str:
    if not value:
        return ""
    try:
        return Path(value).resolve().as_uri()
    except Exception:
        return ""


def build_review() -> Path:
    rows = load_json(PLAN_PATH, [])
    results = load_success_results()
    cards = []
    for item in rows:
        result = results.get(item["candidate_id"], {})
        cards.append(
            f"""
<article class="card" data-id="{esc(item['candidate_id'])}">
  <h3>{esc(item['candidate_id'])}</h3>
  <p>{esc(item['original_d'])} · {esc(item['prefix'])} · new source {esc(item.get('source_id'))} · failed source {esc(item.get('failed_seedream_source_id'))}</p>
  <div class="grid">
    <figure><img src="{esc(file_url(item.get('failed_seedream_path')))}" loading="lazy"><figcaption>failed Seedream</figcaption></figure>
    <figure><img src="{esc(file_url(item.get('source_png')))}" loading="lazy"><figcaption>new safe source PNG</figcaption></figure>
    <figure><img src="{esc(file_url(result.get('local_path')))}" loading="lazy"><figcaption>new image2 safe redo</figcaption></figure>
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
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>image2 safe redo 3 review</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f6f4ef;margin:0;color:#1f2937}}header{{position:sticky;top:0;background:#fff;padding:12px 18px;border-bottom:1px solid #ddd;z-index:2}}.wrap{{padding:16px;max-width:1500px;margin:auto}}.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin-bottom:18px;padding:12px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}figure{{margin:0;border:1px solid #e5e7eb;background:#fafafa;padding:6px;text-align:center}}img{{max-width:100%;height:280px;object-fit:contain;background:#fff}}figcaption{{font-size:12px;color:#555;word-break:break-all}}.fb{{background:#fff7ed;border:1px solid #fed7aa;padding:8px;border-radius:6px}}button{{border:0;border-radius:6px;padding:6px 10px;background:#7c3aed;color:#fff}}button:nth-child(2){{background:#f59e0b}}button:nth-child(3){{background:#ef4444}}input{{min-width:260px;padding:6px}}#exportBox{{width:100%;height:140px}}pre{{white-space:pre-wrap;font-size:11px;max-height:180px;overflow:auto;background:#111827;color:#fff;padding:8px}}@media(max-width:1100px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><header><h2>0616-2 image2 safe redo 3 review</h2><p>3 张 Seedream 失败项改回 image2 安全重做。左：失败 Seedream；中：安全源 PNG；右：新 image2。</p><button onclick="exportFeedback()">导出筛选JSON</button><textarea id="exportBox"></textarea></header><main class="wrap">{''.join(cards)}</main>
<script>
const REVIEW='0616_2_image2_from_seedream_feedback_3_review';let feedback={{}};
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
