from __future__ import annotations

import html
import json
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter


KEY_PATH = Path(r"D:\Desktop\api\www.remove.bg.txt")
OUT = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702"
    r"\l042_removebg_api_trial"
)
SERVED = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_fallback_9_20260702"
    r"\l042_removebg_api_trial"
)
SOURCES = {
    "black": Path(r"E:\jit制图\L042\sku\黑色\生成带纹理背景的尺寸图 (7)_WH_800x800px_1.jpg"),
    "green": Path(r"E:\jit制图\L042\sku\绿色\生成带纹理背景的尺寸图 (10).png"),
}


def compose_previews(png: Path, variant: str) -> dict[str, str]:
    cut = Image.open(png).convert("RGBA")
    single = Image.new("RGBA", (800, 800), (255, 255, 255, 255))
    item = cut.copy()
    item.thumbnail((800, 800), Image.LANCZOS)
    single.alpha_composite(item, ((800 - item.width) // 2, (800 - item.height) // 2))
    single_path = OUT / f"L042_{variant}_removebg_single_preview.jpg"
    single.convert("RGB").save(single_path, quality=94, optimize=True)

    bg = Image.new("RGB", (800, 800), (235, 232, 224))
    draw = ImageDraw.Draw(bg, "RGBA")
    for x in range(-80, 900, 150):
        draw.line((x, 0, x + 260, 800), fill=(255, 255, 255, 28), width=3)
    fg = cut.copy()
    fg.thumbnail((310, 310), Image.LANCZOS)
    for cx, cy in [(190, 180), (610, 180), (400, 400), (190, 620), (610, 620)]:
        layer = bg.convert("RGBA")
        shadow = Image.new("RGBA", fg.size, (0, 0, 0, 0))
        shadow.putalpha(
            fg.getchannel("A")
            .filter(ImageFilter.GaussianBlur(8))
            .point(lambda value: int(value * 0.25))
        )
        x, y = cx - fg.width // 2, cy - fg.height // 2
        layer.alpha_composite(shadow, (x + 7, y + 9))
        layer.alpha_composite(fg, (x, y))
        bg = layer.convert("RGB")
    grid_path = OUT / f"L042_{variant}_removebg_fivegrid_preview.jpg"
    bg.save(grid_path, quality=92, optimize=True)

    return {"single_preview": str(single_path), "fivegrid_preview": str(grid_path)}


def call_removebg(variant: str, source: Path, api_key: str) -> dict:
    record = {"variant": variant, "source": str(source), "status": "pending"}
    with source.open("rb") as handle:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": handle},
            data={"size": "auto", "format": "png"},
            headers={"X-Api-Key": api_key},
            timeout=120,
        )
    record["http_status"] = response.status_code
    for header_name in ["X-Credits-Charged", "X-Credits-Calculated", "X-RateLimit-Remaining"]:
        if header_name in response.headers:
            record[header_name.lower()] = response.headers[header_name]
    if response.status_code != 200:
        record["status"] = "error"
        try:
            record["error_json"] = response.json()
        except Exception:
            record["error_text"] = response.text[:1000]
        return record

    png = OUT / f"L042_{variant}_removebg_api.png"
    png.write_bytes(response.content)
    record["status"] = "ok"
    record["removebg_png"] = str(png)
    record.update(compose_previews(png, variant))
    return record


def copy_for_serving(record: dict) -> None:
    for key in ["removebg_png", "single_preview", "fivegrid_preview"]:
        value = record.get(key)
        if value:
            path = Path(value)
            (SERVED / path.name).write_bytes(path.read_bytes())


def build_review(records: list[dict]) -> None:
    parts = []
    for record in records:
        parts.append(
            f"<article><h2>{html.escape(record['variant'])} - {html.escape(record['status'])}</h2>"
            f"<p>source: {html.escape(record['source'])}</p>"
        )
        if record["status"] == "ok":
            parts.append(
                "<div class='grid'>"
                f"<section><b>remove.bg PNG on white</b><img src='./{Path(record['single_preview']).name}'></section>"
                f"<section><b>remove.bg five-grid</b><img src='./{Path(record['fivegrid_preview']).name}'></section>"
                f"<section><b>transparent PNG</b><img src='./{Path(record['removebg_png']).name}'></section>"
                "</div>"
            )
        else:
            safe = html.escape(json.dumps(record, ensure_ascii=False, indent=2))
            parts.append(f"<pre>{safe}</pre>")
        parts.append("</article>")

    page = f"""<!doctype html>
<meta charset="utf-8">
<title>L042 remove.bg API trial</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;background:#f4f0e7;margin:0;color:#222}}
header{{position:sticky;top:0;background:white;padding:14px 18px;border-bottom:1px solid #ddd}}
main{{max-width:1180px;margin:0 auto;padding:16px;display:grid;gap:16px}}
article{{background:white;border:1px solid #ddd;border-radius:8px;padding:12px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
img{{display:block;width:100%;background:#eee;border:1px solid #ddd}}
pre{{white-space:pre-wrap;background:#111;color:#eee;padding:12px;border-radius:6px}}
@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style>
<header><strong>L042 remove.bg API trial</strong> · whole first-level SKU size chart sent to remove.bg · no workbook writeback</header>
<main>{''.join(parts)}</main>"""
    (SERVED / "index.html").write_text(page, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SERVED.mkdir(parents=True, exist_ok=True)
    api_key = KEY_PATH.read_text(encoding="utf-8").strip()
    records = []
    for variant, source in SOURCES.items():
        record = call_removebg(variant, source, api_key)
        records.append(record)
        copy_for_serving(record)
        if record["status"] != "ok":
            break

    report = {
        "records": records,
        "review": "http://127.0.0.1:8765/outputs/store_newskill_seedream_fallback_9_20260702/l042_removebg_api_trial/index.html",
    }
    (OUT / "l042_removebg_api_trial_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (SERVED / "l042_removebg_api_trial_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    build_review(records)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
