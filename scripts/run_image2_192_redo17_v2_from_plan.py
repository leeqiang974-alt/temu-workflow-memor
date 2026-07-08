from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import shutil
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


BASE_SCRIPT = Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\run_0616_2_low_cost_t_candidates.py")
ORIGINAL_PLAN = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_luxury_set1_review_clean_20260707\candidate_plan_192_luxury_set1.json")
PLAN_V2 = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_full_print_20260707\redo17_newpng_promptfix_execution_plan_v2_after_claude_block_20260707.json")
OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_redo17_v2_newpng_promptfix_20260707")
RESULTS_PATH = OUT / "candidate_results_192_redo17_v2.json"
PLAN_OUT = OUT / "candidate_plan_192_redo17_v2.json"
PROGRESS_PATH = OUT / "candidate_progress_192_redo17_v2.jsonl"
IMAGE2_MODEL = "gpt-image-2"
IMAGE2_RESOLUTION = "1k"
IMAGE2_QUALITY = "standard"


def load_base_module():
    spec = importlib.util.spec_from_file_location("image2_base_0616_2", BASE_SCRIPT)
    if not spec or not spec.loader:
        raise RuntimeError(f"Cannot import base script: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.OUT = OUT
    module.GENERATED = OUT / "generated"
    module.RESULTS_PATH = RESULTS_PATH
    module.PROGRESS_PATH = PROGRESS_PATH
    return module


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_prompt(item: dict) -> str:
    title_hint = " ".join(item.get("titles", [])[:1])[:180]
    variant_hint = "；".join(item.get("variants", [])[:4])[:180]
    feedback = item.get("user_feedback") or "redo requested by review"
    prefix = item["prefix"]
    source_note = item.get("source_selection_note", "")
    scene = item["scene_prompt"]
    lock = item["product_lock"]

    prefix_extra = ""
    if prefix == "L096":
        prefix_extra = (
            "Use only a clearly outdoor setting with visible cues such as lawn, campsite ground, gravel, patio pavers, garden plants, "
            "open sky, balcony railing, deck boards, terrace floor, or courtyard floor. The folded portable grill must stand on its own "
            "legs on grass, gravel, patio pavers, deck boards, terrace floor, or campsite ground before use. Keep the product supported only "
            "by the outdoor ground or floor plane, with any raised furniture separated into the background. Rotate realistic outdoor use scenes: "
            "wild camping, backyard family/friends gathering, lawn picnic, RV campsite, garden party, terrace/deck floor, "
            "courtyard pavers, and park picnic."
        )
    elif prefix == "L043":
        prefix_extra = (
            "L043-AUDIT: product must occupy 34-40 percent of image height. Keep a clean front or top-front inspection view. "
            "Every large hole and the small center hole must remain visible; rear raised detail and panel seams must remain visible. "
            "Folded clothing can be nearby only as background props and must not cover any hole or protrusion."
        )

    return (
        "Create a new Temu ecommerce first-carousel candidate from the input product reference image. "
        "This is a fresh generation from a revised source PNG; do not use or imitate any previously failed generated image. "
        f"Candidate: {item['candidate_id']}. Exact D: {item['exact_d']}. Prefix: {prefix}. "
        f"Workbook title hint: {title_hint}. Variant hint: {variant_hint}. "
        f"User review feedback to avoid: {feedback}. "
        f"Source note: {source_note}. "
        f"Product lock: {lock}. {prefix_extra} "
        f"Scene directive: {scene} "
        "Keep the product complete, physically supported, with realistic contact shadow and matched lighting. "
        "The surrounding scene may change, but the product body, structure, color, silhouette, holes, supports, frames, handles, legs, panels, and accessories must stay faithful to the input reference. "
        "Use clean premium commercial photography, square 1:1 composition, unbranded props, no readable text or logos."
    )


def build_items() -> list[dict]:
    original_plan = {item["d"]: item for item in load_json(ORIGINAL_PLAN)}
    plan = load_json(PLAN_V2)
    items = []
    for redo in plan["items"]:
        original = original_plan.get(redo["original_candidate_id"])
        if not original:
            raise RuntimeError(f"Original candidate not found: {redo['original_candidate_id']}")
        item = dict(original)
        item.update(redo)
        item["d"] = redo["candidate_id"]
        item["original_d"] = redo["exact_d"]
        item["candidate_id"] = redo["candidate_id"]
        item["source_png"] = redo["new_source_png"]
        item["source_id"] = redo["new_source_id"]
        item["source_kind"] = redo.get("source_kind", "redo17_v2_new_source")
        item["run_type"] = "image2_192_redo17_v2_newpng_promptfix"
        item["prompt"] = build_prompt(item)
        items.append(item)
    OUT.mkdir(parents=True, exist_ok=True)
    PLAN_OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return items


def load_results() -> list[dict]:
    if RESULTS_PATH.exists():
        return load_json(RESULTS_PATH)
    return []


def save_results(results: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def run(workers: int, limit: int) -> list[dict]:
    module = load_base_module()
    items = build_items()

    def custom_prompt(item: dict, index_in_prefix: int, prefix_total: int) -> str:
        return item["prompt"]

    def custom_submit(item: dict, index_in_prefix: int, prefix_total: int) -> dict:
        if IMAGE2_MODEL != "gpt-image-2":
            raise RuntimeError(f"Refusing expensive/nonstandard image2 model: {IMAGE2_MODEL}")
        if IMAGE2_RESOLUTION != "1k":
            raise RuntimeError(f"Refusing non-low-cost image2 resolution without explicit approval: {IMAGE2_RESOLUTION}")
        key = module.read_key(module.APIMART_KEY)
        source = Path(item["source_png"])
        prompt = custom_prompt(item, index_in_prefix, prefix_total)
        payload = {
            "model": IMAGE2_MODEL,
            "prompt": prompt,
            "size": "1:1",
            "resolution": IMAGE2_RESOLUTION,
            "quality": IMAGE2_QUALITY,
            "response_format": "url",
            "image_urls": [module.image_to_data_url(source)],
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        started = time.time()
        data = module.request_json("POST", "https://api.apimart.ai/v1/images/generations", headers, payload, timeout=240)
        initial_data = data.get("data")
        task_id = data.get("task_id") or data.get("id")
        if not task_id and isinstance(initial_data, dict):
            task_id = initial_data.get("task_id") or initial_data.get("id")
        if not task_id and isinstance(initial_data, list):
            for entry in initial_data:
                if isinstance(entry, dict) and (entry.get("task_id") or entry.get("id")):
                    task_id = entry.get("task_id") or entry.get("id")
                    break
        image_url = None
        raw_final = data
        if isinstance(initial_data, list) and initial_data:
            for entry in initial_data:
                if isinstance(entry, dict) and (entry.get("url") or entry.get("image_url")):
                    image_url = entry.get("url") or entry.get("image_url")
                    break
        if not image_url and task_id:
            for _ in range(120):
                time.sleep(3)
                raw_final = module.request_json("GET", f"https://api.apimart.ai/v1/tasks/{task_id}", {"Authorization": f"Bearer {key}"}, timeout=120)
                raw_data = raw_final.get("data")
                data_status = raw_data.get("status") if isinstance(raw_data, dict) else ""
                status = str(raw_final.get("status") or raw_final.get("task_status") or data_status or "").lower()
                urls = module.find_urls(raw_final)
                if urls:
                    image_url = urls[0]
                if image_url or status in {"failed", "error", "canceled", "cancelled"}:
                    break
        if not image_url:
            raise RuntimeError(f"APIMart no image url: {json.dumps(raw_final, ensure_ascii=False)[:1000]}")
        target = module.GENERATED / item["prefix"] / f"{module.safe_name(item['d'])}_apimart.png"
        module.download(image_url, target)
        return {
            "provider": "APIMart",
            "model": IMAGE2_MODEL,
            "apimart_resolution": IMAGE2_RESOLUTION,
            "apimart_quality": IMAGE2_QUALITY,
            "d": item["d"],
            "prefix": item["prefix"],
            "rows": item["rows"],
            "source_png": item["source_png"],
            "source_kind": item.get("source_kind"),
            "source_id": item.get("source_id"),
            "source_library_rel": item.get("source_library_rel"),
            "local_path": str(target),
            "image_url": image_url,
            "prompt": prompt,
            "cost_usd_est": 0.006,
            "cost_credits_est": 0.06,
            "elapsed_sec": round(time.time() - started, 2),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "raw_task": raw_final,
        }

    module.build_prompt = custom_prompt
    module.apimart_submit = custom_submit
    existing = load_results()
    done = {r.get("candidate_id") or r.get("d") for r in existing if r.get("status") == "ok"}
    prefix_totals = Counter(item["prefix"] for item in items)
    prefix_index = defaultdict(int)
    queue = []
    for item in items:
        idx = prefix_index[item["prefix"]]
        prefix_index[item["prefix"]] += 1
        if item["candidate_id"] in done:
            continue
        queue.append((item, idx, prefix_totals[item["prefix"]]))
    if limit > 0:
        queue = queue[:limit]

    results = existing
    if not queue:
        return results
    module.GENERATED.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(module.apimart_submit, item, idx, total): item for item, idx, total in queue}
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                result.update(
                    {
                        "status": "ok",
                        "candidate_id": item["candidate_id"],
                        "original_candidate_id": item["original_candidate_id"],
                        "exact_d": item["exact_d"],
                        "user_feedback": item.get("user_feedback", ""),
                        "scene_prompt": item["scene_prompt"],
                        "product_lock": item["product_lock"],
                        "risk_level": item["risk_level"],
                        "source_selection_note": item.get("source_selection_note", ""),
                        "claude_nvidia_plan_review": str(
                            Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_full_print_20260707\claude_nvidia_192_redo17_v2_after_block_review_20260707.md")
                        ),
                    }
                )
            except Exception as exc:
                result = {
                    "status": "error",
                    "candidate_id": item["candidate_id"],
                    "original_candidate_id": item["original_candidate_id"],
                    "exact_d": item["exact_d"],
                    "prefix": item["prefix"],
                    "source_png": item["source_png"],
                    "source_id": item.get("source_id"),
                    "error": repr(exc),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            results.append(result)
            with PROGRESS_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            save_results(results)
            print(f"{result.get('status')} {item['candidate_id']} {result.get('elapsed_sec', '-') } {result.get('error', '')[:140]}", flush=True)
    return results


def rel(path_value: str | None) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    try:
        return path.relative_to(OUT).as_posix()
    except ValueError:
        return path.as_posix()


def review_asset(path_value: str | None, asset_dir_name: str) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.exists():
        return rel(path_value)
    try:
        return path.relative_to(OUT).as_posix()
    except ValueError:
        pass
    asset_dir = OUT / "review_assets" / asset_dir_name
    asset_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem)[:140]
    target = asset_dir / f"{safe_stem}{path.suffix.lower()}"
    if not target.exists() or target.stat().st_size != path.stat().st_size:
        shutil.copy2(path, target)
    return target.relative_to(OUT).as_posix()


def build_review() -> Path:
    items = build_items()
    results = {r.get("candidate_id") or r.get("d"): r for r in load_results()}
    cards = []
    for item in items:
        result = results.get(item["candidate_id"], {})
        img = review_asset(result.get("local_path"), "results")
        src = review_asset(item.get("source_png"), "sources")
        status = result.get("status", "missing")
        safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", item["candidate_id"])
        cards.append(
            f"""
<article class="card" data-id="{html.escape(item['candidate_id'])}" data-prefix="{html.escape(item['prefix'])}">
  <header>
    <strong>{html.escape(item['candidate_id'])}</strong>
    <span>{html.escape(status)}</span>
  </header>
  <div class="meta">D: {html.escape(item['exact_d'])} / source: {html.escape(item.get('source_id',''))} / risk: {html.escape(item.get('risk_level',''))}</div>
  <div class="feedback">原反馈：{html.escape(item.get('user_feedback') or '-')}</div>
  <div class="imgs">
    <figure><figcaption>new source</figcaption><img src="{html.escape(src)}" loading="lazy"></figure>
    <figure><figcaption>image2 result</figcaption>{('<img src=\"' + html.escape(img) + '\" loading=\"lazy\">') if img else '<div class="missing">no image</div>'}</figure>
  </div>
  <div class="prompt"><b>scene</b><br>{html.escape(item.get('scene_prompt',''))}</div>
  <div class="controls">
    <button type="button" data-decision="keep" onclick="mark('{safe_id}','keep')">保留</button>
    <button type="button" data-decision="redo" onclick="mark('{safe_id}','redo')">重做</button>
    <button type="button" data-decision="reject" onclick="mark('{safe_id}','reject')">不要</button>
    <textarea id="fb_{safe_id}" placeholder="填写新的修改意见"></textarea>
  </div>
</article>"""
        )
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>0616_2_image2_192_redo17_v2_review</title>
<style>
body{{margin:0;font-family:Arial,'Microsoft YaHei',sans-serif;background:#f5f2ec;color:#1f2933}}
.bar{{position:sticky;top:0;z-index:5;background:#6d28d9;color:white;padding:12px 18px;display:flex;gap:12px;align-items:center;box-shadow:0 2px 10px #0002}}
.bar button{{border:0;border-radius:6px;padding:8px 12px;background:#14b8a6;color:white;font-weight:700;cursor:pointer}}
.wrap{{padding:16px;display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:14px}}
.card{{background:white;border:1px solid #ddd6cc;border-radius:8px;padding:12px;box-shadow:0 1px 2px #0001}}
.card header{{display:flex;justify-content:space-between;font-size:18px;margin-bottom:8px}}
.meta,.feedback{{font-size:13px;line-height:1.4;margin:4px 0;color:#334155}}
.imgs{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}}
figure{{margin:0;border:1px solid #e5e7eb;background:#fafafa;min-height:260px;display:flex;flex-direction:column}}
figcaption{{font-size:12px;background:#eee;padding:4px 6px}}
img{{max-width:100%;height:320px;object-fit:contain;display:block;margin:auto}}
.missing{{height:320px;display:flex;align-items:center;justify-content:center;color:#991b1b}}
.prompt{{font-size:12px;line-height:1.35;background:#f8fafc;border:1px solid #e2e8f0;padding:8px;margin-top:10px;max-height:120px;overflow:auto}}
.controls{{display:grid;grid-template-columns:80px 80px 80px 1fr;gap:8px;margin-top:10px;align-items:start}}
.controls button{{border:1px solid #d1d5db;border-radius:6px;background:#fff;padding:8px;cursor:pointer}}
.controls button.active[data-decision=keep]{{background:#16a34a;color:white}}
.controls button.active[data-decision=redo]{{background:#f59e0b;color:white}}
.controls button.active[data-decision=reject]{{background:#ef4444;color:white}}
textarea{{min-height:42px;resize:vertical;border:1px solid #d1d5db;border-radius:6px;padding:8px;font-family:inherit}}
</style></head><body>
<div class="bar"><b>0616_2 image2 192 redo17 v2</b><button onclick="exportJson()">导出反馈 JSON</button><button onclick="copyJson()">复制反馈 JSON</button><span id="count">{len(items)} 条</span></div>
<textarea id="jsonPreview" style="display:none;position:sticky;top:58px;z-index:20;width:calc(100% - 32px);height:180px;margin:12px 16px;border:2px solid #14b8a6;border-radius:8px;font-family:Consolas,monospace;background:#f8fafc"></textarea>
<div class="wrap">{''.join(cards)}</div>
<script>
const STORAGE_KEY='0616_2_image2_192_redo17_v2_review_state';
const state=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{}}');
function persist(){{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));}}
function mark(id,decision){{
  state[id]=state[id]||{{}};
  state[id].decision=decision;
  persist();
  document.querySelectorAll(`[id='fb_${{id}}']`).forEach(()=>{{}});
  const card=[...document.querySelectorAll('.card')].find(c=>c.querySelector(`#fb_${{id}}`));
  if(card) card.querySelectorAll('button[data-decision]').forEach(b=>b.classList.toggle('active', b.dataset.decision===decision));
}}
document.querySelectorAll('textarea[id^="fb_"]').forEach(t=>{{
  const id=t.id.slice(3);
  if(state[id]?.feedback) t.value=state[id].feedback;
  t.addEventListener('input',()=>{{state[id]=state[id]||{{}};state[id].feedback=t.value;persist();}});
}});
document.querySelectorAll('.card').forEach(card=>{{
  const raw=card.dataset.id;
  const id=raw.replace(/[^A-Za-z0-9_-]/g,'_');
  const decision=state[id]?.decision;
  if(decision) card.querySelectorAll('button[data-decision]').forEach(b=>b.classList.toggle('active', b.dataset.decision===decision));
}});
function collectFeedback(){{
  const feedback={{}};
  document.querySelectorAll('.card').forEach(card=>{{
    const raw=card.dataset.id;
    const id=raw.replace(/[^A-Za-z0-9_-]/g,'_');
    const text=(document.getElementById('fb_'+id)?.value||'').trim();
    const decision=state[id]?.decision;
    if(decision || text){{
      feedback[raw]={{decision:decision||'comment',feedback:text,prefix:card.dataset.prefix,ts:new Date().toISOString()}};
    }}
  }});
  return {{review:'0616_2_image2_192_redo17_v2_review',exported_at:new Date().toISOString(),feedback}};
}}
function showJson(data){{
  const preview=document.getElementById('jsonPreview');
  preview.style.display='block';
  preview.value=JSON.stringify(data,null,2);
  preview.focus();
  preview.select();
}}
function exportJson(){{
  const data=collectFeedback();
  showJson(data);
  const blob=new Blob([JSON.stringify(data,null,2)],{{type:'application/json'}});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='0616_2_image2_192_redo17_v2_feedback.json'; a.click();
}}
async function copyJson(){{
  const data=collectFeedback();
  showJson(data);
  try{{await navigator.clipboard.writeText(JSON.stringify(data,null,2));}}catch(e){{}}
}}
</script></body></html>"""
    review = OUT / "0616_2_image2_192_redo17_v2_review.html"
    review.write_text(page, encoding="utf-8")
    return review


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["run", "review", "plan"], default="run")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    items = build_items()
    print(json.dumps({"out": str(OUT), "items": len(items), "mode": args.mode}, ensure_ascii=False, indent=2))
    if args.mode == "run":
        run(workers=args.workers, limit=args.limit)
    if args.mode in {"run", "review"}:
        print(build_review())


if __name__ == "__main__":
    main()
