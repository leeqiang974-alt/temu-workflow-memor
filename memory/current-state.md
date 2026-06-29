# Current State

Date: 2026-06-25

## Active Workflow

The active work is the 189-row Temu/Xuanxshop workbook image workflow.

Main goals:

- Complete 189 T first images.
- Rebuild J preview images by strict row-level variant matching.
- Preserve product structure and user feedback locks.
- Keep fourth T image as the size/dimension image when applicable.
- Package the workflow as a reusable Codex skill and portable asset set for another computer.

## Round17 T State

Round17 T review output:

- Source records: `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\seedream_workbook_189_round17\records.json`
- Review page: `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\seedream_workbook_189_round17\round17_workbook_review.html`
- Records: 107
- OK generated images: 107
- Unique T source reference PNGs: 97

Important feedback:

- `L058060501` previously used a bad PNG and was rerun with replacement material.
- User feedback always overrides approved registries.

## Round17 J State

Round17 J strict review output:

- Source records: `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\workbook_189_j_strict_round17\workbook_189_j_strict_round17.json`
- Review page: `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\workbook_189_j_strict_round17\workbook_189_j_strict_round17.html`
- Records: 309
- OK generated images: 309
- Missing matches: 0
- Warnings needing human attention: 50
- Unique J source SKU PNGs: 45

J style rule:

- Use historical `sku-preview-texture-five-grid`.
- Do not default to white background.
- Use soft procedural material backgrounds such as plaster, linen, stone, ceramic, and limewash.
- Use SKU scale around 70%-74% of slot width/height.
- Source priority: `sku文件_最终抠图PNG`, then `sku文件`, then `sku`.

## Portable Packages

Current local portable package paths:

- `C:\Users\Administrator\Documents\Codex\2026-06-25\019ea56a-fa75-7402-bbed-4b384b57ea1d\outputs\temu_xuanxshop_j_skill_portable_20260625_155407.zip`
- `C:\Users\Administrator\Documents\Codex\2026-06-25\019ea56a-fa75-7402-bbed-4b384b57ea1d\outputs\temu_xuanxshop_full_tj_assets_portable_20260625_155823.zip`

The full package includes:

- T source PNGs: 97
- T generated images: 107
- J source SKU PNGs: 45
- J generated images: 309
- Skill files
- Records JSON and review HTML copies


## 2026-06-26 Seedream Prompt Skill Update

Added `skills/product-lifestyle-scene` to Git memory.

Key update:

- Seedream/Jimeng prompts must enforce realistic product usage context before premium styling.
- Product placement must match actual function, weight, contact surface, support/attachment method, gravity, and buyer use case.
- Reject physically absurd placements such as barbecue grills on beds, heavy racks floating on fabric, garden arches on sofas, pet mats on kitchen counters, or kitchen storage on bedroom bedding.
- For racks/shelves/trays/baskets/organizers, loose contents may be replaced for differentiation, but product hardware/body must remain fixed.
- Local prompt builder copies are stored under `skills/product-lifestyle-scene/references/` for audit and reuse.

## 2026-06-29 Image2 Expanded Scene T-First Updates

- Product lifestyle scene skill now separates scene-quality approval from product-consistency approval.
- T-first AI workflow now rotates color palette lanes: cool white, blue-gray, fresh outdoor green, dark luxury, warm wood, soft cream pastel, black-white contrast, neutral overcast.
- Approved Image2 expanded-scene library currently has 5 user-approved records; manifests only are synced, not large images.
- Rejected Round4 Image2 outputs locked out: `L042_premium_garden_border`, `L071_luxury_side_table`, `L072_entryway_shoe_storage`, `L076_premium_pet_corner`.
- High-risk products `L042/L071/L072/L076` should prefer scene-only generation plus exact PNG compositing instead of direct product-fusion redraw.
- Synced at 2026-06-29T22:41:36.
