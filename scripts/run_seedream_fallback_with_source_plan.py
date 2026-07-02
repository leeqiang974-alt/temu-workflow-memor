from __future__ import annotations

import html
import json
import os
import sys
import time
import urllib.request
import uuid
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
from product_specific_seedream_prompts import build_seedream_product_fusion_prompt
from volcengine_jimeng_client import build_seedream_generation_request, call_json, load_volc_credentials


OUT = Path(os.environ["OUT_DIR"])
SOURCE_PLAN_PATH = Path(os.environ["SOURCE_PLAN_PATH"])
FEEDBACK_LOCK_PATH = Path(os.environ["FEEDBACK_LOCK_PATH"])
ONLY_D_VALUES = [value.strip() for value in os.environ.get("ONLY_D_VALUES", "").split(",") if value.strip()]
WORKERS = int(os.environ.get("WORKERS", "1") or "1")
MODE = os.environ.get("MODE", "plan")
MODEL = os.environ.get("SEEDREAM_MODEL", "doubao-seedream-5-0-260128")
KEY_PATH = Path(os.environ.get("VOLC_KEY_PATH", r"D:\Desktop\api\火山即梦apikey.txt"))


def load_json(path: Path):
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


def build_prompt(item: dict) -> str:
    prefix = item["prefix"]
    scene = (
        f"{item.get('scene_lane', '')}. Color lane: {item.get('color_lane', '')}. "
        f"Composition lane: {item.get('composition_lane', '')}. "
        f"Human feedback: {item.get('feedback_cn') or item.get('review_feedback_cn') or 'redo after human review'}. "
        f"Product lock: {item.get('product_lock', '')}. "
        "This is a Seedream/Jimeng fallback after image2/APIMart failed human review. "
        "Use the assigned PNG as the strict product reference; do not reuse or imitate the failed image2 output. "
        "Make the product look natural and photographic, but avoid glossy AI-rendered plastic, surreal lighting, over-smoothed textures, fake showroom style, and impossible product geometry."
    )
    hint = (
        f"Fallback for {item['d']} after reviewed image2 failure. "
        f"Previous failed model: {item.get('fallback_of_model', 'image2/APIMart')}. "
        "Switch model and switch PNG were explicitly requested by the user. "
        "Preserve exact visible hardware and real product use; only the surrounding scene may change."
    )
    if item.get("extra_prompt"):
        hint += " " + item["extra_prompt"]
    return build_seedream_product_fusion_prompt(prefix, item["d"], scene, hint)


def load_items() -> list[dict]:
    plan = load_json(SOURCE_PLAN_PATH)
    feedback_lock = load_json(FEEDBACK_LOCK_PATH)
    plan_items = plan.get("items", {})
    feedback = feedback_lock.get("feedback", {})
    items = []
    for d, item in plan_items.items():
        if ONLY_D_VALUES and d not in ONLY_D_VALUES:
            continue
        source = Path(item["source_png"])
        if source.suffix.lower() != ".png":
            raise RuntimeError(f"{d} source is not PNG: {source}")
        if not source.exists():
            raise RuntimeError(f"{d} source missing: {source}")
        merged = dict(item)
        merged["d"] = d
        merged["prefix"] = item.get("prefix", d[:4])
        merged["feedback_cn"] = feedback.get(d, {}).get("feedback") or item.get("feedback_cn", "")
        merged["decision"] = feedback.get(d, {}).get("decision", "redo")
        merged["prompt"] = build_prompt(merged)
        items.append(merged)
    return items


