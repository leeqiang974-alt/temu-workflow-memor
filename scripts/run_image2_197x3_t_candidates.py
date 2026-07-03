from __future__ import annotations

import importlib.util
import html
import json
import os
import sys
from collections import Counter, defaultdict
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


def _escape(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _url_for_local_path(value: str | None) -> str:
    if not value:
        return ""
    path = Path(value)
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path

    mappings = [
        (OUT.resolve(), f"/outputs/{OUT.name}"),
        (Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs").resolve(), "/outputs"),
    ]
    for root, prefix in mappings:
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            continue
        return prefix + "/" + quote(rel.as_posix(), safe="/")
    return ""


def _load_success_results() -> list[dict]:
    results = load_json(RESULTS_PATH, [])
    success = []
    for item in results:
        local_path = item.get("local_path")
        if item.get("status") == "ok" and local_path and Path(local_path).exists():
            success.append(item)
    return success


def build_review(module=None) -> Path:
    results = _load_success_results()
    by_d: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        by_d[item.get("original_d") or item.get("d") or item.get("candidate_id")].append(item)
    for items in by_d.values():
        items.sort(key=lambda item: (int(item.get("set_no") or 0), item.get("candidate_id") or ""))

    prefix_counts = Counter((d or "")[:4] for d in by_d)
    generated_counts = Counter((item.get("original_d") or item.get("d") or "")[:4] for item in results)
    stats_rows = "\n".join(
        f"<tr><td>{_escape(prefix)}</td><td>{prefix_counts[prefix]}</td><td>{generated_counts[prefix]}</td></tr>"
        for prefix in sorted(prefix_counts)
    )

    cards = []
    for original_d in sorted(by_d):
        items = by_d[original_d]
        first = items[0]
        source_url = _url_for_local_path(first.get("source_png"))
        set_figures = []
        for item in items:
            candidate_id = item.get("candidate_id") or item.get("d") or original_d
            image_url = _url_for_local_path(item.get("local_path"))
            prompt = item.get("prompt") or ""
            set_no = item.get("set_no") or "?"
            set_figures.append(
                f"""
                <section class="candidate" data-candidate="{_escape(candidate_id)}">
                  <figure>
                    <img class="zoomable generated" src="{_escape(image_url)}" loading="lazy" alt="{_escape(candidate_id)}">
                    <figcaption>set{_escape(set_no)} · {_escape(candidate_id)}</figcaption>
                  </figure>
                  <div class="actions">
                    <button onclick="mark('{_escape(candidate_id)}','keep')">保留</button>
                    <button onclick="mark('{_escape(candidate_id)}','redo')">重做</button>
                    <button onclick="mark('{_escape(candidate_id)}','reject')">不要</button>
                    <input id="fb-{_escape(candidate_id)}" placeholder="反馈：错误点/可保留原因">
                  </div>
                  <details><summary>prompt</summary><pre>{_escape(prompt)}</pre></details>
                </section>
                """
            )
        cards.append(
            f"""
            <article class="card" data-d="{_escape(original_d)}" data-prefix="{_escape(first.get('prefix'))}">
              <div class="meta"><b>{_escape(first.get('prefix'))}</b> · {_escape(original_d)} · rows {_escape(','.join(map(str, first.get('rows') or [])))} · source {_escape(first.get('source_kind'))}:{_escape(first.get('source_id'))}</div>
              <div class="compare">
                <figure class="source">
                  <img src="{_escape(source_url)}" loading="lazy" alt="source PNG">
                  <figcaption>source PNG</figcaption>
                </figure>
                <div class="sets">{''.join(set_figures)}</div>
              </div>
            </article>
            """
        )

    target = OUT / "0616_2_image2_197x3_t_candidates_review.html"
    legacy_target = OUT / "0616_2_low_cost_t_candidates_review.html"
    generated_at = datetime.now().isoformat(timespec="seconds")
    body = "\n".join(cards)
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>0616-2 image2 197x3 T首图候选复核</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;margin:0;background:#f6f4ef;color:#1f2933}}
header{{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #ddd;padding:12px 18px;box-shadow:0 2px 10px rgba(0,0,0,.06)}}
.wrap{{padding:16px;max-width:1680px;margin:auto}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin:0 0 18px 0;padding:12px;box-shadow:0 1px 4px rgba(0,0,0,.04)}}
.meta{{font-size:14px;margin-bottom:10px;color:#374151}}
.compare{{display:grid;grid-template-columns:260px 1fr;gap:14px;align-items:start}}
.sets{{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:12px}}
figure{{margin:0;background:#fafafa;border:1px solid #e5e7eb;border-radius:6px;padding:8px;text-align:center}}
figure img{{max-width:100%;height:240px;object-fit:contain;background:#fff;border-radius:4px}}
.source img{{height:260px}}
figcaption{{font-size:12px;color:#4b5563;margin-top:6px;word-break:break-all}}
.candidate{{border:1px solid #e5e7eb;border-radius:6px;padding:8px;background:#fcfcfd}}
.actions{{display:flex;gap:6px;margin-top:8px;align-items:center;flex-wrap:wrap}}
button{{border:0;border-radius:6px;padding:6px 10px;background:#7c3aed;color:white;cursor:pointer}}
button:nth-child(2){{background:#f59e0b}} button:nth-child(3){{background:#ef4444}}
input{{flex:1;min-width:160px;padding:6px;border:1px solid #ddd;border-radius:6px}}
details{{margin-top:8px}} pre{{white-space:pre-wrap;font-size:11px;max-height:160px;overflow:auto;background:#111827;color:#f9fafb;padding:8px;border-radius:6px}}
table{{border-collapse:collapse}} th,td{{border:1px solid #ddd;padding:4px 8px;font-size:12px}}
#exportBox{{width:100%;height:180px;margin-top:10px}}
#modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:999;align-items:center;justify-content:center}}
#modal img{{max-width:94vw;max-height:94vh;background:#fff}}
@media(max-width:1100px){{.compare{{grid-template-columns:1fr}}.sets{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header>
  <h2>0616-2 image2 197x3 T首图候选复核</h2>
  <div>generated_at: {_escape(generated_at)} · unique D: {len(by_d)} · candidates: {len(results)} · sets: {SETS}</div>
  <p>这是备用候选池，不代表已通过，不自动写回表格。每个 D 显示 source PNG + set1/set2/set3。</p>
  <button onclick="exportFeedback()">导出筛选JSON</button>
  <button onclick="clearFeedback()">清空本页筛选</button>
  <button onclick="window.scrollTo({{top:0,behavior:'smooth'}})">回顶部</button>
  <details><summary>按L0xx统计</summary><table><tr><th>L0xx</th><th>D数</th><th>候选数</th></tr>{stats_rows}</table></details>
  <textarea id="exportBox" placeholder="导出的反馈 JSON 会出现在这里"></textarea>
</header>
<main class="wrap">{body}</main>
<div id="modal" onclick="this.style.display='none'"><img id="modalImg"></div>
<script>
const REVIEW='0616_2_image2_197x3_t_candidates_review';
let feedback = JSON.parse(localStorage.getItem(REVIEW + ':feedback') || '{{}}');
function liveFeedbackValue(id) {{
  const el = document.getElementById('fb-' + id);
  return el ? el.value : '';
}}
function mark(id, decision) {{
  feedback[id] = {{decision, feedback: liveFeedbackValue(id), ts: new Date().toISOString()}};
  localStorage.setItem(REVIEW + ':feedback', JSON.stringify(feedback));
  const input = document.getElementById('fb-' + id);
  if (input) input.style.borderColor = decision === 'keep' ? '#16a34a' : (decision === 'redo' ? '#f59e0b' : '#ef4444');
}}
function exportFeedback() {{
  Object.keys(feedback).forEach(id => feedback[id].feedback = liveFeedbackValue(id) || feedback[id].feedback || '');
  const data = {{review: REVIEW, exported_at: new Date().toISOString(), feedback}};
  document.getElementById('exportBox').value = JSON.stringify(data, null, 2);
  navigator.clipboard && navigator.clipboard.writeText(document.getElementById('exportBox').value).catch(()=>{{}});
}}
function clearFeedback() {{
  if (!confirm('清空本页筛选反馈？')) return;
  feedback = {{}};
  localStorage.removeItem(REVIEW + ':feedback');
  document.querySelectorAll('input[id^="fb-"]').forEach(el => {{el.value=''; el.style.borderColor='#ddd';}});
}}
document.querySelectorAll('.zoomable').forEach(img => img.addEventListener('click', () => {{
  document.getElementById('modalImg').src = img.src;
  document.getElementById('modal').style.display = 'flex';
}}));
Object.entries(feedback).forEach(([id, item]) => {{
  const input = document.getElementById('fb-' + id);
  if (input) {{
    input.value = item.feedback || '';
    input.style.borderColor = item.decision === 'keep' ? '#16a34a' : (item.decision === 'redo' ? '#f59e0b' : '#ef4444');
  }}
}});
</script>
</body>
</html>"""
    target.write_text(page, encoding="utf-8")
    legacy_target.write_text(page, encoding="utf-8")
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
