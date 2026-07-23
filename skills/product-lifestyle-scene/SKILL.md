---
name: product-lifestyle-scene
description: Use when generating AI ecommerce lifestyle images from product SKU/reference images, especially when the product must stay visually consistent while scenes, people, scale, orientation, and contained items vary for bulk listing differentiation. Covers Seedream/Jimeng-style prompt strategy, clean PNG/cutout workflow, competitor-style expanded scenes, product compositing, and tableware/object replacement inside racks or storage products.
metadata:
  short-description: Ecommerce product lifestyle scene generation
---

# Product Lifestyle Scene Generation

## Core Principle

Treat the job as **scene generation plus product compositing**, not full product redraw.

## Proven Reference-Edit Operating Model (2026-07-15)

Historical Batch375 review and the Codex + Claude/NVIDIA audit converge on one operating model:

> **Freeze the product boundary; preserve the reference image's selling logic; change only safe non-product variables.**

This is the default for a usable competitor/reference image. It is not a title-to-scene reconstruction task.

### What success actually preserved

The strongest accepted images kept most of the following from the reference, while changing enough details to avoid copying:

- a recognizable product silhouette, color and visible hardware
- the original human presence when it explained scale, use or lifestyle value
- the task relationship between person, product and nearby objects
- room/garden depth, camera distance and believable support/contact
- premium value cues such as stone, wood, linen, glass, metal, spaciousness and refined light

They changed the surrounding variables: person identity/clothing/pose, background material, palette, lighting direction, loose contents, nearby props, crop, product scale within the scene, and sometimes horizontal orientation.

### The three-layer prompt contract

Every reference edit should be assembled in this order:

1. **Product truth layer**: exact visible silhouette, color, count, holes, rails, drawers, panels, supports, connectors, materials and contact relationship. Lock only what is visibly evidenced.
2. **Reference value layer**: explicitly preserve the reference's composition value, people, task logic, spatial depth, camera distance, premium cues and real use context. These are protected assets, not cleanup targets.
3. **Controlled variation layer**: choose 3-5 safe changes from background material, palette, person, pose, loose contents, lighting, crop, camera distance, orientation and harmless props. Do not prescribe a new room or action unless the reference itself is unusable.

Use this compact handoff wording when another agent runs the task:

```text
source_mode: reference_edit
Primary objective: keep the exact visible product and transform the reference image, not rebuild from the title.
Preserve: product boundary and hardware, useful composition, person when it explains scale/use, task logic, room depth, support/contact, camera distance, and premium cues.
Change only: non-product background, palette, lighting, person identity/pose/clothing, loose contents, safe props, crop, scale, or orientation.
Title: product-family/specification hint only; never use it to decide the room, action, camera, scale, or atmosphere.
```

### Person/Task Hard Gate (2026-07-17)

When the reference has a person who demonstrates use, scale, installation,
cleaning, storage, gardening, or another product-related task, classify the run
as `person_task_required`. This is stricter than a general preference for people:
the generated image must contain one visible, realistic person carrying the same
or equivalent task relationship. A clean empty lifestyle room, a tiny unrelated
background figure, or a person covering the product fails the run. Add a specific
`PERSON/TASK LOCK` to every such redo prompt and reject the candidate if it loses
that evidence.

### Priority and failure rule

Use this priority order: **product truth -> physical realism -> reference value -> differentiation -> ecommerce polish**. A result fails if any higher-priority item is broken. In particular, a correct product in an empty generic room is not a success when the source had a useful person, task, premium interior, or spatial story. A beautiful scene is not a success when the product gains parts, loses color/count, or is placed impossibly.

### Prompt preflight before bulk generation

Reject the prompt before spending credits if it contains any of these patterns in `reference_edit` mode:

- `Scene lane:` or an equivalent fixed room/action template
- title-derived room, action, camera, product percentage or support surface
- repeated same-L0xx composition, person posture, palette or product scale
- global instructions that people may only be background atmosphere, or that force a clean empty scene
- a product-family lock that names the whole scene instead of visible hardware
- more than one competing scene direction in the same prompt

Replace them with `scene_edit_intent`: preserve the current reference's scene logic and select a small set of editable non-product variables. Use a detailed scene bank only in `expanded_scene_from_product`, where there is no usable lifestyle reference.

### Product uncertainty rule

If the product is weak, occluded or structurally ambiguous, do not compensate with a longer title or a stronger scene prompt. Select a clearer same-family product reference and keep the scene close to the usable reference. If the alternate reference could be a different product, stop and mark the item for manual review; a wrong product anchor is worse than a discarded output.

For bulk ecommerce images, keep the product hardware/body stable and vary:

- scene type and room scale
- product size in frame
- product position
- horizontal mirror orientation
- people and tasks
- lighting style
- replaceable contents, such as bowls, dishes, cups, files, food, toys, or tools

If exact product fidelity matters, generate the scene separately and composite a clean transparent product PNG afterward.

## Recommended Workflow

1. **Clean the SKU image**
   - Remove measurement labels, red lines, text, logos, prices, watermarks, and UI marks.
   - Keep only the product body and essential accessories.
   - For products with replaceable contents, decide what is fixed hardware and what can change.

2. **Create a clean product PNG**
   - Use transparent background when possible.
   - Preserve product silhouette, angle, color, frame, holes, drawers, racks, wheels, handles, and structural parts.
   - If the source contains text on plates, labels, or packaging, remove it before using as reference.

3. **Use AI for scene generation**
   - Ask the model to use the input only as product hardware/reference.
   - Keep product structure recognizable.
   - Let the scene, people, lighting, scale, mirror direction, and replaceable contents vary.

4. **Prefer post-production for strict consistency**
   - Generate a no-product or low-product scene.
   - Composite the original product PNG with scale, mirror, shadow, and color matching.
   - Add top-right circular product inset afterward for consistency.

## Competitor-Style Expanded Scene Workflow

Use this when the user asks for “像截图那种场景图”, “扩图”, “扩场景”, “高价值场景”, or wants Temu competitor-style lifestyle images.

Core idea: use **product PNG + competitor screenshot/style reference**. The product PNG defines the product; the screenshot only teaches room scale, camera distance, lighting, spatial depth, and ecommerce composition.

Current DXXmall/0616-2 luxury scene bank:

- Use `scripts/luxury_expanded_scene_banks_0616_2.py` for bulk T-first generation and fallback redos.
- It covers the active 29 prefixes from the 195x3 candidate plan and gives each `L0xx` exactly 20 detailed expanded-scene prompts.
- Prompts must use unbranded luxury cues such as stone/travertine, walnut/oak, linen, plain ceramic, brushed metal, boutique-hotel or premium-home styling.
- Do not use named luxury brands, logos, monogram patterns, designer handbag/watch/jewelry silhouettes, readable brand text, screens, fire, candles, alcohol, toys, medicines, weapons, or other risky props.
- If a generation script has a shorter inline `SCENE_BANK`, it must be overridden by the central luxury bank before running.

Input order matters:

1. First image: clean product PNG or best product reference.
2. Second image: competitor-style screenshot for composition/scene mood only.
3. Optional extra images: safe alternate product angles or variants.

Prompt structure:

