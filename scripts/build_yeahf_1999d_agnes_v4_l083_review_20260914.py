"""Build the one-item V4 task-scene review page for L083080809."""
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
V3 = ROOT / "human_redo4_agnes_v3_20260914"
V4 = ROOT / "human_redo1_agnes_v4_l083_task_20260914"
PLAN = V4 / "agnes_v4_l083_task_plan.json"
RESULT = V4 / "agnes_v4_l083_task_manifest.json"
REVIEW = V4 / "review"
ASSETS = REVIEW / "assets"
HTML = REVIEW / "index.html"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def asset(source: Path, name: str) -> dict:
    target = ASSETS / f"{name}{source.suffix.lower()}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {"source_path": str(source), "review_path": str(target), "sha256": sha256(target)}


def url(path: Path) -> str:
    return "/".join(quote(part) for part in path.relative_to(REVIEW).parts)


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8-sig"))["records"][0]
    result = json.loads(RESULT.read_text(encoding="utf-8-sig"))["records"][0]
    if result.get("status") != "validated":
        raise RuntimeError("V4 L083 is not validated")
    files = {
        "product": Path(plan["submitted_images"][0]["path"]),
        "v2": Path(plan["negative_evidence_not_submitted"][2]["path"]),
        "v3": Path(plan["negative_evidence_not_submitted"][3]["path"]),
        "v4": Path(result["local_path"]),
    }
    assets = {key: asset(path, key) for key, path in files.items()}
    (REVIEW / "review_asset_manifest.json").write_text(json.dumps({
        "schema": "yeahf-1999d-agnes-v4-l083-task-review-assets/v1",
        "D": "L083080809",
        "columns": ["product", "v2", "v3", "v4"],
        "assets": assets,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    labels = {"product": "精确D产品参考", "v2": "V2悬空（驳回）", "v3": "V3无任务（驳回）", "v4": "V4任务场景"}
    figures = "".join(
        f'<figure><img loading="eager" src="{url(Path(assets[key]["review_path"]))}" alt="L083080809 {key}"><figcaption>{labels[key]}</figcaption></figure>'
        for key in ("product", "v2", "v3", "v4")
    )
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>L083080809 · V4任务场景审核</title><style>*{{box-sizing:border-box}}body{{margin:0;padding:24px;background:#090c11;color:#f3f6fb;font:15px/1.5 system-ui,"Microsoft YaHei",sans-serif}}main{{max-width:1700px;margin:auto}}h1{{margin:0}}p{{color:#aebbd0}}.images{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:18px}}figure{{margin:0;background:#141a23;border:1px solid #2c3545;border-radius:12px;overflow:hidden}}img{{width:100%;aspect-ratio:1;object-fit:contain;display:block;background:#05070a}}figcaption{{padding:10px;text-align:center}}button{{margin:18px 8px 0 0;border:0;border-radius:8px;padding:10px 18px;color:white;cursor:pointer}}.ok{{background:#14753b}}.bad{{background:#8d2222}}#state{{font-weight:700;color:#ffcf70}}@media(max-width:900px){{.images{{grid-template-columns:repeat(2,1fr)}}}}</style></head><body><main><h1>L083080809 · 任务场景重做</h1><p>要求：底座完整接触桌面，同时人物明确执行收纳任务。当前状态：<span id="state">待审核</span></p><div class="images">{figures}</div><button class="ok" onclick="setDecision('approved')">通过</button><button class="bad" onclick="setDecision('rejected')">不通过</button><button onclick="exportJson()">导出审核JSON</button></main><script>const key='yeahf1999d-agnes-v4-l083-review-v1';let decision=localStorage.getItem(key)||'pending';function render(){{document.getElementById('state').textContent=decision==='approved'?'通过':decision==='rejected'?'不通过':'待审核'}}function setDecision(v){{decision=v;localStorage.setItem(key,v);render()}}function exportJson(){{const data={{schema:'yeahf-1999d-agnes-v4-l083-human-review/v1',exported_at:new Date().toISOString(),decisions:[{{D:'L083080809',decision}}]}};const blob=new Blob([JSON.stringify(data,null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='YeahF_1999D_AgnesV4_L083审核结果.json';a.click();URL.revokeObjectURL(a.href)}}render();</script></body></html>'''
    REVIEW.mkdir(parents=True, exist_ok=True)
    HTML.write_text(html, encoding="utf-8")
    print(json.dumps({"html": str(HTML), "records": 1, "assets": 4}, ensure_ascii=False))


if __name__ == "__main__":
    main()
