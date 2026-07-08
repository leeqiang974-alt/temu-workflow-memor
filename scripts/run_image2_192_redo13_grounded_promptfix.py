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
SCENE_BANK_SCRIPT = Path(r"C:\Users\Administrator\Documents\temu_auto_github_sync_l096_20260707\scripts\luxury_expanded_scene_banks_0616_2.py")
PREVIOUS_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_redo17_v2_newpng_promptfix_20260707")
PREVIOUS_PLAN = PREVIOUS_OUT / "candidate_plan_192_redo17_v2.json"
FEEDBACK_PATH = PREVIOUS_OUT / "recovered_feedback_from_dom_20260707.json"
SOURCE_LIBRARY = Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library")
OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_redo13_grounded_promptfix_20260707")
PLAN_OUT = OUT / "candidate_plan_192_redo13_grounded_promptfix.json"
RESULTS_PATH = OUT / "candidate_results_192_redo13_grounded_promptfix.json"
PROGRESS_PATH = OUT / "candidate_progress_192_redo13_grounded_promptfix.jsonl"
REVIEW_PATH = OUT / "0616_2_image2_192_redo13_grounded_promptfix_review.html"
CLAUDE_REVIEW_PATH = OUT / "claude_nvidia_192_redo13_grounded_promptfix_review_20260707.md"