```text
The first input image is the exact product PNG for [product].
The second input image is only a competitor-style scene/composition reference; learn room scale, camera distance, lighting mood, premium space design and ecommerce composition, but do not copy its person, product, brand, logo, text, layout or exact objects.
Freeze product hardware exactly: [fixed parts].
Only loose removable contents may change: [safe contents].
Create a wide expanded lifestyle scene: [scene].
Realistic use context: [where product is actually used].
The product must sit/stand/hang/attach on a believable support surface with correct gravity and natural contact shadow.
Product occupies about 18-32% of image height; the premium room and lifestyle context occupy most of the image.
People may appear only as softly blurred background lifestyle atmosphere, modest and not touching, holding, leaning on, blocking or merging with the product.
No readable text, logos, watermark, alcohol, fire, candles, electronic screens, toys, medicines, weapons, adult or political content.
Square 1:1. Polished Temu competitor lifestyle image with a larger believable scene.
```

Good expanded-scene directions:

- kitchen organizers/racks: bright luxury kitchen, marble island, glass-front cabinets, pantry sideboard, coffee station, safe patio kitchenette.
- storage drawers/shelves: warm living room sideboard, entryway cabinet, closet shelf, modern kitchen appliance station, industrial loft storage corner.
- fruit/dessert stands: cafe dessert table, luxury dining room, breakfast counter, marble tabletop, coastal kitchen counter.

Do not let “premium” override product realism. A beautiful room is wrong if the product is placed where a buyer would never use it.

Quality gate for this workflow:

- product is smaller but still recognizable
- room scale feels real, not flat wallpaper
- product contacts the correct surface
- no copied competitor product/person/logo/text
- hardware is not changed
- color palette is intentionally differentiated from sibling images, not all warm yellow or beige
- scene differs meaningfully from sibling images
- if the model drifts, keep the scene idea but redo with stricter fixed-product language or use deterministic compositing

Round2 feedback learning:

- Treat scene quality and product consistency as two separate approvals. A beautiful, premium, differentiated scene is not usable unless the product structure also passes.
- For competitor/reference-image transformation, the default mode is **reference-first scene editing**, not title-first scene reconstruction. Preserve the reference image's useful composition, task logic, room depth, people when safe, and premium/luxury visual cues while changing enough non-product elements to avoid similarity.
- Do not let product-family locks become fixed scene templates. Product locks should name only the product's fixed hardware/body and forbidden hallucinations. They should not force one exact room, action, scale, or camera lane unless the user's feedback explicitly requires it.
- Workbook titles are weak hints, not scene commands. Use titles mainly to identify product family and fixed attributes. If the reference image already has a believable high-value scene, modify that scene directly instead of rebuilding from the title's use case.
- Avoid repeated `Scene lane:` wording for every item in the same `L0xx`; it creates same-looking outputs. Use a softer field such as `scene_edit_intent` that says which parts of the reference may change: background palette, person identity/pose, task object, countertop/cabinet material, lighting, props, product placement, and camera distance.
- For high-risk product drift, tighten only the product boundary, not the entire image. If a product is structurally fragile, freeze hardware/body and keep the reference composition closer; do not over-clean people, task, premium decor, or spatial depth.
- 2026-07-13 Codex + Claude/NVIDIA audit agreed that the Batch375 redo prompt drifted into title-driven scene reconstruction. For reference-image edits, `Scene lane:` style fixed room/action templates are forbidden by default. Use `scene_edit_intent` instead: preserve the reference's composition, human/task logic, spatial depth, premium cues, and believable use context; change non-product elements for differentiation. The title may confirm product family/spec only and must not define room type, action, scale, camera, or atmosphere unless the user explicitly says the reference scene is wrong.
- Product lock means visible physical boundary only: silhouette, color, visible rods/rails/holes/drawers/feet/connectors/materials, and support/contact relationship. Never let a product lock silently lock the room, person, exact action, camera angle, lighting, or prop category for every image in the same `L0xx`.
- Before any new redo batch after user feedback about sameness, run a prompt preflight that rejects hard scene lanes, repeated room templates, fixed product-size percentages across a family, and title-first reconstruction. Record `source_mode` as `reference_edit`, `product_anchor`, or `title_reconstruction`; default must be `reference_edit`.
- 2026-07-23 composition-differentiation correction: changing only scene, palette, person, or lighting is still a near-copy when framing and product placement remain unchanged. Before a paid bulk `reference_edit` run, assign each exact D an auditable composition envelope that varies camera distance/zoom, product scale in frame, left/center/right placement, negative space, scene depth, and—only for visually safe symmetric families—whole-product horizontal mirroring. Never mirror a family with directional, asymmetric, count, support, ground-insertion, front-view, or fragile-geometry locks. Keep the original approved manuscript as the only reference anchor; generated candidates remain forbidden anchors.
- 2026-07-23 replaceable-content correction: loose non-product contents are an intentional differentiation axis, but hardware is immutable. L077 may replace pet breed/coat/pose while retaining one believable pet use and a visible product boundary. L095 may replace flower/plant species, colors, and arrangement while preserving planter/basket structure and count. L088/L089 and comparable racks may replace stored/displayed objects while preserving every tier, basket, rod, foot, support, color, and outline. When a scene includes lower cabinetry, only the surrounding cabinet/counter finish, panel style, handles, and color may change; never treat the sale product as replaceable furniture.
- Scene differentiation must be based on product-specific reasoning, not template expansion. Before building or approving a 20-scene bank for any `L0xx`, define the product's realistic use envelope: actual function, support/contact surface, indoor/outdoor boundary, installation/placement method, likely buyer scenarios, safe props, and forbidden contexts. Then decide how broad the scene bank can be.
- Broad multi-scene thinking is encouraged only when the product naturally supports multiple real use contexts. For example, an outdoor portable grill can rotate camping, backyard, lawn picnic, RV campsite, terrace/deck floor, and courtyard gathering scenes. A cabinet-interior rack, under-sink organizer, or strict structural product should stay inside its real functional envelope and vary cabinet style, palette, depth, scale, props, and composition instead of being moved to unrelated rooms or surfaces.
- Do not mechanically force every product into many scene categories. Some products need wide scenario variety; some need narrow context plus strong palette/composition/source-PNG variety. The decision must be made per product before generation and recorded in the source PNG/scene allocation plan.
- When the style reference contains objects structurally similar to the product, such as shelves, racks, baskets, drawers, or stands, the model may merge the style object with the product and silently redesign the product. Use these references only with stricter fixed-hardware language, larger product scale, a high-contrast product source, or switch to deterministic compositing.
- For high-structure products, prefer a clean high-contrast source PNG. Low-contrast white cutouts are more likely to lose thin rods, supports, basket edges, rails, and small vertical parts.
- Do not let “replaceable contents” become “replaceable hardware”. Contents can change only when they are loose objects placed on or inside the product; rods, frames, baskets, shelves, drawers, rails, handles, wheels, legs, and supports remain fixed.
- If a product has a historically repeated failure, add a product-specific lock before generating again instead of relying on generic “do not change product” wording.
- Control color tone as a first-class differentiation variable. Do not let every premium scene become warm yellow, beige, or sunset-toned. Rotate between cool white daylight, blue-gray marble, fresh green outdoor, dark luxury, warm wood, soft cream pastel, clean black-white contrast, and neutral overcast daylight.
- Treat source PNG allocation as a first-class differentiation variable for every L0xx, not just L043. Before running a new batch, prepare a per-D source PNG allocation table and a scene/color/composition plan. Every same-prefix group must vary both source PNG material and scene design. Current known source-uniformity risk groups include L042 and L043; this batch is not retroactively reworked, but all future execution must pass this gate.
- Mode split: do not confuse `reference_edit` with `expanded_scene_from_product`. In `reference_edit`, the input competitor/reference image is the composition source, so hard `Scene lane:` wording is forbidden and the prompt must use `scene_edit_intent` instead. In `expanded_scene_from_product`, where there is no usable lifestyle reference and the model must build a new scene from a product PNG, a scene bank is allowed.
- For `reference_edit`, differentiation should be written as editable variables from the current reference: background material, palette, person identity/pose/clothing, task object, loose contents, lighting, camera distance, and safe props. Do not prescribe one room template, one support surface, or one product percentage unless fixing a specific reviewed failure.
- For `expanded_scene_from_product`, if the user says "扩图", "扩场景", or asks for stronger differentiation without a usable reference scene, the prompt must contain a concrete scene-bank entry. Do not use placeholders or vague wording such as "different scene mood". For each L0xx in a bulk batch, create or load at least 20 category-correct expanded lifestyle scene prompts and rotate/randomize them across exact D and set variants.
- Treat an `expanded_scene_from_product` scene bank with fewer than 20 concrete prompts as incomplete. Preflight should block that mode until the bank is expanded, because 10 prompts is too easy to repeat in 3-set / multi-D candidate pools.
- `expanded_scene_from_product` scene-bank entries must specify camera distance, room/garden scale, support surface, product placement, approximate product size in frame, palette, and safe props. This rule does not apply to `reference_edit`, where the reference image should decide the initial composition and the prompt only edits non-product variables.
- Do not execute image generation, Seedream fallback, image2 redo, or bulk reconstruction until a Claude Code + NVIDIA review has checked the source PNG allocation plan, scene differentiation plan, product locks, and latest GitHub memory rules.

