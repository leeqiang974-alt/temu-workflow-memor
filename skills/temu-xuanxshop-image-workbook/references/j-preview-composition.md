# J Preview Composition

Use this reference when generating or repairing workbook `J` preview images.

## Default Style

Default to the historical `sku-preview-texture-five-grid` style:

- 800 x 800 square image.
- Five repeated SKU previews in a loose five-grid layout:
  - top left
  - top right
  - center
  - bottom left
  - bottom right
- Use a soft textured commercial background, not a pure white background.
- Keep the texture subtle. If the user says the background is too complex, reduce contrast and line density; do not switch to blank white unless explicitly requested.
- Keep each SKU large enough to inspect, but not occupying the whole 1/9-like grid cell. A good starting scale is about 70%-74% of each slot's width/height.
- Use realistic contact shadow, but avoid hard panels, borders, stickers, labels, or decorative frames.

## Background Palette

Use unbranded soft material cues such as:

- `sand_terracotta_plaster`
- `sage_yellow_green_stone`
- `sky_blue_cream_mineral`
- `rose_peach_clay_plaster`
- `oat_beige_linen`
- `aqua_mint_ceramic`
- `lavender_greige_mineral`
- `butter_blue_limewash`

These are generated or composited backgrounds; they do not require external image assets.

## Source Image Priority

Prefer clean variant/cutout sources in this order:

1. `{sku_root}/{prefix}/sku文件_最终抠图PNG`
2. `{sku_root}/{prefix}/sku文件`
3. `{sku_root}/{prefix}/sku`

Within those folders, follow `variant-matching.md`: match by `G` + `SKU货号`, prefer variant folders with positive token matches, and show warnings for fallback matches.

## White Background Rule

Do not interpret "simple", "clean", or "不要复杂背景纹理" as white background. It means:

- lower texture contrast
- fewer decorative marks
- lighter shadows
- less saturated color
- simpler material gradient

Only use white if the user says `白底`, `纯白`, `white background`, or marketplace rules require it.

## Review Requirements

The review page for J must show:

- row number
- `D`
- prefix
- `G` variant
- SKU code
- wanted tokens
- matched tokens
- selected SKU source path
- match mode
- warning/fallback status
- generated J preview image

Do not write J URLs back to Excel until the user approves the review page.
