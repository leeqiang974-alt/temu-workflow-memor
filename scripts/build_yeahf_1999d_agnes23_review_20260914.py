"""Build a same-origin visual review page for the 23 Agnes redo candidates."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(
    r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810"
    r"\t1_cangyuan_current_workbook_t1"
)
PLAN = ROOT / "YeahF_1999D_T1人工驳回105D_双参考重做计划_20260813.json"
RUN = ROOT / "human_redo23_agnes_20260914"
RUN_MANIFEST = RUN / "agnes_failed23_manifest.json"
REVIEW = RUN / "review"
ASSETS = REVIEW / "assets"
ASSET_MANIFEST = REVIEW / "review_asset_manifest.json"
HTML = REVIEW / "index.html"
SHEETS = REVIEW / "contact_sheets"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def copy_asset(source: Path, target: Path) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {
        "source_path": str(source),
        "review_path": str(target),
        "sha256": sha256(target),
        "bytes": target.stat().st_size,
    }


def img_url(path: Path) -> str:
    return "/".join(quote(part) for part in path.relative_to(REVIEW).parts)


def make_contact_sheets(rows: list[dict]) -> list[str]:
    SHEETS.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    paths: list[str] = []
    cell = 250
    label_h = 28
    for page, start in enumerate(range(0, len(rows), 6), start=1):
        subset = rows[start : start + 6]
        canvas = Image.new("RGB", (cell * 4, (cell + label_h) * len(subset)), "#10141b")
        draw = ImageDraw.Draw(canvas)
        for rix, row in enumerate(subset):
            for cix, key in enumerate(("scene", "product", "rejected", "agnes")):
                source = Path(row["review_assets"][key]["review_path"])
                with Image.open(source) as image:
                    image = image.convert("RGB")
                    image.thumbnail((cell, cell), Image.Resampling.LANCZOS)
                    x = cix * cell + (cell - image.width) // 2
                    y = rix * (cell + label_h) + label_h + (cell - image.height) // 2
                    canvas.paste(image, (x, y))
                label = f"{row['D']}  {key}"
                draw.text((cix * cell + 5, rix * (cell + label_h) + 7), label, fill="white", font=font)
        out = SHEETS / f"agnes23_contact_{page:02d}.jpg"
        canvas.save(out, quality=88, optimize=True)
        paths.append(str(out))
    return paths


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8-sig"))
    run = json.loads(RUN_MANIFEST.read_text(encoding="utf-8-sig"))
    states = {row["D"]: row for row in run["records"]}
    failed_d = set(states)
    if len(failed_d) != 23 or any(row.get("status") != "validated" for row in states.values()):
        raise RuntimeError("Agnes 23-D run is not fully validated")
    plans = {row["target_D"]: row for row in plan["records"] if row["target_D"] in failed_d}
    rows: list[dict] = []
    for d_value in sorted(failed_d):
        row = plans[d_value]
        sources = {
            "scene": Path(row["scene_anchor"]),
            "product": Path(row["product_material"]),
            "rejected": Path(row["negative_candidate"]),
            "agnes": Path(states[d_value]["local_path"]),
        }
        review_assets = {}
        for key, source in sources.items():
            target = ASSETS / d_value / f"{key}{source.suffix.lower()}"
            review_assets[key] = copy_asset(source, target)
        rows.append({
            "D": d_value,
            "L0xx": row["l0xx"],
            "G": row.get("G", ""),
            "SKU": row.get("SKU", ""),
            "rejection_reason": row.get("rejection_reason", ""),
            "review_assets": review_assets,
        })

    payload = {
        "schema": "yeahf-1999d-agnes23-review-assets/v1",
        "record_count": len(rows),
        "columns": ["scene", "product", "rejected", "agnes"],
        "rows": rows,
    }
    ASSET_MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    sheets = make_contact_sheets(rows)

    cards = []
    for row in rows:
        d = row["D"]
        images = []
        labels = {
            "scene": "原表T1（场景锚点）",
            "product": "精确D产品参考",
            "rejected": "上一轮被驳回图",
            "agnes": "Agnes 2.5新图",
        }
        for key in ("scene", "product", "rejected", "agnes"):
            p = Path(row["review_assets"][key]["review_path"])
            images.append(
                f'<figure><img loading="eager" src="{img_url(p)}" alt="{d} {key}">'
                f'<figcaption>{labels[key]}</figcaption></figure>'
            )
        cards.append(f'''
        <article class="card" id="d-{d}" data-d="{d}" data-prefix="{row['L0xx']}">
          <header><div><strong>{d}</strong><span>{row['G']} · {row['SKU']}</span></div><b class="state" data-state-for="{d}">待审核</b></header>
          <p class="reason">原驳回原因：{row['rejection_reason']}</p>
          <div class="images">{''.join(images)}</div>
          <div class="actions"><button class="ok" onclick="setDecision('{d}','approved')">通过</button><button class="bad" onclick="setDecision('{d}','rejected')">不通过</button><button onclick="setDecision('{d}','pending')">清除</button></div>
        </article>''')

    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>YeahF 1999D · Agnes 23张重做审核</title><style>
:root{{--bg:#0b0e13;--panel:#141922;--line:#2a3342;--text:#f3f6fb;--muted:#9cabc0;--ok:#22c55e;--bad:#ef4444;--accent:#5ea0ff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 system-ui,"Microsoft YaHei",sans-serif}}
aside{{position:fixed;left:0;top:0;bottom:0;width:230px;padding:18px;background:#10151d;border-right:1px solid var(--line);overflow:auto}}
main{{margin-left:230px;padding:20px;max-width:1800px}} h1{{font-size:20px;margin:0 0 8px}} .muted,.reason{{color:var(--muted)}}
.toolbar{{position:sticky;top:0;z-index:5;background:rgba(11,14,19,.94);backdrop-filter:blur(8px);padding:10px 0;display:flex;gap:8px;align-items:center}}
button{{border:1px solid var(--line);background:#202838;color:white;border-radius:8px;padding:8px 13px;cursor:pointer}}button.ok{{background:#116b35}}button.bad{{background:#7f1d1d}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;margin:0 0 18px;scroll-margin-top:70px}}.card.approved{{border-color:var(--ok)}}.card.rejected{{border-color:var(--bad)}}
header{{display:flex;justify-content:space-between;gap:12px;align-items:center}}header strong{{font-size:18px}}header span{{display:block;color:var(--muted)}}.state{{padding:5px 9px;border-radius:999px;background:#30394a}}
.images{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}figure{{margin:0;background:#0a0d12;border-radius:10px;overflow:hidden}}img{{display:block;width:100%;aspect-ratio:1;object-fit:contain}}figcaption{{padding:7px;text-align:center;color:#ccd6e5}}
.actions{{display:flex;gap:8px;margin-top:12px}}.jump{{display:block;color:#c7d7ef;text-decoration:none;padding:5px 7px;border-radius:6px;margin:2px 0}}.jump.approved{{background:#123b24}}.jump.rejected{{background:#4c1717}}
@media(max-width:1000px){{aside{{position:static;width:auto}}main{{margin:0}}.images{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><aside><h1>Agnes 23张</h1><p class="muted">原T1 / 产品参考 / 驳回图 / 新图</p><p id="stats"></p><button onclick="approveAll()">当页全部通过</button><button onclick="exportJson()">导出审核JSON</button><nav id="nav"></nav></aside>
<main><div class="toolbar"><strong>YeahF 1999D · Agnes Image 2.5 Flash</strong><span class="muted">只审核候选，不回填表格</span></div>{''.join(cards)}</main>
<script>
const key='yeahf1999d-agnes23-review-v1';let decisions=JSON.parse(localStorage.getItem(key)||'{{}}');
const ds=[...document.querySelectorAll('.card')].map(x=>x.dataset.d);
function render(){{let a=0,r=0,p=0;const nav=document.getElementById('nav');nav.innerHTML='';for(const d of ds){{const s=decisions[d]||'pending';a+=s==='approved';r+=s==='rejected';p+=s==='pending';const card=document.getElementById('d-'+d);card.classList.remove('approved','rejected');if(s!=='pending')card.classList.add(s);document.querySelector(`[data-state-for="${{d}}"]`).textContent=s==='approved'?'通过':s==='rejected'?'不通过':'待审核';const link=document.createElement('a');link.href='#d-'+d;link.className='jump '+s;link.textContent=`${{d}} · ${{s==='approved'?'通过':s==='rejected'?'不通过':'待审'}}`;nav.appendChild(link)}}document.getElementById('stats').textContent=`通过 ${{a}} / 不通过 ${{r}} / 待审 ${{p}}`;localStorage.setItem(key,JSON.stringify(decisions))}}
function setDecision(d,s){{decisions[d]=s;render()}}function approveAll(){{for(const d of ds)if(!decisions[d]||decisions[d]==='pending')decisions[d]='approved';render()}}
function exportJson(){{const rows=ds.map(D=>({{D,decision:decisions[D]||'pending'}}));const blob=new Blob([JSON.stringify({{schema:'yeahf-1999d-agnes23-human-review/v1',exported_at:new Date().toISOString(),decisions:rows}},null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='YeahF_1999D_Agnes23审核结果.json';a.click();URL.revokeObjectURL(a.href)}}render();
</script></body></html>'''
    HTML.write_text(html, encoding="utf-8")
    print(json.dumps({"html": str(HTML), "records": len(rows), "assets": len(rows) * 4, "contact_sheets": sheets}, ensure_ascii=False))


if __name__ == "__main__":
    main()
