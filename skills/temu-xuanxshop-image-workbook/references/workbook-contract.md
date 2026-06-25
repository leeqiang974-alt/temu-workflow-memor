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
- Same exact D must have:
  - identical title
  - identical T URL list
  - identical U URL
  - same first T image
- J may differ by row because J follows variant.

## T URL Rules

- T is a newline-separated URL list.
- T must contain at most 10 URLs unless user changes the limit.
- T first is the generated/approved first-carousel image.
- U must equal T first.
- Deduplicate T URLs while preserving order.
- If a size image is locked at position 4, preserve it at position 4 after insert/reorder.

## Fourth Image / Size Image

When the user says the fourth image is a size image or existing workflow expects it:

- Identify size image by position and/or filename/URL clues such as `尺寸`.
- Keep it in T position 4.
- Do not replace it with AI/lifestyle output.
- Validate every same-D T list has position 4 unchanged.

## Title Rules

Same D gets same title. If rewriting titles:

- Prefer 70-80 Chinese characters when possible.
- Put count/spec at the beginning when present: `1件`, `1套`, `三件装`, `50个`, `15/30`, `2/3层`.
- Add a deterministic tracking code like `Q7M`: letter-digit-letter.
- Keep category accurate from product image/source.
- Avoid unsupported claims and prohibited terms.

Avoid terms:

`自动`, `智能`, `AI`, `APP`, `蓝牙`, `wifi`, `遥控`, `感应`, `电动`, `充电`, `电池`, `USB`, `儿童`, `玩具`, `环保`, `有机`, `可降解`, `食品级`, `最佳`, `最好`, `顶级`, `久用不塌陷`, `长久不变形`, `亲肤`, `高弹填充`, `四面延伸`.

## Validation Checklist

Before final delivery, report:

- effective row count
- unique exact D count
- same-D title mismatch count
- title length/forbidden-word count if titles were changed
- empty J count
- empty T count
- T over 10 URLs count
- U != T first count
- same-D T mismatch count
- fourth size image mismatch count when applicable
- SKU source paths containing forbidden words
- missing source assets
- generated image local existence and dimensions
- upload URL prefix checks if OSS/CDN writeback was done

If any count is nonzero, list examples and do not claim the workbook is finished.
