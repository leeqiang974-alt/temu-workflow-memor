from __future__ import annotations

import html
import importlib.util
import json
import os
import re
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
WORKBOOK = Path(
    os.environ.get(
        "WORKBOOK",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702\0616-2_197_最终回传_硬校验修复_L051060505_C列删第1图_20260702.xlsx",
    )
)
ORIGINAL_OUT = Path(
    os.environ.get(
        "ORIGINAL_OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702",
    )
)
OUT = Path(
    os.environ.get(
        "OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_redo_61_20260703",
    )
)
FEEDBACK_LOCK_PATH = Path(
    os.environ.get(
        "FEEDBACK_LOCK_PATH",
        str(ORIGINAL_OUT / "feedback_lock_197x3_review_20260703.json"),
    )
)
ORIGINAL_PLAN_PATH = ORIGINAL_OUT / "candidate_plan_197x3.json"
ORIGINAL_RESULTS_PATH = ORIGINAL_OUT / "candidate_results_197x3.json"

MODE = os.environ.get("MODE", "plan")
WORKERS = int(os.environ.get("WORKERS", "2") or "2")
LIMIT = int(os.environ.get("LIMIT", "0") or "0")
SOURCE_SHIFT_START = int(os.environ.get("SOURCE_SHIFT_START", "3") or "3")
SOURCE_SHIFT_COUNT = int(os.environ.get("SOURCE_SHIFT_COUNT", "18") or "18")
BATCH_LABEL = os.environ.get("BATCH_LABEL", "197x3")
REDO_LABEL = os.environ.get("REDO_LABEL", "redo_61")

PLAN_PATH = OUT / f"{REDO_LABEL}_candidate_plan.json"
RESULTS_PATH = OUT / f"candidate_results_{REDO_LABEL}.json"
PROGRESS_PATH = OUT / f"candidate_progress_{REDO_LABEL}.jsonl"
REVIEW_PATH = OUT / f"0616_2_image2_{BATCH_LABEL}_{REDO_LABEL}_review.html"
SCENE_SCRIPT = Path(
    os.environ.get(
        "SCENE_SCRIPT",
        r"C:\Users\Administrator\Documents\temu自动化\scripts\run_image2_197x3_t_candidates.py",
    )
)
MATERIAL_REJECTLIST = Path(
    os.environ.get(
        "MATERIAL_REJECTLIST",
        r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\material_rejectlist.json",
    )
)


PRODUCT_LOCKS = {
    "L042": (
        "Freeze the garden edging strip/roll, fixing tabs, hole pattern, and black spiral stakes. "
        "Reviewer repeatedly rejected wrong nail/stake shape and wrong stake placement. "
        "Black spiral stakes must keep the original short spiral stake shape and correct quantity feeling. "
        "Do not create long straight pins, fence rods, loose black sticks, outward-facing spikes, decorative bars, "
        "extra lower protruding parts, or stake arrangements that look like a separate fence."
    ),
    "L043": (
        "Freeze the folding board outline, all holes, small center hole, rear raised detail, panel seams, "
        "front outward raised detail, material, and realistic scale relative to clothes. Do not turn it into a tray or pad."
    ),
    "L047": (
        "Keep exactly one black garden arch with the original rods and legs. The bottom is inserted into the ground; "
        "do not add a base, stand, second arch, or changed leg geometry."
    ),
    "L058": "Freeze bucket, mop pole, basket, handle, quantity and proportions; do not add extra buckets or extra mops.",
    "L068": "Freeze organizer/rack appearance and visible structure; do not redesign the frame or compartments.",
    "L071": "Freeze rectangular tabletop, white adjustable vertical support, black adjustment knob, X-shaped white base, and four black caster wheels. Avoid dark scenes that hide the base or wheels.",
    "L072": "Freeze silver metal rods, black connector rings, flip-door drawer fronts, top double black curved handles, and front round handles. Do not turn it into a generic shoe cabinet or drawer chest.",
    "L078": "Use the product with the correct black handle on top. Freeze handle and tray/lid structure.",
    "L081": "Freeze product appearance, shelf/rack proportions, rods and supports; only loose contents may vary.",
    "L082": (
        "Hard lock: preserve the left-right expandable function and telescoping relationship. "
        "The product side must not gain slide rails, extra tracks, drawer rails, or bottom/side rail hardware. "
        "Use under-shelf, closet shelf, cabinet partition or home storage scenes only."
    ),
    "L083": (
        "Hard lock: high appearance-drift risk. Freeze overall proportion, side straight rods, surface metal plate/sheet, "
        "supports, connectors, frame geometry and visible hardware. Do not add extra side-rod details."
    ),
    "L086": (
        "Hard lock: this product group has no white variant. The product itself must not be white. "
        "Use only non-white product material; keep drawer/basket units, front grid/transparent face, top board, "
        "vertical supports, side frame, legs and proportions unchanged."
    ),
    "L087": "Freeze source dimensions and product proportions. Reviewer rejected wrong generated size; preserve exact width/height relationship and all visible parts.",
    "L089": "Freeze product appearance and structure; do not make a generic rack.",
    "L091": (
        "Hard lock: top structure/groove/square-grid pattern is the failure point. Use strict front-facing or only slight perspective. "
        "Freeze the exact top structure, upper edge, drawer surface, transparent door, black handle and white frame. "
        "Do not add, remove, flatten, or invent top parts."
    ),
    "L095": "Freeze basket/frame/planter structure and hanging/holder geometry; do not alter visible product body.",
}

