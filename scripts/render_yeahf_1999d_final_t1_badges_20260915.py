"""Render local final T1 product-identification badges for all 1999 selected images.

This stage is local-only. It performs no OSS upload and no workbook writeback.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat


BASE = Path(r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810")
ROOT = BASE / "t1_cangyuan_current_workbook_t1"
FINALIZATION = ROOT / "finalization_20260914"
SELECTION = FINALIZATION / "YeahF_1999D_final_unbadged_T1_selection_manifest.json"
J_MANIFEST = BASE / "t1_original_j_reference_manifest.jsonl"
TARGET = FINALIZATION / "t1_badged_local_20260915"
IMAGES = TARGET / "images"
MANIFEST = TARGET / "YeahF_1999D_T1_badge_coverage_manifest.json"
REVIEW = TARGET / "YeahF_1999D_T1_badge_review.html"
FONT = Path(r"C:\Windows\Fonts\arialbd.ttf")
HTTP_ROOT = Path(r"D:\Desktop\jit\HJXYmall")


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def corner_score(image: Image.Image, corner: str, box_size: int, margin: int) -> float:
    width, height = image.size
    x = margin if "left" in corner else width - margin - box_size
    y = margin if "top" in corner else height - margin - box_size
    pad = max(3, box_size // 8)
    crop = image.crop((max(0, x - pad), max(0, y - pad), min(width, x + box_size + pad), min(height, y + box_size + pad)))
    gray = crop.convert("L").resize((96, 96))
    edges = gray.filter(ImageFilter.FIND_EDGES)
    return ImageStat.Stat(gray).var[0] + ImageStat.Stat(edges).mean[0] * 12


def choose_corner(image: Image.Image) -> str:
    size = round(min(image.size) * 0.20)
    margin = round(min(image.size) * 0.04)
    corners = ("top-left", "top-right", "bottom-left", "bottom-right")
    return min(corners, key=lambda value: corner_score(image, value, size, margin))


def render(d_value: str, base_path: Path, inset_path: Path) -> tuple[Path, str]:
    target = IMAGES / d_value[:4] / f"{d_value}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(base_path) as source:
        canvas = source.convert("RGBA")
    corner = choose_corner(canvas.convert("RGB"))
    width, height = canvas.size
    size = round(min(width, height) * 0.20)
    margin = round(min(width, height) * 0.04)
    with Image.open(inset_path) as source:
        inset = ImageOps.fit(source.convert("RGBA"), (size, size), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    x = margin if "left" in corner else width - margin - size
    y = margin if "top" in corner else height - margin - size
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(inset, (x, y), mask)
    draw = ImageDraw.Draw(layer)
    draw.ellipse((x, y, x + size - 1, y + size - 1), outline="white", width=max(3, size // 75))
    # 12 px at 800 px, scaled proportionally for 1024/1254 candidates.
    font_size = max(12, round(min(width, height) * 12 / 800))
    font = ImageFont.truetype(str(FONT), font_size)
    label = "THIS IS THE PRODUCT"
    box = draw.textbbox((0, 0), label, font=font, stroke_width=1)
    text_width, text_height = box[2] - box[0], box[3] - box[1]
    text_x = x + (size - text_width) // 2
    text_y = y + size - text_height // 2
    draw.text((text_x, text_y), label, font=font, fill="white", stroke_width=max(1, size // 180), stroke_fill="#101010")
    Image.alpha_composite(canvas, layer).convert("RGB").save(target, "PNG", optimize=True)
    return target, corner


def build_record(task: tuple[str, dict, dict]) -> dict:
    """Render one exact-D badge candidate in an isolated worker process."""
    d_value, selected_row, j_row = task
    base_path = Path(selected_row["local_path"])
    inset_path = Path(j_row["local_path"])
    if sha256(base_path).lower() != str(selected_row["sha256"]).lower():
        raise RuntimeError(f"Selected base hash drift: {d_value}")
    if sha256(inset_path).lower() != str(j_row["sha256"]).lower():
        raise RuntimeError(f"Exact-D inset hash drift: {d_value}")
    rendered, corner = render(d_value, base_path, inset_path)
    return {
        "D": d_value,
        "L0xx": d_value[:4],
        "base_path": str(base_path),
        "base_sha256": selected_row["sha256"],
        "inset_role": "exact_D_direct_J_product_identity",
        "inset_path": str(inset_path),
        "inset_sha256": sha256(inset_path),
        "corner": corner,
        "label": "THIS IS THE PRODUCT",
        "rendered_path": str(rendered),
        "rendered_sha256": sha256(rendered),
        "badge_status": "applied_pending_human_review",
        "oss_status": "not_uploaded",
        "workbook_writeback": False,
    }


def web_url(path: Path) -> str:
    return "/" + quote(path.resolve().relative_to(HTTP_ROOT.resolve()).as_posix(), safe="/")


def build_review(records: list[dict]) -> None:
    cards = []
    for record in records:
        d_value = record["D"]
        cards.append(f'''<article class="card" id="d-{html.escape(d_value)}" data-d="{html.escape(d_value)}" data-search="{html.escape(d_value)} {html.escape(d_value[:4])}"><header><strong>{html.escape(d_value)}</strong><b class="state">待审</b></header><div class="pics"><figure><img loading="lazy" src="{html.escape(web_url(Path(record['base_path'])))}"><figcaption>通过的无角标T1</figcaption></figure><figure><img loading="lazy" src="{html.escape(web_url(Path(record['rendered_path'])))}"><figcaption>最终角标候选</figcaption></figure></div><p>角标源：精确D产品图<br>位置：{html.escape(record['corner'])}</p><div><button class="ok" onclick="decide('{d_value}','approved')">通过</button><button class="bad" onclick="decide('{d_value}','rejected')">不通过</button></div></article>''')
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>YeahF 1999D最终角标审核</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#0b0e13;color:#eef3f9;font:13px/1.45 system-ui,"Microsoft YaHei",sans-serif}}aside{{position:fixed;inset:0 auto 0 0;width:225px;background:#111722;border-right:1px solid #2b3545;padding:16px;overflow:auto}}main{{margin-left:225px;padding:14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(410px,1fr));gap:12px}}input,button{{border:1px solid #344158;border-radius:7px;background:#20293a;color:white;padding:8px}}input{{width:100%;margin:8px 0}}.card{{background:#151c27;border:1px solid #2c374a;border-radius:12px;padding:10px;scroll-margin-top:10px}}.card.approved{{border-color:#22c55e}}.card.rejected{{border-color:#ef4444}}header{{display:flex;justify-content:space-between}}.pics{{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:8px}}figure{{margin:0;background:#07090d}}img{{width:100%;aspect-ratio:1;object-fit:contain;display:block}}figcaption{{padding:6px;text-align:center}}p{{color:#a6b4c8;overflow-wrap:anywhere}}.ok{{background:#116b35}}.bad{{background:#7f1d1d}}nav a{{display:block;color:#c9d5e8;text-decoration:none;padding:4px}}@media(max-width:900px){{aside{{position:static;width:auto}}main{{margin:0;grid-template-columns:1fr}}}}</style></head><body><aside><h1>1999D最终角标</h1><p>逐页查看角标是否遮挡产品、人物、手部、任务和重要结构。</p><input id="q" placeholder="筛选D/L0xx"><p id="stats"></p><button onclick="approveVisible()">当前筛选全部通过</button><button onclick="exportJson()">导出审核JSON</button><nav id="nav"></nav></aside><main>{''.join(cards)}</main><script>const key='yeahf-1999d-final-badge-review-20260915';let decisions=JSON.parse(localStorage.getItem(key)||'{{}}');const cards=[...document.querySelectorAll('.card')];function render(){{let a=0,r=0,p=0;nav.innerHTML='';for(const c of cards){{const d=c.dataset.d,s=decisions[d]||'pending';c.classList.remove('approved','rejected');if(s!=='pending')c.classList.add(s);c.querySelector('.state').textContent=s==='approved'?'通过':s==='rejected'?'不通过':'待审';a+=s==='approved';r+=s==='rejected';p+=s==='pending';if(!c.hidden){{const x=document.createElement('a');x.href='#d-'+d;x.textContent=d+' · '+(s==='approved'?'通过':s==='rejected'?'不通过':'待审');nav.appendChild(x)}}}}stats.textContent=`通过 ${{a}} / 不通过 ${{r}} / 待审 ${{p}}`;localStorage.setItem(key,JSON.stringify(decisions))}}function decide(d,s){{decisions[d]=s;render()}}q.oninput=()=>{{const t=q.value.trim().toUpperCase();for(const c of cards)c.hidden=!c.dataset.search.includes(t);render()}};function approveVisible(){{for(const c of cards)if(!c.hidden)decisions[c.dataset.d]='approved';render()}}function exportJson(){{const rows=cards.map(c=>({{D:c.dataset.d,decision:decisions[c.dataset.d]||'pending'}}));const b=new Blob([JSON.stringify({{schema:'yeahf-1999d-final-badge-human-review/v1',exported_at:new Date().toISOString(),decisions:rows}},null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='YeahF_1999D_最终角标审核结果.json';a.click();URL.revokeObjectURL(a.href)}}render();</script></body></html>'''
    REVIEW.write_text(page, encoding="utf-8")


def main() -> None:
    selection = json.loads(SELECTION.read_text(encoding="utf-8-sig"))
    selected = {row["D"]: row for row in selection["records"]}
    j_by_d = {}
    for line in J_MANIFEST.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            row = json.loads(line)
            j_by_d[str(row["target_D"])] = row
    if len(selected) != 1999 or len(j_by_d) != 1999 or set(selected) != set(j_by_d):
        raise RuntimeError("Selection/product inset coverage mismatch")
    TARGET.mkdir(parents=True, exist_ok=True)
    tasks = [(d_value, selected[d_value], j_by_d[d_value]) for d_value in sorted(selected)]
    records = []
    workers = min(8, max(2, (os.cpu_count() or 4) // 2))
    print(json.dumps({"parallel_workers": workers, "total": len(tasks)}, ensure_ascii=False), flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(build_record, task): task[0] for task in tasks}
        for position, future in enumerate(as_completed(futures), 1):
            records.append(future.result())
            if position % 50 == 0:
                print(json.dumps({"rendered": position, "total": 1999}, ensure_ascii=False), flush=True)
    records.sort(key=lambda row: row["D"])
    if len(records) != 1999 or any(not Path(row["rendered_path"]).is_file() for row in records):
        raise RuntimeError("Badge render coverage failure")
    payload = {
        "schema": "yeahf-1999d-final-t1-badge-coverage/v1",
        "created_at": now(),
        "record_count": len(records),
        "by_L0xx": dict(sorted(Counter(row["L0xx"] for row in records).items())),
        "badge_label": "THIS IS THE PRODUCT",
        "badge_coverage": "1999/1999_local_rendered_pending_human_review",
        "all_rendered_hashes_recorded": True,
        "oss_upload": False,
        "workbook_writeback": False,
        "release_status": "BLOCK_pending_badge_human_review",
        "records": records,
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    build_review(records)
    print(json.dumps({"manifest": str(MANIFEST), "review": str(REVIEW), "rendered": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
