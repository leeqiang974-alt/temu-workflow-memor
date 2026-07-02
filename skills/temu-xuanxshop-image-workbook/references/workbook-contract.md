# Workbook Contract And Validation

## Required Columns

Resolve columns by header text:

- `产品标题`: title
- `产品货号`: exact product group `D`
- `变种属性值一`: variant text `G`
- `SKU货号`: SKU code, useful for row-level variant matching
- `预览图`: `J` row-level preview image URL
- `轮播图`: `T` carousel URL list
- `产品素材图`: `U`, normally equal to first T URL

If headers differ, ask the user to map columns before processing.

## Group Rules

- Effective row: row with non-empty `产品货号`.
- Group key: exact `产品货号`, not only `L0xx` prefix.
- Prefix: first four characters, such as `L042`.
- Row identity is the original Excel row plus exact `D`, `G`, and `SKU货号`; preserve row order unless the user explicitly asks to reorder rows.
- Same exact D must have:
  - identical title
  - identical T URL list
  - identical U URL
  - same first T image
- J may differ by row because J follows variant.

## Cell Preservation And Allowed Writes

Before editing, snapshot all effective rows and headers. For ordinary image/title writeback:

- Allowed write columns are only the requested output columns, typically `产品标题`, `预览图` (J), `轮播图` (T), and `产品素材图` (U).
- Preserve row count, row order, `产品货号` (D), `变种属性值一` (G), `SKU货号`, variant/spec columns, formula cells, and unrequested shop fields.
- Do not rewrite X/AC or other helper/status columns unless the current shop workflow explicitly requires it. If updated, document the rule and row-level before/after values.
- Preserve formulas and number/date/text types in non-target columns.
- Produce a cell-level diff summary listing every changed cell by row, header, old value, and new value.
- If a non-target/protected cell changed, treat it as a validation error unless explicitly approved.

## T URL Rules

- T is a newline-separated URL list.
- T must contain at most 10 URLs unless user changes the limit.
- T first is the generated/approved first-carousel image.
- U must equal T first.
- Deduplicate T URLs while preserving order.
- If a size image is locked at position 4, preserve it at position 4 after insert/reorder.
- Apply user delete/reject locks before final validation, then re-deduplicate and re-cap at 10. Do not allow deleted/rejected URLs to return from existing workbook values or registries.

## Fourth Image / Size Image

When the user says the fourth image is a size image or existing workflow expects it:

- Identify size image by filename/URL/title clues such as `尺寸`, `size`, or `尺码`; do not assume original T[4] is still valid.
- Keep a valid size image in T position 4.
- If the current T[4] is deleted or not a size image, search remaining T URLs or approved size-image records and force a valid size image back to T[4].
- If no valid size image exists, block final delivery and report affected rows/D values.
- Do not replace it with AI/lifestyle output.
- Validate every same-D T list has a size image at position 4.

## Title Rules

Same D gets same title. If rewriting titles:

- Prefer 70-80 Chinese characters when possible.
- Put count/spec at the beginning when present: `1件`, `1套`, `三件装`, `50个`, `15/30`, `2/3层`.
- Add a deterministic tracking code like `Q7M`: letter-digit-letter.
- Keep category accurate from product image/source.
- Avoid unsupported claims and prohibited terms.
- The tracking code/fingerprint is scoped to the workbook and exact D. Never borrow a code from another workbook, another D, or a process/candidate table.
- If building a final writeback after image/T/J repair, recover the reconstructed title by exact D from the original final-confirmed/source workbook so the existing tracking code stays unchanged.
- Do not generate a new title/code during late-stage T/J writeback unless the user explicitly asks to rerun title reconstruction.
- Validate same-D title equality and per-D title-code uniqueness within the file.
- Keep process tables (`过程`, `复检前`, candidate/failure files) out of the title/D fingerprint registry.

Avoid terms:

`自动`, `智能`, `AI`, `APP`, `蓝牙`, `wifi`, `遥控`, `感应`, `电动`, `充电`, `电池`, `USB`, `儿童`, `玩具`, `环保`, `有机`, `可降解`, `食品级`, `最佳`, `最好`, `顶级`, `久用不塌陷`, `长久不变形`, `亲肤`, `高弹填充`, `四面延伸`.

## Validation Checklist

Before final delivery, report:

- effective row count
- unique exact D count
- same-D title mismatch count
- row count/order mismatch count
- protected cell changed count
- title length/forbidden-word count if titles were changed
- empty J count
- empty T count
- T over 10 URLs count
- U != T first count
- same-D T mismatch count
- fourth size image missing/not-at-T4 count when applicable
- deleted/rejected URL returned count
- T over 10 URLs count after all repair/delete/writeback steps
- L042 visual color/source mismatch count when L042 exists
- SKU source paths containing forbidden words
- missing source assets
- generated image local existence and dimensions
- upload URL prefix checks if OSS/CDN writeback was done
- changed-cell diff summary by column

If any count is nonzero, list examples and do not claim the workbook is finished.