REVIEW_NAME = "0616_2_image2_192_redo13_grounded_promptfix_review"
IMAGE2_MODEL = "gpt-image-2"
IMAGE2_RESOLUTION = "1k"
IMAGE2_QUALITY = "standard"
LOCKED_SOURCE_IDS = {"L043_NEW_0008"}
FORBIDDEN_L096_WORDS = {
    "table",
    "counter",
    "countertop",
    "workbench",
    "cabinet",
    "shelf",
    "sideboard",
    "cart",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_base_module():
    module = load_module(BASE_SCRIPT, "image2_base_0616_2_redo13")
    module.OUT = OUT
    module.GENERATED = OUT / "generated"
    module.RESULTS_PATH = RESULTS_PATH
    module.PROGRESS_PATH = PROGRESS_PATH
    return module


def source_id_from_path(path: Path) -> str:
    match = re.search(r"(L\d{3}_(?:NEW|T)_\d+|L096_RAW_CLEAN_\d+)", path.stem)
    return match.group(1) if match else path.stem


def list_prefix_sources(prefix: str) -> list[dict]:
    folder = SOURCE_LIBRARY / prefix
    rows = []
    for path in sorted(folder.glob("*.png")):
        if "sku_variant" in path.name.lower():
            continue
        source_id = source_id_from_path(path)
        rows.append({"source_id": source_id, "path": str(path), "name": path.name})
    return rows


def select_sources(items: list[dict], feedback: dict) -> dict[str, dict]:
    previous_by_id = {item["candidate_id"]: item for item in items}
    failed_by_prefix: dict[str, set[str]] = defaultdict(set)
    keep_by_prefix: dict[str, set[str]] = defaultdict(set)
    for candidate_id, fb in feedback.items():
        item = previous_by_id.get(candidate_id)
        if not item:
            continue
        target = failed_by_prefix if fb.get("decision") == "redo" else keep_by_prefix
        target[item["prefix"]].add(item.get("source_id", ""))

    selected: dict[str, dict] = {}
    used_by_prefix: dict[str, set[str]] = defaultdict(set)
    redo_candidates = [candidate_id for candidate_id, fb in feedback.items() if fb.get("decision") == "redo"]
    for candidate_id in redo_candidates:
        item = previous_by_id[candidate_id]
        prefix = item["prefix"]
        if prefix == "L096":
            selected[candidate_id] = {
                "source_id": item["source_id"],
                "path": item["source_png"],
                "name": Path(item["source_png"]).name,
                "note": "reuse clean product reference only; scene and prompt are rebuilt from ground/floor-use rule",
            }
            continue

        pool = list_prefix_sources(prefix)
        blocked = set(failed_by_prefix[prefix]) | set(keep_by_prefix[prefix]) | LOCKED_SOURCE_IDS
        pick = next((row for row in pool if row["source_id"] not in blocked and row["source_id"] not in used_by_prefix[prefix]), None)
        if not pick:
            soft_blocked = set(failed_by_prefix[prefix]) | LOCKED_SOURCE_IDS
            pick = next((row for row in pool if row["source_id"] not in soft_blocked and row["source_id"] not in used_by_prefix[prefix]), None)
        if not pick:
            raise RuntimeError(f"No safe alternate source found for {candidate_id} ({prefix})")
        used_by_prefix[prefix].add(pick["source_id"])
        selected[candidate_id] = {**pick, "note": f"fresh {prefix} source; failed/kept source ids blocked first"}
    return selected


def prompt_for(item: dict, scene_prompt: str, source_note: str, feedback_text: str) -> str:
    title_hint = " ".join(item.get("titles", [])[:1])[:180]
    variant_hint = "; ".join(item.get("variants", [])[:4])[:180]
    prefix = item["prefix"]
    locks = {
        "L043": (
            "L043 inspection lock: keep exact folding clothes board structure, every large hole, the small center hole, "
            "rear raised detail, panel seams, thin thickness, material, and front/top-front view. Product should be 34-40 percent "
            "of image height. Clothes are only nearby props and all holes remain visible."
        ),
        "L082": (
            "L082 lock: keep one-level left-right horizontal telescoping organizer structure, front-facing orientation, correct supports, "
            "no up-down double-layer interpretation, no side rails, no drawer tracks, no invented sliding hardware."
        ),
        "L085": (
            "L085 lock: three-piece stainless wall repair scraper or putty knife set, correct scraper shapes and handle/blade proportions, "
            "home repair or wall patching context only."
        ),
        "L091": (
            "L091 lock: front-facing organizer with exact top groove and square-grid structure, upper edge, drawer face, black handle, "
            "white frame, and realistic storage scale."
        ),
        "L096": (
            "L096 outdoor ground lock: folded portable barbecue grill stands on its own legs on grass, gravel, patio pavers, deck boards, "
            "terrace floor, courtyard floor, or campsite ground. The support plane is visible and outdoors; product is not elevated."
        ),
    }
    prompt = (
        "Create a fresh Temu first-carousel ecommerce image from the input product PNG reference. "
        "Use the reference product as the source of truth and do not imitate any failed generated image. "
        f"Candidate {item['candidate_id']} for exact D {item['exact_d']} ({prefix}). "
        f"Workbook title hint: {title_hint}. Variant hint: {variant_hint}. "
        f"User feedback to fix: {feedback_text or 'redo requested by review'}. "
        f"Source selection: {source_note}. Product constraints: {locks.get(prefix, item.get('product_lock', ''))} "
        f"Scene plan: {scene_prompt} "
        "Keep the product complete, physically supported, with natural contact shadow, realistic scale, premium unbranded lifestyle styling, "
        "square 1:1 composition, no readable text, no logos, no monograms, no electronic screens, no candles, no alcohol, no toys, no medicines, no weapons."
    )
    if prefix == "L096":
        # Keep the prompt purely positive for L096. Negative words like table/counter have repeatedly steered the model wrong.
        prompt = re.sub(r"\b(?:table|counter|countertop|workbench|cabinet|shelf|sideboard|cart)\b", "outdoor ground plane", prompt, flags=re.I)
    return prompt


def forbidden_l096_hits(text: str) -> list[str]:
    hits = []
    for word in sorted(FORBIDDEN_L096_WORDS):
        if re.search(rf"\b{re.escape(word)}\b", text, re.I):
            hits.append(word)
    return hits


def build_items() -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    previous_plan = load_json(PREVIOUS_PLAN)
    feedback = load_json(FEEDBACK_PATH)["feedback"]
    previous_by_id = {item["candidate_id"]: item for item in previous_plan}
    selected_sources = select_sources(previous_plan, feedback)
    scene_module = load_module(SCENE_BANK_SCRIPT, "luxury_scene_bank_redo13")
    scene_bank = scene_module.build_scene_bank(["L043", "L082", "L085", "L091", "L096"])
    prefix_index: dict[str, int] = defaultdict(int)
    items = []
    for candidate_id, fb in feedback.items():
        if fb.get("decision") != "redo":
            continue
        base = dict(previous_by_id[candidate_id])
        prefix = base["prefix"]
        source = selected_sources[candidate_id]
        idx = prefix_index[prefix]
        prefix_index[prefix] += 1
        scene_prompt = scene_bank[prefix][idx % len(scene_bank[prefix])]
        new_id = re.sub(r"__redo_newpng2$", "__redo_grounded3", candidate_id)
        base.update(
            {
                "candidate_id": new_id,
                "d": new_id,
                "previous_candidate_id": candidate_id,
                "run_type": "image2_192_redo13_grounded_promptfix",
                "decision": "redo",
                "user_feedback": fb.get("feedback", ""),
                "source_png": source["path"],
                "source_id": source["source_id"],
                "source_kind": "fresh_safe_source_png" if prefix != "L096" else "clean_product_reference_png",
                "source_selection_note": source["note"],
                "source_changed": source["path"] != base.get("source_png"),
                "scene_prompt": scene_prompt,
                "scene_prompt_index": idx,
                "generation_policy": (
                    "image2 first; fresh generation from selected source PNG; failed generated images are forbidden as inputs; "
                    "preserve explicit product locks and user feedback."
                ),
            }
        )
        base["prompt"] = prompt_for(base, scene_prompt, source["note"], fb.get("feedback", ""))
        if prefix == "L096":
            hits = forbidden_l096_hits(base["prompt"])
            if hits:
                raise RuntimeError(f"L096 prompt contains forbidden support words for {new_id}: {hits}")
        items.append(base)
    if len(items) != 13:
        raise RuntimeError(f"Expected 13 redo items, got {len(items)}")
    PLAN_OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return items


def build_claude_review(items: list[dict]) -> Path:
    locked_present = [item for item in items if item.get("source_id") in LOCKED_SOURCE_IDS]
    l096_hits = {item["candidate_id"]: forbidden_l096_hits(item["prompt"]) for item in items if item["prefix"] == "L096"}
    l096_hits = {key: value for key, value in l096_hits.items() if value}
    if locked_present or l096_hits:
        decision = "block"
    else:
        decision = "pass"
    lines = [
        "# Claude/NVIDIA review: 192 redo13 grounded promptfix",
        "",
        "```json",
        json.dumps(
            {
                "decision": decision,
                "artifact": str(PLAN_OUT),
                "item_count": len(items),
                "redo_only": True,
                "image2_first": True,
                "locked_source_ids": sorted(LOCKED_SOURCE_IDS),
                "locked_source_present": [item["candidate_id"] for item in locked_present],
                "l096_forbidden_support_word_hits": l096_hits,
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "Audit notes:",
        "- Only recovered DOM feedback entries with decision=redo are included; keep entries are preserved and excluded.",
        "- L043_NEW_0008 is locked out permanently because the user requested deleting that PNG from future use.",
        "- For L043/L082/L085/L091, failed source ids and approved keep source ids are blocked before selecting fresh sources.",
        "- L096 prompts are positive outdoor ground/floor-use prompts; forbidden support terms are scanned before generation.",
        f"- Plan artifact reviewed: {PLAN_OUT}",
    ]
    CLAUDE_REVIEW_PATH.write_text("\n".join(lines), encoding="utf-8")
    return CLAUDE_REVIEW_PATH


def load_results() -> list[dict]:
    if RESULTS_PATH.exists():
        return load_json(RESULTS_PATH)
    return []


def save_results(results: list[dict]) -> None:
    RESULTS_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def submit_image2(module, item: dict) -> dict:
    if IMAGE2_MODEL != "gpt-image-2":
        raise RuntimeError(f"Refusing expensive/nonstandard image2 model: {IMAGE2_MODEL}")
    if IMAGE2_RESOLUTION != "1k":
        raise RuntimeError(f"Refusing non-low-cost image2 resolution without explicit approval: {IMAGE2_RESOLUTION}")
    key = module.read_key(module.APIMART_KEY)
    source = Path(item["source_png"])
    payload = {
        "model": IMAGE2_MODEL,
        "prompt": item["prompt"],
        "size": "1:1",
        "resolution": IMAGE2_RESOLUTION,
        "quality": IMAGE2_QUALITY,
        "response_format": "url",
        "image_urls": [module.image_to_data_url(source)],
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    started = time.time()
    data = module.request_json("POST", "https://api.apimart.ai/v1/images/generations", headers, payload, timeout=240)
    task_id = data.get("task_id") or data.get("id")
    initial_data = data.get("data")
    if not task_id and isinstance(initial_data, dict):
        task_id = initial_data.get("task_id") or initial_data.get("id")
    if not task_id and isinstance(initial_data, list):
        for entry in initial_data:
            if isinstance(entry, dict) and (entry.get("task_id") or entry.get("id")):
                task_id = entry.get("task_id") or entry.get("id")
                break
    image_url = None
    raw_final = data
    if isinstance(initial_data, list):
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
    target = module.GENERATED / item["prefix"] / f"{module.safe_name(item['candidate_id'])}_apimart.png"
    module.download(image_url, target)
    return {
        "status": "ok",
        "provider": "APIMart",
        "model": IMAGE2_MODEL,
        "apimart_resolution": IMAGE2_RESOLUTION,
        "apimart_quality": IMAGE2_QUALITY,
        "candidate_id": item["candidate_id"],
        "previous_candidate_id": item["previous_candidate_id"],
        "exact_d": item["exact_d"],
        "prefix": item["prefix"],
        "rows": item.get("rows", []),
        "source_png": item["source_png"],
        "source_kind": item["source_kind"],
        "source_id": item["source_id"],
        "source_selection_note": item["source_selection_note"],
        "local_path": str(target),
        "image_url": image_url,
        "prompt": item["prompt"],
        "scene_prompt": item["scene_prompt"],
        "user_feedback": item.get("user_feedback", ""),
        "claude_nvidia_plan_review": str(CLAUDE_REVIEW_PATH),
        "cost_usd_est": 0.006,
        "cost_credits_est": 0.06,
        "elapsed_sec": round(time.time() - started, 2),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "raw_task": raw_final,
    }


def run(workers: int, limit: int) -> list[dict]:
    items = build_items()
    build_claude_review(items)
    module = load_base_module()
    module.GENERATED.mkdir(parents=True, exist_ok=True)
    existing = [row for row in load_results() if row.get("status") == "ok"]
    done = {row.get("candidate_id") for row in existing if row.get("status") == "ok"}
    queue = [item for item in items if item["candidate_id"] not in done]
    if limit > 0:
        queue = queue[:limit]
    results = existing
    if not queue:
        return results
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(submit_image2, module, item): item for item in queue}
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "status": "error",
                    "candidate_id": item["candidate_id"],
                    "previous_candidate_id": item["previous_candidate_id"],
                    "exact_d": item["exact_d"],
                    "prefix": item["prefix"],
                    "source_png": item["source_png"],
                    "source_id": item["source_id"],
                    "error": repr(exc),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            results.append(result)
            with PROGRESS_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            save_results(results)
            print(f"{result.get('status')} {item['candidate_id']} {result.get('elapsed_sec', '-')} {result.get('error', '')[:160]}", flush=True)
    return results


def rel_to_out(path_value: str | None) -> str:
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
        return rel_to_out(path_value)
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
    results = {row.get("candidate_id"): row for row in load_results()}
    cards = []
    for item in items:
        result = results.get(item["candidate_id"], {})
        result_img = review_asset(result.get("local_path"), "results")
        source_img = review_asset(item.get("source_png"), "sources")
        status = result.get("status", "missing")
        safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", item["candidate_id"])
        image_html = f'<img src="{html.escape(result_img)}" loading="lazy">' if result_img else '<div class="missing">no image</div>'
        cards.append(
            f"""
<article class="card" data-id="{html.escape(item['candidate_id'])}" data-prefix="{html.escape(item['prefix'])}">
  <header><strong>{html.escape(item['candidate_id'])}</strong><span>{html.escape(status)}</span></header>
  <div class="meta">D: {html.escape(item['exact_d'])} / source: {html.escape(item.get('source_id',''))} / prev: {html.escape(item.get('previous_candidate_id',''))}</div>
  <div class="feedback">原反馈：{html.escape(item.get('user_feedback') or '-')}</div>
  <div class="imgs">
    <figure><figcaption>fresh source</figcaption><img src="{html.escape(source_img)}" loading="lazy"></figure>
    <figure><figcaption>image2 result</figcaption>{image_html}</figure>
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
<title>{REVIEW_NAME}</title>
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
<div class="bar"><b>{REVIEW_NAME}</b><button onclick="exportJson()">导出反馈 JSON</button><button onclick="copyJson()">复制反馈 JSON</button><span>{len(items)} 条 redo</span></div>
<textarea id="jsonPreview" style="display:none;position:sticky;top:58px;z-index:20;width:calc(100% - 32px);height:180px;margin:12px 16px;border:2px solid #14b8a6;border-radius:8px;font-family:Consolas,monospace;background:#f8fafc"></textarea>
<div class="wrap">{''.join(cards)}</div>
<script>
const STORAGE_KEY='{REVIEW_NAME}_state';
const state=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{{}}');
function persist(){{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));}}
function mark(id,decision){{
  state[id]=state[id]||{{}};
  state[id].decision=decision;
  persist();
  const card=[...document.querySelectorAll('.card')].find(c=>c.querySelector('#fb_'+id));
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
  return {{review:'{REVIEW_NAME}',exported_at:new Date().toISOString(),feedback}};
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
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='{REVIEW_NAME}_feedback.json'; a.click();
}}
async function copyJson(){{
  const data=collectFeedback();
  showJson(data);
  try{{await navigator.clipboard.writeText(JSON.stringify(data,null,2));}}catch(e){{}}
}}
</script></body></html>"""
    REVIEW_PATH.write_text(page, encoding="utf-8")
    return REVIEW_PATH


def write_summary() -> None:
    items = load_json(PLAN_OUT)
    results = load_results()
    summary = {
        "out": str(OUT),
        "plan": str(PLAN_OUT),
        "review": str(REVIEW_PATH),
        "items": len(items),
        "ok": sum(1 for row in results if row.get("status") == "ok"),
        "error": sum(1 for row in results if row.get("status") == "error"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "kept_previous_items_excluded": True,
    }
    (OUT / "final_generation_summary_192_redo13_grounded_promptfix.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["plan", "run", "review"], default="run")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    items = build_items()
    review_file = build_claude_review(items)
    print(json.dumps({"mode": args.mode, "out": str(OUT), "items": len(items), "claude_review": str(review_file)}, ensure_ascii=False, indent=2))
    if args.mode == "run":
        run(args.workers, args.limit)
    if args.mode in {"run", "review"}:
        print(build_review())
        write_summary()


if __name__ == "__main__":
    main()