COLOR_LANES = [
    "cool white daylight, clean neutral shadows",
    "blue-gray premium daylight, low saturation",
    "fresh green natural daylight, realistic home/garden tone",
    "dark luxury daylight, controlled contrast",
    "warm wood neutral, avoid yellow cast",
    "soft cream pastel, clean ecommerce look",
    "black-white contrast, crisp but natural",
    "neutral overcast daylight, catalog realism",
]

COMPOSITION_LANES = [
    "lower-left placement, product about 28 percent of image height",
    "center-right placement, product about 32 percent of image height",
    "lower-right placement, product about 26 percent of image height",
    "front catalog composition, product about 36 percent of image height",
    "wider lifestyle scene, product about 24 percent of image height",
    "close lifestyle scene, product about 40 percent of image height",
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
    os.environ["WORKBOOK"] = str(WORKBOOK)
    os.environ["OUT_DIR"] = str(OUT)
    spec = importlib.util.spec_from_file_location("base_image2_0616_2", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base image2 script: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["base_image2_0616_2"] = module
    spec.loader.exec_module(module)
    module.OUT = OUT
    module.GENERATED = OUT / "generated"
    module.PLAN_PATH = OUT / "base_candidate_plan.json"
    module.RESULTS_PATH = OUT / "base_candidate_results.json"
    module.PROGRESS_PATH = OUT / "base_candidate_progress.jsonl"
    return module


def load_scene_module():
    spec = importlib.util.spec_from_file_location("image2_scene_bank", SCENE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load scene bank script: {SCENE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "validate_scene_banks"):
        module.validate_scene_banks()
    return module


def source_fingerprint(item: dict) -> str:
    return str(item.get("source_id") or item.get("source_png") or item.get("source_library_rel") or "")


def looks_like_white_l086_source(path_value: str | None) -> bool:
    if not path_value:
        return True
    text = path_value.lower()
    if any(token in text for token in ["white", "baise", "bai_", "_bai", "白", "白色"]):
        return True
    try:
        from PIL import Image

        image = Image.open(path_value).convert("RGBA").resize((128, 128))
        data = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
        pixels = [(r, g, b) for r, g, b, a in data if a > 20]
        if not pixels:
            return True
        avg = tuple(sum(pixel[i] for pixel in pixels) / len(pixels) for i in range(3))
        brightness = sum(avg) / 3
        saturation = sum(max(pixel) - min(pixel) for pixel in pixels) / len(pixels)
        return brightness > 185 and saturation < 18
    except Exception:
        return False


def load_material_reject_tokens() -> set[str]:
    if not MATERIAL_REJECTLIST.exists():
        return set()
    data = load_json(MATERIAL_REJECTLIST, {})
    tokens: set[str] = set()
    for item in data.get("rejected", []):
        for key in ("material_path", "source_path", "source_png", "source_id", "material_id"):
            value = item.get(key)
            if not value:
                continue
            text = str(value)
            tokens.update({text, Path(text).name, Path(text).stem})
    return tokens


MATERIAL_REJECT_TOKENS = load_material_reject_tokens()


def source_allowed(item: dict) -> bool:
    if not item.get("source_png") or not Path(item["source_png"]).exists():
        return False
    haystack = " ".join(
        str(item.get(key) or "")
        for key in ("source_id", "material_id", "source_png", "source_library_rel", "source_kind")
    )
    path = item.get("source_png")
    if path:
        haystack += f" {Path(path).name} {Path(path).stem}"
    if any(token and token in haystack for token in MATERIAL_REJECT_TOKENS):
        return False
    if item.get("prefix") == "L086" and looks_like_white_l086_source(item.get("source_png")):
        return False
    return True


def build_shift_plans(module, target_ds: set[str]) -> dict[str, list[dict]]:
    original_shift = os.environ.get("SOURCE_SHIFT")
    by_d: dict[str, list[dict]] = defaultdict(list)
    for shift in range(SOURCE_SHIFT_START, SOURCE_SHIFT_START + SOURCE_SHIFT_COUNT):
        os.environ["SOURCE_SHIFT"] = str(shift)
        for item in module.build_plan():
            if item["d"] in target_ds:
                item = dict(item)
                item["source_shift"] = shift
                by_d[item["d"]].append(item)
    if original_shift is None:
        os.environ.pop("SOURCE_SHIFT", None)
    else:
        os.environ["SOURCE_SHIFT"] = original_shift
    return by_d


def choose_source(d_value: str, failed_candidate: dict, options: list[dict], failed_sources_by_d: dict[str, set[str]]) -> tuple[dict, str]:
    failed_sources = failed_sources_by_d.get(d_value, set())
    old_source = source_fingerprint(failed_candidate)

    safe = [item for item in options if source_allowed(item)]
    primary = [item for item in safe if item.get("source_kind") != "sku_variant"]
    candidates = primary or safe

    for item in candidates:
        fp = source_fingerprint(item)
        if fp and fp not in failed_sources and fp != old_source:
            return item, "changed_source_not_in_failed_set"
    for item in candidates:
        fp = source_fingerprint(item)
        if fp and fp != old_source:
            return item, "changed_source"
    if candidates:
        return candidates[0], "safe_source_reused_due_to_limited_pool"
    return dict(failed_candidate), "no_safe_alternate_source"


def feedback_records(lock: dict) -> list[dict]:
    rows = []
    for record in lock.get("records", []):
        if record.get("decision") in {"redo", "reject"}:
            rows.append(record)
    for candidate_id, record in (lock.get("feedback") or {}).items():
        if record.get("decision") not in {"redo", "reject"}:
            continue
        row = dict(record)
        row["candidate_id"] = candidate_id
        row["review_decision"] = record.get("decision")
        row["set"] = record.get("set") or record.get("set_no")
        rows.append(row)
    return rows


def scene_lane(scene_module, prefix: str, index: int) -> str:
    choices = (getattr(scene_module, "EXPANDED_SCENE_BANK", {}) or {}).get(prefix)
    if not choices:
        choices = getattr(scene_module, "DEFAULT_EXPANDED_SCENES", [])
    if not choices:
        raise RuntimeError(f"No concrete expanded scene lane for prefix {prefix}")
    return choices[index % len(choices)]


def prompt_append(item: dict) -> str:
    chunks = [
        f"This is an image2/APIMart redo for one failed {BATCH_LABEL} candidate after human review.",
        f"Failed candidate id: {item.get('failed_candidate_id')}.",
        f"Human review feedback in Chinese: {item.get('redo_reason_cn') or 'redo requested by reviewer'}.",
        f"Assigned scene lane: {item.get('scene_lane')}.",
        f"Assigned color palette lane: {item.get('color_lane')}.",
        f"Assigned composition lane: {item.get('composition_lane')}.",
        f"Source change note: {item.get('source_selection_note')}.",
        "Do not imitate the failed image. Keep the product hardware faithful and use only safe commercial household context.",
    ]
    if item.get("product_lock"):
        chunks.append(f"Extra hard product lock: {item['product_lock']}.")
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


def build_redo_plan(module, scene_module) -> list[dict]:
    lock = load_json(FEEDBACK_LOCK_PATH)
    records = feedback_records(lock)
    old_plan = {item["candidate_id"]: item for item in load_json(ORIGINAL_PLAN_PATH, [])}
    old_results = {item.get("candidate_id"): item for item in load_json(ORIGINAL_RESULTS_PATH, []) if item.get("candidate_id")}
    target_ds = {record["D"] for record in records}
    shift_plans = build_shift_plans(module, target_ds)

    failed_sources_by_d: dict[str, set[str]] = defaultdict(set)
    for record in records:
        old = old_plan.get(record["candidate_id"], {})
        fp = source_fingerprint(old)
        if fp:
            failed_sources_by_d[record["D"]].add(fp)

    prefix_seen = defaultdict(int)
    items = []
    for record in records:
        failed_candidate = old_plan.get(record["candidate_id"])
        if not failed_candidate:
            raise RuntimeError(f"Missing original candidate plan: {record['candidate_id']}")
        d_value = record["D"]
        prefix = record["prefix"]
        index = prefix_seen[prefix]
        prefix_seen[prefix] += 1
        chosen, note = choose_source(d_value, failed_candidate, shift_plans.get(d_value, []), failed_sources_by_d)
        item = dict(chosen)
        redo_id = f"{record['candidate_id']}__redo1"
        item["d"] = redo_id
        item["candidate_id"] = redo_id
        item["original_d"] = d_value
        item["failed_candidate_id"] = record["candidate_id"]
        item["failed_set"] = record.get("set")
        item["review_decision"] = record.get("review_decision") or record.get("decision")
        item["redo_reason_cn"] = record.get("feedback") or ""
        item["redo_of"] = old_results.get(record["candidate_id"], {}).get("local_path")
        item["old_source_png"] = failed_candidate.get("source_png")
        item["old_source_id"] = failed_candidate.get("source_id")
        item["source_selection_note"] = note
        item["source_changed"] = source_fingerprint(item) != source_fingerprint(failed_candidate)
        item["run_type"] = f"image2_{BATCH_LABEL}_candidate_redo_from_feedback"
        item["scene_lane"] = scene_lane(scene_module, prefix, index)
        item["color_lane"] = COLOR_LANES[index % len(COLOR_LANES)]
        item["composition_lane"] = COMPOSITION_LANES[index % len(COMPOSITION_LANES)]
        item["product_lock"] = PRODUCT_LOCKS.get(prefix, "")
        item["redo_prompt_append"] = prompt_append(item)
        if not source_allowed(item):
            item["status"] = "blocked_no_nonwhite_source"
        items.append(item)
    save_json(PLAN_PATH, items)
    write_plan_summary(items)
    return items


def write_plan_summary(items: list[dict]) -> None:
    counts = Counter(item["prefix"] for item in items)
    changed = sum(1 for item in items if item.get("source_changed"))
    blocked = [item for item in items if item.get("status") == "blocked_no_nonwhite_source"]
    rows = [
        f"# {BATCH_LABEL} image2 candidate-level redo plan",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- workbook: `{WORKBOOK}`",
        f"- feedback_lock: `{FEEDBACK_LOCK_PATH}`",
        f"- output: `{OUT}`",
        f"- batch_label: {BATCH_LABEL}",
        f"- redo_label: {REDO_LABEL}",
        f"- redo_candidates: {len(items)}",
        f"- source_changed: {changed}",
        f"- blocked_no_nonwhite_source: {len(blocked)}",
        f"- provider/model: APIMart / gpt-image-2",
        "",
        "## Prefix Counts",
        "",
        "| prefix | redo candidates |",
        "|---|---:|",
    ]
    for prefix in sorted(counts):
        rows.append(f"| {prefix} | {counts[prefix]} |")
    rows.extend(
        [
            "",
            "## Redo Items",
            "",
            "| redo id | original D | old source | new source | source note | feedback |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in items:
        values = {
            "redo_id": item["candidate_id"],
            "d": item["original_d"],
            "old": item.get("old_source_id") or "",
            "new": item.get("source_id") or "",
            "note": item.get("source_selection_note") or "",
            "feedback": item.get("redo_reason_cn") or "",
        }
        values = {key: str(value).replace("|", "/") for key, value in values.items()}
        rows.append("| {redo_id} | {d} | {old} | {new} | {note} | {feedback} |".format(**values))
    (OUT / f"{REDO_LABEL}_candidate_plan.md").write_text("\n".join(rows), encoding="utf-8")


def existing_success() -> set[str]:
    done = set()
    for item in load_json(RESULTS_PATH, []):
        local_path = item.get("local_path")
        if item.get("candidate_id") and local_path and Path(local_path).exists() and item.get("status") != "error":
            done.add(item["candidate_id"])
    return done


def run_items(module, items: list[dict]) -> list[dict]:
    runnable = [item for item in items if item.get("status") != "blocked_no_nonwhite_source" and item.get("source_png")]
    done = existing_success()
    prefix_totals = Counter(item["prefix"] for item in runnable)
    prefix_seen = defaultdict(int)
    queue = []
    for item in runnable:
        index = prefix_seen[item["prefix"]]
        prefix_seen[item["prefix"]] += 1
        if item["candidate_id"] in done:
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
            for key in [
                "candidate_id",
                "original_d",
                "failed_candidate_id",
                "failed_set",
                "review_decision",
                "redo_reason_cn",
                "redo_of",
                "old_source_png",
                "old_source_id",
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
        (ORIGINAL_OUT.resolve(), f"/outputs/{ORIGINAL_OUT.name}"),
        (Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs").resolve(), "/outputs"),
    ]
    for root, prefix in mappings:
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            continue
        return prefix + "/" + quote(rel.as_posix(), safe="/")
    return ""


def load_success_results() -> dict[str, dict]:
    rows = {}
    for item in load_json(RESULTS_PATH, []):
        local_path = item.get("local_path")
        if item.get("status") == "ok" and local_path and Path(local_path).exists():
            rows[item["candidate_id"]] = item
    return rows


def build_review() -> Path:
    plan = load_json(PLAN_PATH, [])
    results = load_success_results()
    old_results = {item.get("candidate_id"): item for item in load_json(ORIGINAL_RESULTS_PATH, []) if item.get("candidate_id")}
    cards = []
    for item in plan:
        result = results.get(item["candidate_id"])
        old = old_results.get(item.get("failed_candidate_id"))
        cards.append(
            f"""
            <article class="card" data-candidate="{_escape(item['candidate_id'])}" data-prefix="{_escape(item['prefix'])}">
              <div class="meta">
                <b>{_escape(item['prefix'])}</b> · {_escape(item['original_d'])} · failed {_escape(item.get('failed_candidate_id'))} · redo {_escape(item['candidate_id'])}<br>
                source {_escape(item.get('source_kind'))}:{_escape(item.get('source_id'))} · old source {_escape(item.get('old_source_id'))} · {_escape(item.get('source_selection_note'))}
              </div>
              <div class="imgs">
                <figure><img class="zoomable" src="{_escape(_url_for_local_path(item.get('redo_of') or (old or {}).get('local_path')))}" loading="lazy"><figcaption>failed candidate</figcaption></figure>
                <figure><img class="zoomable" src="{_escape(_url_for_local_path(item.get('source_png')))}" loading="lazy"><figcaption>new source PNG</figcaption></figure>
                <figure><img class="zoomable" src="{_escape(_url_for_local_path((result or {}).get('local_path')))}" loading="lazy"><figcaption>{'generated' if result else _escape(item.get('status') or 'pending')}</figcaption></figure>
              </div>
              <div class="feedback">用户反馈：{_escape(item.get('redo_reason_cn'))}</div>
              <div class="actions">
                <button onclick="mark('{_escape(item['candidate_id'])}','keep')">保留</button>
                <button onclick="mark('{_escape(item['candidate_id'])}','redo')">重做</button>
                <button onclick="mark('{_escape(item['candidate_id'])}','reject')">不要</button>
                <input id="fb-{_escape(item['candidate_id'])}" placeholder="反馈：错误点/可保留原因">
                <span class="status" id="st-{_escape(item['candidate_id'])}">未筛选</span>
              </div>
              <details><summary>prompt</summary><pre>{_escape((result or {}).get('prompt') or item.get('redo_prompt_append'))}</pre></details>
            </article>
            """
        )
    prefix_counts = Counter(item["prefix"] for item in plan)
    generated_counts = Counter(item["prefix"] for item in results.values())
    stats = "".join(
        f"<tr><td>{_escape(prefix)}</td><td>{prefix_counts[prefix]}</td><td>{generated_counts[prefix]}</td></tr>"
        for prefix in sorted(prefix_counts)
    )
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>0616-2 image2 {BATCH_LABEL} {REDO_LABEL} 复核</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;margin:0;background:#f6f4ef;color:#1f2933}}
header{{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #ddd;padding:12px 18px;box-shadow:0 2px 10px rgba(0,0,0,.06)}}
.wrap{{padding:16px;max-width:1680px;margin:auto}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin:0 0 18px 0;padding:12px;box-shadow:0 1px 4px rgba(0,0,0,.04)}}
.meta{{font-size:14px;margin-bottom:10px;color:#374151;line-height:1.45}}
.imgs{{display:grid;grid-template-columns:repeat(3,minmax(240px,1fr));gap:12px}}
figure{{margin:0;background:#fafafa;border:1px solid #e5e7eb;border-radius:6px;padding:8px;text-align:center}}
figure img{{max-width:100%;height:280px;object-fit:contain;background:#fff;border-radius:4px}}
figcaption{{font-size:12px;color:#4b5563;margin-top:6px;word-break:break-all}}
.feedback{{margin:10px 0;padding:8px;background:#fff7ed;border:1px solid #fed7aa;border-radius:6px;color:#9a3412}}
.actions{{display:flex;gap:6px;margin-top:8px;align-items:center;flex-wrap:wrap}}
button{{border:0;border-radius:6px;padding:6px 10px;background:#7c3aed;color:white;cursor:pointer}}
button:nth-child(2){{background:#f59e0b}} button:nth-child(3){{background:#ef4444}}
button.active{{outline:3px solid rgba(37,99,235,.35);box-shadow:0 0 0 2px #fff inset}}
input{{flex:1;min-width:160px;padding:6px;border:1px solid #ddd;border-radius:6px}}
.status{{font-size:12px;font-weight:700;color:#6b7280;min-width:52px}}
details{{margin-top:8px}} pre{{white-space:pre-wrap;font-size:11px;max-height:180px;overflow:auto;background:#111827;color:#f9fafb;padding:8px;border-radius:6px}}
table{{border-collapse:collapse}} th,td{{border:1px solid #ddd;padding:4px 8px;font-size:12px}}
#exportBox{{width:100%;height:160px;margin-top:10px}}
#modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:999;align-items:center;justify-content:center}}
#modal img{{max-width:94vw;max-height:94vh;background:#fff}}
@media(max-width:1100px){{.imgs{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header>
  <h2>0616-2 image2 {BATCH_LABEL} {REDO_LABEL} 复核</h2>
  <div>generated_at: {_escape(datetime.now().isoformat(timespec='seconds'))} · redo candidates: {len(plan)} · generated: {len(results)}</div>
  <p>左：原失败图；中：本次新 source PNG；右：本次 image2 redo。只供复核，不自动写回表格。</p>
  <button onclick="exportFeedback()">导出筛选JSON</button>
  <button onclick="clearFeedback()">清空本页筛选</button>
  <button onclick="window.scrollTo({{top:0,behavior:'smooth'}})">回顶部</button>
  <details><summary>按L0xx统计</summary><table><tr><th>L0xx</th><th>redo数</th><th>已生成</th></tr>{stats}</table></details>
  <textarea id="exportBox" placeholder="导出的反馈 JSON 会出现在这里"></textarea>
</header>
<main class="wrap">{''.join(cards)}</main>
<div id="modal" onclick="this.style.display='none'"><img id="modalImg"></div>
<script>
const REVIEW='0616_2_image2_{BATCH_LABEL}_{REDO_LABEL}_review';
let feedback = safeLoadFeedback();
function storageGet(key){{try{{return window.localStorage && window.localStorage.getItem(key)}}catch(e){{}} return null;}}
function storageSet(key,value){{try{{window.localStorage && window.localStorage.setItem(key,value)}}catch(e){{}}}}
function storageRemove(key){{try{{window.localStorage && window.localStorage.removeItem(key)}}catch(e){{}}}}
function safeLoadFeedback(){{try{{return JSON.parse(storageGet(REVIEW+':feedback')||'{{}}')}}catch(e){{return {{}}}}}}
window.liveFeedbackValue=function(id){{const el=document.getElementById('fb-'+id); return el?el.value:'';}};
function paintDecision(id,decision){{
  const input=document.getElementById('fb-'+id);
  const section=document.querySelector('[data-candidate="'+CSS.escape(id)+'"]');
  const status=document.getElementById('st-'+id);
  if(input) input.style.borderColor=decision==='keep'?'#16a34a':(decision==='redo'?'#f59e0b':'#ef4444');
  if(section){{
    section.classList.remove('keep','redo','reject');
    section.classList.add(decision);
    section.style.outline=decision==='keep'?'4px solid #16a34a':(decision==='redo'?'4px solid #f59e0b':'4px solid #ef4444');
    section.querySelectorAll('button').forEach(btn=>btn.classList.remove('active'));
    const btn=section.querySelectorAll('button')[decision==='keep'?0:(decision==='redo'?1:2)];
    if(btn) btn.classList.add('active');
  }}
  if(status){{status.textContent=decision==='keep'?'已保留':(decision==='redo'?'已重做':'已不要'); status.style.color=decision==='keep'?'#16a34a':(decision==='redo'?'#d97706':'#dc2626');}}
}}
window.mark=function(id,decision){{feedback[id]={{decision,feedback:window.liveFeedbackValue(id),ts:new Date().toISOString()}}; storageSet(REVIEW+':feedback',JSON.stringify(feedback)); paintDecision(id,decision);}};
window.exportFeedback=function(){{Object.keys(feedback).forEach(id=>feedback[id].feedback=window.liveFeedbackValue(id)||feedback[id].feedback||''); const data={{review:REVIEW,exported_at:new Date().toISOString(),feedback}}; document.getElementById('exportBox').value=JSON.stringify(data,null,2); navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('exportBox').value).catch(()=>{{}});}};
window.clearFeedback=function(){{if(!confirm('清空本页筛选反馈？'))return; feedback={{}}; storageRemove(REVIEW+':feedback'); document.querySelectorAll('.card').forEach(el=>{{el.classList.remove('keep','redo','reject');el.style.outline='';}}); document.querySelectorAll('button.active').forEach(el=>el.classList.remove('active')); document.querySelectorAll('.status').forEach(el=>{{el.textContent='未筛选';el.style.color='#6b7280';}}); document.querySelectorAll('input[id^="fb-"]').forEach(el=>{{el.value='';el.style.borderColor='#ddd';}});}};
document.querySelectorAll('.zoomable').forEach(img=>img.addEventListener('click',()=>{{if(!img.src)return;document.getElementById('modalImg').src=img.src;document.getElementById('modal').style.display='flex';}}));
Object.entries(feedback).forEach(([id,item])=>{{const input=document.getElementById('fb-'+id);if(input)input.value=item.feedback||'';paintDecision(id,item.decision);}});
</script>
</body></html>"""
    REVIEW_PATH.write_text(page, encoding="utf-8")
    return REVIEW_PATH


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    module = load_base_module()
    scene_module = load_scene_module()
    wrap_prompt_builder(module)
    items = build_redo_plan(module, scene_module)
    blocked = sum(1 for item in items if item.get("status") == "blocked_no_nonwhite_source")
    changed = sum(1 for item in items if item.get("source_changed"))
    print(
        json.dumps(
            {
                "mode": MODE,
                "workbook": str(WORKBOOK),
                "feedback_lock": str(FEEDBACK_LOCK_PATH),
                "out": str(OUT),
                "batch_label": BATCH_LABEL,
                "redo_label": REDO_LABEL,
                "redo_candidates": len(items),
                "source_changed": changed,
                "blocked_no_nonwhite_source": blocked,
                "workers": WORKERS,
                "limit": LIMIT,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    if MODE == "run":
        run_items(module, items)
    review = build_review()
    print(f"REVIEW={review}", flush=True)


if __name__ == "__main__":
    main()