## 2026-07-13 Batch375 Reference-Edit Skill Baseline

Use this as the default skill shape when the user provides competitor/reference main images and wants new Temu-style first images by changing scene, people, palette, task, and premium cues while preserving the product.

### What worked

- Treat the reference image as the primary composition source. The model should edit from the reference image, not rebuild a new title-driven scene.
- Match products by workbook row plus four-digit fingerprint. Do not infer identity from chat text or visual similarity alone.
- Preserve the visible product and its contact/support relationship. Product locks should describe only visible physical boundaries: outline, color, rods, holes, drawers, rails, handles, feet, connectors, panels, quantity cues, and loose contents that are allowed to change.
- Preserve useful reference value: camera distance, spatial depth, human/task logic, premium room quality, product placement logic, and realistic use context.
- Differentiation should edit non-product variables: background material, palette, person identity/pose/clothing, task object, loose contents, lighting, safe props, camera crop/expansion, and nearby environment.
- Luxury/premium cues are valuable and should be retained or improved when safe: stone, travertine, marble, walnut/oak, linen, plain ceramic, brushed metal, boutique-hotel or premium-home composition. Keep them unbranded and Temu-safe.
- For very weak product references or structurally fragile products, use a stronger same-product/same-series reference or a fixed product cutout/inset rather than asking the model to hallucinate hidden structure.
- For final workbook handoff, write a deterministic manifest: `row`, `fingerprint`, accepted local image path, discard list, and current T first URL. Another thread should use that manifest for upload/writeback rather than parsing conversation history.

### What failed and must be avoided

- Do not over-clean the reference prompt. Removing the original people, premium scene, and task logic destroys the value of reference-image editing.
- Do not use hard `Scene lane:` templates in `reference_edit` mode. They caused same-`L0xx` products to collapse into repeated room/action patterns and drift away from the reference image.
- Do not let title attributes dictate the room, action, scale, camera, or atmosphere unless the reference scene is clearly wrong. Titles are only weak product-family/spec hints in reference-edit mode.
- Do not freeze scene/layout while trying to freeze product. Product locks are not room locks.
- Do not repeatedly use one visual source, one product pose, one background style, or one warm beige/yellow premium palette for the same `L0xx`.
- Do not write temporary APIMart image URLs or local file paths back to workbook T. Upload accepted local images to durable OSS/CDN first.
- Do not write rejected or discarded fingerprints back to T/U. Batch375 discard examples: `1114`, `2125`, `4329`, `5217`.

### Prompt contract for `reference_edit`

Use fields like:

```text
source_mode: reference_edit
product_identity: [product family/spec confirmed by title or user]
fixed_product_boundary: [visible hardware/body only]
scene_edit_intent: preserve the reference composition, product placement logic, spatial depth, human/task relationship, and premium cues; change non-product elements for differentiation: [palette/person/task/background/props/camera crop]
allowed_changes: [people, loose contents, background, palette, lighting, safe props, camera expansion]
forbidden_changes: [hardware/body/quantity/color/shape/support-contact drift, copied text/logo/brand/watermark, unsafe Temu props]
```

Reject prompts that contain a fixed room/action template unrelated to the reference image, repeated scene banks in reference-edit mode, or product locks that also lock the scene.

### Preflight gate before any future batch

- Classify each item as `reference_edit`, `product_anchor`, or `expanded_scene_from_product`. Default to `reference_edit` when a usable competitor/main image exists.
- For same-`L0xx` items, verify that prompts vary at least three non-product variables and do not share one fixed scene/action template.
- For high-risk products, verify whether the selected reference is strong enough to preserve product structure. If not, switch source, use same-series product support, or choose fixed-product compositing.
- Review accepted/rejected state before writeback. Empty feedback means pass only in the latest review artifact; any explicit user note means redo or discard according to that note.

## Ozon / Russian Marketplace Image Style Baseline

Use this when the target marketplace is Ozon or a Russian-market storefront, especially for household, storage, kitchen, garden, pet, apparel, and small appliance products.

Ozon-style image work is not the same as Temu-style first-image reconstruction. The practical Russian marketplace style is **clear product plus strong Russian infographic plus believable domestic context**. It should feel useful, readable, and trustworthy before it feels luxurious.

### Main image direction

- Product must be immediately identifiable at small mobile thumbnail size.
- Use clean light, neutral, gray, or controlled color backgrounds unless a category clearly benefits from a lifestyle hero.
- Keep the product dominant and uncluttered. If scene elements appear, they must support scale and use, not hide the product.
- Avoid fake luxury, overdecorated rooms, brand-like logos, copied marketplace badges, dense Chinese-style parameter blocks, and AI-looking fantasy scenes.
- If Russian text is needed, generate a clean visual first and add Cyrillic copy in post-production. Do not rely on image-generation models to render readable Russian text.

### Gallery / detail image direction

Build the carousel as a decision funnel:

- image 1: clear product hero
- image 2: product in use or in a believable Russian home/apartment/dacha context
- image 3: size, capacity, dimensions, or fit
- image 4: material, structure, close-up details, or durability proof
- image 5: what is included / set contents / variants
- image 6: use steps or before-after problem solving
- image 7: comparison or objection handling
- image 8+: lifestyle, packaging, installation, care, or buyer scenario if relevant

