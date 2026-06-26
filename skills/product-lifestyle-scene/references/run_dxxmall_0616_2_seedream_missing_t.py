from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import oss2

BASE = Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui")
PROJECT_WORK = Path(r"D:\Desktop\jit\T首图AI重构项目\work")
for path in (BASE / "work", PROJECT_WORK):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import generate_apply_ali_tfirst_0608 as ali_t
from product_specific_seedream_prompts import build_seedream_product_fusion_prompt
from volcengine_jimeng_client import build_seedream_generation_request, call_json, load_volc_credentials


KEY_PATH = Path(r"D:\Desktop\api\火山即梦apikey.txt")
PREFLIGHT = BASE / "work" / "0616_2_preflight_match_v2.json"
PLAN_PATH = BASE / "outputs" / "d_value_differentiation_allocator" / "d_value_differentiation_plan.json"
MATERIAL_REGISTRY = BASE / "outputs" / "final_material_xiangji_standardized" / "final_transparent_png_material_registry_filtered.json"
OUT = BASE / "outputs" / "dxxmall_0616_2_seedream_missing_t"
TASK_LIST_PATH = Path(os.environ.get("DXX_SEEDREAM_TASK_LIST", ""))
if os.environ.get("DXX_SEEDREAM_OUT"):
    OUT = Path(os.environ["DXX_SEEDREAM_OUT"])
FORCE_ALT_MATERIAL = os.environ.get("DXX_SEEDREAM_FORCE_ALT_MATERIAL", "") == "1"
VARIANT_SALT = os.environ.get("DXX_SEEDREAM_VARIANT_SALT", "default")
MODEL = "doubao-seedream-5-0-260128"
MAX_WORKERS = 2

FIXED_LAYER_PREFIXES = {"L042", "L047", "L078", "L082", "L087", "L091"}

HIGH_VALUE_SCENES = {
    "garden": [
        "upscale townhouse courtyard with cut stone path, trimmed greenery and quiet villa garden mood",
        "modern coastal patio with travertine paving, neutral outdoor furniture in the distance and curated plants",
        "premium apartment balcony garden with stone planter surfaces and soft editorial daylight",
    ],
    "cleaning": [
        "boutique hotel style laundry room with warm stone tile, folded plain towels and brushed metal details",
        "premium apartment bathroom corner with marble-look wall tile, matte storage cabinet and clean daylight",
    ],
    "kitchen": [
        "bright marble countertop kitchen with warm wood cabinets and plain ceramic tableware",
        "premium dark kitchen island with stone surface, neutral bowls and soft window light",
    ],
    "storage": [
        "designer home organization corner with warm wood shelves, linen storage boxes and no readable labels",
        "premium walk-in closet shelf with neutral fabric bins, brushed metal accents and soft daylight",
    ],
    "pet": [
        "premium living room pet area with warm wood floor, neutral rug and soft sofa in the background",
        "quiet bedroom corner with linen bedding, subtle stone side table and natural daylight",
    ],
    "fitness": [
        "boutique fitness studio with warm wood floor, neutral wall and soft daylight",
        "minimal wellness room with stone texture, plain towel stack and uncluttered floor",
    ],
    "decor": [
        "boutique lifestyle store display with stone plinth, plain glass vase and soft editorial light",
        "curated living room shelf with ceramic vase, warm wood and clean premium composition",
    ],
}

CATEGORY_BY_PREFIX = {
    "L042": "garden", "L047": "garden", "L048": "garden", "L095": "garden",
    "L058": "cleaning",
    "L063": "fitness",
    "L068": "kitchen", "L074": "kitchen", "L075": "kitchen", "L078": "kitchen", "L088": "kitchen", "L092": "kitchen", "L094": "kitchen",
    "L076": "pet", "L077": "pet",
    "L043": "storage", "L051": "storage", "L071": "storage", "L072": "storage", "L081": "storage", "L082": "storage",
    "L083": "storage", "L085": "decor", "L086": "storage", "L087": "storage", "L089": "storage", "L090": "storage", "L091": "storage", "L096": "storage",
}

REPLACEABLE_CONTENTS_BY_PREFIX = {
    "L074": "The rack frame, tiers, rods, legs and outline must not change, but replace loose tableware with plain ceramic dishes, bowls, cups and utensils in a premium kitchen style.",
    "L078": "The tray or plate structure must not change; use the input as a fixed product cutout and do not expand or redraw product details.",
    "L082": "The organizer structure must not change. Do not add side rails, sliding tracks, extra panels, new boxes, or change surface color.",
    "L087": "The tool shape, blades, handles and exterior must not change; use the input as fixed product identity.",
    "L095": "The basket structure must not change, but the loose artificial flowers or greenery may be varied into tasteful unbranded decorative stems.",
    "L076": "The pet mat shape and surface must not change; do not use a black anti-slip bottom style if it is not in the input.",
}

