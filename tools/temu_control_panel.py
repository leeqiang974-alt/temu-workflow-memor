from __future__ import annotations

import json
import html as html_lib
import mimetypes
import os
import subprocess
import sys
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from openpyxl import load_workbook


BASE_DIR = Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui")
WORK_DIR = BASE_DIR / "work"
OUTPUTS_DIR = BASE_DIR / "outputs"
DXX_OUTPUTS_DIR = Path(r"D:\Desktop\jit\DXXmall\outputs")
PYTHON_EXE = Path(r"D:\Programs\Python\Python311\python.exe")
HOST = "127.0.0.1"
PORT = 8765
STORE_ROOTS = {
    "dxxmall": Path(r"D:\Desktop\jit\DXXmall"),
    "cxxmall": Path(r"D:\Desktop\jit\CXXmall"),
    "fxxmall": Path(r"D:\Desktop\jit\FXXmall"),
}
PRICE_COPY_LOG_PATH = WORK_DIR / "temu_price_copy_events.json"
STORE_PRUNED_STATE_PATH = WORK_DIR / "temu_store_pruned_state.json"
EXCEL_SKIP_WORDS = ("过程", "不入库", "复检前", "候选", "candidate", "review")
EXCEL_PREFERRED_WORDS = ("最终", "回传", "true_final", "提交", "已应用")


def _read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_store(store: str) -> str:
    value = (store or "DXXmall").strip() or "DXXmall"
    known = {"dxxmall": "DXXmall", "cxxmall": "CXXmall", "fxxmall": "FXXmall"}
    return known.get(value.lower(), value)


def _store_root(store: str) -> Path:
    return STORE_ROOTS.get(_normalize_store(store).lower(), STORE_ROOTS["dxxmall"])


def _path_matches_store(path: Path, store: str) -> bool:
    root = _store_root(store)
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _load_price_copy_events():
    data = _read_json(PRICE_COPY_LOG_PATH, [])
    return data if isinstance(data, list) else []


def _save_price_copy_events(events):
    _write_json(PRICE_COPY_LOG_PATH, events)


def _title_tracking_code(title: str) -> str:
    import re

    text = str(title or "").strip()
    candidates = re.findall(r"(?:^|[^A-Z0-9])([A-Z0-9]{3})(?=$|[^A-Z0-9])", text.upper())
    noise = {"CSS", "WEB", "BOX", "SKU", "SPU", "RMB", "CNY"}
    candidates = [c for c in candidates if c not in noise and any(ch.isalpha() for ch in c) and any(ch.isdigit() for ch in c)]
    return candidates[-1] if candidates else ""


def _split_urls(value):
    import re

    if value is None:
        return []
    return [x.strip() for x in re.split(r"[\n,，;；]+", str(value)) if x.strip()]


def _tsv_cell(value):
    text = "" if value is None else str(value)
    return text.replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()


def _rows_to_tsv(rows):
    return "\n".join("\t".join(_tsv_cell(value) for value in row) for row in rows)


def _html_cell(value):
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "<br>".join(html_lib.escape(part) for part in text.split("\n"))


def _rows_to_html_rows(rows):
    html_rows = []
    for row in rows:
        cells = []
        for value in row:
            cells.append(
                '<td style="mso-number-format:\'\\@\';white-space:normal;border:1px solid #d9d9d9;padding:2px 4px;vertical-align:top;">'
                + _html_cell(value)
                + "</td>"
            )
        html_rows.append("<tr>" + "".join(cells) + "</tr>")
    return "\n".join(html_rows)


def _rows_to_excel_html(rows):
    return (
        '<html><head><meta charset="utf-8"></head><body>'
        '<table style="border-collapse:collapse;font-family:Arial,Microsoft YaHei,sans-serif;font-size:11pt;">'
        + _rows_to_html_rows(rows)
        + "</table></body></html>"
    )


def _find_header_col(headers, names):
    normalized = [str(h or "").strip() for h in headers]
    for name in names:
        for idx, header in enumerate(normalized):
            if name in header:
                return idx
    return None


