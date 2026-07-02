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

Do not trust folder names alone. If source folders are known or suspected to contain mixed variants, add a visual validation pass:

- Verify obvious color/title cues when matching color variants.
- Reject files whose visible title/product color contradicts the desired variant, even if the folder path matches.
- Write rejected mixed-source paths and scores/reasons to JSON.
- Build an audit page that shows row, D, G, SKU, expected variant, source path, and generated J side by side.

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
- If the user reports color/variant mismatch, verify the rendered image itself, not only the source folder or filename.
- Do not write back J until the row-level review page is approved.

## L042 Special Case

For L042 garden edging SKU previews:

- Use only first-level files under the provided `L042/sku/黑色` and `L042/sku/绿色` folders unless the user changes the rule.
- Match black rows to black and green rows to green using `G` + `SKU货号`.
- Use the whole SKU size-chart image, preserving `Black/Green size`, dimensions, 30PCS nails, and the product body.
- Reject mixed raw sources by visual color/title checks. A file in `绿色` that visually says `Black size`, or a file in `黑色` that visually presents green, must not be used.
- If remove.bg is requested, try it only while credits are available; stop on `insufficient_credits` and return to the first-level size-chart five-grid plan.
