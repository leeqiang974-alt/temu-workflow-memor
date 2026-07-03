from __future__ import annotations

import html
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


BASE_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702")
REDO61_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_redo_61_20260703")
SEEDREAM_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_197x3_redo_feedback_20260703")
REDO2_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_seedream_redo2_3_20260703")
REDO4_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo4_two_pngs_20260703")
REDO5_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo5_single_png_20260703")

OUT = Path(
    os.environ.get(
        "OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_197x3_passed_pool_20260703",
    )
)

SELECTED_PATH = OUT / "197x3_passed_pool_selected_591.json"
SUMMARY_PATH = OUT / "197x3_passed_pool_summary.json"
SUMMARY_MD_PATH = OUT / "197x3_passed_pool_summary.md"
REVIEW_PATH = OUT / "197x3_passed_pool_review.html"
OVERFLOW_PATH = OUT / "197x3_passed_pool_overflow_approved.json"
REJECTED_PATH = OUT / "197x3_passed_pool_rejected_chain.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def by_candidate_id(rows: list[dict], key: str = "candidate_id") -> dict[str, dict]:
    result = {}
    for row in rows:
        cid = row.get(key) or row.get("d")
        if cid and row.get("status") == "ok":
            result[cid] = row
    return result


def normalize_local_path(row: dict) -> str:
    return str(row.get("local_path") or row.get("local_image") or "")


def slot_from_candidate(candidate_id: str) -> str:
    match = re.match(r"^(L\d{9}__set[123])", candidate_id)
    if not match:
        raise ValueError(f"Cannot derive original slot from candidate id: {candidate_id}")
    return match.group(1)


def d_from_slot(slot: str) -> str:
    return slot.split("__", 1)[0]


def set_no_from_slot(slot: str) -> int:
    match = re.search(r"__set(\d+)", slot)
    if not match:
        return 0
    return int(match.group(1))