def _should_scan_excel(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() not in {".xlsx", ".xlsm"}:
        return False
    lower = str(path).lower()
    name = path.name.lower()
    if name.startswith("~$"):
        return False
    return not any(word.lower() in lower for word in EXCEL_SKIP_WORDS)


def _excel_score(path: Path) -> tuple:
    lower = str(path).lower()
    preferred = sum(1 for word in EXCEL_PREFERRED_WORDS if word.lower() in lower)
    try:
        mtime = path.stat().st_mtime
    except Exception:
        mtime = 0
    return (preferred, mtime)


def _excel_files_for_store(store: str):
    root = _store_root(store)
    if not root.exists():
        return []
    files = [p for p in root.rglob("*.xls*") if _should_scan_excel(p)]
    files.sort(key=_excel_score, reverse=True)
    return files


def _latest_store_workbook(store: str):
    files = _excel_files_for_store(store)
    return files[0] if files else None


def _read_workbook_groups(path: Path):
    wb = load_workbook(path, data_only=False, read_only=True)
    try:
        ws = wb.active
        header_row = None
        header_idx = None
        for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            values = list(row)
            joined = " ".join(str(v or "") for v in values)
            if "产品货号" in joined and ("产品标题" in joined or "轮播图" in joined):
                header_row = values
                header_idx = idx
                break
        if not header_row:
            return {}
        cols = {
            "D": _find_header_col(header_row, ["产品货号", "D"]),
            "title": _find_header_col(header_row, ["产品标题", "标题"]),
            "sku": _find_header_col(header_row, ["SKU货号", "SKU"]),
            "t": _find_header_col(header_row, ["轮播图"]),
        }
        if cols["D"] is None:
            return {}
        groups = {}
        for row_idx, row in enumerate(ws.iter_rows(min_row=header_idx + 1, values_only=True), start=header_idx + 1):
            values = list(row)
            d_value = _tsv_cell(values[cols["D"]] if cols["D"] < len(values) else "")
            if not d_value:
                continue
            item = groups.setdefault(
                d_value,
                {
                    "D": d_value,
                    "title": "",
                    "fingerprint": "",
                    "sku_values": set(),
                    "rows": [],
                    "row_numbers": [],
                    "t_first": "",
                },
            )
            title = _tsv_cell(values[cols["title"]] if cols["title"] is not None and cols["title"] < len(values) else "")
            sku = _tsv_cell(values[cols["sku"]] if cols["sku"] is not None and cols["sku"] < len(values) else "")
            t_value = _tsv_cell(values[cols["t"]] if cols["t"] is not None and cols["t"] < len(values) else "")
            if title and not item["title"]:
                item["title"] = title
                item["fingerprint"] = _title_tracking_code(title)
            if sku:
                item["sku_values"].add(sku.upper())
            if t_value and not item["t_first"]:
                urls = _split_urls(t_value)
                item["t_first"] = urls[0] if urls else ""
            item["rows"].append(values)
            item["row_numbers"].append(row_idx)
        return groups
    finally:
        wb.close()


def _query_d_groups(query: str, store: str):
    query_norm = str(query or "").strip()
    query_upper = query_norm.upper()
    if not query_norm:
        return {"items": [], "error_count": 0}
    items = []
    errors = []
    for path in _excel_files_for_store(store):
        try:
            groups = _read_workbook_groups(path)
        except Exception as exc:
            errors.append({"file": str(path), "error": str(exc)})
            continue
        for d_value, group in groups.items():
            sku_hit = any(query_upper and query_upper in sku for sku in group["sku_values"])
            if query_upper not in {d_value.upper(), group["fingerprint"].upper()} and not sku_hit and query_upper not in group["title"].upper():
                continue
            rows = group["rows"]
            row_numbers = group["row_numbers"]
            items.append(
                {
                    "file": str(path),
                    "file_name": path.name,
                    "sheet": "active",
                    "D": d_value,
                    "title": group["title"],
                    "fingerprint": group["fingerprint"],
                    "t_first": group["t_first"],
                    "row_count": len(rows),
                    "row_range": f"{min(row_numbers)}-{max(row_numbers)}" if row_numbers else "",
                    "row_numbers": row_numbers,
                    "tsv": _rows_to_tsv(rows),
                    "html": _rows_to_excel_html(rows),
                    "htmlRows": _rows_to_html_rows(rows),
                    "column_count": max((len(row) for row in rows), default=0),
                }
            )
    items.sort(key=lambda item: _excel_score(Path(item["file"])), reverse=True)
    return {
        "items": items,
        "query": query_norm,
        "store": _normalize_store(store),
        "error_count": len(errors),
        "errors": errors[:10],
        "built_at": _now_text(),
    }


def _record_price_copy_event(payload):
    query = str(payload.get("D") or payload.get("lookupKey") or "").strip()
    event = {
        "id": f"evt_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "copied_at": _now_text(),
        "store": _normalize_store(payload.get("store") or "DXXmall"),
        "D": str(payload.get("D") or "").strip(),
        "fingerprint": str(payload.get("fingerprint") or "").strip().upper(),
        "title": str(payload.get("title") or "").strip(),
        "source_file": str(payload.get("source_file") or payload.get("file") or "").strip(),
        "source_sheet": str(payload.get("source_sheet") or payload.get("sheet") or "").strip(),
        "row_count": int(payload.get("row_count") or 0),
        "declare_price": payload.get("declare_price"),
        "declare_reference_price": payload.get("declare_reference_price"),
        "lookup": query,
    }
    events = _load_price_copy_events()
    events.append(event)
    _save_price_copy_events(events)
    return {"ok": True, "event": event, "count": len(events)}


def _price_copy_status(store: str, fingerprint: str = "", d_value: str = ""):
    store_norm = _normalize_store(store).lower()
    fp = str(fingerprint or "").strip().upper()
    d_norm = str(d_value or "").strip().upper()
    matches = []
    for event in _load_price_copy_events():
        if str(event.get("store") or "").lower() != store_norm:
            continue
        if fp and str(event.get("fingerprint") or "").upper() == fp:
            matches.append(event)
        elif d_norm and str(event.get("D") or "").upper() == d_norm:
            matches.append(event)
    matches.sort(key=lambda item: str(item.get("copied_at") or ""))
    return {"ok": True, "copied": bool(matches), "count": len(matches), "latest": matches[-1] if matches else None, "events": matches[-20:]}


def _passed_d_events_for_store(store: str):
    store_norm = _normalize_store(store).lower()
    return [event for event in _load_price_copy_events() if str(event.get("store") or "").lower() == store_norm and str(event.get("D") or "").strip()]


def _passed_d_set_for_store(store: str):
    return {str(event.get("D")).strip() for event in _passed_d_events_for_store(store)}


def _record_latest_pruned(store: str, path: Path):
    state = _read_json(STORE_PRUNED_STATE_PATH, {})
    if not isinstance(state, dict):
        state = {}
    state[_normalize_store(store)] = {"path": str(path), "updated_at": _now_text()}
    _write_json(STORE_PRUNED_STATE_PATH, state)


def _latest_pruned_workbook(store: str):
    state = _read_json(STORE_PRUNED_STATE_PATH, {})
    path_text = ((state or {}).get(_normalize_store(store)) or {}).get("path", "")
    if path_text and Path(path_text).exists():
        return Path(path_text)
    root = _store_root(store)
    candidates = list(root.rglob("*剔除已复制D*过程*不入库*.xlsx")) if root.exists() else []
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _generate_store_pruned_workbook(store: str, source: str = ""):
    store = _normalize_store(store)
    source_path = Path(source).resolve() if source else _latest_store_workbook(store)
    passed = _passed_d_set_for_store(store)
    if not source_path or not source_path.exists():
        return {"ok": False, "error": f"没有找到店铺表格：{store}"}
    if not _path_matches_store(source_path, store):
        return {"ok": False, "error": f"表格不属于店铺目录：{source_path}"}
    wb = load_workbook(source_path)
    try:
        ws = wb.active
        header = [ws.cell(1, col).value for col in range(1, ws.max_column + 1)]
        d_col_idx = _find_header_col(header, ["产品货号", "D"])
        if d_col_idx is None:
            return {"ok": False, "error": "缺少产品货号列"}
        d_col = d_col_idx + 1
        remove_rows = []
        for row in range(2, ws.max_row + 1):
            d_value = _tsv_cell(ws.cell(row, d_col).value)
            if d_value and d_value in passed:
                remove_rows.append(row)
        for row in reversed(remove_rows):
            ws.delete_rows(row, 1)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = source_path.with_name(f"{source_path.stem}_剔除已复制D_过程_不入库_{timestamp}.xlsx")
        wb.save(output)
    finally:
        wb.close()
    _record_latest_pruned(store, output)
    report = output.with_suffix(".剔除报告.json")
    data = {
        "ok": True,
        "store": store,
        "source": str(source_path),
        "output": str(output),
        "report": str(report),
        "passed_d_count": len(passed),
        "removed_d_count": len({d for d in passed if d}),
        "removed_row_count": len(remove_rows),
        "kept_row_count": max(0, ws.max_row - 1 - len(remove_rows)) if "ws" in locals() else 0,
        "note": "该文件名含“过程_不入库”，D 搜索索引会跳过；最终上传表请另存为最终/提交命名后再入库。",
    }
    _write_json(report, data)
    return data


def _preflight_store_full_workflow(store: str):
    store = _normalize_store(store)
    source = _latest_pruned_workbook(store)
    errors = []
    warnings = []
    stats = {"effective_rows": 0, "unique_d": 0, "residual_passed_row_count": 0, "missing_fingerprint_count": 0, "duplicate_fingerprint_count": 0, "bad_t4_count": 0}
    if not source:
        return {"ok": False, "store": store, "source": "", "errors": ["没有找到剔除D底表；请先生成剔除D底表。"], "warnings": [], "stats": stats}
    passed = _passed_d_set_for_store(store)
    try:
        groups = _read_workbook_groups(source)
        stats["effective_rows"] = sum(len(g["rows"]) for g in groups.values())
        stats["unique_d"] = len(groups)
        fp_to_d = {}
        for d_value, group in groups.items():
            if d_value in passed:
                stats["residual_passed_row_count"] += len(group["rows"])
            fp = group["fingerprint"]
            if not fp:
                stats["missing_fingerprint_count"] += 1
            else:
                fp_to_d.setdefault(fp, set()).add(d_value)
            if group["rows"]:
                # T4 只做基础提示，不替代最终表格硬校验。
                t_urls = _split_urls(group.get("t_first", ""))
                if len(t_urls) < 1:
                    warnings.append(f"{d_value} 缺少轮播图首图")
        stats["duplicate_fingerprint_count"] = sum(1 for values in fp_to_d.values() if len(values) > 1)
        if stats["residual_passed_row_count"]:
            errors.append(f"底表里仍存在已复制D：{stats['residual_passed_row_count']} 行")
        if stats["duplicate_fingerprint_count"]:
            errors.append(f"发现重复指纹指向多个D：{stats['duplicate_fingerprint_count']} 个")
        if stats["missing_fingerprint_count"]:
            warnings.append(f"标题缺少三位指纹：{stats['missing_fingerprint_count']} 个D")
    except Exception as exc:
        errors.append(f"读取底表失败：{exc}")
    return {"ok": not errors, "store": store, "source": str(source), "errors": errors, "warnings": warnings, "stats": stats}


def _write_bytes(handler: BaseHTTPRequestHandler, status: int, body: bytes, content_type: str):
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Private-Network", "true")
    handler.end_headers()
    handler.wfile.write(body)


def _json_response(handler: BaseHTTPRequestHandler, data, status: int = 200):
    _write_bytes(
        handler,
        status,
        json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
        "application/json; charset=utf-8",
    )


def _html_response(handler: BaseHTTPRequestHandler, html: str, status: int = 200):
    _write_bytes(handler, status, html.encode("utf-8"), "text/html; charset=utf-8")


def _build_t_asset_registry_if_needed(force: bool = False):
    registry_dir = OUTPUTS_DIR / "t_image_asset_registry"
    registry_json = registry_dir / "t_image_asset_registry.json"
    registry_html = registry_dir / "t_image_asset_registry.html"
    script = WORK_DIR / "build_t_image_asset_registry.py"
    if force or not registry_json.exists() or not registry_html.exists():
        if not script.exists():
            raise FileNotFoundError(f"缺少资产库脚本: {script}")
        python_exe = PYTHON_EXE if PYTHON_EXE.exists() else Path(sys.executable)
        subprocess.run(
            [str(python_exe), str(script)],
            cwd=str(WORK_DIR),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    data = _read_json(registry_json, {})
    return {
        "ok": True,
        "registry_json": str(registry_json),
        "registry_html": str(registry_html),
        "url": "/outputs/t_image_asset_registry/t_image_asset_registry.html",
        "summary": data.get("summary", {}),
        "records_preview": (data.get("records") or [])[:50],
    }


def _index_html():
    asset_info = {}
    try:
        asset_info = _build_t_asset_registry_if_needed(False)
    except Exception as exc:
        asset_info = {"ok": False, "error": str(exc)}
    summary = asset_info.get("summary") or {}
    summary_rows = "".join(
        f"<tr><th>{key}</th><td>{json.dumps(value, ensure_ascii=False)}</td></tr>"
        for key, value in summary.items()
        if key in {"total_records", "reusable_records", "current_batch_ready_d_count", "by_tier", "by_status"}
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Temu 自动化控制面板</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #eef2f7; color: #1f2937; }}
    header {{ background: #111827; color: #fff; padding: 16px 24px; }}
    header h1 {{ margin: 0 0 5px; font-size: 22px; }}
    header p {{ margin: 0; color: #cbd5e1; }}
    main {{ max-width: 1360px; margin: 0 auto; padding: 14px 18px 24px; }}
    .tabs {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 12px; }}
    .tab {{ border: 1px solid #c7d2fe; background: #fff; color: #1e40af; padding: 8px 12px; border-radius: 7px; font-weight: 700; cursor: pointer; }}
    .tab.active {{ background: #2563eb; color: #fff; border-color: #2563eb; }}
    .panel {{ display: none; background: #fff; border: 1px solid #d9e1ec; border-radius: 8px; padding: 16px; box-shadow: 0 4px 18px rgba(15, 23, 42, .06); }}
    .panel.active {{ display: block; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .card {{ background: #fff; border: 1px solid #d9e1ec; border-radius: 8px; padding: 14px; }}
    h2 {{ margin: 0 0 10px; font-size: 18px; }}
    h3 {{ margin: 0 0 8px; font-size: 15px; }}
    a.button, button {{ display: inline-block; padding: 8px 12px; border-radius: 7px; border: 1px solid #2563eb; background: #2563eb; color: #fff; text-decoration: none; font-weight: 700; margin: 4px 6px 4px 0; cursor: pointer; }}
    button.secondary, a.secondary {{ background: #fff; color: #2563eb; }}
    button.warn {{ background: #b45309; border-color: #b45309; }}
    input, select {{ padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 7px; margin: 4px 6px 4px 0; }}
    textarea {{ width: 100%; min-height: 170px; border: 1px solid #cbd5e1; border-radius: 7px; padding: 8px; white-space: pre; overflow: auto; box-sizing: border-box; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; background: #fff; }}
    th, td {{ border: 1px solid #d9e1ec; padding: 7px; text-align: left; vertical-align: top; }}
    code {{ background: #eef2ff; padding: 2px 5px; border-radius: 5px; }}
    .ok {{ color: #15803d; font-weight: 700; }}
    .warn {{ color: #b45309; font-weight: 700; }}
    .muted {{ color: #64748b; font-size: 12px; }}
    .box {{ white-space: pre-wrap; background: #f8fafc; border: 1px solid #d9e1ec; border-radius: 8px; padding: 10px; min-height: 70px; overflow: auto; }}
    #urlPreview img {{ max-width: 220px; max-height: 220px; object-fit: contain; border: 1px solid #d9e1ec; margin: 6px; background: #fff; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Temu 自动化控制面板</h1>
    <p>多 tab 工作台已恢复：旧完整源码未找回，本页按历史功能重建；危险旧全流程入口仍受保护。</p>
  </header>
  <main>
    <div class="tabs" id="tabs">
      <button class="tab active" data-tab="overview">总览</button>
      <button class="tab" data-tab="dlookup">D首图查行</button>
      <button class="tab" data-tab="store">店铺新表</button>
      <button class="tab" data-tab="tassets">T首图资产</button>
      <button class="tab" data-tab="sku">出单SKU替换</button>
      <button class="tab" data-tab="imgpreview">图片链接预览</button>
      <button class="tab" data-tab="price">核价追踪</button>
      <button class="tab" data-tab="logs">任务日志</button>
      <button class="tab" data-tab="files">文件与工作流</button>
    </div>

    <section id="overview" class="panel active">
      <h2>总览</h2>
      <div class="grid">
        <div class="card">
          <h3>后台状态</h3>
          <button onclick="loadStatus()">刷新状态</button>
          <a class="button secondary" href="/outputs/">浏览 outputs</a>
          <div id="statusBox" class="box">outputs：<code>{OUTPUTS_DIR}</code><br>work：<code>{WORK_DIR}</code></div>
        </div>
        <div class="card">
          <h3>当前硬规则</h3>
          <div class="box">T 首图首轮 image2/APIMart；失败或复检不合格再 Seedream。
J 图按行 SKU PNG 严格匹配。
T4 固定保留尺寸图；T 最多 10 张。
删除、不要、死刑、错色、白色 L086 等记录不得回流。
技术、workflow、skill 更新必须同步 GitHub。</div>
        </div>
      </div>
    </section>

    <section id="dlookup" class="panel">
      <h2>D首图查行 / 指纹复制测试</h2>
      <div class="card">
        <select id="store"><option>DXXmall</option><option>CXXmall</option><option>FXXmall</option></select>
        <input id="lookup" placeholder="D值 / 标题指纹 / SKU" />
        <button onclick="queryD()">查询</button>
        <button class="secondary" onclick="copyFirst()">复制首个命中D行</button>
        <div id="queryResult" class="box muted">输入 D 值、标题指纹或 SKU 后查询。复制会同时写入 text/html 表格和 TSV，尽量保持 Excel/WPS 单元格格式。</div>
      </div>
    </section>

    <section id="store" class="panel">
      <h2>店铺新表</h2>
      <div class="card">
        <button onclick="previewPassed()">预览已复制D</button>
        <button onclick="generatePruned()">生成剔除D底表</button>
        <button class="secondary" onclick="preflightFull()">预检完整流程</button>
        <button class="warn" onclick="runFull()">生成完整新表（受保护）</button>
        <div id="storeResult" class="box muted">先复制通过 D，再生成剔除D底表。完整新表入口当前受最新规则保护，只允许预检确认。</div>
      </div>
    </section>

    <section id="tassets" class="panel">
      <h2>T首图资产</h2>
      <div class="card">
        <a class="button" href="/outputs/t_image_asset_registry/t_image_asset_registry.html">打开资产库</a>
        <a class="button secondary" href="/api/t-image-assets">查看资产库 API</a>
        <button class="secondary" onclick="rebuildAssets()">重建资产库</button>
        <table>{summary_rows}</table>
      </div>
    </section>

    <section id="sku" class="panel">
      <h2>出单SKU替换</h2>
      <div class="box">旧完整实现源码未恢复；当前先保留入口，避免误以为可以安全自动替换。需要跑出单 SKU 替换时，先按最新表格规则走预检，再单独执行脚本/审核页。</div>
    </section>

    <section id="imgpreview" class="panel">
      <h2>图片链接预览</h2>
      <textarea id="urlInput" placeholder="每行一个图片 URL，或粘贴含逗号/空格分隔的链接"></textarea>
      <button onclick="previewUrls()">预览</button>
      <div id="urlPreview" class="box"></div>
    </section>

    <section id="price" class="panel">
      <h2>核价追踪</h2>
      <div class="box">插件依赖 8765 后台接口；D 行复制已改为富剪贴板 HTML + TSV。翻页、全局筛选和报价记录仍在浏览器扩展侧执行。</div>
    </section>

    <section id="logs" class="panel">
      <h2>任务日志</h2>
      <button onclick="loadJobs()">刷新任务</button>
      <div id="jobsBox" class="box">点击刷新查看后台任务状态。</div>
    </section>

    <section id="files" class="panel">
      <h2>文件与工作流</h2>
      <div class="grid">
        <div class="card"><h3>运行目录</h3><div class="box">work：<code>{WORK_DIR}</code><br>outputs：<code>{OUTPUTS_DIR}</code></div></div>
        <div class="card"><h3>GitHub/本地记忆</h3><div class="box">本次恢复基于 README、docs/current-status.md、workflow 与 skill 规则。旧多 tab 源码未在本地备份中找回。</div></div>
      </div>
    </section>
  </main>
  <script>
    let lastQuery = null;
    const $ = (id) => document.getElementById(id);
    function store() {{ return $("store").value || "DXXmall"; }}
    async function api(path, opts) {{
      const res = await fetch(path, Object.assign({{cache:"no-store"}}, opts || {{}}));
      const text = await res.text();
      let data;
      try {{ data = JSON.parse(text); }} catch (err) {{ data = {{ok:false,error:text}}; }}
      if (!res.ok) throw new Error(data.error || text || ("HTTP " + res.status));
      return data;
    }}
    function summarizeItem(item) {{
      if (!item) return "无命中";
      return [
        "D: " + item.D,
        "文件: " + item.file_name,
        "行: " + item.row_range + " / " + item.row_count + " 行",
        "列数: " + (item.column_count || "-"),
        "标题: " + (item.title || "-"),
        "首图: " + (item.t_first || "-")
      ].join("\\n");
    }}
    async function queryD() {{
      const q = $("lookup").value.trim();
      if (!q) {{ $("queryResult").textContent = "请输入查询值"; return; }}
      $("queryResult").textContent = "查询中……";
      const data = await api("/api/d-groups?d=" + encodeURIComponent(q) + "&store=" + encodeURIComponent(store()));
      lastQuery = data;
      $("queryResult").textContent = "命中: " + ((data.items || []).length) + "\\n\\n" + summarizeItem((data.items || [])[0]);
    }}
    async function copyPayload(text, html) {{
      if (html && navigator.clipboard && navigator.clipboard.write && window.ClipboardItem) {{
        await navigator.clipboard.write([new ClipboardItem({{
          "text/html": new Blob([html], {{type:"text/html;charset=utf-8"}}),
          "text/plain": new Blob([text || ""], {{type:"text/plain;charset=utf-8"}})
        }})]);
      }} else {{
        await navigator.clipboard.writeText(text || "");
      }}
    }}
    async function copyFirst() {{
      const item = lastQuery && lastQuery.items && lastQuery.items[0];
      if (!item) {{ await queryD(); }}
      const fresh = lastQuery && lastQuery.items && lastQuery.items[0];
      if (!fresh) {{ $("queryResult").textContent += "\\n无可复制行"; return; }}
      await copyPayload(fresh.tsv || "", fresh.html || "");
      $("queryResult").textContent += "\\n\\n已复制首个命中 D 行（HTML表格+TSV）。";
    }}
    async function previewPassed() {{
      $("storeResult").textContent = "读取中……";
      const data = await api("/api/store-passed-d?store=" + encodeURIComponent(store()));
      $("storeResult").textContent = "店铺: " + data.store + "\\n复制事件: " + data.event_count + "\\n唯一D: " + data.d_count + "\\n\\n" + (data.d_values || []).join("\\n");
    }}
    async function generatePruned() {{
      $("storeResult").textContent = "生成剔除D底表中……";
      const data = await api("/api/store-pruned-workbook?store=" + encodeURIComponent(store()));
      $("storeResult").textContent = JSON.stringify(data, null, 2);
      if (data.output) await navigator.clipboard.writeText(data.output);
    }}
    async function preflightFull() {{
      $("storeResult").textContent = "预检中……";
      const data = await api("/api/store-full-preflight?store=" + encodeURIComponent(store()));
      $("storeResult").textContent = JSON.stringify(data, null, 2);
    }}
    async function runFull() {{
      $("storeResult").textContent = "请求启动完整流程……";
      try {{
        const data = await api("/api/run", {{method:"POST", body:new URLSearchParams({{action:"store_full_workflow", store:store()}})}});
        $("storeResult").textContent = JSON.stringify(data, null, 2);
      }} catch (err) {{
        $("storeResult").textContent = "已阻止旧完整流程入口：\\n" + err.message;
      }}
    }}
    async function rebuildAssets() {{
      const data = await api("/api/t-image-assets?force=1");
      alert("已重建：" + JSON.stringify(data.summary || data));
    }}
    async function loadStatus() {{
      const data = await api("/api/status");
      $("statusBox").textContent = JSON.stringify(data, null, 2);
    }}
    async function loadJobs() {{
      const data = await api("/api/jobs");
      $("jobsBox").textContent = JSON.stringify(data, null, 2);
    }}
    function previewUrls() {{
      const urls = ($("urlInput").value || "").split(/[\\s,]+/).map(x => x.trim()).filter(Boolean);
      $("urlPreview").innerHTML = urls.map(u => '<a href="' + u.replace(/"/g, "&quot;") + '" target="_blank"><img loading="lazy" src="' + u.replace(/"/g, "&quot;") + '"></a>').join("");
    }}
    document.querySelectorAll(".tab").forEach(btn => btn.addEventListener("click", () => {{
      document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
      document.querySelectorAll(".panel").forEach(x => x.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");
    }}));
    loadStatus().catch(()=>{{}});
  </script>
</body>
</html>"""


class ControlPanelHandler(BaseHTTPRequestHandler):
    server_version = "TemuControlPanelRestoredTabs/1.0"

    def log_message(self, fmt, *args):
        print(f"[8765] {self.address_string()} - {fmt % args}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Access-Control-Request-Private-Network")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = unquote(parsed.path)
            query = parsed.query or ""
            params = parse_qs(query)

            if path in {"/", "/index.html"}:
                return _html_response(self, _index_html())

            if path == "/api/ping":
                return _json_response(self, {"ok": True, "mode": "restored-tabs", "port": PORT})

            if path == "/api/d-groups":
                lookup = (params.get("d") or params.get("fingerprint") or [""])[0]
                store = (params.get("store") or ["DXXmall"])[0]
                return _json_response(self, _query_d_groups(lookup, store))

            if path == "/api/fingerprint-copy":
                lookup = (params.get("fingerprint") or params.get("d") or [""])[0]
                store = (params.get("store") or ["DXXmall"])[0]
                return _json_response(self, _query_d_groups(lookup, store))

            if path in {"/api/copy-rows-by-fingerprint", "/api/search-rows", "/api/search"}:
                lookup = (params.get("fingerprint") or params.get("d") or [""])[0]
                store = (params.get("store") or ["DXXmall"])[0]
                data = _query_d_groups(lookup, store)
                if data.get("items"):
                    data["tsv"] = data["items"][0].get("tsv", "")
                    data["html"] = data["items"][0].get("html", "")
                    data["htmlRows"] = data["items"][0].get("htmlRows", "")
                    data["clipboardText"] = data["tsv"]
                return _json_response(self, data)

            if path == "/api/price-copy-status":
                store = (params.get("store") or ["DXXmall"])[0]
                fingerprint = (params.get("fingerprint") or [""])[0]
                d_value = (params.get("d") or [""])[0]
                return _json_response(self, _price_copy_status(store, fingerprint, d_value))

            if path == "/api/store-passed-d":
                store = (params.get("store") or ["DXXmall"])[0]
                events = _passed_d_events_for_store(store)
                d_values = sorted(_passed_d_set_for_store(store))
                return _json_response(
                    self,
                    {
                        "ok": True,
                        "store": _normalize_store(store),
                        "event_count": len(events),
                        "d_count": len(d_values),
                        "d_values": d_values,
                        "events": events[-100:],
                    },
                )

            if path == "/api/store-pruned-workbook":
                store = (params.get("store") or ["DXXmall"])[0]
                source = (params.get("source") or [""])[0]
                return _json_response(self, _generate_store_pruned_workbook(store, source))

            if path == "/api/store-full-preflight":
                store = (params.get("store") or ["DXXmall"])[0]
                return _json_response(self, _preflight_store_full_workflow(store))

            if path == "/api/jobs":
                return _json_response(self, {"ok": True, "jobs": [], "note": "旧完整后台任务队列源码未恢复；当前仅保留安全状态入口。"})

            if path.startswith("/api/jobs/"):
                return _json_response(self, {"ok": False, "error": "旧完整后台任务队列源码未恢复。"}, 404)

            if path == "/api/status":
                return _json_response(
                    self,
                    {
                        "ok": True,
                        "mode": "restored-tabs",
                        "outputs_dir": str(OUTPUTS_DIR),
                        "work_dir": str(WORK_DIR),
                        "note": "多 Tab 工作台已重建核心插件接口；完整新表入口仍按最新规则保护。",
                    },
                )

            if path == "/api/t-image-assets":
                return _json_response(self, _build_t_asset_registry_if_needed("force=1" in query))

            if path.startswith("/outputs/"):
                rel = path[len("/outputs/") :].replace("/", os.sep)
                if ".." in Path(rel).parts:
                    return _json_response(self, {"ok": False, "error": "非法路径"}, 403)
                target = (OUTPUTS_DIR / rel).resolve()
                if target.is_dir():
                    index_file = target / "index.html"
                    if index_file.exists():
                        target = index_file
                    else:
                        items = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
                        links = "\n".join(
                            f'<li><a href="{path.rstrip("/")}/{item.name}">{item.name}{" /" if item.is_dir() else ""}</a></li>'
                            for item in items
                        )
                        return _html_response(self, f"<h1>{target}</h1><ul>{links}</ul>")
                if not target.exists() or not target.is_file():
                    return _json_response(self, {"ok": False, "error": "文件不存在", "path": str(target)}, 404)
                content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                _write_bytes(self, 200, target.read_bytes(), content_type)
                return

            return _json_response(self, {"ok": False, "error": "未实现的应急接口", "path": path}, 404)
        except Exception as exc:
            return _json_response(
                self,
                {"ok": False, "error": str(exc), "trace": traceback.format_exc()},
                500,
            )

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = unquote(parsed.path)
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8", errors="replace") if length else ""
            if path == "/api/price-copy-event":
                payload = json.loads(raw or "{}")
                if not isinstance(payload, dict):
                    return _json_response(self, {"ok": False, "error": "body must be json object"}, 400)
                return _json_response(self, _record_price_copy_event(payload))

            if path == "/api/run":
                return _json_response(
                    self,
                    {
                        "ok": False,
                        "error": "完整新表任务未在应急修复版中启用。请先按最新 GitHub 规则走 image2/APIMart、J 变体、T4 尺寸图审查流程。",
                    },
                    409,
                )

            return _json_response(self, {"ok": False, "error": "未实现的应急接口", "path": path}, 404)
        except Exception as exc:
            return _json_response(
                self,
                {"ok": False, "error": str(exc), "trace": traceback.format_exc()},
                500,
            )


def main():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), ControlPanelHandler)
    print(f"Temu control panel: http://{HOST}:{PORT}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
