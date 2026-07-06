#!/usr/bin/env python3
"""Build a focused L042 J review with neutral five-cell grids.

This does not write back the workbook. It prints the L042 row-to-source mapping
and creates corrected local J candidates for review.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageOps


OUT_DIR = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_192_writeback_195x3_set1_full_title_j_20260706")
AUDIT_JSON = OUT_DIR / "j_match_audit.json"
REVIEW_DIR = OUT_DIR / "l042_j_neutral_fix_review"
REVIEW_HTML = REVIEW_DIR / "index.html"
L042_SKU_ROOT = Path(r"E:\jit制图\L042\sku")
SIZE = 800


def file_url(path: str | Path) -> str:
    try:
        return Path(path).resolve().as_uri()
    except Exception:
        return ""


def variant_from_row(record: dict[str, Any]) -> tuple[str, str]:
    text = f"{record.get('G') or ''} {record.get('SKU') or ''}".lower()
    if "绿" in text or "green" in text or "l042-02" in text:
        return "green", "绿色"
    return "black", "黑色"


def is_visual_green(path: Path) -> bool:
    image = ImageOps.exif_transpose(Image.open(path)).convert("RGB").resize((220, 220), Image.Resampling.LANCZOS)
    pixels = list(image.getdata())
    green = sum(1 for r, g, b in pixels if g > r + 18 and g > b + 12 and g > 55)
    title = image.crop((0, 0, 95, 36))
    title_pixels = list(title.getdata())
    title_green = sum(1 for r, g, b in title_pixels if g > r + 12 and g > b + 8 and g > 40)
    return (green / max(1, len(pixels))) >= 0.05 and (title_green / max(1, len(title_pixels))) >= 0.03


def valid_sources(color_cn: str) -> list[Path]:
    folder = L042_SKU_ROOT / color_cn
    files = [
        p for p in sorted(folder.iterdir(), key=lambda item: item.name)
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    ]
    preferred_name = "L042_green_final_cutout.png" if color_cn == "绿色" else "L042_black_final_cutout.png"
    preferred = [p for p in files if p.name == preferred_name]
    if preferred:
        return preferred
    out: list[Path] = []
    rejects: list[dict[str, str]] = []
    for path in files:
        green = is_visual_green(path)
        if (color_cn == "绿色" and green) or (color_cn == "黑色" and not green):
            out.append(path)
        else:
            rejects.append({"path": str(path), "reason": f"visual_green={green} does not match {color_cn}"})
    (REVIEW_DIR / "source_rejects").mkdir(parents=True, exist_ok=True)
    (REVIEW_DIR / "source_rejects" / f"L042_{color_cn}_rejects.json").write_text(
        json.dumps(rejects, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not out:
        raise RuntimeError(f"No valid L042 sources for {color_cn}: {folder}")
    return out


def source_for_record(record: dict[str, Any], pools: dict[str, list[Path]]) -> Path:
    variant, _ = variant_from_row(record)
    source = Path(str(record.get("sku_source") or ""))
    expected_root = L042_SKU_ROOT / ("绿色" if variant == "green" else "黑色")
    if source.exists() and expected_root in source.parents and source in pools[variant]:
        return source
    # Stable fallback: sorted first valid source from the correct color folder.
    return pools[variant][0]


def skill_texture_bg(seed: int) -> Image.Image:
    palettes = [
        ((237, 232, 220), (214, 223, 207)),
        ((235, 225, 211), (224, 233, 236)),
        ((232, 228, 218), (235, 215, 204)),
        ((224, 232, 221), (238, 228, 205)),
        ((230, 224, 237), (216, 225, 232)),
    ]
    top, bottom = palettes[seed % len(palettes)]
    canvas = Image.new("RGB", (SIZE, SIZE), top)
    px = canvas.load()
    for y in range(SIZE):
        t = y / (SIZE - 1)
        base = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(SIZE):
            n = ((x * 17 + y * 31 + seed) % 9) - 4
            px[x, y] = tuple(max(0, min(255, c + n)) for c in base)
    canvas = canvas.filter(ImageFilter.GaussianBlur(0.35))
    draw = ImageDraw.Draw(canvas, "RGBA")
    for x in range(-80, 900, 150):
        draw.line((x, 0, x + 260, SIZE), fill=(255, 255, 255, 24), width=3)
    return canvas


def neutral_five_grid(source: Path, out_path: Path, seed: int) -> None:
    source_img = ImageOps.exif_transpose(Image.open(source)).convert("RGBA")
    bbox = source_img.getchannel("A").getbbox()
    if bbox:
        source_img = source_img.crop(bbox)
    # Keep the whole size-chart content, including text, dimensions and nail count.
    source_img.thumbnail((258, 258), Image.Resampling.LANCZOS)
    canvas = skill_texture_bg(seed).convert("RGBA")
    cell = SIZE / 3
    placements = [
        (cell * 0.5, cell * 0.5),
        (cell * 2.5, cell * 0.5),
        (cell * 1.5, cell * 1.5),
        (cell * 0.5, cell * 2.5),
        (cell * 2.5, cell * 2.5),
    ]
    for cx, cy in placements:
        item = source_img.copy()
        x = round(cx - item.width / 2)
        y = round(cy - item.height / 2)
        shadow_layer = Image.new("RGBA", item.size, (0, 0, 0, 0))
        shadow_layer.putalpha(item.getchannel("A").filter(ImageFilter.GaussianBlur(6)).point(lambda v: min(34, v // 6)))
        canvas.alpha_composite(shadow_layer, (x + 5, y + 6))
        canvas.alpha_composite(item, (x, y))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, format="JPEG", quality=88, optimize=True, progressive=True)


def main() -> int:
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8-sig"))
    records = [r for r in data.get("records", []) if str(r.get("D", "")).startswith("L042")]
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    pools = {"black": valid_sources("黑色"), "green": valid_sources("绿色")}
    fixed: list[dict[str, Any]] = []
    for record in records:
        variant, color_cn = variant_from_row(record)
        source = source_for_record(record, pools)
        out_path = REVIEW_DIR / "generated" / f"row{record['row']}_{record['D']}_{variant}_neutral_fivegrid.jpg"
        neutral_five_grid(source, out_path, record["row"])
        fixed.append({
            "row": record["row"],
            "D": record["D"],
            "G": record.get("G"),
            "SKU": record.get("SKU"),
            "expected_variant": variant,
            "expected_folder": color_cn,
            "source": str(source),
            "old_generated": record.get("local_image"),
            "new_generated": str(out_path),
            "old_j": record.get("new_j"),
        })
    (REVIEW_DIR / "l042_neutral_fix_records.json").write_text(
        json.dumps(fixed, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cards = []
    for item in fixed:
        cards.append(
            "<section>"
            f"<h2>{html.escape(str(item['D']))} · row {item['row']} · {html.escape(str(item['expected_folder']))}</h2>"
            f"<p><b>G:</b> {html.escape(str(item['G']))}<br><b>SKU:</b> {html.escape(str(item['SKU']))}<br>"
            f"<b>source:</b> {html.escape(str(item['source']))}</p>"
            "<div class='grid'>"
            f"<figure><figcaption>源图 PNG/JPG</figcaption><img src='{html.escape(file_url(item['source']))}' loading='lazy'></figure>"
            f"<figure><figcaption>旧 J（错误：背景二次干扰）</figcaption><img src='{html.escape(file_url(item['old_generated']))}' loading='lazy'></figure>"
            f"<figure><figcaption>新 J（透明 PNG + skill 软纹理五宫格）</figcaption><img src='{html.escape(file_url(item['new_generated']))}' loading='lazy'></figure>"
            "</div></section>"
        )
    REVIEW_HTML.write_text(
        f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>L042 J neutral fix review</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;margin:18px;background:#f5f6f8;color:#172033}}
header,section{{background:#fff;border:1px solid #d8dee9;border-radius:8px;padding:12px;margin:12px 0}}
h1{{font-size:22px}} h2{{font-size:17px;margin:0 0 8px}} p{{font-size:13px;word-break:break-all}}
.grid{{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:12px}}
figure{{margin:0}} figcaption{{font-size:13px;font-weight:700;margin-bottom:6px}}
img{{width:100%;height:310px;object-fit:contain;background:#fafafa;border:1px solid #e5e7eb}}
.bad{{color:#b42318;font-weight:700}}
</style></head><body><header><h1>L042 J 专项纠错复核</h1>
<p class='bad'>修正点：L042 按 G + SKU 只选 final cutout 透明 PNG，保留 alpha 通道和整张尺寸图文字/钉子，并按 J 背景 skill 生成软纹理五宫格。</p>
<p>records: {len(fixed)}</p></header>{''.join(cards)}</body></html>""",
        encoding="utf-8",
    )
    print(json.dumps({"review": str(REVIEW_HTML), "records": len(fixed)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