### Russian visual taste cues

- Prefer practical domestic realism: apartment kitchen, hallway, balcony, closet, bathroom cabinet, garage, dacha, garden, storage room, pet corner, family table, or small-shop counter.
- Use restrained premium cues: clean wood, stone, tile, linen, matte metal, tidy shelves, daylight, real shadows, and organized space.
- Luxury should mean order, quality, good materials, and comfort, not exaggerated wealth.
- Palette should stay readable and high-contrast: white/gray/wood/black with one accent color; avoid all-beige, muddy yellow, or overly saturated Temu-style collages.
- Russian infographic layout should use large short headings, simple icons, arrows, callouts, and 2-4 key claims per image. Mobile readability is more important than decorative density.

### Ozon prompt rule

For Ozon, prompt generation should separate **image generation** from **infographic layout**:

```text
Generate the clean product/lifestyle visual without text first.
Keep the product accurate, readable, and dominant.
Use a believable Russian-market domestic context.
Leave clean negative space where Russian infographic labels can be added later.
No unreadable AI text, no marketplace logos, no fake badges, no copied brand marks.
```

Then add Russian captions, dimensions, icons, and callouts in a deterministic design layer.

Smart Photo Ozon correction, 2026-07-15:

- In the current Smart Photo pipeline, all Ozon main-gallery AI image slots must be treated as **no-text base images**. This includes size/capacity, structure/detail, set contents, and problem-solution images.
- Do not pass Chinese product titles, Chinese slot labels, or Chinese selling-point phrases into the image model as visible subject/copy. If the product name is only Chinese, refer to it as `the reference product` in prompt-facing text and rely on reference images plus analysis for fidelity.
- Ozon-specific prompts should not inherit Temu-style poster/card/collage layouts. Use Ozon no-text base-image directions first, then add deterministic Russian infographic copy later.

### Ozon visual design system

Use this when planning Smart Photo output for Ozon or Russian-market product images.

Do not treat Ozon as a one-step image-generation problem. The stable workflow is:

1. Generate or edit a clean product / lifestyle base image.
2. Preserve enough negative space for later labels.
3. Add Russian infographic copy, icons, measurements, arrows, badges, and callout lines in a deterministic design layer.

#### Typography

- Use readable Cyrillic sans-serif fonts for most product cards: Inter, Roboto, Manrope, Open Sans, or a similar neutral grotesk.
- Use at most two typefaces in one carousel: one primary sans-serif and one optional accent style.
- Avoid decorative, handwritten, overly condensed, or thin fonts for product specifications.
- Main heading should be short and large; supporting text should be 2-5 words or compact numeric specs.
- Do not ask image-generation models to invent Russian text. If exact Russian copy is not supplied, generate no text and reserve clean label space.

#### Layout

- Keep the product readable in thumbnail size. Do not let labels, icons, people, or props cover the fixed product boundary.
- Keep important copy away from platform UI risk zones: extreme corners, upper-right favorite/icon area, and lower badge/price overlays.
- Use a consistent grid across the carousel: clear margins, predictable alignment, and 1-2 focal zones.
- Use simple icons, arrows, dividers, leader lines, and zoom callouts; avoid dense collage grids.
- Each slide should answer one buyer question: what is it, where is it used, how big is it, what is included, what is the material/structure, what problem does it solve.

#### Content rhythm

- Main image: product clarity and trust, minimal/no text.
- Scene image: believable Russian apartment, kitchen, hallway, balcony, closet, bathroom cabinet, dacha, garden, garage, pet corner, or family table.
- Size/capacity image: one clean product view plus large numeric specs.
- Structure/detail image: close-up or cutaway only if visible/verified from references.
- Set contents image: organized product/accessory layout; do not invent accessories.
- Problem-solution image: before/after or use-step logic, not exaggerated hard-sell advertising.
- Premium lifestyle image: order, material, daylight, comfort, and cleanliness; not fake luxury, mansions, or branded wealth cues.

#### Color and style

- Use neutral/light backgrounds with one controlled accent color. Keep each image to about 3-4 visual colors.
- Rotate palettes across the carousel: clean white/gray, warm wood, cool blue-gray, soft green, muted beige, black-white contrast.
- Russian-market premium should feel practical and trustworthy: tidy room, good material, natural light, real shadows, believable scale.
- Avoid Chinese-style dense parameter walls, Temu-style exaggerated luxury scenes, fake badges, unreadable tiny text, and AI fantasy lighting.

## Temu T-Column First Carousel Workflow

Use this workflow when making the first image inserted into the workbook `T` carousel column.

### Mandatory model order for workbook T images

- For a new workbook/batch, the first pass must generate **every unique exact `D` T first image with image2/APIMart GPT-Image-2** using the current product PNG/material library and product-specific prompt rules.
- For Temu bulk T-first image2/APIMart runs, the low-cost setting is exactly `gpt-image-2` with `resolution: "1k"`; expensive official/unofficial variants and `2k`/`4k` are forbidden unless the user explicitly approves the higher cost. Runners must hard-code/check the allowed model and resolution before submitting any APIMart request.
- Do **not** satisfy a new workbook/batch by directly reusing old Seedream/Jimeng approved records, old `all_sku_tfirst`, Ali single-SKU, ComfyUI background+paste, or background-library compositing outputs.
- Seedream/Jimeng is a fallback/repair model only after image2 review: use it for images that the review marks failed, hallucinated, too similar, structurally wrong, or not premium enough.
- If image2 already has an approved current-batch record for a `D`, reuse that current-batch image2 result. If not, generate it with image2 first; do not skip straight to Seedream.
- When reporting or writing back T images, record provider/model per `D` as `image2_primary` or `seedream_fallback`, so later audits can identify which model produced each first image.

1. **One image per unique D**
   - Treat exact `D` value as the generation unit.
   - Generate exactly one first-carousel image for each unique `D`.
   - If the same `D` has multiple workbook rows or variants, insert the same generated OSS URL as the first `T` image for all rows with that `D`.
   - Do not generate separate first-carousel images for each row unless the user explicitly asks.

2. **T first-image source priority**
   - For AI product-fusion T first images, do **not** default to one SKU preview image per `L0xx`.
   - Use the reviewed product-material PNG registry first, especially selected new-original/象寄 cutout PNGs such as `xiangji_final_png_material_registry.json`.
   - Rotate different approved product PNGs across different exact `D` values under the same `L0xx` so one table does not reuse the same product cutout repeatedly.
   - Exclude any material locked by feedback as bad, rejected, duplicated, hallucination-prone, background-contaminated, blurry, or “不要”.
   - Use SKU variant PNGs only as fallback when a `L0xx` has no approved new-original/product cutout material, or when the task is specifically J preview/SKU variant work.

3. **SKU selection from variants**
   - Use the clean final transparent SKU PNGs as product source images.
   - For single-SKU products, use that one SKU image.
   - For multi-SKU products, include only the distinct variant images represented by that `D` group, not repeated quantity variants.
   - Example: for `L043`, use only white and gray SKU images; do not create four separate foregrounds for `15 white`, `30 white`, `15 gray`, and `30 gray`.
   - Match variants by stable SKU keywords such as black/white/gray/green/pink/purple, walnut/original wood, and numeric variants like 2 or 3.
   - This SKU logic is mainly for J previews, U/SKU material consistency, or last-resort T fallback; it is not the primary source-selection logic for high-differentiation AI T first images.