USAGE_CONTEXT_BY_PREFIX = {
    "L042": "Real use context: garden edging must be on lawn edge, flower bed, stone path, courtyard or patio border; never on bed, sofa, kitchen counter or indoor closet.",
    "L047": "Real use context: garden arch must stand on outdoor ground such as lawn, garden path, patio, seaside grass path or courtyard entrance; never on furniture, bed, sofa or fabric.",
    "L048": "Real use context: artificial leaf fence decoration should attach to balcony railing, garden fence, privacy screen or decor wall.",
    "L058": "Real use context: mop bucket set belongs on bathroom, laundry room, utility room or tiled cleaning floor; never on bed, dining table, sofa or wardrobe shelf.",
    "L063": "Real use context: fitness product belongs on gym floor, exercise mat, studio or home workout corner; never on kitchen counter, bed or dining table.",
    "L076": "Real use context: pet mat belongs on floor, rug, bedroom or living room pet corner; never on counter, shelf, sink or tabletop.",
    "L077": "Real use context: pet product belongs in floor-level pet area, living room rug or bedroom pet corner.",
    "L092": "Real use context: cutting board belongs on kitchen counter, sink side or food prep area; never in bedroom, bathroom or grass.",
}

REALISTIC_USAGE_CONTEXT = (
    "Place the product only in a realistic usage context matching its actual function, weight, gravity, support surface and buyer use case. "
    "The product must sit, stand, hang, lean or attach exactly where this category would naturally be used. "
    "Do not place products in premium-looking but absurd contexts, such as a barbecue grill on a bed, heavy rack floating on fabric, garden arch on a sofa, pet mat on a kitchen counter, or kitchen storage on bedroom bedding. "
    "Use believable contact shadows and physical support."
)


def upload_file(bucket: oss2.Bucket, path: Path, prefix: str, content_type: str = "image/png") -> str:
    object_key = f"{prefix}/{time.strftime('%Y%m%d')}/{uuid.uuid4().hex}_{path.name}"
    bucket.put_object_from_file(object_key, str(path), headers={"Content-Type": content_type})
    return f"https://{bucket.bucket_name}.{bucket.endpoint.replace('https://', '').replace('http://', '')}/{object_key}"


def extract_image_url(payload: dict) -> str | None:
    try:
        return payload["data"][0].get("url")
    except Exception:
        return None


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())


def content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def high_value_scene_for(task: dict) -> str:
    choices = HIGH_VALUE_SCENES.get(CATEGORY_BY_PREFIX.get(task["prefix"], "decor"), HIGH_VALUE_SCENES["decor"])
    return choices[sum(ord(ch) for ch in task["d_value"]) % len(choices)]


def build_scene_and_hint(task: dict) -> tuple[str, str]:
    prefix = task["prefix"]
    fixed_text = ""
    if prefix in FIXED_LAYER_PREFIXES:
        fixed_text = " Treat the input PNG as an unchanged product cutout layer; do not change angle, orientation, outline, material, color or structure."
    if prefix == "L047":
        fixed_text += (
            " For the arch frame, keep the original input PNG arch unchanged as the base layer. "
            "You may only ADD tasteful flowers, vines, soft fabric ribbons or silk drapes attached to the existing arch, "
            "without bending, thickening, duplicating, covering, rebuilding or changing the original black metal arch. "
            "Do not create a second front arch, do not invent extra arch legs, and do not transform the arch into a new shape."
        )
    if prefix == "L082":
        fixed_text += " Absolutely no added side rails, sliding tracks, extra side boxes or changed surface color."
    if prefix == "L087":
        fixed_text += " Keep all visible blades/tools present; no missing blades or extra tools."
    scene = (
        f"{task['scene_description']}. Upgrade it into this realistic non-infringing high-value scene: {high_value_scene_for(task)}. "
        f"Composition: {task['composition']}, product placed {task['position']}, product scale about {int(float(task['scale']) * 100)} percent of image height. "
        f"Lighting: {task['lighting']}; palette: {task['palette']}. "
        f"{REALISTIC_USAGE_CONTEXT} {USAGE_CONTEXT_BY_PREFIX.get(prefix, '')} "
        "Use subtle premium cues only: marble or travertine texture, warm wood, plain ceramic, linen, brushed metal, neutral flowers or towels when category-appropriate. "
        "Keep the product complete, clear and commercially believable. Props must stay secondary and must not touch, hide, replace or merge with product details. "
        "Do not include brand logos, monograms, readable text, luxury packaging, designer bags, watches, jewelry, cars, alcohol, candles, flames, electronic screens, toys, medicines or weapons. "
        f"{REPLACEABLE_CONTENTS_BY_PREFIX.get(prefix, '')}{fixed_text}"
    )
    hint = (
        f"DXXmall 0616-2 missing T-first for {task['d_value']}; preserve exact product identity from the input PNG; "
        "the PNG is the product reference, not a loose inspiration; generate only a premium safe surrounding scene and natural integration"
    )
    return scene, hint


