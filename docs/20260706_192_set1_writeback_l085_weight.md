# 20260706 192 Workbook Set1 T Writeback And L085 Weight Fix

## Scope

- Source workbook:
  `D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702\0616-2_199_最终回传_已应用反馈_L042J重做_T清理_通过T回填_20260702_剔除已复制D_过程_不入库_20260706_114036.xlsx`
- Output workbook:
  `D:\Desktop\jit\DXXmall\outputs\store_newskill_192_writeback_195x3_set1_20260706\0616-2_192_最终回传_195x3第一套T首图回填_L085重量150_T4保留_T够6_20260706.xlsx`
- Passed T source pool:
  `D:\Desktop\jit\DXXmall\outputs\store_newskill_195x3_passed_pool_20260706\final_195x3_passed_pool.json`

## User Correction

- The requested weight correction is `L085 1500 -> 150`.
- `L058` must remain `3500`.

## Actions

- Used set1 from the reviewed 195x3 passed T-first pool.
- Uploaded compressed 800x800 JPEG T-first images to OSS for the 192 exact-D values present in the workbook.
- Replaced T1 for each exact D because all existing D groups had at least 6 T URLs.
- Set U equal to the new T1.
- Preserved valid T4 size image position.
- Deleted blank-D trailing rows from the copied workbook only.
- Kept existing titles and J URLs unchanged, but generated J source-match audit artifacts.
- Changed L085 rows only: 7 rows from `1500.0` to `150`.
- Confirmed L058 rows remain `3500`.

## Validation

- Effective rows: 316
- Unique exact D: 192
- Changed D count: 192
- Empty J: 0
- Empty T: 0
- T over 10 URLs: 0
- T below 6 URLs: 0
- U not equal to T1: 0
- T4 missing/not size: 0
- T4 unreachable: 0
- Unsafe URL occurrences after writeback: 0
- Same-D title mismatch: 0
- Same-D T mismatch: 0
- Title changed: 0
- L085 weight not 150: 0
- J source missing/missing file/forbidden source: 0
- J warnings: 78 non-blocking warnings because J was preserved rather than rebuilt.

## Review Artifacts

- `t_writeback_audit.html`
- `j_match_audit.html`
- `validation_report.json`
- `writeback_report.json`
- `cell_diff_summary.json`