4. **Model layering strategy**
   - For current Temu workbook T first images, use image2/APIMart GPT-Image-2 as the primary full-batch generator.
   - Use Seedream/Jimeng only as a fallback for image2 review failures or targeted redo items.
   - Use Alibaba/DashScope background generation or deterministic compositing only when the user explicitly asks for conservative fixed-PNG compositing or when high-risk structure cannot survive generative fusion.
   - Never rely on any AI output without checking product drift; review gates decide whether image2 passes or Seedream fallback is needed.

5. **Differentiation within the same L0xx**
   - For different `D` values under the same `L0xx`, vary at least three dimensions: scene, background, product scale, position, orientation/mirror, object arrangement, and foreground grouping.
   - Also vary the source product PNG itself whenever an approved material library has enough usable cutouts for that `L0xx`.
   - Source PNG variation is mandatory, not optional, whenever the material library has multiple safe product cutouts. If the library does not have enough variety, pause to select/add material or use fixed-PNG compositing rather than pretending scene-only variation is enough.
   - Choose the scene breadth after reasoning about the product's function. Use broad scenario rotation only for products with genuinely broad use cases; for narrow-use products, keep the context category fixed and create differentiation through room subtype, palette, depth, support surface detail, scale, product placement, props, and source PNG selection.
   - Keep product appearance stable while using controlled variation such as horizontal mirroring, different left/right placement, different product size in frame, and slight angle-like composition changes.
   - For racks, shelves, trays, baskets, boxes, organizers, and similar container products, use replaceable loose contents as a major differentiation axis: tableware, bowls, cups, utensils, towels, files, fruit, flowers, greenery, small household items, or other category-safe props may change when they sit on or inside the product.
   - When replacing loose contents, explicitly freeze the product hardware/body: do not change rods, holes, shelves, tiers, baskets, handles, hooks, wheels, frames, rails, supports, product color, outline, or quantity of structural parts.
   - Avoid making all first-carousel images for one `L0xx` look templated or near-identical.

6. **Temu-safe scene constraints**
   - Prefer safe home/kitchen/patio/dining scenes with natural daylight, cabinets, countertops, sinks, curtains, plants, neutral tableware, towels, and generic household props.
   - Avoid toys, child-focused objects, electronic devices, screens, visible brand logos, branded packaging, fire, flames, candles, decorative lights, bulbs, balloons, dangerous goods, chemicals, alcohol, smoking items, medicines, medical devices, weapons, and prohibited or risky items.
   - People, if used, must remain background-only and must not touch, block, or visually merge with the product.
   - Enforce realistic use-context fit. The product must appear in a scene where a real buyer would naturally use, place, support, hang, store, or display it. Do not put products in visually attractive but physically absurd contexts, such as a barbecue grill on a bed, a heavy rack floating on fabric, a garden arch indoors on a sofa, a pet mat on a kitchen counter, or kitchen storage on bedroom bedding.
   - Scene review must include a reasoned answer to: "Is this a place where a buyer would actually use this exact product?" If the answer is no, the candidate fails even when it looks premium or differentiated.
   - Match contact surface and gravity. Floor products stand on floor/grass/tile; countertop products sit on counters/tables/shelves; wall/fence products attach to walls/fences/railings; outdoor garden products stay on lawn/path/patio/flower bed; cleaning products sit on bathroom/laundry/utility floors. If a product requires support, show believable support.

7. **Workbook insertion**
   - During review, generate local images only; do not upload or insert until approved.
   - After approval, compress/export final images to the requested marketplace size, upload to OSS, then insert the new URL at the beginning of each matching `T` cell.
   - Insert, do not replace the rest of the carousel unless the user gives a reordering rule.
   - If the workbook uses `U` as first material image, set `U` equal to the new first `T` URL only when the user requests carousel writeback.

## Model Selection

- **Seedream/Jimeng-style image generation**: better for creative variation, changing contents inside a product, changing tableware/objects, mirroring, scale shifts, and angle-like variation. It may redraw or modify product details.
- **Alibaba/DashScope background generation**: better for preserving the exact foreground PNG and generating a new background around it. It is weaker for replacing objects inside the product or changing the product angle because it treats the foreground as a fixed cutout.
- **Best bulk workflow**: use Seedream/Jimeng when content variation matters; use Alibaba background generation when product fidelity matters; use deterministic compositing when exact product pixels must stay unchanged.

### Cost/Risk Positioning

- **Alibaba background generation (~0.08/image)**: low cost, high foreground stability, best for transparent PNG foreground plus background replacement. Weak for replacing contents inside products or changing angle.
- **Seedream/Jimeng (~0.22/image)**: higher cost, stronger creative variation, can replace contents, mirror products, change scale, and create stronger scene differentiation. Risk: product drift grows with batch size.
- **Do not choose only by unit price**. Compare stability risk cost: if product details drifting causes rejected listings or misleading images, a cheaper model may be better even if less creative.

### Recommended Layering

1. **High-fidelity listing images**
   - Use Alibaba background generation.
   - Keep product unchanged; vary safe background scenes.
   - Use for main SKUs, structurally complex products, and products where mismatch risk matters.

2. **Strong differentiation listing images**
   - Use Seedream/Jimeng.
   - Allow scene, contents, mirror direction, scale, and composition variation.
   - Use for bulk listing tests and non-critical variations.

3. **Hybrid workflow**
   - Use Seedream/Jimeng to explore ideal scenes, tableware/object combinations, and compositions.
   - Select only outputs where product structure has not drifted too much.
   - Re-composite the true product PNG over the selected scene when fidelity matters.

Stable batch logic:

```text
Seedream/Jimeng: explore scenes, contents, composition, mirror/scale variation
Alibaba or deterministic compositing: final product-fidelity pass
```

### Seedream/Jimeng Drift Risks

When a product PNG/reference image is sent to Seedream/Jimeng many times, expect some outputs to alter:

- rack rods, holes, shelves, drawers, or frame positions
- number of layers, cup holders, hooks, wheels, handles, or side boxes
- internal objects covering or changing product structure
- product proportion, perspective, or silhouette
- color/material details

Use a selection gate. For example, from 20 generated images, keep only 5-8 where product structure is acceptable.

For concrete API call patterns, see [references/model-interfaces.md](references/model-interfaces.md).

## Prompt Rules

Prefer **positive English prompts**. Avoid overusing negative prompts like “no text, no table, no logo” because some image models may latch onto those concepts and generate them.

For Temu-oriented ecommerce images, avoid risky scene elements by positively specifying safe home/kitchen/patio context and plain generic props. Do not include objects or wording that may trigger platform compliance risk.

Always add a realism-fit clause before generation:

```text
Place the product only in a realistic usage context that matches its actual function, weight, support surface, and buyer use case. The product must sit, stand, hang, lean, or attach exactly where this category would naturally be used. Do not place it in a random decorative scene just because it looks premium.
```

Use product-category placement examples:

