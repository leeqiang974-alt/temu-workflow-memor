# 2026-07-08 192 Redo13 Feedback Source Quality Audit

## Feedback Reviewed

Review page:
`http://127.0.0.1:8794/0616_2_image2_192_redo13_grounded_promptfix_review.html`

User feedback JSON timestamp:
`2026-07-08T00:10:53.200Z`

Redo items:

- `L043060502__set1__redo_grounded3`: reference image was not preserved; output became unrelated to the reference.
- `L043060503__set1__redo_grounded3`: reference image was not preserved; output became unrelated to the reference.
- `L091060502__set1__redo_grounded3`: top structure hallucinated again.

Keep items:

- `L043060508__set1__redo_grounded3`
- `L082060504__set1__redo_grounded3`
- `L082060506__set1__redo_grounded3`
- `L085060505__set1__redo_grounded3`
- `L096060501__set1__redo_grounded3`
- `L096060502__set1__redo_grounded3`
- `L096060504__set1__redo_grounded3`
- `L096060505__set1__redo_grounded3`
- `L096060506__set1__redo_grounded3`

## Root Cause

The failed L043/L091 redos were not primarily caused by missing prompt constraints.
The source/reference images were not clean product PNG references:

- `L043_NEW_0003`: already a lifestyle/closet scene with folded clothing on stacked boards.
- `L043_NEW_0005`: contains `6pcs` text, folded clothing, heavy background, and non-cutout edges.
- `L091_T_0015`: low-resolution black-padded scene image with candles/aromatherapy props and only partial top-structure visibility.

When these are passed to image2 as product references, the model treats the input as a concept/scene and redraws a plausible product rather than preserving the actual source structure.

## Rule Updates

- L043 and L091 now have a source-quality gate: do not use scene screenshots, text-labeled images, clothing-covered product photos, black-padded images, or contents-heavy references as direct image2 product references.
- For high-structure products such as L043 and L091, use clean product-only cutouts or generate the background separately and composite the fixed product PNG.
- Lock out this round's bad source ids before any rerun:
  - `L043_NEW_0003`
  - `L043_NEW_0005`
  - `L091_T_0015`
- L096 passed, but prompts should explicitly distinguish fixed grill hardware from replaceable loose contents:
  - fixed: grill body, legs, grate/frame, hinges, panels, supports, silhouette
  - replaceable: safe unlit skewers, vegetables, grill tools, folded foil, picnic-prep props
  - still forbidden: tabletop support, visible flame, smoke, lit charcoal, alcohol, branded packaging

## Next Redo Strategy

Do not rerun the failed L043/L091 items using the same image2 source-prompt pattern.

Before generating:

1. Find or create clean product-only cutouts for L043 and L091.
2. If clean cutouts are not available, use fixed-PNG compositing or scene-only generation plus deterministic overlay.
3. Run Claude/NVIDIA preflight on the source-quality gate before image generation.
4. Keep image2 at `gpt-image-2` + `1k` unless the user explicitly approves higher cost.
