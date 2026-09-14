---
name: temu-tfirst-reference-edit
description: Reconstruct Temu/Xuanxshop T first images with reference_edit using competitor/source reference images and product-material libraries. Use when rebuilding, redoing, reviewing, or planning T first images where product fidelity, scene differentiation, reference-image transformation, library curation, accepted/failed locks, or avoiding cutout-PNG background compositing matters.
---

# Temu T First Reference Reconstruction

Use this skill for high-fidelity T first-image reconstruction. The goal is to retain the actual product's structure while creating a meaningfully different, natural-looking scene, composition, person/task, lighting, or premium presentation.

## Required Context

Before execution, read the active workbook/project rules and the relevant `temu-xuanxshop-image-workbook` references. For APIMart/image2 work, also load `temu-image2-apimart-runner` before choosing a provider, model, resolution, or cost setting.

Treat each exact D as the unit of work. Record its source assets, product restrictions, intended variation, output status, and writeback decision.

## The Three Libraries

Maintain three distinct libraries. They are not a generic background-compositing library.

1. **Reference-image library**: competitor main images, Temu images, and source images. Use these as the source of scene, composition, people, task, palette, lighting, texture, and premium cues in `reference_edit`.
2. **Product-material library**: same-L0xx product views, SKU/variant images, clean cutouts, and clearer same-model images. Use these to recognize, calibrate, and lock product structure when a reference is weak or the model may invent details.
3. **Outcome library**: approved, failed, rejected, and forbidden images with the exact-D scope, feedback, reason, and non-repeat locks. Use it to avoid retrying known-bad compositions or assets.

Read [library roles](references/library-roles.md) when creating or repairing a library index.

## Generation Strategy

Default to **reference_edit / multi-reference reconstruction**, not background replacement.

### Proven execution rule

The reliable pattern from the previous successful batch is:

**product boundary lock + reference-value preservation + controlled non-product variation**.

Do not treat a longer product lock as a better prompt. When the prompt simultaneously fixes product family, room, action, support surface, camera distance, product percentage and premium style, the model tends to produce a repeated template and discard the source person's task, depth and luxury cues. Product locks must describe visible hardware only. Scene instructions must describe what may change from the current reference, not a replacement room recipe.

Use this structure for handoff to another agent:

```text
MODE: reference_edit
KEEP: exact visible product boundary, color, count, hardware, support/contact, useful reference composition, person/use/task logic, spatial depth, camera distance, and premium cues.
EDIT: only background material, palette, light, person identity/pose/clothing, loose contents, safe props, crop, scale, or orientation.
TITLE ROLE: identify product family/specification only. Never derive room, action, camera, scale, or atmosphere from the title.
PASS CONDITION: product is correct, scene is believable, reference value remains, and at least three non-product dimensions differ.
REDO CONDITION: product is correct but person/task/premium value disappeared, or the image became a generic clean template.
```

When a product-specific correction is supplied, append it as a narrow exception after the structure above. Do not rewrite the whole prompt into a new fixed scene. If two instructions conflict, preserve product truth and the reference's original selling logic, then vary only the non-conflicting elements.

- Preserve product silhouette, visible structure, materials, color, assembly, and usable orientation.
- Preserve the reference image's valuable non-product context unless it is unsafe or explicitly wrong: human presence, human task/action logic, product placement, room depth, camera distance, premium/luxury cues, and realistic support/contact relationship.
- Do not over-clean the reference image into an empty generic scene. The job is to transform the reference, not erase its useful scene value.
- If a person appears in the reference and the person helps explain scale, use, task, or lifestyle value, the person/task is a hard preservation requirement. The output must show one visible, anatomically plausible person performing the same product-related task or an equivalent task relationship. The person may change identity, clothing, pose, and position, but may not disappear, be reduced to an irrelevant distant bystander, or block/merge with the product unless the user explicitly requests no person or the category is unsafe for people.
- Keep or improve unbranded premium cues when they exist in the reference: stone, travertine, marble, walnut/oak, linen, plain ceramic, brushed metal, boutique-hotel or high-end home styling. Do not replace a premium scene with a plain cheap-looking room.
- Maintain task rationality. If the reference shows a realistic task, preserve the task relationship while changing non-product details; do not create impossible placement, floating products, wrong storage location, or a product used in an unrelated room.
- Avoid visible AI traces: melted hands, distorted furniture, impossible shadows, duplicate products, over-smoothed plastic surfaces, fake luxury logos, incoherent reflections, warped shelves, and unnatural object scale.
- Change at least three meaningful visual dimensions across different D values within a shared L0xx where product truth allows it: scene, composition, person/task, scale, palette/light, orientation, or props.
- Use product materials as structural evidence or additional image references when the source is blurry, cropped, structurally complex, or prone to hallucination.
- Describe and verify product-critical details explicitly: handles, rods, shelves, holes, baskets, trays, folds, feet, fasteners, color blocks, and outline.

