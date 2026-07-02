from __future__ import annotations

import html
import json
import shutil
from pathlib import Path


REPORT_PATH = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702"
    r"\l042_random_sizechart_j\l042_random_sizechart_j_report.json"
)
SERVED = Path(
    r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_fallback_9_20260702"
    r"\l042_j_pair_audit"
)


def build_card(record: dict | None, expected: str, d_value: str, errors: list[dict]) -> str:
    if record is None:
        errors.append({"d": d_value, "expected": expected, "error": "missing"})
        return f"<section class='bad'><h3>MISSING {expected}</h3></section>"

    expected_folder = "\\黑色\\" if expected == "black" else "\\绿色\\"
    ok = record["variant"] == expected and expected_folder in record["source"]
    if not ok:
        errors.append({"d": d_value, "expected": expected, "record": record})
    class_name = "ok" if ok else "bad"
    return f"""<section class="{class_name}">
<h3>{html.escape(expected.upper())} / row {record['row']}</h3>
<p><b>G:</b> {html.escape(str(record['g']))}</p>
<p><b>SKU:</b> {html.escape(str(record['sku']))}</p>
<p><b>variant:</b> {html.escape(str(record['variant']))}</p>
<p><b>source:</b> {html.escape(record['source'])}</p>
<img src="./{html.escape(Path(record['j_path']).name)}" loading="lazy">
</section>"""


def main() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    SERVED.mkdir(parents=True, exist_ok=True)
    for record in report["records"]:
        path = Path(record["j_path"])
        shutil.copy2(path, SERVED / path.name)

    by_d: dict[str, dict[str, dict]] = {}
    for record in report["records"]:
        by_d.setdefault(record["d"], {})[record["variant"]] = record

    errors: list[dict] = []
    rows = []
    for d_value in sorted(by_d):
        pair = by_d[d_value]
        rows.append(
            f"""<article>
<h2>{html.escape(d_value)}</h2>
<div class="pair">
{build_card(pair.get("black"), "black", d_value, errors)}
{build_card(pair.get("green"), "green", d_value, errors)}
</div>
</article>"""
        )

    page = f"""<!doctype html>
<meta charset="utf-8">
<title>L042 black green pair audit</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;margin:0;background:#f4f0e7;color:#222}}
header{{position:sticky;top:0;background:#fff;padding:14px 18px;border-bottom:1px solid #ddd;z-index:2}}
main{{max-width:1280px;margin:0 auto;padding:16px;display:grid;gap:16px}}
article{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px}}
h2{{margin:0 0 10px;font-size:18px}}h3{{margin:0 0 8px;font-size:15px}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
section{{border:4px solid #ddd;border-radius:8px;padding:10px;background:#fafafa}}
section.ok{{border-color:#2da44e}}section.bad{{border-color:#d1242f;background:#fff1f1}}
p{{font-size:12px;margin:4px 0;word-break:break-all}}
img{{display:block;width:100%;height:auto;border:1px solid #ccc;background:#eee;margin-top:8px}}
.badge{{display:inline-block;padding:3px 8px;border-radius:999px;background:#eee;margin-left:8px}}
@media(max-width:900px){{.pair{{grid-template-columns:1fr}}}}
</style>
<header><strong>L042 黑/绿成对匹配审核</strong>
<span class="badge">D pairs: {len(by_d)}</span>
<span class="badge">errors: {len(errors)}</span>
<br>规则：同一 D 左黑右绿；黑必须来自 黑色 一级文件夹，绿必须来自 绿色 一级文件夹。
</header>
<main>{''.join(rows)}</main>"""
    (SERVED / "index.html").write_text(page, encoding="utf-8")
    (SERVED / "pair_audit_report.json").write_text(
        json.dumps({"errors": errors, "pairs": by_d}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "url": "http://127.0.0.1:8765/outputs/store_newskill_seedream_fallback_9_20260702/l042_j_pair_audit/index.html",
                "error_count": len(errors),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
