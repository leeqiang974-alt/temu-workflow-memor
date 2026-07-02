from __future__ import annotations

import html
import json
import math
from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage


WORKBOOK = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702"
    r"\0616-2_199_最终回传_已应用反馈_L042J重做_T清理_20260702.xlsx"
)
SKU_ROOT = Path(r"E:\jit制图\L042\sku")
OUT_ROOT = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702"
    r"\l042_clean_j_redo"
)
SERVED_ROOT = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_fallback_9_20260702"
    r"\l042_j_review_clean_redo"
)


def normalize_token(value: object) -> str:
    return str(value or "").strip().lower()


def classify_variant(g_value: object, sku_value: object) -> str:
    text = normalize_token(g_value) + " " + normalize_token(sku_value)
    if any(token in text for token in ["绿", "green"]):
        return "green"
    return "black"


def choose_source(color_cn: str) -> Path:
    folder = SKU_ROOT / color_cn
    candidates = [p for p in sorted(folder.iterdir()) if p.is_file()]
    if not candidates:
        raise FileNotFoundError(folder)
    # Prefer the least busy white/marble source among first-level files; all are size charts,
    # so the downstream mask keeps only the large product component.
    def score(path: Path) -> tuple[int, int, str]:
        name = path.name
        wh_penalty = 1 if "_WH_" in name else 0
        return (wh_penalty, path.stat().st_size, name)

    return sorted(candidates, key=score)[0]


def clean_mask(path: Path, color: str) -> tuple[Image.Image, dict]:
    image = Image.open(path).convert("RGB").resize((800, 800), Image.LANCZOS)
    arr = np.array(image).astype(np.int16)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    yy, xx = np.mgrid[:800, :800]
    product_zone = (xx >= 235) & (xx <= 760) & (yy >= 90) & (yy <= 650)
    if color == "green":
        mask = (g > r + 18) & (g > b + 12) & (g > 55) & product_zone
    else:
        dark = (r < 150) & (g < 150) & (b < 150) & ((r + g + b) < 360)
        mask = dark & product_zone

    mask = ndimage.binary_opening(mask, structure=np.ones((2, 2)))
    mask = ndimage.binary_closing(mask, structure=np.ones((7, 7)))
    labels, count = ndimage.label(mask)

    keep = np.zeros(mask.shape, dtype=bool)
    components = []
    for idx in range(1, count + 1):
        ys, xs = np.where(labels == idx)
        if xs.size == 0:
            continue
        area = int(xs.size)
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        width, height = x1 - x0 + 1, y1 - y0 + 1
        if area < 900 or width < 35 or height < 30:
            continue
        if y0 > 580:
            continue
        components.append(
            {
                "idx": idx,
                "area": area,
                "bbox": [x0, y0, x1, y1],
                "width": width,
                "height": height,
            }
        )

    components.sort(key=lambda item: item["area"], reverse=True)
    for item in components[:3]:
        keep |= labels == item["idx"]

    keep = ndimage.binary_dilation(keep, structure=np.ones((5, 5)), iterations=1)
    keep = ndimage.binary_fill_holes(keep)
    alpha = Image.fromarray((keep.astype(np.uint8) * 255), "L").filter(
        ImageFilter.GaussianBlur(1.0)
    )
    rgba = image.convert("RGBA")
    rgba.putalpha(alpha)

    ys, xs = np.where(np.array(alpha) > 8)
    if xs.size == 0:
        raise RuntimeError(f"no product extracted from {path}")
    pad = 18
    x0, x1 = max(int(xs.min()) - pad, 0), min(int(xs.max()) + pad, 799)
    y0, y1 = max(int(ys.min()) - pad, 0), min(int(ys.max()) + pad, 799)
    cutout = rgba.crop((x0, y0, x1 + 1, y1 + 1))
    return cutout, {"source": str(path), "bbox": [x0, y0, x1, y1], "components": components[:5]}