### Reference-Edit Hard Rules

When the source is a competitor/reference main image, use this intent:

```text
source_mode: reference_edit
Preserve: product boundary, product support/contact, reference composition value, room depth, human/task logic when useful, premium cues, believable use context.
Change: background material/palette, person identity/clothing/pose, nearby props, loose contents, lighting, camera crop/expansion, and safe non-product scene details.
Do not change: product hardware/body, quantity, visible structure, color/spec, support logic, or real product function.
Do not erase: useful people, task logic, premium room quality, spatial depth, or scale cues unless they are unsafe or explicitly rejected.
```

Reject or redo outputs where:

- People disappeared even though the reference person helped explain use, scale, or lifestyle.
- A retained person is no longer visibly related to the product task, is cropped to unusable fragments, or makes the product harder to inspect.
- The premium/luxury feel was downgraded into a plain generic room.
- The scene was rebuilt from title/template instead of edited from the reference.
- The product is reasonable-looking but the scene has obvious AI traces, impossible placement, weak contact shadow, or wrong task logic.
- Same-L0xx outputs collapse into one repeated composition, room type, action, palette, or product scale.

### Source Chain And Prompt Contract

For a batch that declares an approved historical T1 library, use that library as the only direct `reference_edit` source. Do not feed an earlier generated/reworked T1 output back as a new reference merely because its D matches. A new D may map to a historical source D; record that mapping explicitly.

Build every production prompt from this contract, then append only a narrow product-specific lock:

```text
MODE: reference_edit
SOURCE: approved historical T1 for {source_D}; this is the product and reference-value anchor.
KEEP: exact visible product boundary, color, count, hardware, support/contact,
useful composition, person/task logic when present, spatial depth, camera distance,
and premium cues.
EDIT ONLY: background material/palette, light, person identity/clothing/pose,
loose safe props, and a small crop/scale/orientation adjustment.
TITLE ROLE: product-family/specification check only; never derive a replacement room,
task, support surface, camera or atmosphere from the title.
REJECT: changed hardware, color/count drift, impossible use/support, missing useful
person/task, generic empty template, readable text/logos, warped hands/furniture,
or a scene too similar to sibling D images.
```

### Person/Task Retention Gate (2026-07-17)

Before generating a reference edit, classify the source as `person_task_required` when a visible person supplies use, scale, installation, cleaning, storage, gardening, or lifestyle evidence. For that class, append this explicit prompt block after the product lock:

```text
PERSON/TASK LOCK: the source contains a useful person and product-related task.
The output MUST retain one fully visible, believable person doing the same or an
equivalent product-related task. Keep the person separate from the product; do
not crop the person into fragments and do not let hands, clothing, or props hide
the product hardware. An empty room or passive background person is a failure.
```

Visual review must reject `person_task_required` candidates that lose the person
or task even when the product itself is correct. This is a first-class redo reason,
not a cosmetic preference.

### Verified Reference Gate (2026-07-17)

Neither a same-`L0xx` folder name nor a historical source record proves product
identity. Visually validate every exception/redo anchor against a confirmed product
material before submission. Quarantine a mismatch by exact path and source ID.
For example, the historical path labelled `L087070901_9654.png` was actually an
L042 garden-edging scene and must never be used as an L087 T1 reference.

Use the reference's product and selling logic first. Do not add a separate title-first
scene lane to a usable reference-edit prompt. Require at least three safe non-product
differences across same-`L0xx` sibling outputs, without erasing the original scene value.
For high-risk structure families, attach a clear same-`L0xx` product-material image as
structural evidence and reject rather than freely redraw uncertain hardware.

### Active YeahF 1999D Human-Rejection Correction (2026-08-13)

Human review is authoritative. A rejected generated candidate is negative evidence and
must never become a later reference image, product-material image, badge input, OSS
asset, or workbook writeback source. A redo must return to the current-workbook T1 for
scene/composition and add a separately verified product-material input when the product
appearance in that T1 or the first generated candidate is unreliable.