def write_plan_artifacts(items: list[dict]) -> None:
    rows = []
    for item in items:
        rows.append(
            {
                "d": item["d"],
                "prefix": item["prefix"],
                "model": MODEL,
                "source_png": item["source_png"],
                "source_id": item.get("source_id"),
                "source_kind": item.get("source_kind"),
                "fallback_of": item.get("fallback_of"),
                "feedback_cn": item.get("feedback_cn"),
                "scene_lane": item.get("scene_lane"),
                "color_lane": item.get("color_lane"),
                "composition_lane": item.get("composition_lane"),
                "product_lock": item.get("product_lock"),
                "extra_prompt": item.get("extra_prompt", ""),
            }
        )
    save_json(OUT / "seedream_fallback_source_allocation_plan.json", {"items": rows})
    md = [
        "# Seedream fallback source allocation plan",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- target_count: {len(rows)}",
        f"- model: `{MODEL}`",
        f"- feedback_lock: `{FEEDBACK_LOCK_PATH}`",
        f"- source_plan: `{SOURCE_PLAN_PATH}`",
        "",
        "| D | source_id | scene | color | composition | feedback |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        clean = {key: str(value or "").replace("|", "/") for key, value in row.items()}
        md.append("| {d} | {source_id} | {scene_lane} | {color_lane} | {composition_lane} | {feedback_cn} |".format(**clean))
    (OUT / "seedream_fallback_source_allocation_plan.md").write_text("\n".join(md), encoding="utf-8")


def run_one(item: dict, bucket: oss2.Bucket, credentials) -> dict:
    source = Path(item["source_png"])
    reference_url = upload_file(bucket, source, f"temu-jit/dxxmall-0616-2/seedream-fallback-reference/{item['prefix']}")
    method, url, headers, body = build_seedream_generation_request(
        credentials,
        item["prompt"],
        model=MODEL,
        image_urls=[reference_url],
        size="2K",
    )
    status_code, payload, elapsed = call_json(method, url, headers, body, timeout=180, credentials=credentials)
    response = {"status": status_code, "payload": payload, "elapsed": elapsed}
    image_url = extract_image_url(payload)
    if status_code >= 400 or not image_url:
        raise RuntimeError(json.dumps(response, ensure_ascii=False)[:1600])
    local = OUT / "generated" / item["prefix"] / f"{item['d']}_seedream_fallback_{uuid.uuid4().hex[:8]}.jpg"
    download(image_url, local)
    return {
        "status": "ok",
        "provider": "Volcengine",
        "model": MODEL,
        "run_type": "seedream_fallback_after_image2_review",
        "d": item["d"],
        "prefix": item["prefix"],
        "source_png": str(source),
        "source_kind": item.get("source_kind"),
        "source_id": item.get("source_id"),
        "reference_url": reference_url,
        "local_image": str(local),
        "image_url": image_url,
        "fallback_of": item.get("fallback_of"),
        "fallback_of_model": item.get("fallback_of_model", "image2/APIMart"),
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


def run_items(items: list[dict]) -> list[dict]:
    oss_config = ali_t.ali.read_oss_config()
    bucket = oss2.Bucket(
        oss2.Auth(oss_config["access_key_id"], oss_config["access_key_secret"]),
        f"https://{oss_config['endpoint']}",
        oss_config["bucket"],
    )
    credentials = load_volc_credentials(KEY_PATH)
    records_path = OUT / "seedream_fallback_results.json"
    progress_path = OUT / "seedream_fallback_progress.jsonl"
    records = load_json(records_path) if records_path.exists() else []
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(run_one, item, bucket, credentials): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                record = future.result()
            except Exception as error:
                record = {
                    "status": "error",
                    "provider": "Volcengine",
                    "model": MODEL,
                    "run_type": "seedream_fallback_after_image2_review",
                    "d": item["d"],
                    "prefix": item["prefix"],
                    "source_png": item.get("source_png"),
                    "source_kind": item.get("source_kind"),
                    "source_id": item.get("source_id"),
                    "fallback_of": item.get("fallback_of"),
                    "feedback_cn": item.get("feedback_cn"),
                    "error": str(error),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            records.append(record)
            with progress_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            save_json(records_path, records)
            print(f"{record['status']} {record['d']} {record.get('elapsed_sec','-')}s {record.get('error','')[:120]}", flush=True)
    return records


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    items = load_items()
    write_plan_artifacts(items)
    print(json.dumps({"mode": MODE, "out": str(OUT), "items": len(items), "workers": WORKERS, "model": MODEL}, ensure_ascii=False, indent=2))
    if MODE == "run":
        run_items(items)


if __name__ == "__main__":
    main()
