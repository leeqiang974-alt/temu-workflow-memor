"""Upload and write back the explicitly approved L095 three-grid J repair only."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import oss2
from openpyxl import load_workbook
from PIL import Image


PROJECT = Path(r"C:\Users\Administrator\Documents\temu自动化")
ROOT = PROJECT / "outputs" / "yeahf_title_dedup_20260709" / "yeahf_400d_refill_20260718"
SOURCE = ROOT / "YeahF_398D_剔除T1不可用L085两组_待J_T1回填.xlsx"
REPAIR = ROOT / "j_l095_three_grid_repair_20260718" / "l095_three_grid_j_repair_manifest.json"
OUT = ROOT / "YeahF_398D_L095三格J修正_待其余J血缘补齐.xlsx"
UPLOAD = ROOT / "j_l095_three_grid_repair_20260718" / "l095_three_grid_oss_manifest_20260718.json"
REPORT = ROOT / "YeahF_398D_L095三格J修正_写回报告_20260718.json"
PREFIX = "temu-jit/yeahf-398d/l095-three-grid-j-repair"

COMFYUI = Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui")
if str(COMFYUI / "work") not in sys.path:
    sys.path.insert(0, str(COMFYUI / "work"))
import generate_apply_ali_tfirst_0608 as ali_t


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def update_preview_json(value: object, url: str) -> str:
    payload = json.loads(clean(value))
    changed = 0
    def visit(node: Any) -> None:
        nonlocal changed
        if isinstance(node, dict):
            if "previewImgUrls" in node:
                node["previewImgUrls"] = url
                changed += 1
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)
    visit(payload)
    if changed != 1:
        raise RuntimeError(f"expected exactly one previewImgUrls field, got {changed}")
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def upload(bucket: oss2.Bucket, state: dict, path: Path, d_value: str, row: int) -> str:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    key_id = f"{row}:{digest}"
    cached = state.setdefault("uploaded", {}).get(key_id)
    if cached:
        return cached["url"]
    object_key = f"{PREFIX}/{time.strftime('%Y%m%d')}/r{row:04d}_{d_value}_{digest[:20]}.jpg"
    bucket.put_object(object_key, data, headers={"Content-Type": mimetypes.guess_type(path.name)[0] or "image/jpeg"})
    endpoint = bucket.endpoint.removeprefix("https://").removeprefix("http://")
    url = f"https://{bucket.bucket_name}.{endpoint}/{object_key}"
    state["uploaded"][key_id] = {"row": row, "D": d_value, "path": str(path), "sha256": digest, "url": url, "source": r"E:\JIT制图--新店\L095\sku文件_最终抠图PNG\3\3.png"}
    save(UPLOAD, state)
    return url


def main() -> None:
    manifest = json.loads(REPAIR.read_text(encoding="utf-8"))
    records = manifest["records"]
    if len(records) != 12:
        raise RuntimeError(f"expected 12 records, got {len(records)}")
    for item in records:
        if item["SKU"] != "L095-01" or not item["D"].startswith("L095"):
            raise RuntimeError(f"bad repair target: {item}")
        if item["confirmed_source"] != r"E:\JIT制图--新店\L095\sku文件_最终抠图PNG\3\3.png":
            raise RuntimeError(f"unapproved source: {item['confirmed_source']}")
        image = Image.open(item["candidate_local_path"])
        if image.size != (800, 800):
            raise RuntimeError(f"candidate not 800x800: {item['candidate_local_path']} {image.size}")
    config = ali_t.ali.read_oss_config()
    bucket = oss2.Bucket(oss2.Auth(config["access_key_id"], config["access_key_secret"]), f"https://{config['endpoint']}", config["bucket"])
    state = json.loads(UPLOAD.read_text(encoding="utf-8")) if UPLOAD.exists() else {"uploaded": {}}
    urls = {int(item["row"]): upload(bucket, state, Path(item["candidate_local_path"]), item["D"], int(item["row"])) for item in records}
    shutil.copy2(SOURCE, OUT)
    wb = load_workbook(OUT)
    ws = wb.active
    headers = {clean(cell.value): index + 1 for index, cell in enumerate(ws[1])}
    before = {(row, headers["预览图"]): ws.cell(row, headers["预览图"]).value for row in urls}
    before.update({(row, headers["SKC属性"]): ws.cell(row, headers["SKC属性"]).value for row in urls})
    changed: list[dict] = []
    for item in records:
        row = int(item["row"])
        if clean(ws.cell(row, headers["产品货号"]).value) != item["D"] or clean(ws.cell(row, headers["SKU货号"]).value) != "L095-01":
            raise RuntimeError(f"row identity drift at {row}")
        new_url = urls[row]
        ws.cell(row, headers["预览图"]).value = new_url
        ws.cell(row, headers["SKC属性"]).value = update_preview_json(ws.cell(row, headers["SKC属性"]).value, new_url)
        changed.append({"row": row, "D": item["D"], "G": item["G"], "SKU": "L095-01", "old_j": item["old_j"], "new_j": new_url, "source": item["confirmed_source"], "local": item["candidate_local_path"]})
    wb.save(OUT)
    # Re-import and prove that exactly the intended J/AC cells changed.
    verify = load_workbook(OUT, read_only=True, data_only=False).active
    verification: list[dict] = []
    for item in changed:
        row = item["row"]
        new_j = clean(verify.cell(row, headers["预览图"]).value)
        skc = json.loads(clean(verify.cell(row, headers["SKC属性"]).value))[0]
        ok = new_j == item["new_j"] and clean(skc.get("previewImgUrls")) == new_j and clean(skc.get("extCode")) == item["D"]
        verification.append({"row": row, "ok": ok, "J": new_j, "AC_preview": clean(skc.get("previewImgUrls")), "AC_extCode": clean(skc.get("extCode"))})
    if not all(item["ok"] for item in verification):
        raise RuntimeError("post-writeback J/AC verification failed")
    report = {"source": str(SOURCE), "output": str(OUT), "changed_cells": {"J": 12, "AC": 12}, "unchanged_columns": 52, "records": changed, "verification": verification, "oss_manifest": str(UPLOAD)}
    save(REPORT, report)
    print(json.dumps({"status": "complete", "output": str(OUT), "changed_rows": len(changed), "report": str(REPORT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
