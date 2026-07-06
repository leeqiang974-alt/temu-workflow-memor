# 2026-07-06 L043 J quantity overlay correction

## Issue

The first L043 quantity repair regenerated a new five-grid image from the
white/gray SKU source PNG. User feedback clarified that the existing/current
L043 five-grid J composition was already visually good.

## Rule

For L043 J quantity repair:

- Keep the existing approved/current five-grid J composition as the base image.
- Derive quantity from row `G` + `SKU货号`.
- Overlay `15 PCS` or `30 PCS` once at the whole image's top-left corner in red.
- Do not regenerate a different five-grid layout from `白.png` / `灰.png` when
  the existing composition is visually approved.

## Updated Artifacts

- `scripts/repair_l043_j_quantity_review.py`
- `D:\Desktop\jit\DXXmall\outputs\store_newskill_192_writeback_195x3_set1_full_title_j_20260706\l043_j_quantity_fix_review\index.html`
- `D:\Desktop\jit\DXXmall\outputs\store_newskill_192_writeback_195x3_set1_full_title_j_20260706\combined_j_corrections_review\index.html`
