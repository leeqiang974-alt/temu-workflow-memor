#!/usr/bin/env python3
"""Build a focused L043 J review with 15/30 PCS quantity labels.

This script does not write back the workbook. It creates corrected local J
candidates for user review. L043 keeps the existing good five-grid J
composition and only overlays the row quantity label at the top-left corner.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


OUT_DIR = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_192_writeback_195x3_set1_full_title_j_20260706")
AUDIT_JSON = OUT_DIR / "j_match_audit.json"
REVIEW_DIR = OUT_DIR / "l043_j_quantity_fix_review"
REVIEW_HTML = REVIEW_DIR / "index.html"
L043_SKU_ROOT = Path(r"E:\JIT制图--新店\L043\sku文件_最终抠图PNG")
SIZE = 800
CELL = SIZE // 3


def image_src(value: str | Path | None) -> str:
    if not value:
        return ""
    text = str(value)
    if text.startswith(("http://", "https://", "file://")):
        return text
    try:
        return Path(text).resolve().as_uri()
    except Exception:
        return ""


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def parse_color(record: dict[str, Any]) -> tuple[str, str, Path]:
    text = f"{record.get('G') or ''} {record.get('SKU') or record.get('SKU货号') or ''} {record.get('sku_source') or ''}".lower()
    if "灰" in text or "gray" in text or "grey" in text or r"\灰" in text or "/灰" in text:
        return "gray", "灰色", L043_SKU_ROOT / "灰" / "灰.png"
    return "white", "白色", L043_SKU_ROOT / "白" / "白.png"


def parse_quantity(record: dict[str, Any]) -> tuple[str, str]:
    text = f"{record.get('G') or ''} {record.get('SKU') or record.get('SKU货号') or ''}"
    normalized = re.sub(r"\s+", "", text)
    if "30" in normalized or "三十" in normalized:
        return "30 PCS", "30"
    if "15" in normalized or "十五" in normalized:
        return "15 PCS", "15"
    return "", "missing_quantity"


def draw_label(draw: ImageDraw.ImageDraw, x: int, y: int, label: str) -> None:
    if not label:
        return
    font = load_font(38)
    draw.text(
        (x, y),
        label,
        font=font,
        fill=(214, 28, 25, 255),
        stroke_width=2,
        stroke_fill=(255, 245, 190, 255),
    )


def add_quantity_to_existing_j(base_path: Path, label: str, out_path: Path) -> None:
    canvas = ImageOps.exif_transpose(Image.open(base_path)).convert("RGBA").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(canvas, "RGBA")
    # Historical L043 J repair: keep the existing approved five-grid image and
    # add the quantity only once at the whole image's top-left corner.
    draw_label(draw, 22, 18, label)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, format="JPEG", quality=90, optimize=True, progressive=True)


def main() -> int:
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8-sig"))
    records = [r for r in data.get("records", []) if str(r.get("D", "")).startswith("L043")]
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    fixed: list[dict[str, Any]] = []
    for record in records:
        color_key, color_label, source = parse_color(record)
        quantity_label, quantity_token = parse_quantity(record)
        warnings: list[str] = []
        if not source.exists():
            warnings.append("missing_source")
        if not quantity_label:
            warnings.append("missing_quantity")
        base_path = Path(str(record.get("local_image") or ""))
        if not base_path.exists():
            base_path = Path(str(record.get("old_generated") or ""))
        if not base_path.exists():
            warnings.append("missing_existing_j_base")
        out_path = REVIEW_DIR / "generated" / (
            f"row{record['row']}_{record['D']}_{color_key}_{quantity_token}_label_on_existing_j.jpg"
        )
        if base_path.exists() and quantity_label:
            add_quantity_to_existing_j(base_path, quantity_label, out_path)
        fixed.append(
            {
                "row": record.get("row"),
                "D": record.get("D"),
                "G": record.get("G"),
                "SKU": record.get("SKU") or record.get("SKU货号"),
                "expected_color": color_label,
                "quantity_label": quantity_label,
                "sku_root": str(L043_SKU_ROOT),
                "source": str(source),
                "old_generated": str(base_path) if base_path.exists() else record.get("local_image"),
                "old_j": record.get("new_j"),
                "new_generated": str(out_path) if out_path.exists() else "",
                "warnings": warnings,
            }
        )
    (REVIEW_DIR / "l043_quantity_fix_records.json").write_text(
        json.dumps(fixed, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cards = []
    for item in fixed:
        warn = " / ".join(item["warnings"]) if item["warnings"] else "OK"
        cards.append(
            "<section>"
            f"<h2>{html.escape(str(item['D']))} · row {item['row']} · "
            f"{html.escape(str(item['expected_color']))} · {html.escape(str(item['quantity_label']))}</h2>"
            f"<p><b>G:</b> {html.escape(str(item['G']))}<br>"
            f"<b>SKU:</b> {html.escape(str(item['SKU']))}<br>"
            f"<b>source:</b> {html.escape(str(item['source']))}<br>"
            f"<b>status:</b> {html.escape(warn)}</p>"
            "<div class='grid'>"
            f"<figure><figcaption>源图 PNG</figcaption><img src='{html.escape(image_src(item['source']))}' loading='lazy'></figure>"
            f"<figure><figcaption>旧 J</figcaption><img src='{html.escape(image_src(item['old_generated'] or item['old_j']))}' loading='lazy'></figure>"
            f"<figure><figcaption>新 J（保留旧图，仅左上角加数量）</figcaption><img src='{html.escape(image_src(item['new_generated']))}' loading='lazy'></figure>"
            "</div></section>"
        )
    REVIEW_HTML.write_text(
        f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>L043 J quantity fix review</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;margin:18px;background:#f5f6f8;color:#172033}}
header,section{{background:#fff;border:1px solid #d8dee9;border-radius:8px;padding:12px;margin:12px 0}}
h1{{font-size:22px}} h2{{font-size:17px;margin:0 0 8px}} p{{font-size:13px;word-break:break-all;line-height:1.45}}
.grid{{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:12px}}
figure{{margin:0}} figcaption{{font-size:13px;font-weight:700;margin-bottom:6px}}
img{{width:100%;height:310px;object-fit:contain;background:#fafafa;border:1px solid #e5e7eb}}
.bad{{color:#b42318;font-weight:700}}
</style></head><body><header><h1>L043 J 数量标注专项纠错复核</h1>
<p class='bad'>修正点：L043 保留原来好看的五宫格 J，只在整张图左上角叠加 15 PCS / 30 PCS 红色数量标注；该页只用于复核，未写回 Excel。</p>
<p>records: {len(fixed)} ｜ warnings: {sum(1 for item in fixed if item['warnings'])}</p></header>{''.join(cards)}</body></html>""",
        encoding="utf-8",
    )
    print(json.dumps({"review": str(REVIEW_HTML), "records": len(fixed)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