- garden edging, arches, fence greenery: lawn, garden path, patio, fence, balcony railing, flower bed, courtyard; not bed, sofa, kitchen counter, or indoor closet.
- kitchen racks, trays, dish organizers, cutting boards: countertop, sink side, dining table, pantry shelf, sideboard; not bed, bathroom floor, garden soil, or sofa.
- cleaning buckets and mops: bathroom, laundry room, utility room, tiled floor, cleaning closet; not bed, dining table, sofa, or wardrobe shelf.
- pet mats: floor, rug, bedroom/living room pet corner; not kitchen counter, shelf, sink, or outdoor garden as the main placement.
- storage boxes, drawers, shoe cabinets, wardrobe organizers: closet, cabinet, entryway, bedroom floor, shelf, desk, wardrobe; not grass, beach, bed surface unless the product is actually bedding-related.
- fitness products: gym floor, exercise mat, studio, home workout corner; not kitchen counter, bed, dining table, or garden display.
- barbecue/outdoor cooking products: patio floor, terrace floor, yard grass, campsite ground, gravel pad, deck boards, courtyard pavers, or safe open outdoor ground/floor surface without visible flames; not indoor counters, ordinary tables, picnic tables as support, bed, sofa, bedroom, bathroom, or wardrobe.

Risky elements to avoid in generated scenes:

- toys or child-focused play items
- electronic products
- electronic display screens
- visible brand logos or branded packaging
- fire, open flame, candles, stoves with flame, barbecue fire
- decorative lights, string lights, lit bulbs, strong artificial lighting fixtures
- prohibited goods, dangerous goods, weapons, sharp hazardous props, chemicals
- alcohol bottles, smoking items, medicines, medical devices, adult or politically sensitive items

Prefer safe props:

- plants, curtains, cabinets, shelves, neutral tableware, towels, fruit, bread, coffee cups without logos, plain kitchen tools, sink, countertop, dining table, chairs, windows, natural daylight

Use “only as hardware reference” when contents can change:

```text
Use the input image only as the product hardware reference.
Keep the product hardware consistent: [fixed structure list].
Replace the contents with [new contents list].
Create a wide realistic lifestyle scene that fits the product's real use case: [scene].
Place the product on a believable support surface for this category: [floor/counter/wall/fence/shelf/table/patio/lawn].
The product may be horizontally mirrored and scaled smaller.
The product occupies about [20-35]% of image height, complete and clear.
People stay in the background and do not touch or block the product.
Commercial lifestyle photography, natural shadows, clean premium composition.
```

Use this replaceable-contents clause for racks, shelves, trays, baskets, boxes, and organizers:

```text
Treat the product body as fixed hardware. Keep every structural part unchanged: frame, rods, shelves, tiers, hooks, handles, holes, rails, baskets, legs, supports, wheels, color, outline and silhouette. Only replace loose removable contents placed on or inside the product with category-safe unbranded items: [plates/bowls/cups/utensils/towels/files/fruit/artificial flowers/greenery/household props]. The replacement contents must not cover, merge with, or redesign the product hardware.
```

For same-`L0xx` bulk variation, combine replaceable contents with at least two other changes:

- scene type or room scale
- product scale and placement
- lighting and color palette
- original vs mirrored orientation when the product allows mirroring
- foreground/background depth and composition

Do not use content replacement for products where the “contents” are actually fixed product structure. If uncertain, treat the entire visible object as fixed hardware and vary only the scene.

Use “fixed cutout layer” when the product should not change:

```text
Use the input image as an unchanged product cutout layer.
Do not redesign or redraw the product.
Keep the same color, structure, outline, holes, accessories, and silhouette.
Create a realistic background that matches where this product is actually used and composite this exact product cutout into the scene.
Use correct contact surface and gravity; do not place the product on an impossible or category-wrong surface.
Only add natural contact shadow and slight environmental light matching.
```

### Current Product-Specific Corrections

