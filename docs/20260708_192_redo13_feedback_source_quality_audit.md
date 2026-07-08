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

When these are passed to image2 as if they were clean full-product reconstruction references, the model treats the input as a concept/scene and redraws a plausible product rather than preserving the actual visible source relationship.

This does not mean every clothing-covered/contextual L043 source is unusable. The mistake is asking the model to infer a complete board from a partial or covered source. Such sources can still be used in a contextual-fusion mode where the whole visible PNG subject, such as board plus folded clothing, is fused into a larger lifestyle scene without inventing hidden product details.

## Rule Updates

- L043 now has a source-use gate, not a blanket source ban:
  - full product reconstruction or complete-structure inspection requires a clean product-only cutout, fixed-PNG compositing, or a scene-only generation plus overlay;
  - clothing-covered/contextual sources such as `L043_NEW_0003` and `L043_NEW_0005` can be used as whole PNG+clothing fusion references, but prompts must preserve only the visible combined subject and must not invent hidden board parts.
- L091 still has a source-quality gate: do not use black-padded, low-resolution, contents-heavy, or partial-top-view references as direct top-structure references.
- Lock out only true hard-bad source ids for this redo path:
  - `L091_T_0015`
- L096 passed, but prompts should explicitly distinguish fixed grill hardware from replaceable loose contents:
  - fixed: grill body, legs, grate/frame, hinges, panels, supports, silhouette
  - replaceable: safe unlit skewers, vegetables, grill tools, folded foil, picnic-prep props
  - still forbidden: tabletop support, visible flame, smoke, lit charcoal, alcohol, branded packaging

## Next Redo Strategy

Do not rerun the failed L043/L091 items using the same image2 source-prompt pattern.

Before generating:

1. For L043 complete-structure images, find or create clean product-only cutouts.
2. For L043 contextual images, use the whole visible PNG subject, such as product plus folded clothing, as the fusion reference and do not infer hidden board structure.
3. For L091, use a clean product-only top-structure reference or fixed-PNG compositing.
4. Run Claude/NVIDIA preflight on the source-use gate before image generation.
5. Keep image2 at `gpt-image-2` + `1k` unless the user explicitly approves higher cost.