def load_tasks() -> list[dict]:
    if TASK_LIST_PATH and TASK_LIST_PATH.exists():
        task_payload = json.loads(TASK_LIST_PATH.read_text(encoding="utf-8"))
        missing = task_payload.get("d_values", task_payload if isinstance(task_payload, list) else [])
    else:
        missing = json.loads(PREFLIGHT.read_text(encoding="utf-8"))["unmatched"]
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))["allocations"]
    by_d = {item["d_value"]: item for item in plan}
    fallback_by_prefix: dict[str, list[dict]] = {}
    if MATERIAL_REGISTRY.exists():
        for record in json.loads(MATERIAL_REGISTRY.read_text(encoding="utf-8")).get("records", []):
            prefix = record.get("prefix")
            standard_png = record.get("standard_png")
            if prefix and standard_png and Path(standard_png).exists():
                fallback_by_prefix.setdefault(prefix, []).append(record)

    def material_token(path_text: str) -> str:
        name = Path(path_text).name
        return re.sub(r"^(\\d+_)?", "", name).lower()

    def choose_alt_item(d_value: str, current_item: dict | None) -> dict | None:
        prefix = d_value[:4]
        candidates = fallback_by_prefix.get(prefix, [])
        if not candidates:
            return None
        current_path = str((current_item or {}).get("material_path") or "")
        current_token = material_token(current_path)
        filtered = []
        for candidate in candidates:
            candidate_path = str(candidate.get("standard_png") or "")
            if candidate_path == current_path:
                continue
            if current_token and material_token(candidate_path) == current_token:
                continue
            filtered.append(candidate)
        pool = filtered or candidates
        index = sum(ord(ch) for ch in f"{VARIANT_SALT}|{d_value}") % len(pool)
        return pool[index]
    records_path = OUT / "records.json"
    done = set()
    if records_path.exists():
        for record in json.loads(records_path.read_text(encoding="utf-8")):
            if record.get("status") == "ok":
                done.add(record.get("d_value"))
    tasks = []
    for d_value in missing:
        if d_value in done:
            continue
        item = by_d.get(d_value)
        if FORCE_ALT_MATERIAL:
            alt = choose_alt_item(d_value, item)
            if alt:
                if item:
                    item = dict(item)
                else:
                    item = {
                        "d_value": d_value,
                        "prefix": d_value[:4],
                        "first_row": None,
                        "scene_id": "fallback_premium_home_scene",
                        "scene_description": "premium home organization scene with realistic interior depth",
                        "position": "lower_right",
                        "scale": 0.32,
                        "mirror": False,
                        "mirror_allowed": True,
                        "lighting": "natural_window_light",
                        "palette": "warm_neutral",
                        "composition": "clean commercial lifestyle composition",
                        "signature": f"{d_value}|fallback|{alt.get('id', '')}",
                    }
                item["material_kind"] = alt.get("kind", "alt_material")
                item["material_path"] = alt["standard_png"]
                item["material_rel"] = alt.get("standard_png_rel", "")
                item["source_path"] = alt.get("source_path", "")
                item["signature"] = f"{item.get('signature','')}|alt-material|{alt.get('id','')}|{VARIANT_SALT}"

        if not item:
            prefix = d_value[:4]
            candidates = fallback_by_prefix.get(prefix, [])
            if not candidates:
                continue
            candidate = candidates[sum(ord(ch) for ch in d_value) % len(candidates)]
            item = {
                "d_value": d_value,
                "prefix": prefix,
                "first_row": None,
                "material_kind": candidate.get("kind", "fallback_material"),
                "material_path": candidate["standard_png"],
                "material_rel": candidate.get("standard_png_rel", ""),
                "source_path": candidate.get("source_path", ""),
                "scene_id": "fallback_premium_home_scene",
                "scene_description": "premium home organization scene with realistic interior depth",
                "position": "lower_right",
                "scale": 0.32,
                "mirror": False,
                "mirror_allowed": True,
                "lighting": "natural_window_light",
                "palette": "warm_neutral",
                "composition": "clean commercial lifestyle composition",
                "signature": f"{d_value}|fallback|{candidate.get('id', '')}",
            }
        material_path = Path(item.get("material_path") or "")
        if not material_path.exists():
            continue
        scene, hint = build_scene_and_hint(item)
        tasks.append({**item, "scene": scene, "hint": hint, "variant": "0616_2_missing_seedream"})
    return tasks


