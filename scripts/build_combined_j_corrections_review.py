#!/usr/bin/env python3
"""Build a combined J review page with corrected local J candidates.

This review does not write back Excel. It merges the current full J audit with
focused L042/L043 corrected candidates so the user can inspect all J rows in
one page.
"""

from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any


OUT_DIR = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_192_writeback_195x3_set1_full_title_j_20260706")
FULL_AUDIT = OUT_DIR / "j_match_audit.json"
L042_FIX = OUT_DIR / "l042_j_neutral_fix_review" / "l042_neutral_fix_records.json"
L043_FIX = OUT_DIR / "l043_j_quantity_fix_review" / "l043_quantity_fix_records.json"
REVIEW_DIR = OUT_DIR / "combined_j_corrections_review"
REVIEW_HTML = REVIEW_DIR / "index.html"
REVIEW_JSON = REVIEW_DIR / "combined_j_corrections_review.json"


def load_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        return list(data.get("records", []))
    return list(data)


def src(value: object) -> str:
    if not value:
        return ""
    text = str(value)
    if text.startswith(("http://", "https://", "file://")):
        return text
    try:
        return Path(text).resolve().as_uri()
    except Exception:
        return ""


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def main() -> int:
    full = load_records(FULL_AUDIT)
    l042 = {int(r["row"]): r for r in load_records(L042_FIX)}
    l043 = {int(r["row"]): r for r in load_records(L043_FIX)}

    merged: list[dict[str, Any]] = []
    for record in full:
        row = int(record["row"])
        d_value = str(record.get("D") or "")
        prefix = d_value[:4]
        if row in l042:
            fix = l042[row]
            status = "corrected_l042_final_cutout"
            source = fix.get("source")
            generated = fix.get("new_generated")
            match_mode = "l042_final_cutout_alpha_skill_texture"
            wanted = [fix.get("expected_variant")]
            matched = [Path(str(source)).name]
            warning = ""
            note = "L042 final transparent cutout PNG, alpha preserved, soft texture five-grid."
        elif row in l043:
            fix = l043[row]
            status = "corrected_l043_quantity"
            source = fix.get("source")
            generated = fix.get("new_generated")
            match_mode = "l043_color_quantity_label"
            wanted = [fix.get("expected_color"), fix.get("quantity_label")]
            matched = [Path(str(source)).name, fix.get("quantity_label")]
            warning = "; ".join(fix.get("warnings") or [])
            note = "L043 white/gray source with 15 PCS / 30 PCS label from G + SKU."
        else:
            status = "current_full_audit"
            source = record.get("sku_source")
            generated = record.get("local_image") or record.get("new_j") or record.get("current_j")
            match_mode = record.get("match_mode")
            wanted = record.get("wanted_tokens") or []
            matched = record.get("matched_tokens") or []
            warning = record.get("warning") or ""
            note = "Current full J audit record."
        merged.append(
            {
                "row": row,
                "D": d_value,
                "prefix": prefix,
                "G": record.get("G"),
                "SKU": record.get("SKU"),
                "status": status,
                "match_mode": match_mode,
                "wanted_tokens": wanted,
                "matched_tokens": matched,
                "warning": warning,
                "note": note,
                "sku_root": record.get("sku_root"),
                "sku_source": source,
                "current_j": record.get("current_j") or record.get("new_j"),
                "old_local_image": record.get("local_image"),
                "review_image": generated,
            }
        )

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_JSON.write_text(json.dumps({"records": merged}, ensure_ascii=False, indent=2), encoding="utf-8")

    status_counts = Counter(r["status"] for r in merged)
    prefix_counts = Counter(r["prefix"] for r in merged)
    cards = []
    for r in merged:
        classes = f"card {esc(r['status'])} prefix-{esc(r['prefix'])}"
        warn = f"<span class='warn'>{esc(r['warning'])}</span>" if r["warning"] else "<span class='ok'>OK</span>"
        cards.append(
            f"""<section class="{classes}" data-prefix="{esc(r['prefix'])}" data-status="{esc(r['status'])}">
  <div class="meta">
    <h2>{esc(r['D'])} · row {esc(r['row'])}</h2>
    <p><b>status:</b> {esc(r['status'])}<br>
    <b>G:</b> {esc(r['G'])}<br>
    <b>SKU:</b> {esc(r['SKU'])}<br>
    <b>mode:</b> {esc(r['match_mode'])}<br>
    <b>wanted:</b> {esc(", ".join(str(x) for x in r['wanted_tokens'] if x))}<br>
    <b>matched:</b> {esc(", ".join(str(x) for x in r['matched_tokens'] if x))}<br>
    <b>source:</b> {esc(r['sku_source'])}<br>
    <b>warning:</b> {warn}<br>
    <b>note:</b> {esc(r['note'])}</p>
  </div>
  <div class="imgs">
    <figure><figcaption>SKU 源图</figcaption><img loading="lazy" src="{esc(src(r['sku_source']))}"></figure>
    <figure><figcaption>当前/旧 J</figcaption><img loading="lazy" src="{esc(src(r['old_local_image'] or r['current_j']))}"></figure>
    <figure><figcaption>本页复核 J</figcaption><img loading="lazy" src="{esc(src(r['review_image']))}"></figure>
  </div>
</section>"""
        )

    prefix_options = "\n".join(
        f'<button type="button" data-filter-prefix="{esc(prefix)}">{esc(prefix)} ({count})</button>'
        for prefix, count in sorted(prefix_counts.items())
    )
    status_summary = " ｜ ".join(f"{status}: {count}" for status, count in sorted(status_counts.items()))
    REVIEW_HTML.write_text(
        f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>Combined J corrections review</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;margin:0;background:#f4f6f8;color:#182033}}
header{{position:sticky;top:0;z-index:2;background:#fff;border-bottom:1px solid #d8dee9;padding:12px 16px}}
h1{{font-size:22px;margin:0 0 8px}} h2{{font-size:16px;margin:0 0 6px}}
.summary{{font-size:13px;line-height:1.45}} .toolbar{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}}
button{{border:1px solid #a7b4c7;background:#fff;border-radius:6px;padding:6px 9px;cursor:pointer}}
button.active{{background:#254edb;color:#fff;border-color:#254edb}}
main{{padding:12px 16px}}
.card{{background:#fff;border:1px solid #d8dee9;border-radius:8px;margin:12px 0;padding:12px;display:grid;grid-template-columns:minmax(260px,0.9fr) minmax(520px,2fr);gap:12px}}
.meta p{{font-size:13px;line-height:1.45;word-break:break-all;margin:0}}
.imgs{{display:grid;grid-template-columns:repeat(3,minmax(160px,1fr));gap:10px}}
figure{{margin:0}} figcaption{{font-size:13px;font-weight:700;margin-bottom:5px}}
img{{width:100%;height:260px;object-fit:contain;background:#fafafa;border:1px solid #e5e7eb}}
.corrected_l042_final_cutout{{border-left:5px solid #0f9f6e}}
.corrected_l043_quantity{{border-left:5px solid #7c3aed}}
.current_full_audit{{border-left:5px solid #94a3b8}}
.ok{{color:#07834f;font-weight:700}} .warn{{color:#b42318;font-weight:700}}
@media(max-width:900px){{.card{{grid-template-columns:1fr}}.imgs{{grid-template-columns:1fr}}img{{height:320px}}}}
</style></head><body>
<header>
  <h1>J 合并修正复核页</h1>
  <div class="summary">
    records: {len(merged)} ｜ {esc(status_summary)}<br>
    修正覆盖：L042 使用 final cutout 透明 PNG + skill 软纹理背景；L043 使用白/灰源 PNG + 15/30 PCS 标注。未标记 corrected 的行保持当前全量 J 审核记录。
  </div>
  <div class="toolbar">
    <button type="button" class="active" data-filter-status="all">全部</button>
    <button type="button" data-filter-status="corrected_l042_final_cutout">只看 L042 修正</button>
    <button type="button" data-filter-status="corrected_l043_quantity">只看 L043 修正</button>
    <button type="button" data-filter-status="current_full_audit">只看其他当前 J</button>
    {prefix_options}
  </div>
</header>
<main>{''.join(cards)}</main>
<script>
const buttons=[...document.querySelectorAll('button')];
let status='all'; let prefix='all';
function applyFilter(){{
  document.querySelectorAll('.card').forEach(card=>{{
    const okStatus = status === 'all' || card.dataset.status === status;
    const okPrefix = prefix === 'all' || card.dataset.prefix === prefix;
    card.style.display = okStatus && okPrefix ? '' : 'none';
  }});
}}
buttons.forEach(btn=>btn.addEventListener('click',()=>{{
  if(btn.dataset.filterStatus){{ status=btn.dataset.filterStatus; document.querySelectorAll('[data-filter-status]').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); }}
  if(btn.dataset.filterPrefix){{ prefix = prefix === btn.dataset.filterPrefix ? 'all' : btn.dataset.filterPrefix; document.querySelectorAll('[data-filter-prefix]').forEach(b=>b.classList.remove('active')); if(prefix!=='all') btn.classList.add('active'); }}
  applyFilter();
}}));
</script>
</body></html>""",
        encoding="utf-8",
    )
    print(json.dumps({"review": str(REVIEW_HTML), "records": len(merged), "status_counts": dict(status_counts)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
