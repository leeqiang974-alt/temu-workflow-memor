# SKU And Variant Matching

## Portable Inputs

Ask for `sku_root` if not known. Expected layout:

```text
sku_root/
  L042/
    sku文件_最终抠图PNG/
      black-or-variant-folder/
      green-or-variant-folder/
```

Do not hard-code drive letters. On another computer, the user may provide a different root.

## Clean Source Rules

Allowed image extensions: `.png`, `.jpg`, `.jpeg`, `.webp`.

Reject source paths containing:

- `九宫格`
- `9grid`
- `out`
- `output`
- `背景素材`
- generated preview/output folders
- prior product set folders unless the user explicitly chooses them

Prefer first-level files only:

1. Look in `{sku_root}/{prefix}/sku文件_最终抠图PNG`.
2. If that does not exist, look in `{sku_root}/{prefix}/sku文件`.
3. If that does not exist, look in `{sku_root}/{prefix}/sku`.
4. If clean first-level image files exist, match among those.
5. If no clean first-level image files exist, match first-level variant folders.
6. Inside a matched variant folder, choose clean first-level image files only.
7. Do not recurse into nested folders unless the user explicitly approves it.

## Token Matching

Extract tokens from `G` and `SKU货号`. Use title only as a last-resort hint because it can pollute matching.

Canonical tokens:

- black: `黑`, `black`
- white: `白`, `透明`, `white`
- gray: `灰`, `grey`, `gray`
- yellow: `黄`, `yellow`
- green: `绿`, `green`
- pink: `粉`, `pink`
- red: `红`, `red`
- blue: `蓝`, `blue`
- purple: `紫`, `purple`
- beige/wood: `杏`, `米`, `原木`, `木色`, `胡桃`, `wood`
- quantity/spec: `2`, `双`, `两`, `二`, `3`, `三`, `15`, `30`, `50`

Scoring:

- Strongly prefer color/material token match.
- Use quantity tokens only to disambiguate within a matched color/material.
- If no positive token matches, mark as warning/fallback and show the chosen source in review.

## T First Matching

T first image usually represents the whole D product group. For multi-variant D:

- Use distinct variant images represented by the D group.
- Do not repeat quantity variants unnecessarily.
- Example: if L043 has white/gray and 15/30 counts, use white and gray as distinct visual variants, not four separate duplicated foregrounds unless the user wants all counts visible.

## J Matching

J is row-level:

- Match each row using `G` + `SKU货号`.
- Print row, D, G, SKU, wanted tokens, matched tokens, source image, match mode, and warnings.
- Use the five-preview textured J composition in `j-preview-composition.md`.
- If the user says all J values are suspect, rebuild all J rows rather than patching a few rows.
- Do not write back J until the row-level review page is approved.
