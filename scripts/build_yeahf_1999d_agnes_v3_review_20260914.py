"""Build a same-origin review page for four Agnes V3 redo candidates."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from urllib.parse import quote


ROOT = Path(
    r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810"
    r"\t1_cangyuan_current_workbook_t1"
)
RUN = ROOT / "human_redo4_agnes_v3_20260914"
PLAN = RUN / "agnes_v3_redo4_plan.json"
RESULT = RUN / "agnes_v3_redo4_manifest.json"
REVIEW = RUN / "review"
ASSETS = REVIEW / "assets"
HTML = REVIEW / "index.html"
ASSET_MANIFEST = REVIEW / "review_asset_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def copy_asset(source: Path, target: Path) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {"source_path": str(source), "review_path": str(target), "sha256": sha256(target)}


def url(path: Path) -> str:
    return "/".join(quote(part) for part in path.relative_to(REVIEW).parts)


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8-sig"))
    result = json.loads(RESULT.read_text(encoding="utf-8-sig"))
    states = {row["D"]: row for row in result["records"]}
    if len(states) != 4 or any(row.get("status") != "validated" for row in states.values()):
        raise RuntimeError("Agnes V3 result is not 4/4 validated")
    rows = []
    for source in plan["records"]:
        d_value = source["D"]
        files = {
            "old_t1": Path(source["planning_evidence_not_submitted"][0]["path"]),
            "product": Path(source["submitted_images"][0]["path"]),
            "agnes_v2": Path(source["negative_evidence_not_submitted"][2]["path"]),
            "agnes_v3": Path(states[d_value]["local_path"]),
        }
        assets = {key: copy_asset(path, ASSETS / d_value / f"{key}{path.suffix.lower()}") for key, path in files.items()}
        rows.append({
            "D": d_value,
            "G": source.get("G", ""),
            "SKU": source.get("SKU", ""),
            "reason": source["human_rejection_reason"],
            "scene_recipe": source["scene_recipe"],
            "assets": assets,
        })
    ASSET_MANIFEST.write_text(json.dumps({
        "schema": "yeahf-1999d-agnes-v3-review-assets/v1",
        "record_count": len(rows),
        "columns": ["old_t1", "product", "agnes_v2", "agnes_v3"],
        "rows": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    labels = {"old_t1": "原表T1", "product": "精确D产品参考", "agnes_v2": "第二版（已驳回）", "agnes_v3": "第三版重做"}
    cards = []
    for row in rows:
        figures = []
        for key in ("old_t1", "product", "agnes_v2", "agnes_v3"):
            path = Path(row["assets"][key]["review_path"])
            figures.append(f'<figure><img loading="eager" src="{url(path)}" alt="{row["D"]} {key}"><figcaption>{labels[key]}</figcaption></figure>')
        d_value = row["D"]
        cards.append(f'''<article class="card" id="d-{d_value}" data-d="{d_value}"><header><div><strong>{d_value}</strong><span>{row['G']} · {row['SKU']}</span></div><b class="state" data-state-for="{d_value}">待审核</b></header><p class="reason">上版问题：{row['reason']}</p><p class="recipe">新配方：{row['scene_recipe']}</p><div class="images">{''.join(figures)}</div><div class="actions"><button class="ok" onclick="setDecision('{d_value}','approved')">通过</button><button class="bad" onclick="setDecision('{d_value}','rejected')">不通过</button><button onclick="setDecision('{d_value}','pending')">清除</button></div></article>''')

    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>YeahF 1999D · Agnes V3 4张重做审核</title><style>
:root{{--bg:#090c11;--panel:#141a23;--line:#2c3545;--text:#f3f6fb;--muted:#9dadc3;--ok:#22c55e;--bad:#ef4444}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 system-ui,"Microsoft YaHei",sans-serif}}aside{{position:fixed;inset:0 auto 0 0;width:230px;padding:18px;background:#10151d;border-right:1px solid var(--line);overflow:auto}}main{{margin-left:230px;padding:20px;max-width:1800px}}h1{{font-size:20px;margin:0 0 6px}}.muted,.recipe,header span{{color:var(--muted)}}.reason{{color:#ffcf70;font-weight:700}}button{{border:1px solid var(--line);background:#202838;color:#fff;border-radius:8px;padding:8px 13px;cursor:pointer}}button.ok{{background:#116b35}}button.bad{{background:#7f1d1d}}.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:18px;scroll-margin-top:20px}}.card.approved{{border-color:var(--ok)}}.card.rejected{{border-color:var(--bad)}}header{{display:flex;justify-content:space-between;align-items:center;gap:12px}}header strong{{font-size:18px}}header span{{display:block}}.state{{padding:5px 9px;border-radius:999px;background:#30394a}}.images{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}figure{{margin:0;background:#07090d;border-radius:10px;overflow:hidden}}img{{width:100%;aspect-ratio:1;object-fit:contain;display:block}}figcaption{{padding:7px;text-align:center}}.actions{{display:flex;gap:8px;margin-top:12px}}.jump{{display:block;color:#cad7e9;text-decoration:none;padding:6px;border-radius:6px}}.jump.approved{{background:#123b24}}.jump.rejected{{background:#4c1717}}@media(max-width:1000px){{aside{{position:static;width:auto}}main{{margin:0}}.images{{grid-template-columns:repeat(2,1fr)}}}}</style></head><body><aside><h1>Agnes V3 · 4张</h1><p class="muted">原T1 / 产品 / 驳回图 / 重做图</p><p id="stats"></p><button onclick="approveAll()">当页全部通过</button><button onclick="exportJson()">导出审核JSON</button><nav id="nav"></nav></aside><main>{''.join(cards)}</main><script>
const key='yeahf1999d-agnes-v3-review-v1';let decisions=JSON.parse(localStorage.getItem(key)||'{{}}');const ds=[...document.querySelectorAll('.card')].map(x=>x.dataset.d);function render(){{let a=0,r=0,p=0;const nav=document.getElementById('nav');nav.innerHTML='';for(const d of ds){{const s=decisions[d]||'pending';a+=s==='approved';r+=s==='rejected';p+=s==='pending';const card=document.getElementById('d-'+d);card.classList.remove('approved','rejected');if(s!=='pending')card.classList.add(s);document.querySelector(`[data-state-for="${{d}}"]`).textContent=s==='approved'?'通过':s==='rejected'?'不通过':'待审核';const link=document.createElement('a');link.href='#d-'+d;link.className='jump '+s;link.textContent=`${{d}} · ${{s==='approved'?'通过':s==='rejected'?'不通过':'待审'}}`;nav.appendChild(link)}}document.getElementById('stats').textContent=`通过 ${{a}} / 不通过 ${{r}} / 待审 ${{p}}`;localStorage.setItem(key,JSON.stringify(decisions))}}function setDecision(d,s){{decisions[d]=s;render()}}function approveAll(){{for(const d of ds)if(!decisions[d]||decisions[d]==='pending')decisions[d]='approved';render()}}function exportJson(){{const rows=ds.map(D=>({{D,decision:decisions[D]||'pending'}}));const blob=new Blob([JSON.stringify({{schema:'yeahf-1999d-agnes-v3-4-human-review/v1',exported_at:new Date().toISOString(),decisions:rows}},null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='YeahF_1999D_AgnesV3_4审核结果.json';a.click();URL.revokeObjectURL(a.href)}}render();
</script></body></html>'''
    REVIEW.mkdir(parents=True, exist_ok=True)
    HTML.write_text(html, encoding="utf-8")
    print(json.dumps({"html": str(HTML), "records": len(rows), "assets": len(rows) * 4}, ensure_ascii=False))


if __name__ == "__main__":
    main()
