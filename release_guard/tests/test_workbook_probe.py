from pathlib import Path
import pytest

openpyxl = pytest.importorskip("openpyxl")
from release_guard.workbook_probe import probe_xlsx

def test_probe_reads_a_realistic_54_column_workbook(tmp_path):
    path=tmp_path/"fixture.xlsx"; wb=openpyxl.Workbook(); ws=wb.active; ws.title="pddkj_product"
    headers=[f"H{i}" for i in range(54)]; headers[3]="产品货号"; headers[6]="变种属性值一"; headers[9]="预览图"; headers[11]="SKU货号"; headers[19]="轮播图"; headers[20]="产品素材图"
    ws.append(headers); row=[None]*54; row[3]="L095-00"; row[6]="2格"; row[11]="SKU-2"; ws.append(row); wb.save(path)
    result=probe_xlsx(path); sheet=result["sheets"][0]
    assert sheet["header_count"]==54; assert sheet["physical_row_count"]==1; assert sheet["physical_rows"][0]["D"]=="L095-00"