- **L081 (`wrong_product_appearance_inheritance`)**: same-`L0xx` inheritance is
  forbidden. Resolve every rejected exact D independently to a visually verified
  exact-D/exact-variant product material with row-level `D + G + SKU` provenance and
  include that image in the paid edit request. The current-workbook T1 remains only the
  scene/composition anchor. Do not let its foreground product, a sibling D, a generic
  L081 family image, the title, or a previous generated candidate define product
  appearance.
- **L043 (`product_appearance_changed`)** and **L072
  (`product_appearance_hallucinated`)**: include a verified exact-D product-material
  image and lock all visible product geometry, color, quantity/specification, holes,
  panels, handles, rods, connectors, drawers/layers, feet and proportions. Edit only
  non-product scene variables. A plausible-looking redesign is still a hard failure.
- **L068 (`product_appearance_changed_and_proportion_wrong`)**: lock exact silhouette,
  part relationships and width/height/depth ratios against verified product material.
  Reject stretched, compressed, widened, narrowed or otherwise plausible-looking but
  proportionally incorrect products.
- **L082 (`wrong_product_appearance`)**: lock the complete organizer body, extension
  mechanism, supports, surfaces and proportions. A generic shelf or visually similar
  organizer is not an acceptable substitute.
- **L083/L091 (`product_appearance_detail_error`)**: treat small hardware and surface
  details as identity evidence, not cosmetic defects. L083 must preserve rods, metal
  plates/sheets, supports and connectors; L091 must preserve the exact top structure,
  groove/recess pattern, transparent front, handle and upper-edge geometry.
- Before paid submission, record hashes for the current-workbook T1 scene anchor, the
  verified product-material image and the rejected candidate. Block submission when
  the product-material source is unresolved, cross-D, only same-prefix, visually
  unverified, or when the request still supplies only the unreliable T1.

For the 2026-08-13 review file, `L042080933` and `L042080944` are explicitly approved;
they must not enter the rejection/redo queue.

### Agnes 1999D Scene-Freeze And Product-Fusion Correction (2026-09-14)

The 23-image `agnes-image-2.5-flash` retry batch was human-rejected in full. Treat
all 23 outputs as permanent negative evidence. Their generally good product-detail
retention does not compensate for these failures: the scene stayed nearly unchanged,
the same person/pose was retained, and requested foreground/midground/background,
camera-angle and depth variations were not executed.

The old conservative contract caused this failure. Do not tell Agnes both to preserve
the source composition/camera/person-task relationship and to create substantial
scene differentiation. Phrases such as `preserve scene composition`, `preserve camera
relationship`, `preserve person/task logic`, and `small crop adjustment` make the first
reference dominate and reduce the job to near-copy editing.

For a differentiation redo, keep only the **use/function logic**, not the source pixels:

- require a new room/layout or materially reorganized setting;
- require a different person identity, face, clothing, pose and placement when a person
  remains useful, while retaining only the equivalent product-related task;
- assign an explicit new camera lane (three-quarter side, lower eye level, higher oblique,
  near-product wide angle, or deeper telephoto) and change product position/scale;
- require distinct foreground, midground and background elements rather than generic
  wording such as `add depth`;
- reject the result when the original cabinet layout, person, camera height, crop and
  object arrangement remain recognizably unchanged.

Agnes may fuse conflicting products across multi-image references even when the prompt
labels one image `scene only`. `L082080805` is the sentinel: the white pull-out shelf in
the current-workbook T1 and the dark exact-D shelf were rendered together as overlapping
products. Therefore, when a scene anchor contains a product whose colour/structure
conflicts with the exact-D material, never submit that full scene image beside the
product reference. First produce and verify a scene-only anchor with the old product
removed, or use the exact-D product as the only image reference and translate the old
T1's useful context into text. Put the exact-D product reference first. One prompt is
not a reliable mask and cannot prevent cross-reference product fusion.

Before another bulk Agnes retry, run two controlled diagnostics: one non-conflicting D
with a product-first, strong-differentiation prompt, and one conflicting D such as
`L082080805` with no full old-product scene reference. Human approval of both tests is
required before batch submission.

For the 2026-09-14 V2 diagnostic, product-only submission removed the old-scene freeze
and the L082 black/white product fusion: submit only the visually verified exact-D
product image, keep old T1/rejected outputs as hashed evidence but not model inputs,
and express the new scene/person/camera/depth recipe in text. This is a diagnostic
strategy, not automatic approval; exact count, mechanism, proportion and fine detail
still require human visual review before badge, OSS or workbook writeback.

