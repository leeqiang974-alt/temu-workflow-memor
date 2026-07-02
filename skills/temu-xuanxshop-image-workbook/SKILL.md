---
name: temu-xuanxshop-image-workbook
description: End-to-end Temu/Xuanxshop ecommerce Excel workbook image workflow. Use when processing product spreadsheets with Chinese titles, D product groups, G variant attributes, J preview images, T carousel images, U material image, SKU image matching, first-image generation/editing, size-image preservation, OSS URL writeback, review pages, deletion/reject feedback, or validation reports. Designed for portable use across computers by asking for workbook path, SKU/material roots, background assets, upload credentials, and available image models at runtime.
---

# Temu/Xuanxshop Image Workbook

## Goal

Process Temu/Xuanxshop-style product workbooks without hard-coded machine paths. Ask for the workbook, asset roots, upload target, and model availability when needed. Keep every operation auditable before writing back to Excel.

Use this skill for workbooks with columns like:

- `产品标题`
- `产品货号` (`D` value, exact product group)
- `变种属性值一` (`G` variant)
- `预览图` (`J`)
- `SKU货号` (`L`)
- `轮播图` (`T`)
- `产品素材图` (`U`)

Read the relevant reference before acting:

- For workbook schema and validation: `references/workbook-contract.md`
- For SKU/J matching: `references/variant-matching.md`
- For J five-preview composition and background style: `references/j-preview-composition.md`
- For T first image, size image, U writeback: `references/t-carousel.md`
- For AI/lifestyle image generation: `references/image-generation.md`
- For review pages, feedback locks, deletion lists: `references/review-feedback.md`

## Runtime Inputs

Do not assume fixed paths. If missing, ask for:

- Source workbook path (`.xlsx`)
- Output folder for generated reports/pages
- SKU/material root, usually containing `{L0xx}/sku`
- Optional clean transparent PNG library for T first-image generation
- Optional background/material scene library
- Upload credentials and target prefix, if writing OSS/CDN URLs
- Available image generation model/API, if AI generation is requested
- Marketplace image constraints: size, file type, max bytes, URL count limits

Prefer local review outputs first. Upload/write back only after user approval.

## Workflow

1. **Copy and inspect workbook**
   - Work on a copied workbook in the current project/workspace.
   - Detect header columns by name, not column letters.
   - Treat blank `产品货号` rows as separators and do not process them.
   - Count effective rows and unique exact `D` values.

2. **Build group model**
   - Exact `D` is the product group.
   - Same `D` rows share title, T first image, T carousel, and U first material.
   - J is row-level: each row may have its own variant preview based on `G` and `SKU货号`.

3. **Preflight assets**
   - Match SKU/material candidates before generating or uploading.
   - Report missing folders, missing clean first-level images, variant ambiguity, and forbidden paths.
   - Never silently recurse into generated folders such as `九宫格`, `9grid`, `out`, `output`, or background/output directories.

4. **Create review artifacts before writeback**
   - For image-heavy work, build an HTML review page.
   - Use lazy loading or per-D loading for large 100+ image audits.
   - Include row, D, prefix, variant, SKU, source image, generated image, prompt/scene, and status.
   - Add delete/reject/restore/export controls when the user is screening images.
   - Export feedback from the current UI state, not only previously saved browser localStorage. If the user types Chinese feedback after clicking `redo`/`reject`, the export must read live input values so reasons are not lost.