def make_background(seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    base = np.zeros((800, 800, 3), dtype=np.float32)
    palettes = [
        ((229, 224, 210), (190, 205, 179)),
        ((230, 218, 199), (205, 221, 226)),
        ((224, 219, 207), (233, 207, 194)),
        ((219, 226, 214), (234, 224, 202)),
    ]
    a, b = palettes[seed % len(palettes)]
    for y in range(800):
        t = y / 799
        base[y, :, :] = np.array(a) * (1 - t) + np.array(b) * t
    noise = rng.normal(0, 5, (800, 800, 1))
    base += noise
    image = Image.fromarray(np.uint8(np.clip(base, 0, 255)), "RGB").filter(
        ImageFilter.GaussianBlur(0.4)
    )
    draw = ImageDraw.Draw(image, "RGBA")
    for _ in range(26):
        x = int(rng.integers(-80, 760))
        y = int(rng.integers(-80, 760))
        w = int(rng.integers(120, 320))
        draw.arc((x, y, x + w, y + w), 0, 360, fill=(255, 255, 255, 22), width=2)
    return image


def paste_product(canvas: Image.Image, cutout: Image.Image, center: tuple[int, int], width: int, angle: float) -> None:
    item = cutout.copy()
    ratio = width / item.width
    item = item.resize((width, max(1, int(item.height * ratio))), Image.LANCZOS)
    item = item.rotate(angle, expand=True, resample=Image.BICUBIC)
    shadow = Image.new("RGBA", item.size, (0, 0, 0, 0))
    shadow_alpha = item.getchannel("A").filter(ImageFilter.GaussianBlur(7))
    shadow.putalpha(shadow_alpha.point(lambda v: int(v * 0.28)))
    x = int(center[0] - item.width / 2)
    y = int(center[1] - item.height / 2)
    canvas.alpha_composite(shadow, (x + 7, y + 10))
    canvas.alpha_composite(item, (x, y))


def make_j_preview(cutout: Image.Image, out_path: Path, seed: int) -> None:
    canvas = make_background(seed).convert("RGBA")
    placements = [
        ((232, 205), 274, -5),
        ((568, 205), 266, 5),
        ((400, 410), 306, 0),
        ((238, 620), 260, 6),
        ((562, 620), 268, -6),
    ]
    for center, width, angle in placements:
        paste_product(canvas, cutout, center, width, angle)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "JPEG", quality=92, optimize=True)


def workbook_l042_rows() -> list[dict]:
    wb = load_workbook(WORKBOOK, data_only=False)
    ws = wb.active
    headers = {str(cell.value).strip(): cell.column for cell in ws[1] if cell.value}
    d_col = headers["产品货号"]
    g_col = headers.get("变种属性值一")
    l_col = headers.get("SKU货号")
    j_col = headers["预览图"]
    rows = []
    for row in range(2, ws.max_row + 1):
        d_value = ws.cell(row, d_col).value
        if not d_value or not str(d_value).startswith("L042"):
            continue
        rows.append(
            {
                "row": row,
                "d": str(d_value),
                "g": ws.cell(row, g_col).value if g_col else "",
                "sku": ws.cell(row, l_col).value if l_col else "",
                "old_j": ws.cell(row, j_col).value,
            }
        )
    return rows


def build_review(rows: list[dict], records: dict[str, dict]) -> None:
    SERVED_ROOT.mkdir(parents=True, exist_ok=True)
    for path in OUT_ROOT.glob("*"):
        if path.is_file():
            target = SERVED_ROOT / path.name
            target.write_bytes(path.read_bytes())

    body = []
    for row in rows:
        variant = classify_variant(row["g"], row["sku"])
        rec = records[variant]
        img_name = Path(rec["j_path"]).name
        body.append(
            f"<article><h3>row {row['row']} / {html.escape(row['d'])} / {variant}</h3>"
            f"<p>G: {html.escape(str(row['g']))} | SKU: {html.escape(str(row['sku']))}</p>"
            f"<p>source: {html.escape(rec['source'])}</p>"
            f"<img src='./{html.escape(img_name)}' loading='lazy'></article>"
        )
    html_text = f"""<!doctype html>
<meta charset="utf-8">
<title>L042 J clean redo</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;margin:0;background:#f5f1e9;color:#1f2328}}
header{{position:sticky;top:0;background:#fff;padding:14px 18px;border-bottom:1px solid #ddd;z-index:2}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;padding:16px}}
article{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px}}
h3{{font-size:15px;margin:0 0 6px}} p{{font-size:12px;margin:4px 0;word-break:break-all}}
img{{width:100%;height:auto;border:1px solid #ddd;background:#eee}}
</style>
<header><strong>L042 J clean redo</strong> · {len(rows)} rows · first-level black/green sources only · text/nails removed by component mask</header>
<main>{''.join(body)}</main>"""
    (SERVED_ROOT / "index.html").write_text(html_text, encoding="utf-8")


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict] = {}
    for variant, color_cn in [("black", "黑色"), ("green", "绿色")]:
        source = choose_source(color_cn)
        cutout, meta = clean_mask(source, variant)
        cutout_path = OUT_ROOT / f"L042_{variant}_clean_product.png"
        cutout.save(cutout_path)
        j_path = OUT_ROOT / f"L042_{variant}_clean_j.jpg"
        make_j_preview(cutout, j_path, 42 if variant == "black" else 43)
        records[variant] = {
            "variant": variant,
            "source": str(source),
            "cutout_path": str(cutout_path),
            "j_path": str(j_path),
            "meta": meta,
        }
    rows = workbook_l042_rows()
    build_review(rows, records)
    report = {"workbook": str(WORKBOOK), "rows": rows, "records": records, "review": str(SERVED_ROOT / "index.html")}
    (OUT_ROOT / "l042_clean_j_redo_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"rows": len(rows), "review": str(SERVED_ROOT / "index.html")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
