---
name: product-lifestyle-scene
description: Use when generating AI ecommerce lifestyle images from product SKU/reference images, especially when the product must stay visually consistent while scenes, people, scale, orientation, and contained items vary for bulk listing differentiation. Covers Seedream/Jimeng-style prompt strategy, clean PNG/cutout workflow, scene-only generation, product compositing, and tableware/object replacement inside racks or storage products.
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

## Temu T-Column First Carousel Workflow

Use this workflow when making the first image inserted into the workbook `T` carousel column.

1. **One image per unique D**
   - Treat exact `D` value as the generation unit.
   - Generate exactly one first-carousel image for each unique `D`.
   - If the same `D` has multiple workbook rows or variants, insert the same generated OSS URL as the first `T` image for all rows with that `D`.
   - Do not generate separate first-carousel images for each row unless the user explicitly asks.

2. **SKU selection from variants**
   - Use the clean final transparent SKU PNGs as product source images.
   - For single-SKU products, use that one SKU image.
   - For multi-SKU products, include only the distinct variant images represented by that `D` group, not repeated quantity variants.
   - Example: for `L043`, use only white and gray SKU images; do not create four separate foregrounds for `15 white`, `30 white`, `15 gray`, and `30 gray`.
   - Match variants by stable SKU keywords such as black/white/gray/green/pink/purple, walnut/original wood, and numeric variants like 2 or 3.

3. **Model layering strategy**
   - Use Alibaba/DashScope background generation for the final high-fidelity pass when the product structure must stay exact.
   - Use Seedream/Jimeng for creative exploration when stronger lifestyle variation, contents changes, mirror direction, scale variation, or composition ideation matters.
   - For bulk listing safety, prefer hybrid: Seedream/Jimeng explores scenes, then the true SKU PNG is composited back or passed through Alibaba/fixed compositing to preserve product fidelity.
   - Never rely on a Seedream/Jimeng output without checking product drift.

4. **Differentiation within the same L0xx**
   - For different `D` values under the same `L0xx`, vary at least three dimensions: scene, background, product scale, position, orientation/mirror, object arrangement, and foreground grouping.
   - Keep product appearance stable while using controlled variation such as horizontal mirroring, different left/right placement, different product size in frame, and slight angle-like composition changes.
   - For racks, shelves, trays, baskets, boxes, organizers, and similar container products, use replaceable loose contents as a major differentiation axis: tableware, bowls, cups, utensils, towels, files, fruit, flowers, greenery, small household items, or other category-safe props may change when they sit on or inside the product.
   - When replacing loose contents, explicitly freeze the product hardware/body: do not change rods, holes, shelves, tiers, baskets, handles, hooks, wheels, frames, rails, supports, product color, outline, or quantity of structural parts.
   - Avoid making all first-carousel images for one `L0xx` look templated or near-identical.

5. **Temu-safe scene constraints**
   - Prefer safe home/kitchen/patio/dining scenes with natural daylight, cabinets, countertops, sinks, curtains, plants, neutral tableware, towels, and generic household props.
   - Avoid toys, child-focused objects, electronic devices, screens, visible brand logos, branded packaging, fire, flames, candles, decorative lights, bulbs, balloons, dangerous goods, chemicals, alcohol, smoking items, medicines, medical devices, weapons, and prohibited or risky items.
   - People, if used, must remain background-only and must not touch, block, or visually merge with the product.
   - Enforce realistic use-context fit. The product must appear in a scene where a real buyer would naturally use, place, support, hang, store, or display it. Do not put products in visually attractive but physically absurd contexts, such as a barbecue grill on a bed, a heavy rack floating on fabric, a garden arch indoors on a sofa, a pet mat on a kitchen counter, or kitchen storage on bedroom bedding.
   - Match contact surface and gravity. Floor products stand on floor/grass/tile; countertop products sit on counters/tables/shelves; wall/fence products attach to walls/fences/railings; outdoor garden products stay on lawn/path/patio/flower bed; cleaning products sit on bathroom/laundry/utility floors. If a product requires support, show believable support.

6. **Workbook insertion**
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

## Scene Differentiation Matrix

Vary at least 3 dimensions per image:

- **Scene**: white kitchen, warm wood kitchen, compact apartment kitchen, safe outdoor patio kitchen without fire or lights, farmhouse kitchen, dark luxury kitchen, balcony kitchenette, family dining room.
- **Task**: preparing breakfast, washing dishes, arranging tableware, cleaning after dinner, barbecue cleanup, family brunch, coffee making.
- **Product Scale**: 20%, 25%, 30%, 35%, or 45% of image height.
- **Position**: lower right, lower left, center-right, side counter, near sink, on island.
- **Orientation**: original direction or horizontally mirrored.
- **Contents**: white plates, blue plates, cream plates, matte gray plates, green bowls, beige bowls, glass cups, smoke-gray glasses, bamboo chopsticks, silver cutlery.
- **Lighting**: morning daylight, warm sunset, soft overcast, natural window light, premium dark kitchen ambient daylight. Avoid visible bulbs, string lights, candles, fire, or screen glow for Temu-safe outputs.

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
