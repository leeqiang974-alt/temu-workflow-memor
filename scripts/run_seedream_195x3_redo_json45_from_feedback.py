from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import urllib.request
import uuid
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import oss2


BASE = Path(os.environ.get("COMFYUI_BASE", r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui"))
PROJECT_WORK = Path(os.environ.get("T_FIRST_PROJECT_WORK", r"D:\Desktop\jit\T首图AI重构项目\work"))
for path in (BASE / "work", PROJECT_WORK):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import generate_apply_ali_tfirst_0608 as ali_t
from volcengine_jimeng_client import build_seedream_generation_request, call_json, load_volc_credentials


OUT = Path(
    os.environ.get(
        "OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_195x3_redo_json45_feedback_20260706",
    )
)
SOURCE_OUT = Path(
    os.environ.get(
        "SOURCE_OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_195x3_redo_json45_20260706",
    )
)
FEEDBACK_EXPORT = Path(
    os.environ.get(
        "FEEDBACK_EXPORT",
        r"C:\Users\Administrator\.codex\attachments\5e987ad8-7e2b-4c27-ba4f-047e3eb03947\pasted-text.txt",
    )
)
PLAN_PATH = SOURCE_OUT / "redo_json45_20260706_candidate_plan.json"
RESULTS_PATH = SOURCE_OUT / "candidate_results_redo_json45_20260706.json"
MATERIAL_REJECTLIST = Path(
    os.environ.get("MATERIAL_REJECTLIST", r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\material_rejectlist.json")
)
MODEL = os.environ.get("SEEDREAM_MODEL", "doubao-seedream-5-0-260128")
KEY_PATH = Path(os.environ.get("VOLC_KEY_PATH", r"D:\Desktop\api\火山即梦apikey.txt"))
MODE = os.environ.get("MODE", "plan")
WORKERS = int(os.environ.get("WORKERS", "1") or "1")
LIMIT = int(os.environ.get("LIMIT", "0") or "0")

RAW_FEEDBACK_PATH = OUT / "redo_json45_review_feedback_raw_20260706.json"
LOCK_PATH = OUT / "feedback_lock_redo_json45_seedream_20260706.json"
SOURCE_PLAN_PATH = OUT / "source_plan_seedream_from_redo_json45_feedback_20260706.json"
SOURCE_PLAN_MD = OUT / "source_plan_seedream_from_redo_json45_feedback_20260706.md"
RESULTS_OUT = OUT / "seedream_fallback_results.json"
PROGRESS_OUT = OUT / "seedream_fallback_progress.jsonl"
REVIEW_PATH = OUT / "0616_2_seedream_from_195x3_redo_json45_feedback_13_review.html"


PRODUCT_LOCKS = {
    "L042": (
        "Freeze the green/black garden edging strip or roll, fixing tabs, hole pattern, roll geometry, and black spiral stakes. "
        "The reviewer said the nails/stakes were seriously wrong. The black spiral stakes must keep the original short spiral stake shape and correct quantity feeling. "
        "Do not create long straight pins, fence rods, loose black sticks, outward-facing spikes, decorative bars, extra lower protruding parts, or a separate fence-like stake arrangement."
    ),
    "L043": (
        "Freeze the folding board outline, all holes, small center hole, rear raised detail, front raised detail, panel seams, material, thickness, and realistic scale relative to folded clothes. "
        "Do not turn it into a tray, pad, mat, generic folder, or smooth AI-designed board. If the source PNG is locked out, use a different safe L043 PNG."
    ),
    "L081": "Freeze shelf/rack proportions, panels, rods, supports, edges, color, and visible functional structure. Only loose surrounding scene props may vary.",
    "L082": (
        "Hard lock: preserve the left-right expandable/telescoping function and front-facing shelf/body relationship. "
        "Do not add side slide rails, drawer rails, bottom tracks, metal runners, or any sliding hardware not present in the source. "
        "The product must remain an under-shelf/cabinet organizer, not a drawer slide system."
    ),
    "L091": (
        "Hard lock: the top structure/groove/square-grid pattern is the repeated failure point. Use strict front-facing or only very slight perspective. "
        "Freeze the exact top structure, upper edge, drawer surface, transparent door, black handle, and white frame. "
        "Do not add, remove, flatten, rotate, or invent top parts."
    ),
}

COLOR_LANES = [
    "cool white daylight with clean neutral shadows",
    "blue-gray premium daylight, low saturation",
    "fresh green natural daylight, realistic garden/home tone",
    "dark luxury daylight with controlled contrast",
    "warm wood neutral, avoid yellow cast",
    "soft cream pastel, clean ecommerce look",
    "black-white contrast, crisp but natural",
    "neutral overcast daylight, catalog realism",
]

COMPOSITION_LANES = [
    "pulled-back lower-left placement, product about 16-20 percent of image height",
    "pulled-back center-right placement, product about 18-22 percent of image height",
    "wide lower-right placement, product about 15-19 percent of image height",
    "front catalog wide scene, product about 20-24 percent of image height for inspection",
    "wide lifestyle scene with real depth, product about 14-18 percent of image height",
    "wide practical use scene, product about 18-22 percent of image height",
]

SCENE_BANK = {
    "L042": [
        "wide garden path border scene with stone walkway, flower bed, and lawn depth; product complete near lower third, black spiral stakes visible beside the edging",
        "wide patio planter border scene with soil trough and potted greenery; product small but clear, stakes laid naturally next to roll, no separate fence",
        "wide courtyard flower-bed edge scene with gravel and grass layers; product on correct outdoor surface, pulled-back camera, realistic contact shadow",
        "wide balcony planter strip scene with railing and plant boxes; product used as garden edging, not on furniture, stakes preserved",
    ],
    "L043": [
        "wide walk-in closet island scene with folded sweaters far around the board; product on shelf, pulled-back camera, holes and rear raised detail visible",
        "wide laundry room folding counter scene with cabinets and linen background; product lower-center, board complete in a pulled-back wide frame",
        "wide wardrobe shelf organization scene with shirts as loose props; product small but clear, panel seams and center hole frozen",
        "wide boutique apparel prep table scene with real room depth; product on table, folded garments nearby but not covering holes",
        "wide compact closet floor-and-shelf scene with varied cool palette; product around 18-22 percent height, not a generic mat",
        "wide bedroom wardrobe corner scene with daylight and organized clothes; board flat, complete, holes visible, no AI redesign",
        "wide laundry cabinet scene with countertop and storage depth; product lower-left, rear raised detail preserved",
        "wide dorm closet organization scene with neutral shelves; product on correct surface, complete, clear, no oversized scale",
    ],
    "L081": [
        "wide organized home storage shelf scene with real room depth and safe household props; product lower-left, structure frozen",
        "wide pantry or utility sideboard scene with neutral daylight; product complete and clear, no structure redesign",
        "wide living room storage corner scene with shelves in background; product on believable support surface, pulled-back camera",
    ],
    "L082": [
        "wide under-sink kitchen cabinet scene with left-right expandable function visible; no side rails or drawer slides, product lower-center",
        "wide pantry shelf organization scene with telescoping width clear; product on shelf, no extra tracks, pulled-back cabinet context",
        "wide bathroom vanity lower-cabinet scene with bottles as loose props; product complete, no side rail hardware",
    ],
    "L091": [
        "wide front-facing closet organizer scene with wardrobe depth; product lower-center, top groove/grid fully visible, no angle change",
        "wide vanity counter organization scene with strict front-facing product; top structure frozen, surrounding room pulled back",
        "wide entryway cabinet storage scene with cool white daylight; product around 20-24 percent height, top grid intact",
    ],
}

DEFAULT_SCENES = [
    "wide expanded lifestyle scene with real room depth, camera pulled back, product complete and clear around 16-22 percent of image height",
    "wide realistic use scene with believable support surface, deeper background perspective, natural daylight and product lower third",
    "wide premium ecommerce scene with varied palette, safe unbranded props, and product small but inspectable",
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


def content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def upload_file(bucket: oss2.Bucket, path: Path, prefix: str) -> str:
    object_key = f"{prefix}/{time.strftime('%Y%m%d')}/{uuid.uuid4().hex}_{path.name}"
    bucket.put_object_from_file(object_key, str(path), headers={"Content-Type": content_type(path)})
    endpoint = bucket.endpoint.replace("https://", "").replace("http://", "")
    return f"https://{bucket.bucket_name}.{endpoint}/{object_key}"


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())


def extract_image_url(payload: dict) -> str | None:
    try:
        return payload["data"][0].get("url")
    except Exception:
        return None


def source_id_from_path(path: Path) -> str:
    stem = path.stem
    match = re.search(r"(L\d{3}_(?:NEW|T)_\d{4})", stem)
    if match:
        return match.group(1)
    match = re.search(r"(L\d{3})", stem)
    if match:
        return match.group(1)
    return stem


def reject_tokens() -> set[str]:
    data = load_json(MATERIAL_REJECTLIST, {"rejected": []})
    tokens: set[str] = set()
    for item in data.get("rejected", []):
        for key in ("material_path", "source_path", "source_png", "source_id", "material_id"):
            value = item.get(key)
            if not value:
                continue
            text = str(value)
            tokens.update({text, Path(text).name, Path(text).stem})
    return tokens


def safe_source(path: Path, prefix: str, blocked: set[str]) -> bool:
    text = f"{path} {path.name} {path.stem} {source_id_from_path(path)}"
    if any(token and token in text for token in blocked):
        return False
    if prefix == "L086" and any(token in text.lower() for token in ("white", "baise", "bai_", "_bai", "白", "白色")):
        return False
    return path.exists() and path.suffix.lower() == ".png"


def prefix_pool(prefix: str, current_source: Path, blocked: set[str]) -> list[Path]:
    folder = current_source.parent
    candidates = [path for path in sorted(folder.glob("*.png")) if safe_source(path, prefix, blocked)]
    return candidates


def choose_source(item: dict, feedback: str, used_by_prefix: dict[str, set[str]], bad_sources: set[str]) -> tuple[Path, str]:
    prefix = item["prefix"]
    current = Path(item["source_png"])
    current_key = str(current)
    must_change = any(token in feedback for token in ("丢弃", "废掉", "换png", "换PNG", "png废", "PNG废"))
    duplicate_in_round = current_key in used_by_prefix[prefix]
    pool = prefix_pool(prefix, current, reject_tokens() | bad_sources)
    if must_change or duplicate_in_round:
        for path in pool:
            key = str(path)
            if key != current_key and key not in used_by_prefix[prefix]:
                used_by_prefix[prefix].add(key)
                return path, "changed_source_due_to_feedback_or_prefix_duplicate"
        if must_change:
            raise RuntimeError(f"{item['candidate_id']} requires source change but no safe alternate source was found")
    used_by_prefix[prefix].add(current_key)
    return current, "kept_failed_image2_source_for_seedream_model_switch"


def scene_for(prefix: str, index: int) -> str:
    scenes = SCENE_BANK.get(prefix) or DEFAULT_SCENES
    return scenes[index % len(scenes)]


def update_material_rejectlist(bad_sources: set[str], plan_by_id: dict[str, dict], feedback: dict) -> None:
    if not bad_sources:
        return
    data = load_json(MATERIAL_REJECTLIST, {"updatedAt": "", "rejected": []})
    existing = {
        str(item.get("material_path") or item.get("source_png") or item.get("source_id") or "")
        for item in data.get("rejected", [])
    }
    additions = []
    for cid, row in feedback.items():
        text = row.get("feedback") or ""
        if not any(token in text for token in ("丢弃", "废掉", "png废", "PNG废")):
            continue
        item = plan_by_id.get(cid, {})
        source = item.get("source_png")
        if not source or source in existing:
            continue
        additions.append(
            {
                "d_value": item.get("original_d") or cid.split("__")[0],
                "prefix": item.get("prefix") or cid[:4],
                "source_id": item.get("source_id"),
                "material_path": source,
                "reason": f"用户在 195x3 redo_json45 复核反馈中要求丢弃该 PNG：{text}",
                "source": "195x3_redo_json45_seedream_feedback_20260706",
            }
        )
    if additions:
        data.setdefault("rejected", []).extend(additions)
        data["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_json(MATERIAL_REJECTLIST, data)


def build_prompt(item: dict) -> str:
    prefix = item["prefix"]
    product_lock = item.get("product_lock") or PRODUCT_LOCKS.get(prefix, "")
    return (
        "Use the input transparent PNG as the strict product reference for a Seedream/Jimeng fallback first-carousel image. "
        "This is after a reviewed image2/APIMart failure; do not reuse or imitate the failed image2 output. "
        "Apply the same first-generation restrictions: preserve the exact product body, structure, color, visible hardware, holes, rails, rods, drawers, stakes, handles, top details and silhouette; only the surrounding lifestyle scene, safe loose props, lighting, placement and scale may change. "
        f"Human review feedback in Chinese: {item.get('feedback_cn') or 'redo requested'}. "
        f"Scene direction: {item['scene_lane']}. "
        "Expanded-scene requirement: camera pulled back with a larger real room/garden/cabinet environment, visible front/mid/background layers, a real support surface, believable gravity and natural contact shadow. For rooms or gardens show several meters of contextual depth; for cabinets show at least 40-60cm of interior shelf/counter depth. The product must be complete and clear but not tightly cropped; target product size is about 14-22 percent of image height, or 20-24 percent only when fine structural inspection is required. Never make a tight product crop. "
        f"Color palette lane: {item['color_lane']}. "
        f"Composition lane: {item['composition_lane']}. "
        f"Hard product lock: {product_lock}. "
        "Use only realistic category-correct placement. Outdoor garden products stay on lawn, garden path, patio, soil, balcony planter or flower-bed surfaces. Closet/laundry/storage products stay on shelves, counters, cabinet interiors or floors where buyers actually use them. "
        "Safe Temu/ecommerce restrictions: no readable text, no logos, no branded packaging, no electronic screens, no fire, no flames, no candles, no decorative lights, no alcohol, no toys, no medicines, no weapons, no hazardous props, and no people touching or blocking the product. "
        "Avoid glossy AI-rendered plastic, surreal lighting, over-smoothed textures, fake showroom style, impossible product geometry, and random decorative scenes. "
        f"Product code: {item['candidate_id']}. Source selection: {item.get('source_selection_note')}. Original D: {item.get('original_d')}."
    )


def build_lock_and_plan() -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = load_json(FEEDBACK_EXPORT)
    save_json(RAW_FEEDBACK_PATH, raw)
    feedback = raw.get("feedback", {})
    plan_by_id = {item["candidate_id"]: item for item in load_json(PLAN_PATH)}
    result_by_id = {item.get("candidate_id"): item for item in load_json(RESULTS_PATH, []) if item.get("candidate_id")}
    redo_ids = [cid for cid, row in feedback.items() if row.get("decision") == "redo"]
    keep_ids = [cid for cid, row in feedback.items() if row.get("decision") == "keep"]

    bad_sources: set[str] = set()
    for cid in redo_ids:
        item = plan_by_id[cid]
        fb = feedback[cid].get("feedback") or ""
        if any(token in fb for token in ("丢弃", "废掉", "png废", "PNG废")):
            bad_sources.add(str(item["source_png"]))
            bad_sources.add(str(item.get("source_id") or ""))
    update_material_rejectlist(bad_sources, plan_by_id, feedback)

    used_by_prefix: dict[str, set[str]] = defaultdict(set)
    prefix_seen: dict[str, int] = defaultdict(int)
    rows = []
    for cid in redo_ids:
        source_item = dict(plan_by_id[cid])
        fb = feedback[cid].get("feedback") or ""
        prefix = source_item["prefix"]
        index = prefix_seen[prefix]
        prefix_seen[prefix] += 1
        source_path, source_note = choose_source(source_item, fb, used_by_prefix, bad_sources)
        source_item["source_png"] = str(source_path)
        source_item["source_id"] = source_id_from_path(source_path)
        source_item["source_selection_note"] = source_note
        source_item["feedback_cn"] = fb
        source_item["fallback_of"] = result_by_id.get(cid, {}).get("local_path")
        source_item["fallback_of_model"] = "image2/APIMart redo_json45"
        source_item["scene_lane"] = scene_for(prefix, index)
        source_item["color_lane"] = COLOR_LANES[index % len(COLOR_LANES)]
        source_item["composition_lane"] = COMPOSITION_LANES[index % len(COMPOSITION_LANES)]
        source_item["product_lock"] = PRODUCT_LOCKS.get(prefix, source_item.get("product_lock", ""))
        source_item["prompt"] = build_prompt(source_item)
        rows.append(source_item)

    lock = {
        "review": raw.get("review"),
        "exported_at": raw.get("exported_at"),
        "locked_at": datetime.now().isoformat(timespec="seconds"),
        "rule": "Only explicit redo from 195x3 redo_json45 review goes to Seedream fallback; explicit keep remains keep. Redo still follows first-generation hard restrictions and expanded-scene rules.",
        "source_feedback_file": str(RAW_FEEDBACK_PATH),
        "image2_redo_plan": str(PLAN_PATH),
        "image2_redo_results": str(RESULTS_PATH),
        "counts": {"explicit_feedback": len(feedback), "redo": len(redo_ids), "keep": len(keep_ids)},
        "bad_sources": sorted(bad_sources),
        "source_plan_audit": {
            "source_id_semantics": "selected_source_ids are product PNG material source ids, not generated image review ids. Seedream eligibility is determined by candidate_id review decision == redo.",
            "target_count": len(rows),
            "target_candidate_decisions": {item["candidate_id"]: feedback[item["candidate_id"]].get("decision") for item in rows},
            "keep_items_in_seedream_targets": [item["candidate_id"] for item in rows if feedback[item["candidate_id"]].get("decision") != "redo"],
            "discarded_source_ids": sorted({plan_by_id[cid].get("source_id") for cid in redo_ids if cid in plan_by_id and any(token in (feedback[cid].get("feedback") or "") for token in ("丢弃", "废掉", "png废", "PNG废"))}),
            "selected_source_ids": [item.get("source_id") for item in rows],
            "selected_source_paths_exist": {item["candidate_id"]: Path(item["source_png"]).exists() for item in rows},
            "discarded_source_referenced_in_selected_sources": any(
                item.get("source_id") in {plan_by_id[cid].get("source_id") for cid in redo_ids if cid in plan_by_id and any(token in (feedback[cid].get("feedback") or "") for token in ("丢弃", "废掉", "png废", "PNG废"))}
                for item in rows
            ),
            "feedback_prompt_origin": {item["candidate_id"]: item.get("feedback_cn") for item in rows},
            "feedback_prompt_hits": {item["candidate_id"]: (item.get("feedback_cn") or "") in item.get("prompt", "") for item in rows},
            "old_28_42_ratio_prompt_hits": [item["candidate_id"] for item in rows if "28-42" in item.get("prompt", "")],
            "expanded_scene_prompt_hits": [item["candidate_id"] for item in rows if "14-22 percent" in item.get("prompt", "") and "front/mid/background" in item.get("prompt", "")],
            "candidate_ids": [item["candidate_id"] for item in rows],
        },
        "feedback": {
            cid: {
                "decision": feedback[cid].get("decision"),
                "feedback": feedback[cid].get("feedback", ""),
                "ts": feedback[cid].get("ts"),
                "original_d": plan_by_id.get(cid, {}).get("original_d"),
                "prefix": plan_by_id.get(cid, {}).get("prefix"),
                "source_png": plan_by_id.get(cid, {}).get("source_png"),
                "source_id": plan_by_id.get(cid, {}).get("source_id"),
            }
            for cid in feedback
        },
    }
    save_json(LOCK_PATH, lock)
    save_json(SOURCE_PLAN_PATH, {"name": "seedream_from_195x3_redo_json45_feedback_20260706", "created_at": datetime.now().isoformat(timespec="seconds"), "items": {item["candidate_id"]: item for item in rows}})
    write_plan_md(rows)
    return rows


def write_plan_md(rows: list[dict]) -> None:
    lines = [
        "# Seedream fallback plan from 195x3 redo_json45 feedback",
        "",
        f"- created_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- source_feedback: `{RAW_FEEDBACK_PATH}`",
        f"- feedback_lock: `{LOCK_PATH}`",
        f"- source_plan: `{SOURCE_PLAN_PATH}`",
        f"- target_count: {len(rows)}",
        f"- provider/model: Volcengine / {MODEL}",
        "- gating: no upload/writeback; local review only",
        "- prompt change: forced pulled-back expanded scenes; product usually 14-22% image height, not tight close crop",
        "",
        "| candidate | original D | prefix | source_id | source note | scene | feedback |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in rows:
        vals = {
            "candidate": item["candidate_id"],
            "original": item.get("original_d"),
            "prefix": item.get("prefix"),
            "source": item.get("source_id"),
            "note": item.get("source_selection_note"),
            "scene": item.get("scene_lane"),
            "feedback": item.get("feedback_cn"),
        }
        vals = {key: str(value or "").replace("|", "/") for key, value in vals.items()}
        lines.append("| {candidate} | {original} | {prefix} | {source} | {note} | {scene} | {feedback} |".format(**vals))
    SOURCE_PLAN_MD.write_text("\n".join(lines), encoding="utf-8")


def run_one(item: dict, bucket: oss2.Bucket, credentials) -> dict:
    source = Path(item["source_png"])
    reference_url = upload_file(bucket, source, f"temu-jit/dxxmall-0616-2/seedream-195x3-redo-json45-reference/{item['prefix']}")
    method, url, headers, body = build_seedream_generation_request(
        credentials,
        item["prompt"],
        model=MODEL,
        image_urls=[reference_url],
        size="2K",
    )
    status_code, payload, elapsed = call_json(method, url, headers, body, timeout=180, credentials=credentials)
    image_url = extract_image_url(payload)
    response = {"status": status_code, "payload": payload, "elapsed": elapsed}
    if status_code >= 400 or not image_url:
        raise RuntimeError(json.dumps(response, ensure_ascii=False)[:1600])
    local = OUT / "generated" / item["prefix"] / f"{item['candidate_id']}_seedream_fallback_{uuid.uuid4().hex[:8]}.jpg"
    download(image_url, local)
    record = {
        "status": "ok",
        "provider": "Volcengine",
        "model": MODEL,
        "run_type": "seedream_fallback_after_195x3_redo_json45_review",
        "candidate_id": item["candidate_id"],
        "d": item["candidate_id"],
        "original_d": item.get("original_d"),
        "prefix": item["prefix"],
        "source_png": str(source),
        "source_kind": item.get("source_kind"),
        "source_id": item.get("source_id"),
        "source_selection_note": item.get("source_selection_note"),
        "reference_url": reference_url,
        "local_image": str(local),
        "local_path": str(local),
        "image_url": image_url,
        "fallback_of": item.get("fallback_of"),
        "fallback_of_model": item.get("fallback_of_model"),
        "feedback_cn": item.get("feedback_cn"),
        "scene_lane": item.get("scene_lane"),
        "color_lane": item.get("color_lane"),
        "composition_lane": item.get("composition_lane"),
        "product_lock": item.get("product_lock"),
        "prompt": item["prompt"],
        "response": response,
        "elapsed_sec": elapsed,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    return record


def run_items(rows: list[dict]) -> list[dict]:
    queue = rows[: LIMIT or None]
    existing = {item.get("candidate_id") for item in load_json(RESULTS_OUT, []) if item.get("status") == "ok" and Path(item.get("local_path", "")).exists()}
    queue = [item for item in queue if item["candidate_id"] not in existing]
    records = load_json(RESULTS_OUT, [])
    oss_config = ali_t.ali.read_oss_config()
    bucket = oss2.Bucket(
        oss2.Auth(oss_config["access_key_id"], oss_config["access_key_secret"]),
        f"https://{oss_config['endpoint']}",
        oss_config["bucket"],
    )
    credentials = load_volc_credentials(KEY_PATH)
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(run_one, item, bucket, credentials): item for item in queue}
        for future in as_completed(futures):
            item = futures[future]
            try:
                record = future.result()
            except Exception as error:
                record = {
                    "status": "error",
                    "provider": "Volcengine",
                    "model": MODEL,
                    "candidate_id": item["candidate_id"],
                    "d": item["candidate_id"],
                    "original_d": item.get("original_d"),
                    "prefix": item["prefix"],
                    "source_png": item.get("source_png"),
                    "source_id": item.get("source_id"),
                    "feedback_cn": item.get("feedback_cn"),
                    "error": str(error),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            records.append(record)
            with PROGRESS_OUT.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            save_json(RESULTS_OUT, records)
            print(f"{record['status']} {record['candidate_id']} {record.get('elapsed_sec','-')}s {record.get('error','')[:120]}", flush=True)
    return records


def as_file_url(value: str | None) -> str:
    if not value:
        return ""
    try:
        return Path(value).resolve().as_uri()
    except Exception:
        return ""


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def build_review(rows: list[dict]) -> Path:
    records = {item.get("candidate_id"): item for item in load_json(RESULTS_OUT, []) if item.get("status") == "ok"}
    cards = []
    for item in rows:
        result = records.get(item["candidate_id"], {})
        cards.append(
            f"""
<article class="card" data-candidate="{esc(item['candidate_id'])}" data-prefix="{esc(item['prefix'])}">
  <div class="meta"><b>{esc(item['prefix'])}</b> · {esc(item['original_d'])} · {esc(item['candidate_id'])}<br>
  source {esc(item.get('source_kind'))}:{esc(item.get('source_id'))} · {esc(item.get('source_selection_note'))}<br>
  反馈：{esc(item.get('feedback_cn'))}</div>
  <div class="imgs">
    <figure><img class="zoomable" src="{esc(as_file_url(item.get('fallback_of')))}" loading="lazy"><figcaption>image2 redo failed</figcaption></figure>
    <figure><img class="zoomable" src="{esc(as_file_url(item.get('source_png')))}" loading="lazy"><figcaption>Seedream source PNG</figcaption></figure>
    <figure><img class="zoomable" src="{esc(as_file_url(result.get('local_path')))}" loading="lazy"><figcaption>Seedream fallback result</figcaption></figure>
  </div>
  <div class="actions">
    <button onclick="mark('{esc(item['candidate_id'])}','keep')">保留</button>
    <button onclick="mark('{esc(item['candidate_id'])}','redo')">重做</button>
    <button onclick="mark('{esc(item['candidate_id'])}','reject')">不要</button>
    <input id="fb-{esc(item['candidate_id'])}" placeholder="反馈：错误点/可保留原因">
    <span class="status" id="st-{esc(item['candidate_id'])}">未筛选</span>
  </div>
  <details><summary>prompt</summary><pre>{esc(item.get('prompt'))}</pre></details>
</article>
"""
        )
    prefix_counts = Counter(item["prefix"] for item in rows)
    ok_counts = Counter(item.get("prefix") for item in records.values())
    stats = "".join(
        f"<tr><td>{esc(prefix)}</td><td>{prefix_counts[prefix]}</td><td>{ok_counts[prefix]}</td></tr>"
        for prefix in sorted(prefix_counts)
    )
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>0616-2 Seedream fallback 13 review</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;margin:0;background:#f6f4ef;color:#1f2933}}header{{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #ddd;padding:12px 18px;box-shadow:0 2px 10px rgba(0,0,0,.06)}}.wrap{{padding:16px;max-width:1680px;margin:auto}}.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin:0 0 18px 0;padding:12px;box-shadow:0 1px 4px rgba(0,0,0,.04)}}.meta{{font-size:14px;margin-bottom:10px;color:#374151;line-height:1.45}}.imgs{{display:grid;grid-template-columns:repeat(3,minmax(240px,1fr));gap:12px}}figure{{margin:0;background:#fafafa;border:1px solid #e5e7eb;border-radius:6px;padding:8px;text-align:center}}figure img{{max-width:100%;height:280px;object-fit:contain;background:#fff;border-radius:4px}}figcaption{{font-size:12px;color:#4b5563;margin-top:6px;word-break:break-all}}.actions{{display:flex;gap:6px;margin-top:8px;align-items:center;flex-wrap:wrap}}button{{border:0;border-radius:6px;padding:6px 10px;background:#7c3aed;color:white;cursor:pointer}}button:nth-child(2){{background:#f59e0b}}button:nth-child(3){{background:#ef4444}}button.active{{outline:3px solid rgba(37,99,235,.35);box-shadow:0 0 0 2px #fff inset}}input{{flex:1;min-width:160px;padding:6px;border:1px solid #ddd;border-radius:6px}}.status{{font-size:12px;font-weight:700;color:#6b7280;min-width:52px}}details{{margin-top:8px}}pre{{white-space:pre-wrap;font-size:11px;max-height:180px;overflow:auto;background:#111827;color:#f9fafb;padding:8px;border-radius:6px}}table{{border-collapse:collapse}}th,td{{border:1px solid #ddd;padding:4px 8px;font-size:12px}}#exportBox{{width:100%;height:160px;margin-top:10px}}#modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:999;align-items:center;justify-content:center}}#modal img{{max-width:94vw;max-height:94vh;background:#fff}}@media(max-width:1100px){{.imgs{{grid-template-columns:1fr}}}}
</style></head><body><header>
<h2>0616-2 Seedream fallback 13 复核</h2>
<div>generated_at: {esc(datetime.now().isoformat(timespec='seconds'))} · Seedream 成功: {len(records)} / {len(rows)}</div>
<p>左：image2 redo 失败图；中：Seedream source PNG；右：Seedream 结果。只供复核，不自动写回表格。</p>
<button onclick="exportFeedback()">导出筛选JSON</button><button onclick="clearFeedback()">清空本页筛选</button><button onclick="window.scrollTo({{top:0,behavior:'smooth'}})">回顶部</button>
<details><summary>按L0xx统计</summary><table><tr><th>L0xx</th><th>待Seedream</th><th>成功</th></tr>{stats}</table></details><textarea id="exportBox" placeholder="导出的反馈 JSON 会出现在这里"></textarea></header>
<main class="wrap">{''.join(cards)}</main><div id="modal" onclick="this.style.display='none'"><img id="modalImg"></div>
<script>
const REVIEW='0616_2_seedream_from_195x3_redo_json45_feedback_13_review';let feedback=safeLoadFeedback();
function storageGet(key){{try{{return window.localStorage&&window.localStorage.getItem(key)}}catch(e){{}}return null;}}
function storageSet(key,value){{try{{window.localStorage&&window.localStorage.setItem(key,value)}}catch(e){{}}}}
function storageRemove(key){{try{{window.localStorage&&window.localStorage.removeItem(key)}}catch(e){{}}}}
function safeLoadFeedback(){{try{{return JSON.parse(storageGet(REVIEW+':feedback')||'{{}}')}}catch(e){{return {{}}}}}}
window.liveFeedbackValue=function(id){{const el=document.getElementById('fb-'+id);return el?el.value:'';}};
function paintDecision(id,decision){{const input=document.getElementById('fb-'+id);const section=document.querySelector('[data-candidate="'+CSS.escape(id)+'"]');const status=document.getElementById('st-'+id);if(input)input.style.borderColor=decision==='keep'?'#16a34a':(decision==='redo'?'#f59e0b':'#ef4444');if(section){{section.style.outline=decision==='keep'?'4px solid #16a34a':(decision==='redo'?'4px solid #f59e0b':'4px solid #ef4444');section.querySelectorAll('button').forEach(btn=>btn.classList.remove('active'));const btn=section.querySelectorAll('button')[decision==='keep'?0:(decision==='redo'?1:2)];if(btn)btn.classList.add('active');}}if(status){{status.textContent=decision==='keep'?'已保留':(decision==='redo'?'已重做':'已不要');status.style.color=decision==='keep'?'#16a34a':(decision==='redo'?'#d97706':'#dc2626');}}}}
window.mark=function(id,decision){{feedback[id]={{decision,feedback:window.liveFeedbackValue(id),ts:new Date().toISOString()}};storageSet(REVIEW+':feedback',JSON.stringify(feedback));paintDecision(id,decision);}};
window.exportFeedback=function(){{Object.keys(feedback).forEach(id=>feedback[id].feedback=window.liveFeedbackValue(id)||feedback[id].feedback||'');const data={{review:REVIEW,exported_at:new Date().toISOString(),feedback}};document.getElementById('exportBox').value=JSON.stringify(data,null,2);navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('exportBox').value).catch(()=>{{}});}};
window.clearFeedback=function(){{if(!confirm('清空本页筛选反馈？'))return;feedback={{}};storageRemove(REVIEW+':feedback');document.querySelectorAll('.card').forEach(el=>el.style.outline='');document.querySelectorAll('button.active').forEach(el=>el.classList.remove('active'));document.querySelectorAll('.status').forEach(el=>{{el.textContent='未筛选';el.style.color='#6b7280';}});document.querySelectorAll('input[id^="fb-"]').forEach(el=>{{el.value='';el.style.borderColor='#ddd';}});}};
document.querySelectorAll('.zoomable').forEach(img=>img.addEventListener('click',()=>{{if(!img.src)return;document.getElementById('modalImg').src=img.src;document.getElementById('modal').style.display='flex';}}));
Object.entries(feedback).forEach(([id,item])=>{{const input=document.getElementById('fb-'+id);if(input)input.value=item.feedback||'';paintDecision(id,item.decision);}});
</script></body></html>"""
    REVIEW_PATH.write_text(page, encoding="utf-8")
    return REVIEW_PATH


def main() -> None:
    rows = build_lock_and_plan()
    print(
        json.dumps(
            {
                "mode": MODE,
                "out": str(OUT),
                "feedback_lock": str(LOCK_PATH),
                "source_plan": str(SOURCE_PLAN_PATH),
                "target_count": len(rows),
                "workers": WORKERS,
                "model": MODEL,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    if MODE == "run":
        run_items(rows)
    review = build_review(rows)
    print(f"REVIEW={review}", flush=True)


if __name__ == "__main__":
    main()
