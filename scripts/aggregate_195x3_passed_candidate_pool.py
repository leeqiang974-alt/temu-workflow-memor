from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


BASE_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_195x3_t_candidates_20260705")
REDO_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_195x3_redo_json45_20260706")
SEEDREAM_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_195x3_redo_json45_feedback_20260706")
SAFE3_OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_from_seedream_feedback_3_20260706")
OUT = Path(r"D:\Desktop\jit\DXXmall\outputs\store_newskill_195x3_passed_pool_20260706")


def load_json(path: Path, default=None):
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def file_url(value: str | None) -> str:
    if not value:
        return ""
    try:
        return Path(value).resolve().as_uri()
    except Exception:
        return ""


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def choose_ok_by_candidate(rows: list[dict]) -> dict[str, dict]:
    chosen: dict[str, dict] = {}
    for row in rows:
        cid = row.get("candidate_id") or row.get("d")
        local_path = row.get("local_path") or row.get("local_image")
        if not cid or row.get("status") not in {None, "ok"} or not local_path or not Path(local_path).exists():
            continue
        old = chosen.get(cid)
        if old is None or str(row.get("created_at", "")) >= str(old.get("created_at", "")):
            chosen[cid] = row
    return chosen


def selected_record(slot: dict, row: dict, stage: str, reason: str, chain: list[dict]) -> dict:
    return {
        "slot_id": slot["candidate_id"],
        "original_d": slot["original_d"],
        "prefix": slot["prefix"],
        "set_no": slot["set_no"],
        "selected_stage": stage,
        "selection_reason": reason,
        "selected_candidate_id": row.get("candidate_id") or row.get("d"),
        "provider": row.get("provider"),
        "model": row.get("model"),
        "local_path": row.get("local_path") or row.get("local_image"),
        "image_url": row.get("image_url"),
        "source_png": row.get("source_png"),
        "source_kind": row.get("source_kind"),
        "source_id": row.get("source_id"),
        "scene_lane": row.get("scene_lane"),
        "color_lane": row.get("color_lane"),
        "composition_lane": row.get("composition_lane"),
        "chain": chain,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    base_plan = load_json(BASE_OUT / "candidate_plan_197x3.json")
    base_results = choose_ok_by_candidate(load_json(BASE_OUT / "candidate_results_197x3.json"))
    initial_lock = load_json(BASE_OUT / "feedback_lock_20260706_from_decision_review.json")
    initial_bad = set((initial_lock.get("feedback") or {}).keys())

    redo_plan = load_json(REDO_OUT / "redo_json45_20260706_candidate_plan.json")
    redo_results = choose_ok_by_candidate(load_json(REDO_OUT / "candidate_results_redo_json45_20260706.json"))
    redo_feedback = load_json(SEEDREAM_OUT / "redo_json45_review_feedback_raw_20260706.json").get("feedback", {})

    seedream_plan = load_json(SEEDREAM_OUT / "source_plan_seedream_from_redo_json45_feedback_20260706.json")["items"]
    seedream_results = choose_ok_by_candidate(load_json(SEEDREAM_OUT / "seedream_fallback_results.json"))
    seedream_feedback = load_json(SAFE3_OUT / "seedream_13_review_feedback_raw_20260706.json").get("feedback", {})

    safe3_results = choose_ok_by_candidate(load_json(SAFE3_OUT / "image2_from_seedream_feedback_3_results.json"))
    safe3_plan = {item["candidate_id"]: item for item in load_json(SAFE3_OUT / "image2_from_seedream_feedback_3_plan.json")}

    slot_by_id = {item["candidate_id"]: item for item in base_plan}
    selected: dict[str, dict] = {}
    chain_by_slot: dict[str, list[dict]] = defaultdict(list)

    for slot_id, slot in slot_by_id.items():
        base_row = base_results.get(slot_id)
        if not base_row:
            chain_by_slot[slot_id].append({"stage": "original_image2", "decision": "missing_result"})
            continue
        if slot_id in initial_bad:
            fb = initial_lock["feedback"][slot_id]
            chain_by_slot[slot_id].append(
                {
                    "stage": "original_image2",
                    "candidate_id": slot_id,
                    "decision": fb.get("decision"),
                    "feedback": fb.get("feedback", ""),
                    "source_id": base_row.get("source_id"),
                    "local_path": base_row.get("local_path"),
                }
            )
        else:
            selected[slot_id] = selected_record(slot, base_row, "original_image2_keep", "not_marked_in_initial_review", chain_by_slot[slot_id])

    for item in redo_plan:
        redo_id = item["candidate_id"]
        slot_id = item["failed_candidate_id"]
        slot = slot_by_id[slot_id]
        row = redo_results.get(redo_id)
        if not row:
            chain_by_slot[slot_id].append({"stage": "image2_redo_json45", "candidate_id": redo_id, "decision": "missing_result"})
            continue
        decision = (redo_feedback.get(redo_id) or {}).get("decision", "keep")
        feedback = (redo_feedback.get(redo_id) or {}).get("feedback", "")
        source = "explicit" if redo_id in redo_feedback else "default_unreviewed_keep"
        chain_by_slot[slot_id].append(
            {
                "stage": "image2_redo_json45",
                "candidate_id": redo_id,
                "decision": decision,
                "feedback": feedback,
                "decision_source": source,
                "source_id": row.get("source_id"),
                "local_path": row.get("local_path"),
            }
        )
        if decision in {"redo", "reject"}:
            continue
        selected[slot_id] = selected_record(slot, row, "image2_redo_json45_keep", source, chain_by_slot[slot_id])

    for seedream_id, item in seedream_plan.items():
        slot_id = item["failed_candidate_id"]
        slot = slot_by_id[slot_id]
        row = seedream_results.get(seedream_id)
        if not row:
            chain_by_slot[slot_id].append({"stage": "seedream_fallback", "candidate_id": seedream_id, "decision": "missing_result"})
            continue
        decision = (seedream_feedback.get(seedream_id) or {}).get("decision", "keep")
        feedback = (seedream_feedback.get(seedream_id) or {}).get("feedback", "")
        chain_by_slot[slot_id].append(
            {
                "stage": "seedream_fallback",
                "candidate_id": seedream_id,
                "decision": decision,
                "feedback": feedback,
                "source_id": row.get("source_id"),
                "local_path": row.get("local_path") or row.get("local_image"),
            }
        )
        if decision in {"redo", "reject"}:
            continue
        selected[slot_id] = selected_record(slot, row, "seedream_fallback_keep", "explicit_seedream_review_keep", chain_by_slot[slot_id])

    for safe_id, row in safe3_results.items():
        item = safe3_plan[safe_id]
        seedream_id = item["failed_seedream_id"]
        slot_id = seedream_plan[seedream_id]["failed_candidate_id"]
        slot = slot_by_id[slot_id]
        chain_by_slot[slot_id].append(
            {
                "stage": "image2_safe_after_seedream_feedback",
                "candidate_id": safe_id,
                "decision": "keep",
                "feedback": "用户确认全部通过",
                "source_id": row.get("source_id"),
                "local_path": row.get("local_path"),
            }
        )
        selected[slot_id] = selected_record(slot, row, "image2_safe_after_seedream_keep", "user_confirmed_all_3_pass", chain_by_slot[slot_id])

    records = [selected[key] for key in sorted(selected, key=lambda cid: (slot_by_id[cid]["original_d"], slot_by_id[cid]["set_no"]))]
    by_d: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_d[record["original_d"]].append(record)
    by_d_sorted = {d: sorted(rows, key=lambda row: row["set_no"]) for d, rows in sorted(by_d.items())}

    missing_slots = [slot_id for slot_id in slot_by_id if slot_id not in selected]
    bad_set_counts = {d: len(rows) for d, rows in by_d_sorted.items() if len(rows) != 3}
    missing_files = [row["slot_id"] for row in records if not Path(row.get("local_path") or "").exists()]
    duplicate_slots = [slot for slot, count in Counter(row["slot_id"] for row in records).items() if count > 1]
    stage_counts = Counter(row["selected_stage"] for row in records)
    prefix_counts = Counter(row["prefix"] for row in records)

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "output": str(OUT),
        "total_slots_expected": len(base_plan),
        "total_selected": len(records),
        "unique_d": len(by_d_sorted),
        "expected_sets_per_d": 3,
        "missing_slots": missing_slots,
        "bad_set_counts": bad_set_counts,
        "missing_files": missing_files,
        "duplicate_slots": duplicate_slots,
        "stage_counts": dict(stage_counts),
        "prefix_counts": dict(sorted(prefix_counts.items())),
        "source_artifacts": {
            "base_plan": str(BASE_OUT / "candidate_plan_197x3.json"),
            "initial_feedback_lock": str(BASE_OUT / "feedback_lock_20260706_from_decision_review.json"),
            "redo_results": str(REDO_OUT / "candidate_results_redo_json45_20260706.json"),
            "seedream_results": str(SEEDREAM_OUT / "seedream_fallback_results.json"),
            "safe3_results": str(SAFE3_OUT / "image2_from_seedream_feedback_3_results.json"),
        },
    }
    if missing_slots or bad_set_counts or missing_files or duplicate_slots:
        summary["status"] = "blocked"
    else:
        summary["status"] = "ok"

    save_json(OUT / "final_195x3_passed_pool.json", records)
    save_json(OUT / "final_195x3_passed_pool_by_d.json", by_d_sorted)
    save_json(OUT / "final_195x3_passed_pool_summary.json", summary)
    write_summary_md(summary)
    write_html(by_d_sorted, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def write_summary_md(summary: dict) -> None:
    lines = [
        "# 195x3 Passed Candidate Pool",
        "",
        f"- created_at: {summary['created_at']}",
        f"- status: `{summary['status']}`",
        f"- total_slots_expected: {summary['total_slots_expected']}",
        f"- total_selected: {summary['total_selected']}",
        f"- unique_d: {summary['unique_d']}",
        f"- expected_sets_per_d: {summary['expected_sets_per_d']}",
        f"- missing_slots: {len(summary['missing_slots'])}",
        f"- bad_set_counts: {len(summary['bad_set_counts'])}",
        f"- missing_files: {len(summary['missing_files'])}",
        f"- duplicate_slots: {len(summary['duplicate_slots'])}",
        "",
        "## Stage Counts",
        "",
        "| stage | count |",
        "|---|---:|",
    ]
    for stage, count in summary["stage_counts"].items():
        lines.append(f"| {stage} | {count} |")
    lines.extend(["", "## Source Artifacts", ""])
    for key, value in summary["source_artifacts"].items():
        lines.append(f"- {key}: `{value}`")
    (OUT / "final_195x3_passed_pool_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_html(by_d: dict[str, list[dict]], summary: dict) -> None:
    rows = []
    for d, items in by_d.items():
        cells = []
        for item in items:
            cells.append(
                f"""
<td>
  <div class="slot">set {item['set_no']} · {esc(item['selected_stage'])}</div>
  <img src="{esc(file_url(item['local_path']))}" loading="lazy">
  <div class="meta">{esc(item['selected_candidate_id'])}<br>source {esc(item.get('source_id'))}</div>
</td>"""
            )
        while len(cells) < 3:
            cells.append("<td class='missing'>missing</td>")
        rows.append(f"<tr><th>{esc(d)}</th>{''.join(cells)}</tr>")
    stage_rows = "".join(f"<tr><td>{esc(k)}</td><td>{v}</td></tr>" for k, v in summary["stage_counts"].items())
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>195x3 passed pool</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;margin:0;background:#f6f4ef;color:#1f2937}}
header{{position:sticky;top:0;background:#fff;border-bottom:1px solid #ddd;padding:12px 18px;z-index:2}}
main{{padding:16px}}table{{border-collapse:collapse;width:100%;background:#fff}}th,td{{border:1px solid #ddd;vertical-align:top;padding:8px}}th{{width:120px;background:#f9fafb;position:sticky;left:0}}td{{width:31%}}img{{width:100%;height:220px;object-fit:contain;background:#fff}}.slot{{font-weight:700;color:#4c1d95;margin-bottom:6px}}.meta{{font-size:12px;color:#4b5563;word-break:break-all;margin-top:6px}}.missing{{background:#fee2e2;color:#991b1b}}.stats{{display:flex;gap:14px;flex-wrap:wrap}}.stats div{{background:#f3f4f6;border-radius:6px;padding:6px 8px}}details{{margin-top:8px}}.small td,.small th{{font-size:12px;padding:4px 8px}}
</style></head><body><header>
<h2>195x3 Passed Candidate Pool</h2>
<div class="stats"><div>status: <b>{esc(summary['status'])}</b></div><div>selected: {summary['total_selected']} / {summary['total_slots_expected']}</div><div>D: {summary['unique_d']}</div><div>sets/D: 3</div><div>missing files: {len(summary['missing_files'])}</div></div>
<details><summary>Stage counts</summary><table class="small"><tr><th>stage</th><th>count</th></tr>{stage_rows}</table></details>
</header><main><table><tbody>{''.join(rows)}</tbody></table></main></body></html>"""
    (OUT / "final_195x3_passed_pool_review.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
