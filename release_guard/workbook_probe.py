"""Read-only workbook profiler for Release Guard integration tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HEADERS = ("产品标题", "产品货号", "变种属性值一", "SKU货号", "预览图", "轮播图", "产品素材图", "SKC属性")

def probe_xlsx(path: str | Path) -> dict[str, Any]:
    try:
        from openpyxl import load_workbook
    except ImportError as e:
        raise RuntimeError("openpyxl is required for workbook probing") from e
    p = Path(path).resolve()
    if not p.is_file():
        raise FileNotFoundError(p)
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    wb = load_workbook(p, read_only=True, data_only=False)
    sheets = []
    for ws in wb.worksheets:
        values = list(ws.iter_rows(values_only=True))
        headers = [str(x).strip() if x is not None else "" for x in (values[0] if values else ())]
        index = {h: i for i, h in enumerate(headers)}
        missing = [h for h in HEADERS if h not in index]
        physical_rows = []
        for row_number, row in enumerate(values[1:], start=2):
            d = row[index["产品货号"]] if "产品货号" in index and index["产品货号"] < len(row) else None
            if d is None or str(d).strip() == "":
                continue
            get = lambda h: row[index[h]] if h in index and index[h] < len(row) else None
            physical_rows.append({"row": row_number, "D": str(d), "G": str(get("变种属性值一") or ""),
                                  "SKU": str(get("SKU货号") or ""), "J": str(get("预览图") or ""),
                                  "T": str(get("轮播图") or ""), "U": str(get("产品素材图") or "")})
        sheets.append({"sheet": ws.title, "dimension": ws.calculate_dimension(), "header_count": len(headers),
                       "headers": headers, "missing_required_headers": missing,
                       "physical_row_count": len(physical_rows), "physical_rows": physical_rows})
    return {"schema": "temu-release-workbook-probe/v1", "path": str(p), "sha256": digest,
            "sheet_count": len(sheets), "sheets": sheets}

def write_probe(path: str | Path, output: str | Path) -> dict[str, Any]:
    data = probe_xlsx(path)
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
