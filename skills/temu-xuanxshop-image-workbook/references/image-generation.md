# AI Image Generation And Product Fidelity

## Ask For Model Availability

Do not assume a model. Ask what is available:

- deterministic PIL/local compositing
- background generation model that preserves foreground cutout
- Seedream/Jimeng-style creative image model
- other image model/API

Ask for API credentials only when needed. Do not print credentials.

## Model Choice

- Use deterministic compositing for maximum product fidelity.
- Use background generation around a transparent PNG when product structure must remain exact.
- Use Seedream/Jimeng-style generation for stronger scene differentiation, content replacement, mirroring, or scale variation, but expect product drift.
- For strict work, use hybrid: generate/explore scene, then composite exact PNG back.

## Prompt Rules

Prefer English positive prompts. Avoid long negative prompt lists unless required.

Always specify:

- input image role: unchanged cutout layer vs hardware reference
- fixed product structure: rods, holes, shelves, handles, wheels, drawers, frame, tray, basket, color, silhouette
- allowed changes: background, lighting, scale, mirror, loose contents
- forbidden drift: no new parts, no missing parts, no changed color/material
- safe commercial scene: home/kitchen/patio/dining/storage/pet/fitness as appropriate

## Luxury / High-Value Styling Without Infringement

Use unbranded premium cues:

- marble/travertine/stone texture
- warm wood
- linen
- plain ceramic
- brushed metal
- boutique hotel styling
- clean editorial daylight
- upscale home decor
- neutral flowers, towels, fruit, tableware

Avoid:

- brand logos
- monogram patterns
- recognizable luxury brand packaging
- designer handbags/watch/jewelry silhouettes
- readable brand text
- counterfeit-like props
- electronic screens
- fire/flames/candles
- alcohol, medicines, weapons, toys, child-focused props

## Product Structures

For racks, shelves, trays, baskets, pet mats:

- Product body/frame/shelves/rods/basket/tray/holes/supports/outline must stay unchanged.
- Loose contents may vary only when the product already contains loose items.
- People/animals may be background cues only and must not touch, block, or merge with product.

## Differentiation

For different D under same L0xx, vary at least three:

- scene
- background
- product scale
- position
- orientation/mirror
- lighting
- prop arrangement
- loose contents

If user marks “too similar”, lock those D for redo and force a different scene/scale/position/material source where possible.

## Review Gate

Never rely on AI output without review. Check:

- product body recognizable
- no structural hallucination
- no color/material drift
- no source text/measurement marks leaked
- product is complete and clear
- no risky scene elements
- same-prefix images are differentiated
