from __future__ import annotations

import hashlib
import html
import json
import os
from pathlib import Path
from urllib.parse import quote


LIBRARY_ROOT = Path(r"D:\temu素材库\T首图候选暂存")
BATCH_ROOT = LIBRARY_ROOT / "YeahF_2000D_苍猿GPTImage2_重新生成闭环_20260723"
CANDIDATES = BATCH_ROOT / "candidates"
PLAN = Path(
    r"C:\Users\Administrator\Documents\temu自动化\outputs\yeahf_merged_d_0721"
    r"\YeahF_2000D_苍猿T1原稿参考任务清单_20260723.json"
)
PROGRESS = BATCH_ROOT / "cangyuan_closed_loop_progress_20260723.jsonl"
REVIEW_DIR = BATCH_ROOT / "review_289d_20260723"
REVIEW_HTML = REVIEW_DIR / "YeahF_2000D_新增289D_苍猿T1_原稿对照全量审核.html"
REVIEW_MANIFEST = REVIEW_DIR / "YeahF_2000D_新增289D_苍猿T1_全量审核清单.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def latest_progress() -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for line in PROGRESS.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("D"):
            latest[str(record["D"])] = record
    return latest


def url_from_library(path: Path) -> str:
    relative = path.resolve().relative_to(LIBRARY_ROOT.resolve())
    return "/" + "/".join(quote(part) for part in relative.parts)


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))["records"]
    latest = latest_progress()
    if len(plan) != 289:
        raise RuntimeError(f"expected 289 plan records, got {len(plan)}")

    rows: list[dict] = []
    failures: list[str] = []
    for index, item in enumerate(plan, start=1):
        d_value = str(item["target_D"])
        candidate = CANDIDATES / d_value[:4] / f"{d_value}.png"
        reference = Path(item["reference_image"])
        state = latest.get(d_value, {})
        if state.get("status") != "validated":
            failures.append(f"{d_value}: status={state.get('status')}")
            continue
        if not candidate.is_file() or not reference.is_file():
            failures.append(
                f"{d_value}: candidate={candidate.is_file()} reference={reference.is_file()}"
            )
            continue
        output_sha = sha256_file(candidate)
        if output_sha != state.get("output_sha256"):
            failures.append(f"{d_value}: output SHA mismatch")
            continue
        reference_sha = sha256_file(reference)
        if reference_sha != item.get("reference_sha256"):
            failures.append(f"{d_value}: reference SHA mismatch")
            continue
        rows.append(
            {
                "index": index,
                "D": d_value,
                "L0xx": item["l0xx"],
                "source_D": item["source_D"],
                "variants": item.get("variants", []),
                "reference_path": str(reference),
                "reference_sha256": reference_sha,
                "reference_url": url_from_library(reference),
                "candidate_path": str(candidate),
                "candidate_sha256": output_sha,
                "candidate_url": url_from_library(candidate),
                "task_id": state.get("task_id", ""),
                "width": state.get("width"),
                "height": state.get("height"),
                "prompt": item.get("prompt", ""),
                "review_status": "PENDING_USER_VISUAL_REVIEW",
            }
        )

    if failures or len(rows) != 289:
        raise RuntimeError(
            "review build blocked; " + json.dumps(failures, ensure_ascii=False)
        )

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_MANIFEST.write_text(
        json.dumps(
            {
                "schema": "yeahf-289d-cangyuan-review/v1",
                "count": len(rows),
                "server_root": str(LIBRARY_ROOT),
                "all_candidates_locally_validated": True,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    prefixes = sorted({row["L0xx"] for row in rows})
    prefix_options = "".join(
        f'<option value="{html.escape(prefix)}">{html.escape(prefix)}</option>'
        for prefix in prefixes
    )
    cards = []
    for row in rows:
        variants = "；".join(
            f"{v.get('G', '')} / {v.get('SKU', '')}" for v in row["variants"]
        )
        cards.append(
            f"""
<article class="card" data-prefix="{html.escape(row['L0xx'])}" data-d="{html.escape(row['D'])}">
  <header><b>{row['index']:03d}. {html.escape(row['D'])}</b><span>{html.escape(row['L0xx'])} · 原稿 {html.escape(row['source_D'])}</span></header>
  <div class="images">
    <figure><img loading="lazy" src="{row['reference_url']}" alt="{html.escape(row['D'])} 原稿"><figcaption>原稿参考</figcaption></figure>
    <figure><img loading="lazy" src="{row['candidate_url']}" alt="{html.escape(row['D'])} 苍猿结果"><figcaption>苍猿 T1</figcaption></figure>
  </div>
  <p class="variants">{html.escape(variants)}</p>
  <details><summary>路径、哈希与任务</summary>
    <div class="mono">task: {html.escape(str(row['task_id']))}</div>
    <div class="mono">原稿: {html.escape(row['reference_path'])}</div>
    <div class="mono">原稿 SHA: {row['reference_sha256']}</div>
    <div class="mono">结果: {html.escape(row['candidate_path'])}</div>
    <div class="mono">结果 SHA: {row['candidate_sha256']}</div>
  </details>
</article>"""
        )

    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>YeahF 2000D 新增289D 苍猿T1全量审核</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#f4f6f8;color:#17202a;font-family:"Segoe UI","Microsoft YaHei",sans-serif}}
.toolbar{{position:sticky;top:0;z-index:10;background:#111827;color:#fff;padding:14px 18px;box-shadow:0 2px 10px #0004}}
.toolbar h1{{font-size:20px;margin:0 0 10px}} .controls{{display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
select,input{{padding:8px 10px;border-radius:7px;border:1px solid #64748b}} .count{{font-weight:700;color:#93c5fd}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(560px,1fr));gap:14px;padding:16px}}
.card{{background:#fff;border:1px solid #dbe2ea;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px #0f172a12}}
.card header{{display:flex;justify-content:space-between;gap:10px;padding:10px 12px;background:#eef2ff}}
.card header span{{color:#475569}} .images{{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:8px}}
figure{{margin:0;background:#e5e7eb;border-radius:8px;overflow:hidden}} img{{display:block;width:100%;aspect-ratio:1/1;object-fit:contain;background:#ddd}}
figcaption{{padding:6px 8px;text-align:center;font-weight:700}} .variants{{margin:4px 12px 10px;color:#334155}}
details{{margin:0 12px 12px}} .mono{{font:12px Consolas,monospace;overflow-wrap:anywhere;margin-top:5px;color:#475569}}
.hidden{{display:none}} @media(max-width:700px){{.grid{{grid-template-columns:1fr;padding:8px}}.images{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="toolbar">
  <h1>YeahF 2000D · 新增 289D 苍猿 T1 原稿对照全量审核</h1>
  <div class="controls">
    <select id="prefix"><option value="">全部 L0xx</option>{prefix_options}</select>
    <input id="search" placeholder="搜索 D，例如 L047072664">
    <span class="count" id="count">289 / 289</span>
    <span>全部图片已本地解码、尺寸和 SHA-256 验证；尚未代表视觉通过。</span>
  </div>
</div>
<main class="grid" id="grid">{''.join(cards)}</main>
<script>
const cards=[...document.querySelectorAll('.card')], prefix=document.querySelector('#prefix'), search=document.querySelector('#search'), count=document.querySelector('#count');
function filter(){{const p=prefix.value,q=search.value.trim().toUpperCase();let n=0;cards.forEach(c=>{{const ok=(!p||c.dataset.prefix===p)&&(!q||c.dataset.d.includes(q));c.classList.toggle('hidden',!ok);if(ok)n++}});count.textContent=`${{n}} / 289`;}}
prefix.addEventListener('change',filter);search.addEventListener('input',filter);
</script>
</body></html>"""
    REVIEW_HTML.write_text(page, encoding="utf-8")
    print(
        json.dumps(
            {
                "count": len(rows),
                "html": str(REVIEW_HTML),
                "manifest": str(REVIEW_MANIFEST),
                "server_root": str(LIBRARY_ROOT),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