def candidate_url(value: str | None) -> str:
    if not value:
        return ""
    path = Path(value)
    roots = [
        (OUT, f"/outputs/{OUT.name}"),
        (BASE_OUT, f"/outputs/{BASE_OUT.name}"),
        (REDO61_OUT, f"/outputs/{REDO61_OUT.name}"),
        (SEEDREAM_OUT, f"/outputs/{SEEDREAM_OUT.name}"),
        (REDO2_OUT, f"/outputs/{REDO2_OUT.name}"),
        (REDO4_OUT, f"/outputs/{REDO4_OUT.name}"),
        (REDO5_OUT, f"/outputs/{REDO5_OUT.name}"),
        (Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs"), "/outputs"),
    ]
    for root, prefix in roots:
        try:
            rel = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        return prefix + "/" + quote(rel.as_posix(), safe="/")
    return ""


def make_entry(row: dict, slot: str, source_stage: str, decision_basis: str) -> dict:
    local_path = normalize_local_path(row)
    cid = row.get("candidate_id") or row.get("d")
    if source_stage == "seedream_fallback" and cid and not str(cid).endswith("__seedream_fallback"):
        cid = f"{cid}__seedream_fallback"
    return {
        "original_d": d_from_slot(slot),
        "slot": slot,
        "set_no": set_no_from_slot(slot),
        "candidate_id": cid,
        "source_stage": source_stage,
        "decision_basis": decision_basis,
        "provider": row.get("provider"),
        "model": row.get("model"),
        "source_id": row.get("source_id"),
        "source_png": row.get("source_png"),
        "local_path": local_path,
        "url": candidate_url(local_path),
        "status": row.get("status"),
        "cost_usd_est": row.get("cost_usd_est", 0),
        "prompt": row.get("prompt", ""),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    base_results = by_candidate_id(load_json(BASE_OUT / "candidate_results_197x3.json"))
    initial_lock = load_json(BASE_OUT / "feedback_lock_197x3_review_20260703.json")
    redo61_results = by_candidate_id(load_json(REDO61_OUT / "candidate_results_redo_61.json"))
    redo61_lock = load_json(SEEDREAM_OUT / "feedback_lock_redo_61_review_seedream_20260703.json")
    seedream_results = by_candidate_id(load_json(SEEDREAM_OUT / "seedream_fallback_results.json"), key="d")
    seedream_redo2_lock = load_json(REDO2_OUT / "feedback_lock_seedream_16_review_redo2_20260703.json")
    redo2_results = by_candidate_id(load_json(REDO2_OUT / "image2_seedream_redo2_3_results.json"))
    redo4_results = by_candidate_id(load_json(REDO4_OUT / "l043060503_ai_redo4_two_pngs_results.json"))
    redo5_results = by_candidate_id(load_json(REDO5_OUT / "l043060503_ai_redo5_single_png_results.json"))

    initial_redo_ids = {record["candidate_id"] for record in initial_lock["records"]}
    redo61_decisions = redo61_lock["feedback"]
    seedream_redo2_ids = set(seedream_redo2_lock["feedback"])

    latest_user_pass = {
        "L043060503__set3__redo1__redo5_ai_single": {
            "decision": "keep",
            "feedback": "可以了，通过了，归集起来，197一共3套",
            "ts": "2026-07-03",
        }
    }

    selected_by_slot: dict[str, dict] = {}
    rejected_chain: list[dict] = []
    overflow_approved: list[dict] = []

    for cid, row in sorted(base_results.items()):
        slot = slot_from_candidate(cid)
        if cid not in initial_redo_ids:
            selected_by_slot[slot] = make_entry(row, slot, "original_image2_197x3", "original_not_marked_redo")
            continue
        rejected_chain.append({"candidate_id": cid, "slot": slot, "stage": "original_image2", "reason": "initial_review_redo"})

    for original_id in sorted(initial_redo_ids):
        slot = slot_from_candidate(original_id)
        redo1_id = f"{original_id}__redo1"
        decision = redo61_decisions.get(redo1_id, {})
        if not decision:
            raise RuntimeError(f"Missing redo61 decision: {redo1_id}")

        if decision.get("decision") == "keep":
            row = redo61_results.get(redo1_id)
            if not row:
                raise RuntimeError(f"Missing kept redo61 result: {redo1_id}")
            selected_by_slot[slot] = make_entry(row, slot, "image2_redo61", decision.get("source", "redo61_keep"))
            continue

        rejected_chain.append(
            {
                "candidate_id": redo1_id,
                "slot": slot,
                "stage": "image2_redo61",
                "reason": decision.get("feedback") or "redo61_review_redo",
            }
        )

        if redo1_id in seedream_redo2_ids:
            seedream_row = seedream_results.get(redo1_id)
            if seedream_row:
                rejected_chain.append(
                    {
                        "candidate_id": redo1_id,
                        "slot": slot,
                        "stage": "seedream_fallback",
                        "reason": seedream_redo2_lock["feedback"][redo1_id].get("feedback") or "seedream_review_redo",
                        "local_path": normalize_local_path(seedream_row),
                    }
                )
            if slot == "L043060503__set3":
                redo2_id = "L043060503__set3__redo1__redo2_image2"
                rejected_chain.append(
                    {
                        "candidate_id": redo2_id,
                        "slot": slot,
                        "stage": "image2_redo2",
                        "reason": "用户反馈：还是错；后续 redo4/redo5 替换",
                    }
                )
                redo4_bad = redo4_results["L043060503__set3__redo1__redo4_ai_a"]
                rejected_chain.append(
                    {
                        "candidate_id": "L043060503__set3__redo1__redo4_ai_a",
                        "slot": slot,
                        "stage": "image2_redo4",
                        "reason": "png的一致性太差了，换个png",
                        "source_id": redo4_bad.get("source_id"),
                        "local_path": normalize_local_path(redo4_bad),
                    }
                )
                redo4_good = redo4_results["L043060503__set3__redo1__redo4_ai_b"]
                overflow_approved.append(
                    make_entry(
                        redo4_good,
                        slot,
                        "image2_redo4_extra_pass",
                        "user_keep_through_overflow_backup",
                    )
                )
                row = redo5_results["L043060503__set3__redo1__redo5_ai_single"]
                selected_by_slot[slot] = make_entry(
                    row,
                    slot,
                    "image2_redo5_latest_pass",
                    latest_user_pass["L043060503__set3__redo1__redo5_ai_single"]["feedback"],
                )
                continue

            redo2_match = None
            for row in redo2_results.values():
                if row.get("failed_seedream_id") == redo1_id:
                    redo2_match = row
                    break
            if not redo2_match:
                raise RuntimeError(f"Missing redo2 replacement for {redo1_id}")
            selected_by_slot[slot] = make_entry(redo2_match, slot, "image2_redo2", "seedream_review_redo_then_image2_pass")
            continue

        seedream_row = seedream_results.get(redo1_id)
        if not seedream_row:
            raise RuntimeError(f"Missing seedream fallback result: {redo1_id}")
        selected_by_slot[slot] = make_entry(seedream_row, slot, "seedream_fallback", "redo61_review_redo_seedream_default_pass")

    selected = [selected_by_slot[slot] for slot in sorted(selected_by_slot, key=lambda value: (d_from_slot(value), set_no_from_slot(value)))]
    groups: dict[str, list[dict]] = defaultdict(list)
    for entry in selected:
        groups[entry["original_d"]].append(entry)

    bad_counts = {d: len(items) for d, items in groups.items() if len(items) != 3}
    missing_images = [entry for entry in selected if not entry["local_path"] or not Path(entry["local_path"]).exists()]
    selected_ids = {entry["candidate_id"] for entry in selected}
    rejected_ids = {entry["candidate_id"] for entry in rejected_chain}
    rejected_collision = sorted(selected_ids & rejected_ids)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rule": "197 exact D groups, exactly 3 selected candidates per D. Latest user-approved redo5 is selected for L043060503 set3; redo4_b kept as overflow approved backup.",
        "counts": {
            "selected": len(selected),
            "unique_d": len(groups),
            "bad_group_count": len(bad_counts),
            "overflow_approved": len(overflow_approved),
            "rejected_chain": len(rejected_chain),
            "missing_images": len(missing_images),
            "rejected_collision": len(rejected_collision),
        },
        "source_stage_counts": dict(Counter(entry["source_stage"] for entry in selected)),
        "bad_groups": bad_counts,
        "missing_images": missing_images,
        "rejected_collision": rejected_collision,
        "latest_user_pass": latest_user_pass,
    }
    if bad_counts or missing_images or rejected_collision:
        summary["status"] = "blocked"
    else:
        summary["status"] = "ok"

    save_json(SELECTED_PATH, selected)
    save_json(SUMMARY_PATH, summary)
    save_json(OVERFLOW_PATH, overflow_approved)
    save_json(REJECTED_PATH, rejected_chain)
    write_summary_md(summary)
    write_review_html(selected, overflow_approved, rejected_chain, summary)
    print(json.dumps({"out": str(OUT), "status": summary["status"], "selected": len(selected), "unique_d": len(groups), "review": str(REVIEW_PATH)}, ensure_ascii=False, indent=2))


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def write_summary_md(summary: dict) -> None:
    lines = [
        "# 197x3 Passed Pool Aggregation",
        "",
        f"- generated_at: {summary['generated_at']}",
        f"- status: `{summary['status']}`",
        f"- selected: `{summary['counts']['selected']}`",
        f"- unique_d: `{summary['counts']['unique_d']}`",
        f"- bad_group_count: `{summary['counts']['bad_group_count']}`",
        f"- overflow_approved: `{summary['counts']['overflow_approved']}`",
        f"- missing_images: `{summary['counts']['missing_images']}`",
        f"- rejected_collision: `{summary['counts']['rejected_collision']}`",
        "",
        "## Source Stage Counts",
        "",
        "| stage | count |",
        "|---|---:|",
    ]
    for stage, count in sorted(summary["source_stage_counts"].items()):
        lines.append(f"| {stage} | {count} |")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- selected JSON: `{SELECTED_PATH}`",
            f"- overflow approved JSON: `{OVERFLOW_PATH}`",
            f"- rejected chain JSON: `{REJECTED_PATH}`",
            f"- review HTML: `{REVIEW_PATH}`",
            "",
            "Note: this aggregation does not write back Excel and does not upload final product images.",
        ]
    )
    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_review_html(selected: list[dict], overflow: list[dict], rejected: list[dict], summary: dict) -> None:
    groups: dict[str, list[dict]] = defaultdict(list)
    for entry in selected:
        groups[entry["original_d"]].append(entry)
    cards = []
    for d_value in sorted(groups):
        imgs = []
        for entry in sorted(groups[d_value], key=lambda item: item["set_no"]):
            imgs.append(
                f"""<figure>
  <img loading="lazy" src="{esc(entry['url'])}">
  <figcaption>set{entry['set_no']} · {esc(entry['candidate_id'])}<br>{esc(entry['source_stage'])} · {esc(entry.get('source_id'))}</figcaption>
</figure>"""
            )
        cards.append(
            f"""<section class="card">
  <h3>{esc(d_value)} <span>{len(groups[d_value])}/3</span></h3>
  <div class="grid">{''.join(imgs)}</div>
</section>"""
        )

    overflow_rows = "\n".join(
        f"<tr><td>{esc(item['original_d'])}</td><td>{esc(item['slot'])}</td><td>{esc(item['candidate_id'])}</td><td>{esc(item['source_stage'])}</td><td><a href='{esc(item['url'])}' target='_blank'>image</a></td></tr>"
        for item in overflow
    )
    rejected_rows = "\n".join(
        f"<tr><td>{esc(item.get('slot'))}</td><td>{esc(item.get('candidate_id'))}</td><td>{esc(item.get('stage'))}</td><td>{esc(item.get('reason'))}</td></tr>"
        for item in rejected
    )
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>197x3 Passed Pool</title>
<style>
body{{margin:0;background:#f5f3ee;color:#1f2937;font-family:Arial,"Microsoft YaHei",sans-serif}}
header{{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid #ddd;padding:12px 18px}}
.wrap{{max-width:1600px;margin:0 auto;padding:16px}}
.stats{{display:flex;gap:10px;flex-wrap:wrap}}
.stats b{{background:#eef2ff;border:1px solid #c7d2fe;border-radius:6px;padding:5px 8px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin:12px 0;padding:10px}}
.card h3{{margin:0 0 8px;font-size:16px;display:flex;justify-content:space-between}}
.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}}
figure{{margin:0;border:1px solid #e5e7eb;background:#fafafa;padding:6px}}
img{{display:block;width:100%;height:260px;object-fit:contain;background:#fff}}
figcaption{{font-size:12px;line-height:1.35;color:#555;word-break:break-all}}
details{{background:#fff;border:1px solid #ddd;border-radius:8px;margin:12px 0;padding:10px}}
table{{width:100%;border-collapse:collapse;font-size:12px;background:#fff}}
td,th{{border:1px solid #e5e7eb;padding:5px;vertical-align:top}}
@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header>
  <h2>197x3 Passed Pool Aggregation</h2>
  <div class="stats">
    <b>status {esc(summary['status'])}</b>
    <b>selected {summary['counts']['selected']}</b>
    <b>D {summary['counts']['unique_d']}</b>
    <b>bad groups {summary['counts']['bad_group_count']}</b>
    <b>overflow {summary['counts']['overflow_approved']}</b>
    <b>missing {summary['counts']['missing_images']}</b>
  </div>
</header>
<main class="wrap">
  <details open><summary>归集说明</summary>
    <p>每个 exact D 主池严格 3 张。L043060503 set3 使用本轮通过的 redo5；redo4_b 作为额外通过备份，不进入主池。此页不写回 Excel、不上传。</p>
  </details>
  {''.join(cards)}
  <details><summary>额外通过备份 overflow_approved ({len(overflow)})</summary><table><tr><th>D</th><th>slot</th><th>candidate</th><th>stage</th><th>image</th></tr>{overflow_rows}</table></details>
  <details><summary>剔除链 rejected_chain ({len(rejected)})</summary><table><tr><th>slot</th><th>candidate</th><th>stage</th><th>reason</th></tr>{rejected_rows}</table></details>
</main>
</body>
</html>"""
    REVIEW_PATH.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