- **L042 garden edging strip**: high risk for AI redraw. Direct product-fusion often reconstructs the green strip surface, perforated fixing tabs, holes, and black spiral stakes incorrectly. Prefer deterministic compositing or scene-only generation plus exact PNG overlay. If using image generation, freeze the green flexible strip, edge fixing tabs, hole pattern, roll shape, and black spiral stakes; reject any output where the strip surface texture, hole count, tab structure, stake shape, or roll geometry is redesigned.
- **L042 nail/stake lock**: black spiral stakes must keep the original short spiral stake shape and correct quantity feeling. Reject long straight pins, fence rods, loose black sticks, outward-facing spikes, decorative bars, or any scene where the stakes are arranged as a separate fence-like object.
- **L043 folding clothes stacking board**: critical high-failure product. High risk for source-material sameness, product redraw, missing small center hole, wrong hole count, missing rear/front raised detail, and scale drift. Do not use one unified-looking PNG across all L043 exact D values. For any L043 redo, do not continue editing the failed generated image. If the user says `不要这个png`, `删掉这个png`, or source consistency is poor, lock out that exact source path/source_id before the next run. Source use must be mode-specific: for full product reconstruction or a complete-structure inspection image, use a clean high-contrast product-only cutout, or generate the scene separately and composite the fixed product PNG; do not ask the model to reconstruct hidden board structure from a source where clothing covers the product or only a small portion is visible. For contextual fusion, a clothing-covered or scene-like PNG may be used as the whole visible product+clothing reference object; in that mode preserve the visible combined subject, the clothing-on-board relationship, and the realistic use feeling, and do not invent or expose covered holes or hidden board parts. Use larger inspection scale, about 34-40% of image height, when full structure must be visible, with a clean front/top-front view. Do not mirror, rotate, or redraw the board unless the task is explicitly contextual fusion with visible structure preserved. Freeze the flat folding board outline, exact hole count, all large holes, the small center hole, rear raised detail, front raised detail, panel seams, material, and thin board thickness whenever those parts are visible and relevant to the requested image. Reject outputs where the board becomes a generic tray/pad, loses visible rear/front raised detail, changes visible hole positions/count, loses a visible small center hole, or appears unrealistically huge/small next to garments. If multiple L043 attempts fail structure checks, stop free-redrawing with the same model/prompt and switch to a different material source, fixed-PNG compositing/scene-only background, or contextual fusion with no hidden-part invention.
- **L071 mobile adjustable table**: expanded lifestyle scenes can look good but may alter the product into a generic side table. Freeze rectangular tabletop, white adjustable vertical support, black adjustment knob, X-shaped white base, and four black caster wheels. Avoid dark lounge scenes that hide or simplify the base/wheels. Reject any output with changed leg/base geometry, missing wheels, added shelves/drawers, or wrong support structure.
- **L072 flip-door shoe cabinet rack**: high hallucination risk. Freeze silver metal rods, black connector rings, vertically stacked flip-door drawers, top double black curved handles, three round handles on each drawer front, and no wheels. Do not let it become a generic shoe cabinet, dresser, drawer chest, or sideboard. Reject if drawer fronts, handles, rod frame, or connector rings are redesigned.
- **L076 gray plush pet mat**: do not use images where the product becomes a cushion, blanket, rug, pet bed with side walls, or patterned fabric. Freeze one flat rectangular gray long-plush mat with white edge binding and visible thickness. Avoid pets covering the product; a pet may be nearby only if the mat surface remains visible. Reject if plush surface, shape, border, thickness, or color is changed.
- **L047 garden arch**: do not let the source pool collapse to one or two near-identical PNGs. If approved `kept_cutout` material is limited after reject filtering, include safe `retry_new_original` product references that are not in the reject list. Keep one black arch only; flowers/ribbons may be added onto the existing arch but must not create an extra arch.
- **L048 artificial greenery privacy fence**: do not use kitchen, pantry, counter, shelf, or indoor storage scenes. This product is an outdoor/balcony/terrace fence-screen product. Place it attached vertically to balcony railing, patio fence, courtyard wall, garden fence, terrace divider, or outdoor privacy screen support only. Freeze the leaf panel grid, vine coverage, connector points, sheet shape, color, and flexible fence-screen silhouette.
- **L051 brown kraft paper gift bags**: do not use kitchen-storage scenes. Use gift wrapping tables, boutique retail counters, party favor tables, wedding/holiday packaging stations, small-shop checkout counters, or home craft packaging desks. Freeze kraft paper material, handle loops, bag quantity feeling, folded edges, and upright/open bag silhouettes. Avoid readable text, logos, branded labels, balloons, and food-packaging confusion.
- **L068/L074/L075 dish drying racks**: generic `kitchen_storage` is too loose for these. Use sink-side, over-sink, drainboard, wet countertop, or dishwashing drying-zone scenes. The sink edge, faucet blur, drainboard, or wet-zone context should be visible. Freeze rack tiers, rods, drain tray, cover/top details, supports, length relationship, and detachable/over-sink structure. Reject dry pantry, sideboard, bedroom, bathroom, or ordinary countertop scenes without sink/drying context.
- **L063 fitness board**: do not generate people using the product. The product should be fused as a fixed reference into an empty gym, fitness studio, training room, garage gym, rubber gym floor, or exercise mat scene. Avoid ordinary cozy home/bedroom styling unless explicitly requested. No hands, body parts, models, demonstrations, or product-use action shots. Do not change holes, rails, pedals, bands, handles, board outline, or surface structure. If a source PNG is identified as the wrong product, lock that source out immediately.
- **L077 cat scratcher / cat house**: never place this product on kitchen counters, pantry shelves, sideboards, or storage cabinets. It belongs on the floor in a living-room pet corner, bedroom pet area, hallway, home office, or window-side cat nook. Freeze corrugated scratch board texture, layered cat-house body, ventilation slots, openings, edges, color, and silhouette. Cats may appear only if they do not cover or merge with the product.
- **L078 covered divided food/picnic tray**: do not treat this as generic storage. Use dining table, kitchen prep counter, patio table, outdoor picnic table, serving sideboard, or home buffet scenes. Freeze six compartments, transparent lid, black top handle, tray body, proportions, and food-safe serving shape. The black handle is a hard visual feature and must remain visible.
- **L082 expandable under-shelf organizer**: keep the left-right expandable function visible and believable. For redos marked direction wrong, do not mirror, rotate, flip, or change the source orientation; preserve the left-right telescoping axis horizontally and front-facing. Freeze the shelf/body outline, telescoping extension relationship, support surfaces, proportions, and front-facing structure. The side of the product must not gain slide rails, extra tracks, drawer rails, or hardware that is not present in the source. Reject any output with side/bottom rail hallucination, missing left-right expansion detail, changed direction, changed usage context, or a generic shelf redesign.
- **L083 multi-function sliding storage rack**: high appearance-drift risk, but do not lock every image into an under-sink/drain-pipe scene. Preserve the overall proportion, side straight rods, sliding basket/plate details, supports, connectors, frame geometry, and visible hardware. Valid contexts include an under-sink cabinet, premium utility cabinet, pantry lower shelf, wardrobe/linen cabinet, or a luxurious gold-toned countertop/storage console when the product is realistically supported. For user-directed premium redo images, keep a visible gold/brass-toned countertop or base while varying its stone, wood, cabinet, and surrounding decor. Reject drainage-pipe-only repetition, added side rods, changed surface plate, ratio drift, or generic rack conversion.
- **L085 wall repair scraper set**: never use kitchen-storage or food scenes. This is a three-piece stainless putty scraper/wall repair tool set. Use home repair workbench, wall patching prep table, drop cloth, utility tool bench, paint-prep workstation, or interior wall maintenance context. Freeze three scraper sizes, metal blades, handles, straight edges, proportions, and tool-set quantity. Avoid active unsafe handling, hazardous chemicals, readable packaging, and power-tool domination.
- **L086 kitchen/storage rack**: keep the two drawer/basket units, front grid/transparent drawer face, top board, vertical supports, side frame, legs, and proportions unchanged. Hard color/material lock: this group has no white variant, so remove and block every white product source, white product material record, and generated white-product output from T/J/candidate/writeback workflows. Use kitchen counter, sideboard, pantry, coffee station, closet/storage counter, or home appliance station scenes. Avoid industrial shelf/workshop references when they contain many racks or shelving units, because the model may merge them into the product and change scale/proportion.
- **L086 visual reject lock**: path/name checks are not enough. If user review visually identifies a source PNG or generated candidate as white-product contamination, immediately add the exact `source_png`/`source_id` to the material rejectlist and exclude it before rerun.
- **L087 two-tier under-sink metal rack**: do not use generic kitchen countertop or sideboard scenes. Use sink-base cabinet, vanity lower cabinet, utility cabinet, under-shelf bay, or cabinet-interior storage scenes. Freeze the two-tier frame, basket/shelf structure, width-height relationship, visible rods, supports, and proportions.
- **L088 stepped fruit basket rack**: this is an offset stepped multi-basket rack, not a straight generic dessert stand. Freeze the offset basket layout, long bottom basket, upper baskets, central/vertical support rods, side rods, feet, color, outline, and all visible connectors. Do not simplify it into a three-tier tower, remove the middle vertical support, merge baskets, straighten the stepped layout, or convert it into a cafe dessert display stand. Prefer black/high-contrast product PNGs or add a clear product inset when rods are easy to lose.
- **L091 drawer organizer**: top structure and scene proportion are hard failure points. Avoid changing angle; use strict front-facing or only very slight perspective. Product should be around 30-36% of image height and placed realistically on a closet shelf, vanity shelf, entry cabinet, or storage cubby, not floating, too tiny, or oversized in a random room. Freeze the front-view drawer surface, transparent door, black handle, white frame, exact top structure, groove, square/grid recess pattern, and upper edge geometry. Do not add, remove, flatten, or invent top parts. Do not use low-resolution scene screenshots, black-padded images, candles/aromatherapy/contents-heavy references, or sources where the top groove is only partly visible as direct image2 references; they cause top-structure hallucination. Use a clear product-only reference or fixed-PNG compositing for L091 redos. Avoid same-tone closet scenes; rotate warm walnut closet, cool white closet, dark premium closet, and entryway cabinet palettes while preserving the exact top structure.
- **L092 cutting board set**: vary kitchen color palettes strongly: cool gray marble, warm wood, dark stone, and white-tile sink-side scenes. Keep exact hole count and hole positions.
- **L094 fruit bowl**: cross-use 2-layer and 3-layer specifications for differentiation. Alternate 2-tier foreground, 3-tier foreground, and natural scenes with both variants where appropriate. Keep bamboo stand, white ceramic bowls, screws, rods, and tier structure correct.
- **L095 hanging/planting basket**: rotate a broad outdoor scene bank: balcony railing herb garden, patio planting corner, greenhouse bench, sunny terrace, courtyard wall garden, apartment balcony, porch deck, backyard raised-bed, modern balcony corner, and garden workbench. Reject batches where L095 shares one generic green garden background or close-up planter composition across most outputs.
- **L096 folding portable barbecue grill**: this is an outdoor cooking product, not a kitchen-counter or tabletop storage item. Use broad but realistic outdoor use scenes: wild camping on campsite ground, lawn picnic, Western family/friends backyard gathering, courtyard or patio outdoor meal prep, RV campsite, garden party, park picnic, terrace/deck floor, and open-air family outdoor dining. The product must stand on its own legs on grass, campsite ground, gravel, patio pavers, courtyard floor, deck boards, terrace floor, or another heat-safe outdoor ground/floor surface. Do not place the grill on an ordinary table, picnic table, patio table, balcony table, camp table, workbench, cart, kitchen counter, sideboard, shelf, cabinet, indoor decorative surface, appliance corner, sink area, closet, bedroom, sofa, or bathroom. Outdoor props and people may appear as background atmosphere only; they must not touch, block, or merge with the product. Keep folding grill body, frame, legs, grate, hinge/locking structure, panels, supports, color, and silhouette unchanged. Because it is a grill, only loose contents on/near the grate may change: safe unbranded unlit skewers, vegetables, grill tools, folded foil, or picnic-prep props can vary when appropriate. These contents must not cover, merge with, or redesign the grill hardware. Avoid open flame, smoke, lit charcoal, candles, alcohol, branded packaging, and electronics. Do not collapse all prompts into one support direction; rotate camping, backyard, lawn, patio, deck, courtyard, RV, park, garden-party, and terrace-floor scenarios.

