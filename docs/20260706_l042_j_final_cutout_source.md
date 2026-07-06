# 2026-07-06 L042 J final cutout source normalization

## Change

Copied the verified transparent L042 J SKU PNGs into the current L042 special-case logic path:

- `E:\JIT制图--新店\L042\sku文件_最终抠图PNG\黑\黑.png`
  -> `E:\jit制图\L042\sku\黑色\L042_black_final_cutout.png`
- `E:\JIT制图--新店\L042\sku文件_最终抠图PNG\绿\绿.png`
  -> `E:\jit制图\L042\sku\绿色\L042_green_final_cutout.png`

Both target files were verified as `RGBA`, 800 x 800, with alpha range `(0, 255)`.

## Rule

When generating L042 J previews, if these normalized final cutout files exist, use only:

- `L042_black_final_cutout.png` for black rows
- `L042_green_final_cutout.png` for green rows

Do not randomly choose older RGB size-chart files from the same folders.

## Verification

Updated and checked these scripts so their L042 source pools return only the normalized final cutouts:

- `scripts/writeback_192_with_195x3_t_pool.py`
- `scripts/fix_195_set3_l042_l086_j.py`
- `scripts/repair_l042_j_neutral_review.py`

The regenerated L042 review manifest has 10 rows:

- 5 rows using `L042_black_final_cutout.png`
- 5 rows using `L042_green_final_cutout.png`
