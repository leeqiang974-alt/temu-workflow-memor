"""Build a paginated, low-latency human review page for final T1 badges."""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote


ROOT = Path(r"D:\Desktop\jit\HJXYmall")
BADGE_DIR = ROOT / "YeahF_1999D_0808新作_执行资料_20260810" / "t1_cangyuan_current_workbook_t1" / "finalization_20260914" / "t1_badged_local_20260915"
MANIFEST = BADGE_DIR / "YeahF_1999D_T1_badge_coverage_manifest.json"
OUTPUT = BADGE_DIR / "YeahF_1999D_T1_badge_review.html"


def url(path: str) -> str:
    rel = Path(path).resolve().relative_to(ROOT.resolve()).as_posix()
    return "/" + quote(rel, safe="/")


def main() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    records = payload["records"]
    cards = []
    for i, row in enumerate(records):
        d = str(row["D"])
        cards.append(
            f'<article class="card" data-i="{i}" data-d="{html.escape(d)}" data-family="{html.escape(d[:4])}">'
            f'<header><strong>{html.escape(d)}</strong><b class="state">待审</b></header>'
            '<div class="pics">'
            f'<figure><img loading="lazy" data-src="{html.escape(url(row["base_path"]))}"><figcaption>已通过的无角标 T1</figcaption></figure>'
            f'<figure><img loading="lazy" data-src="{html.escape(url(row["rendered_path"]))}"><figcaption>最终角标候选</figcaption></figure>'
            '</div>'
            f'<p>角标源：精确 D 产品图；位置：{html.escape(row["corner"])}</p>'
            f'<div class="actions"><button class="ok" onclick="decide(\'{d}\',\'approved\',this)">通过</button>'
            f'<button class="bad" onclick="decide(\'{d}\',\'rejected\',this)">不通过</button></div></article>'
        )
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>YeahF 1999D 最终角标审核</title>
<style>*{{box-sizing:border-box}}html{{scroll-behavior:auto}}body{{margin:0;background:#0b0e13;color:#eef3f9;font:13px/1.45 system-ui,"Microsoft YaHei",sans-serif}}aside{{position:fixed;inset:0 auto 0 0;width:245px;background:#111722;border-right:1px solid #2b3545;padding:14px;overflow:auto}}main{{margin-left:245px;padding:14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:12px;align-items:start}}input,button{{border:1px solid #344158;border-radius:7px;background:#20293a;color:#fff;padding:8px}}input{{width:100%;margin:8px 0}}button{{cursor:pointer}}button:disabled{{opacity:.45;cursor:not-allowed}}.toolbar{{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:8px 0}}.card{{background:#151c27;border:1px solid #2c374a;border-radius:12px;padding:10px}}.card.approved{{border-color:#22c55e;box-shadow:0 0 0 1px #22c55e55}}.card.rejected{{border-color:#ef4444;box-shadow:0 0 0 1px #ef444455}}header{{display:flex;justify-content:space-between}}.pics{{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:8px}}figure{{margin:0;background:#07090d}}img{{width:100%;aspect-ratio:1;object-fit:contain;display:block;background:#07090d}}figcaption{{padding:6px;text-align:center}}p{{color:#a6b4c8}}.ok{{background:#116b35}}.bad{{background:#7f1d1d}}#pageList button{{display:block;width:100%;text-align:left;margin:3px 0;padding:5px}}#pageList button.approved{{border-color:#22c55e}}#pageList button.rejected{{border-color:#ef4444}}#pageList button.pending{{border-color:#64748b}}.hint{{color:#9fb0c8}}@media(max-width:900px){{aside{{position:static;width:auto}}main{{margin:0;grid-template-columns:1fr}}}}</style></head><body><aside><h1>1999D 最终角标</h1><p class="hint">每页 20 个。点击不会跳回首页；左侧即时显示当页状态。</p><input id="q" placeholder="输入 D 或 L0xx 筛选"><p id="stats"></p><p id="pageStats"></p><div class="toolbar"><button id="prev" onclick="move(-1)">上一页</button><button id="next" onclick="move(1)">下一页</button></div><button style="width:100%;background:#116b35" onclick="approvePage()">当页全部通过</button><button style="width:100%;margin-top:7px" onclick="exportJson()">导出审核 JSON</button><div id="pageList"></div></aside><main id="main">{''.join(cards)}</main>
<script>const key='yeahf-1999d-final-badge-review-20260915-v2',size=10,cards=[...document.querySelectorAll('.card')];let decisions=JSON.parse(localStorage.getItem(key)||'{{}}'),page=0,filtered=cards.slice();function stateOf(d){{return decisions[d]||'pending'}}function paint(c){{const s=stateOf(c.dataset.d);c.classList.remove('approved','rejected');if(s!=='pending')c.classList.add(s);c.querySelector('.state').textContent=s==='approved'?'通过':s==='rejected'?'不通过':'待审'}}function loadImg(c){{for(const img of c.querySelectorAll('img[data-src]')){{img.src=img.dataset.src;delete img.dataset.src}}}}function render(){{const pages=Math.max(1,Math.ceil(filtered.length/size));page=Math.max(0,Math.min(page,pages-1));for(const c of cards)c.hidden=true;const shown=filtered.slice(page*size,page*size+size);for(const c of shown){{c.hidden=false;paint(c);loadImg(c)}}const all=cards.map(c=>stateOf(c.dataset.d));stats.textContent=`总计：通过 ${{all.filter(x=>x==='approved').length}} / 不通过 ${{all.filter(x=>x==='rejected').length}} / 待审 ${{all.filter(x=>x==='pending').length}}`;pageStats.textContent=`筛选 ${{filtered.length}} 个 · 第 ${{page+1}} / ${{pages}} 页`;prev.disabled=page===0;next.disabled=page>=pages-1;pageList.innerHTML='';for(const c of shown){{const b=document.createElement('button'),s=stateOf(c.dataset.d);b.textContent=c.dataset.d+' · '+(s==='approved'?'通过':s==='rejected'?'不通过':'待审');b.className=s;b.onclick=()=>c.scrollIntoView({{block:'start'}});pageList.appendChild(b)}}localStorage.setItem(key,JSON.stringify(decisions))}}function decide(d,s,button){{decisions[d]=s;paint(button.closest('.card'));render()}}function move(n){{page+=n;render();window.scrollTo(0,0)}}q.oninput=()=>{{const t=q.value.trim().toUpperCase();filtered=cards.filter(c=>!t||c.dataset.d.includes(t)||c.dataset.family.includes(t));page=0;render();window.scrollTo(0,0)}};function approvePage(){{for(const c of filtered.slice(page*size,page*size+size))decisions[c.dataset.d]='approved';render()}}function exportJson(){{const rows=cards.map(c=>({{D:c.dataset.d,decision:stateOf(c.dataset.d)}}));const b=new Blob([JSON.stringify({{schema:'yeahf-1999d-final-badge-human-review/v1',exported_at:new Date().toISOString(),decisions:rows}},null,2)],{{type:'application/json'}}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='YeahF_1999D_最终角标审核结果.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}}render();</script></body></html>'''
    OUTPUT.write_text(page, encoding="utf-8")
    print(json.dumps({"records": len(records), "output": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
