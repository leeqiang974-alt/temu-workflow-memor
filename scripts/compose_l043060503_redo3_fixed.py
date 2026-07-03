from __future__ import annotations

import html
import json
import math
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFilter


OUT = Path(os.environ.get("OUT_DIR", r"D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_fixed_redo3_20260703"))
MODE = os.environ.get("MODE", "plan")

FAILED_REDO2 = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_seedream_redo2_3_20260703\generated\L043\L043060503__set3__redo1__redo2_image2_apimart.png"
)
FAILED_SEEDREAM = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_197x3_redo_feedback_20260703\generated\L043\L043060503__set3__redo1_seedream_fallback_6f7a982d.jpg"
)

SOURCES = [
    {
        "candidate_id": "L043060503__set3__redo1__redo3_fixed_a",
        "source_id": "L043_NEW_0038",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L043\kept_0035_0035_L043_NEW_0038_kept.png",
        "placement": "large-left-product, preserve hands/clothing context",
    },
    {
        "candidate_id": "L043060503__set3__redo1__redo3_fixed_b",
        "source_id": "L043_NEW_0043",
        "source_png": r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\selected_280_xiangji_cutout\kept_plus_sku_variant_plus_retry_new_original_library\L043\kept_0036_0036_L043_NEW_0043_kept.png",
        "placement": "center-product-with-person-context, preserve stack structure",
    },
]

PLAN_PATH = OUT / "l043060503_redo3_fixed_plan.json"
RESULTS_PATH = OUT / "l043060503_redo3_fixed_results.json"
REVIEW_PATH = OUT / "l043060503_redo3_fixed_review.html"
LOCK_PATH = OUT / "feedback_lock_l043060503_redo3_fixed_20260703.json"


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_background(size: int = 800) -> Image.Image:
    base = Image.new("RGB", (size, size), (242, 237, 228))
    draw = ImageDraw.Draw(base)
    for y in range(size):
        shade = int(18 * y / size)
        draw.line([(0, y), (size, y)], fill=(242 - shade, 237 - shade, 228 - shade))
    for x in range(0, size, 56):
        draw.line([(x, 0), (x + 120, size)], fill=(230, 224, 214), width=1)
    overlay = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((48, 72, 752, 730), radius=28, fill=(255, 255, 255, 58))
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGBA")


def alpha_bbox(image: Image.Image):
    return image.getchannel("A").getbbox()


def compose(item: dict) -> dict:
    source = Path(item["source_png"])
    image = Image.open(source).convert("RGBA")
    bbox = alpha_bbox(image) or (0, 0, image.width, image.height)
    crop = image.crop(bbox)
    max_w = 760
    max_h = 690
    scale = min(max_w / crop.width, max_h / crop.height, 1.12)
    new_size = (max(1, int(crop.width * scale)), max(1, int(crop.height * scale)))
    crop = crop.resize(new_size, Image.LANCZOS)

    canvas = make_background(800)
    x = (800 - crop.width) // 2
    y = 96 if crop.height < 620 else (800 - crop.height) // 2
    if item["candidate_id"].endswith("_fixed_a"):
        x = max(18, min(x, 42))
        y = max(52, y)
    else:
        x = max(54, x)
        y = max(24, y)

    shadow_alpha = crop.getchannel("A").filter(ImageFilter.GaussianBlur(14))
    shadow = Image.new("RGBA", crop.size, (52, 40, 28, 82))
    shadow.putalpha(shadow_alpha.point(lambda v: int(v * 0.42)))
    canvas.alpha_composite(shadow, (x + 8, y + 12))
    canvas.alpha_composite(crop, (x, y))

    out_path = OUT / "generated" / "L043" / f"{item['candidate_id']}.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, quality=95)
    result = dict(item)
    result.update(
        {
            "status": "ok",
            "provider": "fixed_png_composite",
            "model": "Pillow deterministic composite",
            "local_path": str(out_path),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "failed_redo2": str(FAILED_REDO2),
            "failed_seedream": str(FAILED_SEEDREAM),
            "locked_bad_source_ids": ["L043_NEW_0008", "L043_NEW_0025"],
            "notes": "Exact source PNG pixels composited onto a simple ecommerce background. No AI redraw.",
        }
    )
    return result


def build_plan() -> list[dict]:
    plan = []
    for item in SOURCES:
        source = Path(item["source_png"])
        if not source.exists():
            raise FileNotFoundError(source)
        plan.append(
            {
                **item,
                "original_d": "L043060503",
                "failed_candidate_id": "L043060503__set3__redo1__redo2_image2",
                "review_feedback_cn": "还是错",
                "run_type": "fixed_png_composite_after_image2_seedream_image2_failures",
                "locked_bad_source_ids": ["L043_NEW_0008", "L043_NEW_0025"],
                "hard_rule": "Do not redraw product. Preserve exact source pixels, folding-board holes, small center hole, raised edge detail, panel stack, clothing context, and scale.",
                "no_excel_writeback": True,
                "no_final_upload": True,
            }
        )
    save_json(PLAN_PATH, plan)
    write_plan_md(plan)
    save_json(
        LOCK_PATH,
        {
            "review": "0616_2_image2_seedream_redo2_3_review",
            "locked_at": datetime.now().isoformat(timespec="seconds"),
            "feedback": {
                "L043060503__set3__redo1__redo2_image2": {
                    "decision": "redo",
                    "feedback": "还是错",
                    "ts": "2026-07-03T04:39:51.927Z",
                }
            },
            "locked_bad_source_ids": ["L043_NEW_0008", "L043_NEW_0025"],
            "next_action": "fixed PNG composite candidates, no AI redraw",
        },
    )
    return plan


