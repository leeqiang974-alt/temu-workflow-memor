"""Build a focused three-way review page for the 18 user-directed T1 redos."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path


ROOT = Path(r"C:\Users\Administrator\Documents\temu自动化")
OUT = ROOT / r"outputs\yeahf_title_dedup_20260709\yeahf_400d_refill_20260718"
TARGET = OUT / "t1_user_redo_focus_review_20260719"
PAGE = TARGET / "YeahF_398D_T1_18张重做三联审查_20260719.html"
REDO = Path(r"D:\temu素材库\T首图候选暂存\YeahF_398D_用户重做_20260719\cangyuan_user_redo_manifest_20260719.json")
sys.path.insert(0, str(ROOT / "scripts"))
import build_yeahf_398d_t1_badged_local_review_20260719 as global_review  # noqa: E402


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def main() -> None:
    redo_rows = {str(row["D"]): row for row in json.loads(REDO.read_text(encoding="utf-8"))["records"]}
    global_rows = {str(row["D"]): row for row in json.loads(global_review.MANIFEST.read_text(encoding="utf-8"))["records"]}
    cards = []
    for d_value, redo in redo_rows.items():
        current = global_rows[d_value]
        source_url = global_review.review_url(Path(redo["source_t1"]), d_value + "-source")
        redo_url = global_review.review_url(Path(redo["local_path"]), d_value)
        badge_url = global_review.review_url(Path(current["rendered_path"]), d_value)
        cards.append(f'''<article class="card" data-d="{esc(d_value)}" data-prefix="{esc(d_value[:4])}">
<h2>{esc(d_value)} <small>{esc(current.get("provider"))}</small></h2>
<div class="pics"><figure><img loading="lazy" src="{esc(source_url)}"><figcaption>369成功源图</figcaption></figure><figure><img loading="lazy" src="{esc(redo_url)}"><figcaption>本次重做（无角标）</figcaption></figure><figure><img loading="lazy" src="{esc(badge_url)}"><figcaption>本次重做（角标候选）</figcaption></figure></div>
<p>硬锁：{esc(redo.get("feedback_lock"))}<br>source SHA-256: {esc(redo.get("source_sha256"))}<br>output SHA-256: {esc(redo.get("output_sha256"))}</p>
<div class="decision"><select><option value="pending">待审</option><option value="approve">通过</option><option value="redo">再重做</option><option value="reject">丢弃D</option></select><textarea placeholder="审核意见"></textarea></div></article>''')
    css = """*{box-sizing:border-box}body{margin:0;background:#eef2f5;font:13px Arial,'Microsoft YaHei';color:#17212b}.top{position:sticky;top:0;z-index:4;background:#fff;border-bottom:2px solid #6d28d9;padding:12px 16px}.top h1{font-size:19px;margin:0 0 5px}.top p{margin:4px 0;color:#526474}.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}input,button,select,textarea{font:inherit;padding:7px;border:1px solid #b7c5d1;border-radius:4px;background:#fff}input{width:260px}main{padding:14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(760px,1fr));gap:12px}.card{background:#fff;border:1px solid #ccd7e0;border-radius:6px;padding:10px}.pics{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}figure{margin:0}img{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:#e8edf1;cursor:zoom-in}figcaption{font-size:11px;color:#62717e;padding:3px 0}h2{font-size:15px;margin:2px 0 7px}h2 small{font-weight:normal;color:#687887}p{font-size:10px;line-height:1.35;color:#5d6d78;overflow-wrap:anywhere}.decision{display:grid;grid-template-columns:100px 1fr;gap:7px}textarea{height:45px}.hidden{display:none}#modal{display:none;position:fixed;inset:0;z-index:9;background:#000d;place-items:center;padding:18px}#modal.open{display:grid}#modal img{max-width:95vw;max-height:92vh;width:auto;height:auto}"""
    script = """const key='yeahf-398d-t1-redo18-review-20260719';const state=JSON.parse(localStorage.getItem(key)||'{}');const cards=[...document.querySelectorAll('.card')];const refresh=()=>summary.textContent=`已决定 ${Object.keys(state).length}/18`;cards.forEach(c=>{const d=c.dataset.d,s=c.querySelector('select'),t=c.querySelector('textarea');if(state[d]){s.value=state[d].decision;t.value=state[d].note||''}const save=()=>{state[d]={decision:s.value,note:t.value};localStorage.setItem(key,JSON.stringify(state));refresh()};s.onchange=save;t.oninput=save;c.querySelectorAll('img').forEach(i=>i.onclick=()=>{modal.classList.add('open');modal.querySelector('img').src=i.src})});refresh();q.oninput=()=>{const v=q.value.trim().toUpperCase();cards.forEach(c=>c.classList.toggle('hidden',!(c.dataset.d.includes(v)||c.dataset.prefix.includes(v))))};modal.onclick=()=>modal.classList.remove('open');exportBtn.onclick=()=>{const blob=new Blob([JSON.stringify({batch:key,exported_at:new Date().toISOString(),decisions:state},null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='yeahf_398d_t1_redo18_decisions_20260719.json';a.click();URL.revokeObjectURL(a.href)}"""
    TARGET.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>YeahF 398D T1 18张重做审查</title><style>{css}</style><body><section class="top"><h1>YeahF 398D · T1 18张用户指定重做审查</h1><p>左：369成功源图；中：本次重做无角标；右：本次重做角标候选。当前仍为本地候选，未OSS、未写表。</p><div class="controls"><input id="q" placeholder="搜索 D / L0xx"><button id="exportBtn">导出决定 JSON</button><span id="summary"></span></div></section><main>{''.join(cards)}</main><div id="modal"><img></div><script>{script}</script></body></html>''', encoding="utf-8")
    print(json.dumps({"cards": len(cards), "page": str(PAGE)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