Agnes concurrency is queue-sensitive. In the verified 23-D run, eight workers caused
HTTP 503 `image queue is full`; four workers remained unstable immediately after that
saturation; after a 60-second cooldown, two workers completed every remaining item.
Default to two workers, use bounded cooldown/retry, and treat 503 queue-full as provider
capacity rather than a prompt/product failure. Do not default to eight workers.

The 2026-09-14 V2 human review adds three cross-batch locks. First, cast diversity is a
batch property: rotate young adults, adults, middle-aged people and selected no-person
scenes; do not let elderly people dominate merely because each single prompt says
`different person`. Second, physical support is product truth: every foot/base must
visibly contact one continuous surface with plausible contact shadows, the complete
product must stay inside the supporting tabletop/counter boundary, and no generated
floor stand, cart base, caster, rail or hidden support may be added. Third, when scale
or proportion is rejected, lock both the product's intrinsic width/height/depth ratios
and its intended frame occupancy/real-world relationship to a person or pet; a correct
silhouette at an implausible size still fails.

### Compositing Boundary

Do **not** default to “cutout PNG pasted onto a ComfyUI background.” It is rejected for normal T-first reconstruction because it commonly looks synthetic and produces weak differentiation.

Use deterministic PNG compositing only when the user explicitly asks for it, or as a documented exception where reference editing cannot preserve a high-risk product structure. Mark that output as a compositing exception in the outcome library and submit it for visual review.

## Review and Approval

Generate or collect a review page before writeback. Check:

- The image represents the exact D / L0xx product, not merely a similar product.
- The product structure and variant-facing visual cues are credible.
- The scene is natural, the product fits the frame, and no key part is cropped or distorted.
- The output does not repeat a failed or forbidden source/recipe.
- Same-L0xx images are differentiated without changing product truth.

User feedback overrides automatic scoring. Move rejected images to the outcome library with a precise reason; promote only accepted images to the writeback candidate list.

## Paid Async Provider Zero-Loss Gate

For Cangyuan, APIMart, or any paid asynchronous image provider, production execution
must be one resumable closed-loop runner:

`submit -> query -> immediate download -> decode/dimension validation -> SHA-256 -> manifest`

- Never use a submission-only production script followed by a separate manual download
  step. Provider result URLs may be temporary.
- Keep at most 8 paid tasks in flight. A single generation or isolated download failure
  does not stop unrelated work: quarantine that exact D, continue the queue, and never
  auto-resubmit it.
- Stop new paid submissions only for classified systemic failures: insufficient balance
  or payment rejection, authentication/permission failure, non-recoverable quota/policy
  block, invalid endpoint/model configuration, local disk/manifest write failure, or
  repeated same-class completed-result download failures indicating provider-wide
  expiry/outage.
- Transient network/rate-limit errors use bounded backoff while other tasks continue.
  When a systemic pause is triggered, continue collecting every already-submitted task
  and report the evidence; do not abandon successful in-flight results.
- Before batches larger than 5, require one paid end-to-end smoke task whose result is
  locally downloaded and validated.
- Provider `completed` is only an intermediate state. Final success requires a readable
  local image, expected dimensions, SHA-256, and an exact-D manifest record.
- Persist task IDs immediately and resume them after interruption. Never resubmit an
  existing task ID automatically.
- Reconcile every run as:
  `submitted = validated_local + explicit_failed + still_in_flight`.
  Missing or unknown tasks block review-page generation and workbook writeback.
- Report failures for user approval; never automatically pay for retries.

## Workbook Writeback

Write back only accepted, durable OSS/CDN URLs. Never write local paths or temporary provider URLs.

- Insert the approved new image as T1 for its exact D.
- Make U follow T1 when the workbook uses U as the material/first-image field.
- Preserve carousel positions that are already locked, especially the T4 size-image slot. Do not overwrite, reorder, or replace non-requested images.
- Apply consistent T/U values to every physical row of the same exact D.
- Output a new workbook copy and verify the completed URLs, T1/U consistency, carousel length, and unchanged protected slots.

## Deliverables

Keep an auditable exact-D plan and outcome table containing source reference IDs, product-material IDs, prompt/edit intent, output location, approval status, rejection reason, and final OSS/CDN URL.
