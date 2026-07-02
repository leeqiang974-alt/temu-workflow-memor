---
name: product-lifestyle-scene
description: Use when generating AI ecommerce lifestyle images from product SKU/reference images, especially when the product must stay visually consistent while scenes, people, scale, orientation, and contained items vary for bulk listing differentiation. Covers Seedream/Jimeng-style prompt strategy, clean PNG/cutout workflow, competitor-style expanded scenes, product compositing, and tableware/object replacement inside racks or storage products.
metadata:
  short-description: Ecommerce product lifestyle scene generation
---

# Product Lifestyle Scene Generation

## Core Principle

Treat the job as **scene generation plus product compositing**, not full product redraw.

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
- When the style reference contains objects structurally similar to the product, such as shelves, racks, baskets, drawers, or stands, the model may merge the style object with the product and silently redesign the product. Use these references only with stricter fixed-hardware language, larger product scale, a high-contrast product source, or switch to deterministic compositing.
- For high-structure products, prefer a clean high-contrast source PNG. Low-contrast white cutouts are more likely to lose thin rods, supports, basket edges, rails, and small vertical parts.
- Do not let “replaceable contents” become “replaceable hardware”. Contents can change only when they are loose objects placed on or inside the product; rods, frames, baskets, shelves, drawers, rails, handles, wheels, legs, and supports remain fixed.
- If a product has a historically repeated failure, add a product-specific lock before generating again instead of relying on generic “do not change product” wording.
- Control color tone as a first-class differentiation variable. Do not let every premium scene become warm yellow, beige, or sunset-toned. Rotate between cool white daylight, blue-gray marble, fresh green outdoor, dark luxury, warm wood, soft cream pastel, clean black-white contrast, and neutral overcast daylight.

## Temu T-Column First Carousel Workflow

Use this workflow when making the first image inserted into the workbook `T` carousel column.

### Mandatory model order for workbook T images

- For a new workbook/batch, the first pass must generate **every unique exact `D` T first image with image2/APIMart GPT-Image-2** using the current product PNG/material library and product-specific prompt rules.
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
   - Keep product appearance stable while using controlled variation such as horizontal mirroring, different left/right placement, different product size in frame, and slight angle-like composition changes.
   - For racks, shelves, trays, baskets, boxes, organizers, and similar container products, use replaceable loose contents as a major differentiation axis: tableware, bowls, cups, utensils, towels, files, fruit, flowers, greenery, small household items, or other category-safe props may change when they sit on or inside the product.
   - When replacing loose contents, explicitly freeze the product hardware/body: do not change rods, holes, shelves, tiers, baskets, handles, hooks, wheels, frames, rails, supports, product color, outline, or quantity of structural parts.
   - Avoid making all first-carousel images for one `L0xx` look templated or near-identical.