def run_one(task: dict, bucket: oss2.Bucket, credentials) -> dict:
    d_value = task["d_value"]
    prefix = task["prefix"]
    material_path = Path(task["material_path"])
    reference_url = upload_file(bucket, material_path, f"temu-jit/dxxmall-0616-2/seedream-reference/{prefix}", content_type(material_path))
    prompt = build_seedream_product_fusion_prompt(prefix, task["scene"], task["hint"])
    request_args = build_seedream_generation_request(
        credentials,
        prompt,
        model=MODEL,
        image_urls=[reference_url],
        size="2K",
    )
    status_code, response, _elapsed = call_json(*request_args, timeout=180, credentials=credentials)
    if status_code >= 400:
        raise RuntimeError(f"HTTP {status_code}: {json.dumps(response, ensure_ascii=False)[:1000]}")
    image_url = extract_image_url(response)
    if not image_url:
        raise RuntimeError(json.dumps(response, ensure_ascii=False)[:1000])
    local = OUT / "generated" / prefix / f"{d_value}_{uuid.uuid4().hex[:8]}.jpg"
    download(image_url, local)
    return {
        "status": "ok",
        "prefix": prefix,
        "d_value": d_value,
        "variant": task["variant"],
        "material_path": str(material_path),
        "reference_url": reference_url,
        "local_image": str(local),
        "image_url": image_url,
        "prompt": prompt,
        "scene": task["scene"],
        "hint": task["hint"],
    }


def build_page(records: list[dict]) -> Path:
    cards = []
    for record in records:
        if record.get("status") != "ok":
            cards.append(f"<div class='card err'><h3>{html.escape(record.get('d_value', ''))}</h3><pre>{html.escape(record.get('error', ''))}</pre></div>")
            continue
        rel = Path(record["local_image"]).relative_to(OUT).as_posix()
        cards.append(
            f"<div class='card'><h3>{html.escape(record['prefix'])} · {html.escape(record['d_value'])}</h3>"
            f"<img src='{html.escape(rel)}'><p>{html.escape(Path(record['material_path']).name)}</p></div>"
        )
    page = OUT / "dxxmall_0616_2_seedream_missing_t.html"
    page.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>0616-2 即梦缺口T首图</title>"
        "<style>body{font-family:Arial,'Microsoft YaHei',sans-serif;background:#f6f4ef;margin:24px}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px}.card{background:white;border-radius:14px;padding:12px;box-shadow:0 4px 18px #0001}"
        "img{width:100%;border-radius:10px}.err{border:2px solid #f55}h1{margin-top:0}</style></head><body>"
        f"<h1>0616-2 即梦缺口T首图 · {sum(1 for r in records if r.get('status') == 'ok')}张</h1><div class='grid'>"
        + "\n".join(cards)
        + "</div></body></html>",
        encoding="utf-8",
    )
    return page


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks()
    if not tasks:
        print(json.dumps({"message": "no pending tasks", "out": str(OUT)}, ensure_ascii=False))
        return 0
    oss_config = ali_t.ali.read_oss_config()
    bucket = oss2.Bucket(
        oss2.Auth(oss_config["access_key_id"], oss_config["access_key_secret"]),
        f"https://{oss_config['endpoint']}",
        oss_config["bucket"],
    )
    credentials = load_volc_credentials(KEY_PATH)
    records_path = OUT / "records.json"
    records = json.loads(records_path.read_text(encoding="utf-8")) if records_path.exists() else []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_one, task, bucket, credentials): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                record = future.result()
            except Exception as exc:
                record = {"status": "error", "prefix": task["prefix"], "d_value": task["d_value"], "error": str(exc)}
            records.append(record)
            records_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"d_value": record.get("d_value"), "status": record.get("status")}, ensure_ascii=False), flush=True)
    page = build_page(records)
    print(json.dumps({"records": str(records_path), "page": str(page), "ok": sum(1 for r in records if r.get("status") == "ok")}, ensure_ascii=False, indent=2))
    return 0 if all(r.get("status") == "ok" for r in records if r.get("d_value") in {t["d_value"] for t in tasks}) else 1


if __name__ == "__main__":
    raise SystemExit(main())