## Scene Differentiation Matrix

Vary at least 3 dimensions per image:

- **Scene**: white kitchen, warm wood kitchen, compact apartment kitchen, safe outdoor patio kitchen without fire or lights, farmhouse kitchen, dark luxury kitchen, balcony kitchenette, family dining room.
- **Task**: preparing breakfast, washing dishes, arranging tableware, cleaning after dinner, barbecue cleanup, family brunch, coffee making.
- **Product Scale**: 20%, 25%, 30%, 35%, or 45% of image height.
- **Position**: lower right, lower left, center-right, side counter, near sink, on island.
- **Orientation**: original direction or horizontally mirrored.
- **Contents**: white plates, blue plates, cream plates, matte gray plates, green bowls, beige bowls, glass cups, smoke-gray glasses, bamboo chopsticks, silver cutlery.
- **Lighting**: morning daylight, warm sunset, soft overcast, natural window light, premium dark kitchen ambient daylight. Avoid visible bulbs, string lights, candles, fire, or screen glow for Temu-safe outputs.

### Color Palette Rotation

For bulk T-first images, rotate visual color tone deliberately. First-screen differentiation should be visible even before checking product details.

- **Cool White Daylight**: white cabinets, pale marble, silver-gray accents, clean morning light.
- **Blue-Gray Premium**: slate, soft blue-gray walls, cool marble, calm overcast daylight.
- **Fresh Green Outdoor**: lawn, garden, plants, natural green and stone, bright but not cartoon-like.
- **Dark Luxury**: charcoal, dark wood, black metal, controlled daylight, premium contrast.
- **Warm Wood**: walnut, oak, beige fabric, home warmth; use sparingly so the set does not turn uniformly yellow.
- **Soft Cream Pastel**: ivory, pale peach, mint, butter blue, gentle ecommerce softness.
- **Black-White Contrast**: white room with black frame accents, crisp modern composition.
- **Neutral Overcast**: gray-white natural light, low saturation, realistic product catalog style.

When generating multiple images in the same batch, explicitly assign one palette lane per image in the prompt, for example: `Color palette lane: cool white daylight, avoid warm yellow cast.`

## Dish Rack Example

Use this pattern for dish racks where the black rack must stay but bowls/dishes can vary:

```text
Use the input image only as the product hardware reference. The product is a black two-tier kitchen dish drying rack with side utensil holder, front glass hanging rail, plate slots, rectangular black base tray, black legs and side supports. Keep this rack hardware recognizable, but it may be horizontally mirrored and scaled smaller. Replace all tableware inside the rack with cream ceramic plates, olive green bowls, clear glass cups, silver cutlery, and bamboo chopsticks. Ignore measurement labels, text, numbers, arrows, red marks, and the original background.

Wide realistic lifestyle photo: outdoor patio kitchen after a family barbecue, wooden dining table, plants, warm string lights, sliding glass door, people chatting softly blurred in the background. Put the rack on a side counter near a small sink, mirrored, complete and clear, only 24 percent of image height. Scene takes most of the image. Premium commercial photography, warm evening light, natural shadows, square composition.
```

For Temu-safe output, replace risky barbecue/light wording:

```text
Wide realistic lifestyle photo: clean outdoor patio kitchenette after a family meal, wooden dining table, green plants, sliding glass door, neutral home decor, people chatting softly blurred in the background. Put the rack on a side counter near a small sink, mirrored, complete and clear, only 24 percent of image height. Scene takes most of the image. Premium commercial photography, natural evening daylight, realistic shadows, square composition. Use only safe generic household props, no visible brands, no electronic screens, no fire, no flames, no candles, no decorative light bulbs.
```

## Quality Checks

## Ozon Production Mode

When the platform is Ozon, use a two-layer carousel workflow: generate a product-faithful base image, then add verified Russian information graphics in post-production. Do not interpret `no_text` on the AI base as “the final Ozon card must have no information.”

Assign reference roles before prompting: `identity`, `structure`, `scale`, `bundle`, and `usage_scene`. Identity decides what product is being sold; structure and scale verify it; usage_scene supplies placement/task context only. Never average multiple references into a new product.

Use low AI freedom for hero, size, structure and bundle slots; medium freedom for usage scene and premium lifestyle slots. A structure, size or set-content slot that becomes a generic lifestyle scene is a failure. For fragile racks, drawers, cabinets, trays, folding mechanisms or exact-count products, use identity plus structure references and reject any changed layer, rail, hole, handle, support, color or accessory count.

Persist the Ozon slot plan with `reference_roles_used`, `product_risk_tier`, `fixed_product_boundary`, `allowed_variations`, `verified_copy`, `post_layout_task`, and `review_status` so later ERP batches do not depend on conversation memory.

After generation, verify:

- product body is recognizable and not over-redesigned
- scene placement matches the product's real function, support surface, gravity, and usage location
- fixed hardware stayed consistent
- replaceable contents changed as requested
- scene is meaningfully different from prior images
- product is clear even when smaller
- no source measurement marks or plate text leaked into the output
- product is not blocked by people, plants, props, or foreground objects
- no Temu-risk elements appear: toys, electronics, screens, brand logos, fire/flames, visible decorative lights, dangerous goods, prohibited goods, alcohol, smoking items, medicines, or hazardous props

If the model modifies the product too much, switch to a deterministic workflow: scene-only generation plus programmatic PNG compositing.