6. **Temu-safe scene constraints**
   - Prefer safe home/kitchen/patio/dining scenes with natural daylight, cabinets, countertops, sinks, curtains, plants, neutral tableware, towels, and generic household props.
   - Avoid toys, child-focused objects, electronic devices, screens, visible brand logos, branded packaging, fire, flames, candles, decorative lights, bulbs, balloons, dangerous goods, chemicals, alcohol, smoking items, medicines, medical devices, weapons, and prohibited or risky items.
   - People, if used, must remain background-only and must not touch, block, or visually merge with the product.
   - Enforce realistic use-context fit. The product must appear in a scene where a real buyer would naturally use, place, support, hang, store, or display it. Do not put products in visually attractive but physically absurd contexts, such as a barbecue grill on a bed, a heavy rack floating on fabric, a garden arch indoors on a sofa, a pet mat on a kitchen counter, or kitchen storage on bedroom bedding.
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
- barbecue/outdoor cooking products: patio, terrace, outdoor table, yard, campsite-style safe open area without visible flames; not bed, sofa, bedroom, bathroom, or wardrobe.

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
- **L043 folding clothes stacking board**: high risk for source-material sameness and scale drift. Do not use one unified-looking PNG across all L043 exact D values. Rotate distinct source PNGs where possible, including different approved white/gray board sources or angles that clearly preserve the same board structure. Freeze the flat folding board outline, all holes, the small center hole, rear raised detail, panel seams, material, and realistic scale relative to clothing. Reject outputs where the board becomes a generic tray/pad, loses rear raised detail, changes hole positions, or appears unrealistically huge/small next to garments. If available L043 cutouts are too uniform, pause to select better source PNGs or use fixed-PNG compositing rather than hallucinating variety.
- **L071 mobile adjustable table**: expanded lifestyle scenes can look good but may alter the product into a generic side table. Freeze rectangular tabletop, white adjustable vertical support, black adjustment knob, X-shaped white base, and four black caster wheels. Avoid dark lounge scenes that hide or simplify the base/wheels. Reject any output with changed leg/base geometry, missing wheels, added shelves/drawers, or wrong support structure.
- **L072 flip-door shoe cabinet rack**: high hallucination risk. Freeze silver metal rods, black connector rings, vertically stacked flip-door drawers, top double black curved handles, three round handles on each drawer front, and no wheels. Do not let it become a generic shoe cabinet, dresser, drawer chest, or sideboard. Reject if drawer fronts, handles, rod frame, or connector rings are redesigned.
- **L076 gray plush pet mat**: do not use images where the product becomes a cushion, blanket, rug, pet bed with side walls, or patterned fabric. Freeze one flat rectangular gray long-plush mat with white edge binding and visible thickness. Avoid pets covering the product; a pet may be nearby only if the mat surface remains visible. Reject if plush surface, shape, border, thickness, or color is changed.
- **L047 garden arch**: do not let the source pool collapse to one or two near-identical PNGs. If approved `kept_cutout` material is limited after reject filtering, include safe `retry_new_original` product references that are not in the reject list. Keep one black arch only; flowers/ribbons may be added onto the existing arch but must not create an extra arch.
- **L063 fitness board**: do not generate people using the product. The product should be fused as a fixed reference into an empty gym, fitness studio, training room, garage gym, rubber gym floor, or exercise mat scene. Avoid ordinary cozy home/bedroom styling unless explicitly requested. No hands, body parts, models, demonstrations, or product-use action shots. Do not change holes, rails, pedals, bands, handles, board outline, or surface structure. If a source PNG is identified as the wrong product, lock that source out immediately.
- **L086 kitchen/storage rack**: keep the two drawer/basket units, front grid/transparent drawer face, top board, vertical supports, side frame, legs, and proportions unchanged. Use kitchen counter, sideboard, pantry, coffee station, closet/storage counter, or home appliance station scenes. Avoid industrial shelf/workshop references when they contain many racks or shelving units, because the model may merge them into the product and change scale/proportion.
- **L088 stepped fruit basket rack**: this is an offset stepped multi-basket rack, not a straight generic dessert stand. Freeze the offset basket layout, long bottom basket, upper baskets, central/vertical support rods, side rods, feet, color, outline, and all visible connectors. Do not simplify it into a three-tier tower, remove the middle vertical support, merge baskets, straighten the stepped layout, or convert it into a cafe dessert display stand. Prefer black/high-contrast product PNGs or add a clear product inset when rods are easy to lose.
- **L091 drawer organizer**: avoid same-tone closet scenes. Rotate warm walnut closet, cool white closet, dark premium closet, and entryway cabinet palettes while keeping the front-view drawer surface, transparent door, black handle, white frame, and exact top structure/groove/grid pattern unchanged. Prefer strict front-facing views when the top structure tends to hallucinate.
- **L092 cutting board set**: vary kitchen color palettes strongly: cool gray marble, warm wood, dark stone, and white-tile sink-side scenes. Keep exact hole count and hole positions.
- **L094 fruit bowl**: cross-use 2-layer and 3-layer specifications for differentiation. Alternate 2-tier foreground, 3-tier foreground, and natural scenes with both variants where appropriate. Keep bamboo stand, white ceramic bowls, screws, rods, and tier structure correct.

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
