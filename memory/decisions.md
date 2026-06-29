# Decisions

## GitHub Memory

Use GitHub as the cloud memory for the workflow.

Commit lightweight, auditable state:

- Markdown summaries
- JSON manifests
- feedback lock files
- skill files
- reusable scripts

Avoid committing bulky images directly unless intentionally using Git LFS or release attachments.

## J Preview Rule

J preview images must use strict row-level variant matching:

- Match each workbook row by `产品货号`, `变种属性值一`, and `SKU货号`.
- Show source path and warning status in review pages.
- Use the five-preview textured composition.
- Do not interpret "simple background" as white background.

## T First Image Rule

T first image is normally one image per exact `D` product group.

- Same `D` rows share T first image and U.
- Preserve product structure.
- Reject bad PNGs permanently once user says "不要".
- For same `L0xx`, force visual differentiation when user marks images too similar.

## Luxury Styling Rule

Use unbranded premium cues only:

- marble, travertine, stone
- warm wood
- linen
- plain ceramic
- brushed metal
- boutique hotel or upscale home styling

Avoid brand logos, monograms, recognizable luxury packaging, counterfeit-like props, readable brand text, and risky objects.


## Seedream Realistic Usage Context Rule

When generating T first images with Seedream/Jimeng, scene realism is a hard requirement before visual styling.

Prompt order should be:

1. Product identity and fixed structure.
2. Realistic usage context: function, support surface, installation method, weight, gravity, buyer use case.
3. Product-category placement constraints and impossible-scene exclusions.
4. Premium unbranded styling and differentiation.

Do not accept beautiful scenes if the product would not realistically be used or supported there.
## 2026-06-29 — Image2 T-First Scene Generation Rules

- Do not treat beautiful expanded scenes as automatically usable; product consistency is a separate gate.
- Use color palette lanes to avoid first-screen sameness across T-first images.
- Put approved generated scene records into a manifest-only library and lock rejected samples globally.
- For products that repeatedly hallucinate under image fusion, switch to deterministic product PNG compositing.
