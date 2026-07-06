# 20260706 192 Workbook Set1 Full Title/J/T Writeback And L085 Weight Fix

## Correction

The earlier `store_newskill_192_writeback_195x3_set1_20260706` workbook was only a late-stage T-first writeback. It preserved title and J, so it is not the complete workbook deliverable for this request.

The corrected deliverable is:

`D:\Desktop\jit\DXXmall\outputs\store_newskill_192_writeback_195x3_set1_full_title_j_20260706\0616-2_192_最终回传_195x3第一套T首图回填_标题J全量重做_L085重量150_T4保留_T够6_20260706.xlsx`

## Executed Scope

- Used set1 from the reviewed `195x3` passed T-first pool.
- Replaced T1 for 192 exact-D groups.
- Set U equal to T1.
- Preserved valid T4 size-image position.
- Kept T URL count between 6 and 10.
- Rewrote product titles for all 316 effective rows with this workbook's per-D title fingerprint salt:
  `0616-2-192-set1-title-fingerprint-20260706`
- Rebuilt J preview images for all 316 effective rows.
- Wrote rebuilt J URLs to `预览图`.
- Synchronized `SKC属性.previewImgUrls` to each rebuilt J URL.
- Changed only L085 weight rows from `1500.0` to `150`.
- Confirmed L058 weight remains `3500`.
- Confirmed L085 rows have no `1500` residual in any cell.

## Validation

- Effective rows: 316
- Unique exact D: 192
- Title changed cells: 316
- J changed cells: 316
- SKC preview changed cells: 316
- L085 weight changes: 7
- Empty J/T: 0
- T over 10: 0
- T below 6: 0
- U not T1: 0
- T4 missing/not size: 0
- T4 unreachable: 0
- Unsafe URL occurrences after writeback: 0
- Same-D title mismatch: 0
- Title code missing/mismatch/duplicate: 0
- Forbidden title words: 0
- J not rebuilt URL: 0
- SKC preview not synced to J: 0
- L085 `1500` residual: 0
- L085 weight not 150: 0
- L058 weight changed: 0
- J missing source/file/forbidden source: 0
- J warnings: 73 non-blocking low-confidence/fallback source notices, with source provenance present for every row.

Independent check returned empty issue lists for:

- L058 bad weight
- L085 bad weight
- L085 `1500` residual
- SKC preview not synced to J
- missing title code
- U mismatch
- T count issue

Claude/NVIDIA final gate passed for the corrected workbook and reviewed:

- corrected workbook
- `validation_report.json`
- `t_writeback_audit.html`
- `j_match_audit.html`