5. **Generate/edit T first images**
   - One T first image per unique exact `D`, unless the user explicitly asks row-level T images.
   - Current T first-image rule: for a new workbook/batch, generate all unique exact `D` first images with image2/APIMart GPT-Image-2 first, then review. Only images that fail review should go to Seedream/Jimeng fallback or targeted redo.
   - Do not treat old Seedream approved records, old Ali single-SKU outputs, ComfyUI background+paste outputs, or `all_sku_tfirst` outputs as satisfying the new T first-image stage.
   - Reuse approved outputs only if no later user feedback rejects or marks them similar/wrong.
   - For AI product-fusion T first images, use the approved product-material PNG registry first, such as selected new-original/象寄 cutout PNG records. Do not repeatedly use the same SKU preview PNG for every `D` under one `L0xx`.
   - Rotate different approved source PNGs across same-`L0xx` D groups and record `source_kind`, `source_id`, and source path in the review artifact.
   - Before image generation, build a source-material allocation plan for every `L0xx`: exact `D`, `source_png/source_kind/source_id`, scene lane, color lane, product scale, placement, and composition difference.
   - Every `L0xx` must satisfy both PNG material differentiation and scene differentiation. Do not pass a batch that only varies scenes while reusing one near-identical PNG, or only varies PNGs while keeping templated scenes.
   - If the user says a same-`L0xx` group uses overly uniform PNG material, the next redo must switch or expand the source material pool instead of reusing one near-identical product cutout across many exact `D` values. Current known risk groups include L042 and L043.
   - Current L043 rule: folding-board T redos must rotate distinct source PNGs and preserve board holes, small center hole, rear raised detail, outline, and realistic scale against clothing. Do not continue using one unified-looking PNG across the whole L043 group; if the material pool is insufficient, pause to add/select better source PNGs or use fixed-PNG compositing.
   - Record each generated T first image with `provider`, `model`, `source_png`, `prompt`, `status`, and `fallback_of` when Seedream is used after image2 failure.
   - Treat SKU variant PNGs as T fallback only when no approved product-material cutout exists, or when the user explicitly asks to use SKU images for T.
   - Preserve product body. For high-risk structures, prefer fixed PNG compositing or conservative background generation.
   - For same `L0xx`, differentiate by scene, scale, position, orientation, background, and props.

6. **Generate J preview images**
   - Rebuild J by row-level variant matching.
   - J preview images are SKU/variant driven and may use SKU PNGs; this does not imply T first images should use the same SKU preview source.
   - Use the established five-preview textured composition, not a plain white background, unless the user explicitly asks for white.
   - Print or review every row-level match: `D`, row, `G`, `SKU货号`, matched tokens, selected SKU source, and warning if fallback was used.
   - If many rows have no positive token match, stop before writeback and ask for better SKU folders or mapping.

7. **Write back only after approval**
   - Insert approved T first image as first URL in T for all rows with same `D`.
   - Preserve or reorder existing T according to user instruction.
   - Keep fourth image as the size image when the workbook expects that.
   - Set U equal to T first image.
   - Write J row by row from approved variant previews.

8. **Validate**
   - Run the checklist in `references/workbook-contract.md`.
   - Produce a machine-readable JSON report and a human-readable summary.

## Non-Negotiable Rules

- User feedback beats historical approved state. If the user says a D/image/PNG is wrong, similar, hallucinated, or “不要”, lock it out before rerunning.
- New workbook T images must not bypass image2/APIMart first pass. Seedream/Jimeng is only the fallback for reviewed image2 failures unless the user explicitly overrides the model order.
- Reviewed image2 `redo` items are failures for final writeback. They must enter feedback lock first, then go to Seedream/Jimeng fallback or a specific redo plan; do not write those image2 outputs back to T/U.
- Future image generation, reconstruction, Seedream fallback, or image2 redo must pass Claude Code + NVIDIA review before execution. The review package must include GitHub memory evidence, redo/fallback D list with Chinese feedback, source PNG allocation, scene/color/composition plan, and high-risk product locks.
- Do not let a previous round’s approved registry skip a D that appears in the current redo list.
- Never write into the only source workbook. Always copy first.
- Never expose access keys or credentials in chat or reports.
- Do not upload or write back unreviewed AI images.
- If the page is too heavy to browse, rebuild it with lazy loading, pagination, or per-D loading.

## Deliverables

For a complete run, create:

- Preflight JSON/HTML: workbook structure, group counts, asset matches
- Review HTML: T and/or J images with source details
- Feedback lock JSON: rejected outputs, bad PNGs, redo D list, too-similar list, wrong-match list
- Generated records JSON: prompts, source material, local output, model response, status
- Final workbook copy
- Validation JSON/summary
