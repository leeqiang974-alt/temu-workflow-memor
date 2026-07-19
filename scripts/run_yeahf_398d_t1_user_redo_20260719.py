"""Generate the 2026-07-19 user-directed YeahF 398-D T1 redos.

The 18 candidates remain local and unbadged.  No OSS upload or workbook
writeback occurs in this runner.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import mimetypes
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image


WORKSPACE = Path(r"C:\Users\Administrator\Documents\temu自动化")
BACKEND = Path(r"D:\JackWPP\smartphoto_backend")
OUT_ROOT = WORKSPACE / r"outputs\yeahf_title_dedup_20260709\yeahf_400d_refill_20260718"
PLAN_PATH = OUT_ROOT / "t1_execution_plan_20260718.json"
OUT = Path(r"D:\temu素材库\T首图候选暂存\YeahF_398D_用户重做_20260719")
CANDIDATES = OUT / "base_candidates"
MANIFEST = OUT / "cangyuan_user_redo_manifest_20260719.json"
PROGRESS = OUT / "cangyuan_user_redo_progress_20260719.jsonl"
RUNNER_PATH = BACKEND / "scripts" / "run_cangyuan_yeahf400_t1_sample_20260717.py"

TARGETS = [
    "L043070901", "L043070903", "L043070909", "L043070906", "L043070911",
    "L043070910", "L043070913", "L043070914", "L043070916", "L043070915",
    "L058070904", "L058070906", "L058070927",
    "L068070917", "L068070915", "L068070953",
    "L076070905", "L076070903",
]

# These three paid tasks were accepted upstream before C: ran out of space.
# Recover them by task id; never submit them a second time.
RECOVERY_TASKS = {
    "L043070901": "task_37P7wsDQUVbBdrY7Eanmol3TZjmPIxUA",
    "L043070903": "task_eVcWcoqmVweAW3CacGRTktFddfYxML96",
    "L043070909": "task_gOTdC39Iuu7vZcIl11gzWTr81N1tduxR",
}

FEEDBACK = {
    "L043": (
        "LOCALIZED PRODUCT-IMMUTABLE EDIT: the folding board and every visible item "
        "touching or resting on it are an immutable foreground subject. Preserve the exact "
        "product pixels in place: same boundary, size, position, viewing angle, color, thin "
        "silhouette, hole count and locations, small center hole, raised rear detail and panel "
        "seams. Do not redraw, reconstruct, mirror, rotate, crop, cover, simplify or recolor any "
        "part of the product. Edit only the scene outside the product contour: change background "
        "materials, restrained premium palette, lighting and the identity/clothing of a useful "
        "person while keeping the same task relationship. Keep the product at its source-image "
        "scale and inspection clarity. This is a background/person/color edit, not a product "
        "generation task."
    ),
    "L058": (
        "BLACK-RED MOP BUCKET HARD LOCK: preserve the complete black-and-red mop bucket set as "
        "the main focal product. The black bucket body, red wringer/insert and red structural "
        "accents must all remain clearly visible, complete and correctly connected. Never replace "
        "it with a plain bucket, hide the black bucket, lose the red components, or make the mop "
        "more prominent than the bucket. Keep the source product boundary, size, angle and floor "
        "contact unchanged; edit only surrounding room materials, palette, light, safe props and "
        "person presentation outside the product."
    ),
    "L068": (
        "PRODUCT SCALE HARD LOCK: preserve the exact sink-side rack structure and keep it at least "
        "the same on-canvas width and height as in the source image. Do not pull the camera back, "
        "shrink the rack, turn it into background decor, crop it, or add foreground objects over it. "
        "Keep tiers, rods, tray, supports, length relationship, color and sink/counter contact. "
        "Change only non-product surroundings, restrained premium palette, lighting and safe props."
    ),
    "L076": (
        "PET-AND-PRODUCT RELATIONSHIP HARD LOCK: retain one clearly visible realistic pet using or "
        "resting naturally on the same pet mat, as in the source. The pet may change breed/color/pose "
        "slightly but must not disappear. Preserve the mat's exact visible boundary, rectangular "
        "shape, plush surface, edge binding, thickness, scale and floor contact; keep enough mat "
        "surface visible around the pet to prove the product. Do not invent side walls, cushions, "
        "raised rims or a different bed structure. Change only the surrounding room, palette, "
        "lighting and harmless decor while retaining pet contact and product truth."
    ),
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def append(record: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def main() -> None:
    os.chdir(BACKEND)
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    from app.services.reference_images import LoadedReferenceImage
    from app.services.upstream import WhataiClient

    runner = load_module(RUNNER_PATH, "cangyuan_prompt_runner_20260719")
    records_by_d = {str(row["d"]): row for row in json.loads(PLAN_PATH.read_text(encoding="utf-8"))["records"]}
    missing = [d for d in TARGETS if d not in records_by_d]
    if missing:
        raise RuntimeError(f"missing execution-plan D: {missing}")
    client = WhataiClient()
    if not client._image_api_key_value() or not client._is_cangyuan_image_base():
        raise RuntimeError("Cangyuan configuration unavailable; fake fallback forbidden")

    submissions: list[dict] = []
    records: list[dict] = []
    for d_value in TARGETS:
        item = records_by_d[d_value]
        source = Path(item["reference_image"])
        if not source.is_file():
            raise RuntimeError(f"missing approved 369 source for {d_value}: {source}")
        with Image.open(source) as image:
            width, height = image.size
        content = source.read_bytes()
        reference = LoadedReferenceImage(
            image_id=f"yeahf398-redo-{d_value}", slot_type="front", display_order=1,
            source_url=str(source), width=width, height=height,
            mime_type=mimetypes.guess_type(source.name)[0] or "image/png",
            file_size=len(content), file_name=source.name, path=source, content=content,
        )
        profile = runner.variation_profile(d_value)
        base_prompt = (
            "MODE: conservative localized reference edit. Use the supplied approved 369-D image "
            "as the sole exact-product and selling-logic anchor. Preserve useful person/task, "
            "support/contact, camera relationship and premium realism. Make a clearly different "
            "but equivalent scene by changing only non-product background, environmental palette, "
            "lighting, safe loose props and person identity/clothing where present. No readable "
            "text, logos, branding, warped hands, duplicated product or impossible contact. "
            + FEEDBACK[d_value[:4]]
            + " Square 1:1 polished ecommerce photograph."
        )
        prompt = runner.cangyuan_reference_edit_prompt(base_prompt, profile)
        started = time.monotonic()
        recovery_task = RECOVERY_TASKS.get(d_value)
        if recovery_task:
            submission = {
                "submission_id": d_value, "task_id": recovery_task,
                "upstream_endpoint": "/v1/images/edits", "task_path": "/images/edits",
                "prompt": prompt, "size": "1024x1024", "aspect_ratio": "1:1",
                "reference_images": [reference],
            }
        else:
            submission = client.submit_image_request(
                prompt=prompt, size="1024x1024", aspect_ratio="1:1",
                reference_images=[reference], error_key="yeahf398_user_redo_20260719",
            )
            if submission.get("upstream_endpoint") == "/local/fake-image" or not submission.get("task_id"):
                raise RuntimeError(f"fake/taskless response rejected for {d_value}")
        submissions.append(submission)
        record = {
            "D": d_value, "L0xx": d_value[:4],
            "status": "recovery_pending" if recovery_task else "submitted",
            "provider": "Cangyuan", "provider_label": "苍猿 gpt-image-2 用户重做",
            "model": "gpt-image-2", "mode": "localized_reference_edit",
            "source_t1": str(source), "source_sha256": sha256(source),
            "source_369_d": item.get("source_369_d"), "feedback_lock": FEEDBACK[d_value[:4]],
            "variation_profile": profile, "prompt": prompt,
            "task_id": submission.get("task_id"), "upstream_endpoint": submission.get("upstream_endpoint"),
            "submit_elapsed_sec": round(time.monotonic() - started, 2),
            "writeback": "blocked_until_user_visual_approval",
        }
        records.append(record)
        append(record)
        print(json.dumps({"submitted": d_value, "task_id": record["task_id"], "recovered": bool(recovery_task)}, ensure_ascii=False), flush=True)

    completed = client.poll_image_tasks(submissions, "yeahf398_user_redo_20260719", initial_delay_seconds=5)
    for record, submission in zip(records, submissions, strict=True):
        task_id = str(submission.get("task_id") or "")
        result = completed.get(task_id)
        if not result:
            record.update({"status": "failed", "reason": f"missing completed result task={task_id}"})
            append(record)
            continue
        content = client.download_image_bytes(submission, result, "yeahf398_user_redo_20260719")
        target = CANDIDATES / record["L0xx"] / f"{record['D']}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        record.update({
            "status": "completed", "image_url": result.get("url", ""),
            "local_path": str(target), "output_sha256": sha256(target), "bytes": len(content),
        })
        append(record)
        print(json.dumps({"completed": record["D"], "bytes": len(content)}, ensure_ascii=False), flush=True)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scope": "18 user-directed local T1 redos only",
        "provider": "Cangyuan", "model": "gpt-image-2",
        "source_policy": "approved 369 exact-D/same-family source only",
        "oss_upload": False, "workbook_writeback": False,
        "records": records,
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "finished", "completed": sum(r["status"] == "completed" for r in records), "manifest": str(MANIFEST)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