def write_plan_md(plan: list[dict]) -> None:
    lines = [
        "# L043060503 redo3 fixed composite plan",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- output: `{OUT}`",
        "- reason: user marked `L043060503__set3__redo1__redo2_image2` as `还是错`.",
        "- method: deterministic fixed PNG compositing, no AI redraw.",
        "- locked bad sources: `L043_NEW_0008`, `L043_NEW_0025`.",
        "- no Excel writeback; no final product upload.",
        "",
        "| candidate | source | method |",
        "|---|---|---|",
    ]
    for item in plan:
        lines.append(f"| {item['candidate_id']} | {item['source_id']} | {item['placement']} |")
    (OUT / "l043060503_redo3_fixed_plan.md").write_text("\n".join(lines), encoding="utf-8")


def url_for(path_value: str | Path | None) -> str:
    if not path_value:
        return ""
    path = Path(path_value).resolve()
    roots = [
        (OUT.resolve(), f"/outputs/{OUT.name}"),
        (Path(r"D:\Desktop\jit\DXXmall\outputs").resolve(), "/outputs"),
        (Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs").resolve(), "/outputs"),
    ]
    for root, prefix in roots:
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        return prefix + "/" + quote(rel.as_posix(), safe="/")
    return ""


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def build_review(results: list[dict]) -> None:
    cards = []
    for item in results:
        local_path = item.get("local_path")
        result_caption = "fixed composite candidate" if local_path else "pending until MODE=run"
        cards.append(
            f"""
<article class="card">
  <h3>{esc(item['candidate_id'])}</h3>
  <p>source {esc(item['source_id'])} · locked bad {esc(','.join(item['locked_bad_source_ids']))}</p>
  <div class="grid">
    <figure><img src="{esc(url_for(FAILED_REDO2))}" loading="lazy"><figcaption>failed image2 redo2</figcaption></figure>
    <figure><img src="{esc(url_for(item['source_png']))}" loading="lazy"><figcaption>fixed source PNG</figcaption></figure>
    <figure><img src="{esc(url_for(local_path))}" loading="lazy"><figcaption>{esc(result_caption)}</figcaption></figure>
  </div>
  <p class="note">{esc(item.get('notes') or item.get('hard_rule'))}</p>
  <div class="actions">
    <button onclick="mark('{esc(item['candidate_id'])}','keep')">保留</button>
    <button onclick="mark('{esc(item['candidate_id'])}','redo')">重做</button>
    <button onclick="mark('{esc(item['candidate_id'])}','reject')">不要</button>
    <input id="fb-{esc(item['candidate_id'])}" placeholder="反馈">
    <span id="st-{esc(item['candidate_id'])}">未筛选</span>
  </div>
</article>"""
        )
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>L043060503 fixed redo3 review</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f6f4ef;margin:0;color:#1f2937}}header{{position:sticky;top:0;background:#fff;padding:12px 18px;border-bottom:1px solid #ddd;z-index:2}}
.wrap{{padding:16px;max-width:1500px;margin:auto}}.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin-bottom:18px;padding:12px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
figure{{margin:0;border:1px solid #e5e7eb;background:#fafafa;padding:6px;text-align:center}}img{{max-width:100%;height:320px;object-fit:contain;background:#fff}}figcaption{{font-size:12px;color:#555;word-break:break-all}}
.note{{background:#ecfdf5;border:1px solid #a7f3d0;padding:8px;border-radius:6px}}button{{border:0;border-radius:6px;padding:6px 10px;background:#7c3aed;color:#fff}}button:nth-child(2){{background:#f59e0b}}button:nth-child(3){{background:#ef4444}}
input{{min-width:260px;padding:6px}}#exportBox{{width:100%;height:130px}}@media(max-width:1100px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><header><h2>L043060503 fixed redo3 review</h2><p>固定 PNG 合成，不走 AI 重画。左：失败 image2；中：源 PNG；右：新候选。</p><button onclick="exportFeedback()">导出筛选JSON</button><textarea id="exportBox"></textarea></header><main class="wrap">{''.join(cards)}</main>
<script>
const REVIEW='l043060503_redo3_fixed_review';let feedback={{}};
function mark(id,decision){{feedback[id]={{decision,feedback:document.getElementById('fb-'+id)?.value||'',ts:new Date().toISOString()}};document.getElementById('st-'+id).textContent=decision;}}
function exportFeedback(){{for(const id of Object.keys(feedback))feedback[id].feedback=document.getElementById('fb-'+id)?.value||feedback[id].feedback||'';const data={{review:REVIEW,exported_at:new Date().toISOString(),feedback}};document.getElementById('exportBox').value=JSON.stringify(data,null,2);navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('exportBox').value).catch(()=>{{}});}}
</script></body></html>"""
    REVIEW_PATH.write_text(page, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plan = build_plan()
    results = []
    if MODE == "run":
        results = [compose(item) for item in plan]
        save_json(RESULTS_PATH, results)
    else:
        results = plan
    build_review(results)
    print(json.dumps({"mode": MODE, "out": str(OUT), "count": len(plan), "review": str(REVIEW_PATH)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
