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
   - Snapshot immutable/key columns before changes: row index, D, G, SKU, source title, existing J/T/U, and any shop-specific helper columns such as X/AC.

2. **Build group model**
   - Exact `D` is the product group.
   - Same `D` rows share title, T first image, T carousel, and U first material.
   - J is row-level: each row may have its own variant preview based on `G` and `SKU货号`.
   - Title fingerprints/tracking codes are per workbook and per exact D; do not reuse a title code from another file or another D.
   - Classify the task before editing:
     - **Complete/new/redo workbook**: title, J, T, U, T4, URL safety, feedback locks, and changed-cell diff are all in scope by default.
     - **Late-stage repair/writeback**: only the explicitly requested columns are in scope, such as T/U replacement or URL repair.
     - Do not classify broad wording such as "make a workbook", "redo a workbook", "do a table", or "final writeback table" as late-stage T-only repair unless the user explicitly says only T/U should change or titles/J should be preserved.

3. **Preflight assets**
   - Match SKU/material candidates before generating or uploading.
   - Report missing folders, missing clean first-level images, variant ambiguity, and forbidden paths.
   - Never silently recurse into generated folders such as `九宫格`, `9grid`, `out`, `output`, or background/output directories.
   - Do not trust folder names alone for color variants. When a batch has known mixed source folders, verify visual color/title signals and write rejected source files to a machine-readable reject list.

4. **Create review artifacts before writeback**
   - For image-heavy work, build an HTML review page.
   - Use lazy loading or per-D loading for large 100+ image audits.
   - Include row, D, prefix, variant, SKU, source image, generated image, prompt/scene, and status.
   - Add delete/reject/restore/export controls when the user is screening images.
   - Export feedback from the current UI state, not only previously saved browser localStorage. If the user types Chinese feedback after clicking `redo`/`reject`, the export must read live input values so reasons are not lost.
   - Feedback export must be non-destructive. Never navigate away from the review page, replace the current tab, open a blank/JSON-only page that steals the review state, or depend on a popup window. Use download, clipboard, inline modal/textarea preview, and live DOM recovery so the page remains usable after export.

5. **Generate/edit T first images**
   - One T first image per unique exact `D`, unless the user explicitly asks row-level T images.
   - Current T first-image rule: for a new workbook/batch, generate all unique exact `D` first images with image2/APIMart GPT-Image-2 first, then review. Only images that fail review should go to Seedream/Jimeng fallback or targeted redo.
   - Image2/APIMart low-cost model is exactly `gpt-image-2` at `resolution: "1k"`. Do not use expensive or unofficial/official model variants, and do not use `2k`/`4k` for Temu bulk T-first work unless the user explicitly approves the higher cost. Every image2 runner must declare model/resolution as constants and refuse to run if they are not exactly `gpt-image-2` + `1k`.
   - Do not treat old Seedream approved records, old Ali single-SKU outputs, ComfyUI background+paste outputs, or `all_sku_tfirst` outputs as satisfying the new T first-image stage.
   - Reuse approved outputs only if no later user feedback rejects or marks them similar/wrong.
   - For AI product-fusion T first images, use the approved product-material PNG registry first, such as selected new-original/象寄 cutout PNG records. Do not repeatedly use the same SKU preview PNG for every `D` under one `L0xx`.
   - Rotate different approved source PNGs across same-`L0xx` D groups and record `source_kind`, `source_id`, and source path in the review artifact.
   - Before image generation, build a source-material allocation plan for every `L0xx`: exact `D`, `source_png/source_kind/source_id`, scene lane, color lane, product scale, placement, and composition difference.
   - Every `L0xx` must satisfy both PNG material differentiation and scene differentiation. Do not pass a batch that only varies scenes while reusing one near-identical PNG, or only varies PNGs while keeping templated scenes.
   - Before approving scene differentiation for any `L0xx`, define the product's realistic use envelope: actual function, support/contact surface, indoor/outdoor boundary, installation/placement method, likely buyer scenarios, safe props, and forbidden contexts. Decide from that reasoning whether the product needs broad multi-scene rotation or a narrower scene family with palette/composition/source-PNG variation.
   - Multi-scene thinking is not limited to L096, but it is not automatic for every product. Products with broad real use cases should rotate multiple reasonable scenarios; products with narrow real use cases must stay inside their functional context and differentiate through room subtype, palette, camera depth, placement, scale, props, and PNG source variation.
   - Scene lanes must be concrete expanded-scene prompts, not placeholders such as `set_1_scene_lane` or generic text like "different scene mood". For each `L0xx` before bulk T generation, prepare at least 20 category-correct expanded lifestyle scene prompts and rotate/randomize them across exact `D` and set variants.
   - For DXXmall/0616-2 T-first generation and redo/fallback work, load `scripts/luxury_expanded_scene_banks_0616_2.py` before using older inline scene banks. It provides 20 detailed unbranded luxury expanded-scene prompts per active `L0xx`, with stone/travertine, walnut/oak, linen, plain ceramic, brushed metal, boutique-hotel or premium-home cues.
   - Luxury scene prompts must remain Temu-safe: no named luxury brands, logos, monograms, readable brand text, designer handbag/watch/jewelry silhouettes, screens, fire, candles, alcohol, toys, medicines, weapons, or risky props.
   - The preflight must fail if any active `L0xx` custom expanded-scene bank, or the default scene bank used for uncategorized prefixes, has fewer than 20 concrete scene prompts.
   - "扩图/扩场景" means camera-pulled-back lifestyle scenes with real spatial depth, product occupying roughly 18-28% of the frame when safe, varied support surfaces, placement, room/garden scale, color palette, and props. A tight product crop with a slightly different background does not satisfy expanded-scene differentiation.
   - A batch cannot pass the preflight if a same-`L0xx` group has enough source PNGs but most candidates still share one visual product pose, one background type, or one generic close-up composition.
   - If the user says a same-`L0xx` group uses overly uniform PNG material, the next redo must switch or expand the source material pool instead of reusing one near-identical product cutout across many exact `D` values. Current known risk groups include L042 and L043.
   - Current L043 rule: folding-board T redos are a critical high-failure group. Rotate distinct source PNGs and preserve board holes, small center hole, rear/front raised detail, outline, panel seams, thin board thickness, and realistic scale against clothing. Do not continue using one unified-looking PNG across the whole L043 group. If the user says `不要这个png`, `删掉这个png`, or source consistency is poor, lock out that exact `source_png/source_id` before any rerun. After repeated L043 structure failures, do not keep free-redrawing the product with the same model/prompt; switch to a different approved PNG, fixed-PNG compositing/scene-only generation, or pause to add better material.
   - L043 source-use gate: separate "full product reconstruction" from "contextual fusion". If the goal is to show the complete folding board structure, use a clean high-contrast cutout/product-only source, or generate a scene separately and composite the fixed product PNG. Do not ask image2 to infer hidden board structure from a source where clothing covers most of the product or where only a small portion is visible. However, clothing-covered/contextual PNGs may be used as a whole PNG+clothes/reference-object fusion source when the output only needs to preserve the visible combined subject and its realistic use feeling. In that mode, the prompt must not invent the covered/hidden parts; it should keep the visible board+clothing relationship and fuse that combined reference into a broader scene.
   - Record each generated T first image with `provider`, `model`, `source_png`, `prompt`, `status`, and `fallback_of` when Seedream is used after image2 failure.
   - Treat SKU variant PNGs as T fallback only when no approved product-material cutout exists, or when the user explicitly asks to use SKU images for T.
   - Preserve product body. For high-risk structures, prefer fixed PNG compositing or conservative background generation.
   - For same `L0xx`, differentiate by scene, scale, position, orientation, background, and props.

6. **Generate J preview images**
   - Rebuild J by row-level variant matching.
   - J preview images are SKU/variant driven and may use SKU PNGs; this does not imply T first images should use the same SKU preview source.
   - Before rebuilding J, declare the exact batch `sku_root` and candidate source family. Historical DXXmall/0616-2 J correction records used `E:\JIT制图--新店\{L0xx}\sku文件_最终抠图PNG`, with L043 explicitly using `白\白.png` and `灰\灰.png`; raw DXXmall SKU images may also exist under `E:\jit制图\{L0xx}\sku`. Do not substitute T product-material PNG pools such as selected/kept/Xiangji T cutout libraries for J unless the user explicitly approves that migration.
   - J source provenance is a hard gate: every generated row must have a machine-readable match record containing `row`, exact `D`, `G`, `SKU货号`, `sku_root`, `sku_source`, `wanted_tokens`, `matched_tokens`, `match_mode`, and `warning`. If the source root is unknown or any row lacks `sku_source`, stop before writing back.
   - Use the established five-preview textured composition, not a plain white background, unless the user explicitly asks for white.
   - Print or review every row-level match: `D`, row, `G`, `SKU货号`, matched tokens, selected SKU source, and warning if fallback was used.
   - For color variants, build a pair/group audit page when practical: show same-D rows side by side with `G`, `SKU货号`, source path, visual source checks, and generated J.
   - If many rows have no positive token match, stop before writeback and ask for better SKU folders or mapping.
   - If the user asks to "make a workbook", "redo a workbook", "do a new table", or similar broad workbook wording, J rebuild and J source audit are in scope by default. Only skip J rebuilding when the user explicitly says the task is T-only or J must be preserved.
   - Final validation must prove more than "J is non-empty": include J source/match records, row-level variant matching status, generated J review/audit path, and whether the user approved the J review.
   - For every complete/new/redo workbook, J execution is mandatory and must be treated as a first-class deliverable, not a side effect of T writeback. The run must include a full row-level J source manifest, a generated/repaired J image for every effective row, a review/audit page, SKC preview synchronization evidence, and changed-cell validation. Do not deliver a new workbook if J was skipped, silently preserved, or only checked as non-empty.

7. **Write back only after approval**
   - Insert approved T first image as first URL in T for all rows with same `D`.
   - Preserve or reorder existing T according to user instruction.
   - Keep the fourth image as the size image when the workbook expects that. Detect size images by filename/title clues, not merely by original position.
   - Set U equal to T first image.
   - Write J row by row from approved variant previews.
   - For a complete/new/redo workbook, write titles from the current run's title reconstruction with a per-file/per-exact-D fingerprint. Do not silently preserve source titles.
   - For a late-stage T/J/URL repair, recover existing title fingerprints from the current final-confirmed source workbook by exact D only when the task is explicitly a repair or the user says to keep titles.
   - Do not change unrequested columns. If helper/status columns such as X/AC require updates for the shop workflow, validate them against the current shop rule and list the exact rows changed.

8. **Validate**
   - Run the checklist in `references/workbook-contract.md`.
   - Produce a machine-readable JSON report and a human-readable summary.
   - If T1 product-identification badges/callouts are required for the batch, require
     exact-D badge evidence from source image through rendered local image, visual
     approval, uploaded OSS URL, and final T1/U writeback. A complete T1 manifest,
     `U == T1`, or T4 correctness does not prove that a badge exists.
   - Keep T1 badge approval separate from J badge approval. L043 J quantity labels
     must never satisfy a T1 `THIS IS THE PRODUCT` badge requirement.
   - Do not describe an ad-hoc report as release PASS. Official PASS requires every
     required evidence record to be PASS plus a release certificate; UNKNOWN, CHECK,
     missing certificate, or absent badge evidence is BLOCKED.

9. **Repair workbook image URLs when upload errors mention images**
   - If Temu/Xuanxshop upload errors mention empty image links, carousel image URL, SKC preview image URL, image upload timeout, 404, or an OSS URL that does not respond, do not repair only the single D or URL named in the error.
   - Run a workbook-wide scan for every `ozonshanghai.oss-cn-shanghai.aliyuncs.com` URL in every cell.
   - Treat OSS URLs with no image extension as suspicious/truncated. Resolve them by OSS metadata and bucket prefix lookup only when the current key prefix uniquely matches one image object (`.jpg`, `.jpeg`, `.png`, `.webp`).
   - Percent-encode final image URLs that contain Chinese characters, spaces, parentheses, or other unsafe path characters before delivery. Raw Excel strings such as `尺寸图 (8).jpg` may exist in the sheet but fail marketplace/browser display unless encoded.
   - Do not guess between multiple prefix matches. Put ambiguous or missing matches into an unresolved report and stop before delivery.
   - After replacements, rescan the output workbook. Delivery requires zero unresolved suspicious OSS URLs and zero post-scan bad URLs.
   - Do not rely only on D/effective-row validation for upload-ready sheets. Some shop upload/export tables can have blank `产品货号`; still scan every cell in the workbook and report total URL occurrences, unsafe URL occurrences, and unsafe cells.
   - Old `.xls` or 50-column upload workbooks must be converted/copied to the current 54-column template shape, including tail columns `SKCID`, `SKUID`, `创建时间`, and `更新时间`.
   - Delete or clearly retire earlier narrow repair outputs when a full repair supersedes them, so users do not accidentally upload stale bad copies.

## Non-Negotiable Rules

- User feedback beats historical approved state. If the user says a D/image/PNG is wrong, similar, hallucinated, or “不要”, lock it out before rerunning.
- New workbook T images must not bypass image2/APIMart first pass. Seedream/Jimeng is only the fallback for reviewed image2 failures unless the user explicitly overrides the model order.
- APIMart image2 cost lock: Temu bulk image2 generation must use exactly `gpt-image-2` with `resolution: "1k"` by default. Any expensive official/unofficial model variant is forbidden, and `2k`/`4k` resolution is forbidden unless the user explicitly approves the higher cost for that run. Scripts, plans, and generated records must not retain or reuse unauthorized high-cost settings. Add runtime guards before every APIMart call.
- Reviewed image2 `redo` items are failures for final writeback. They must enter feedback lock first, then go to Seedream/Jimeng fallback or a specific redo plan; do not write those image2 outputs back to T/U.
- Future image generation, reconstruction, Seedream fallback, or image2 redo must pass Claude Code + NVIDIA review before execution. The review package must include GitHub memory evidence, redo/fallback D list with Chinese feedback, source PNG allocation, scene/color/composition plan, and high-risk product locks.
- Claude/NVIDIA scene review must explicitly check product-specific scene reasoning, not just whether there are many prompts. The review must answer whether each active `L0xx` has the correct scene breadth for its real use envelope, and whether broader multi-scene variation is justified or should be constrained.
- Final delivery is also gated. Before saying a Temu workbook, image batch, plugin fix, or upload-ready sheet is complete, create a Claude Code + NVIDIA final review file, then run `scripts\require_claude_nvidia_review.ps1` against the review file and the exact output artifact path. Missing review, non-pass decision, or a review that does not mention the artifact path blocks delivery.
- Claude/NVIDIA review prompts must not narrow a broad workbook request into "T-only" unless the user explicitly scoped it that way. For broad workbook outputs, the prompt must include title, J, T, U, T4, feedback locks, URL safety, changed-cell diff, and review-page evidence. A final gate that only checks "J non-empty" is insufficient and must be treated as a failed gate.
- J rebuild provenance is mandatory. A workbook cannot be delivered if the J audit only proves non-empty URLs; it must prove row-level `G` + `SKU货号` matching and list the actual PNG source path used for each row. Unknown source roots, missing `sku_source`, or silent fallback across old/new SKU libraries block delivery.
- New workbook delivery must always execute the current J rules to completion: L042 final cutout source rule, L043 quantity overlay rule, L086 beige/wood mapping and no-white rule, row-level manifest, review page, SKC preview sync, and cell diff validation. A workbook generated with new T images but stale or unverified J values is not deliverable.
- T fourth image is a hard size-image slot. If a delete/reject removes the current fourth image, find another valid size image and force it back to T[4]. If none exists, do not deliver a final workbook.
- T must contain at most 10 URLs after all deletes, T1 replacements, and T4 repairs.
- Reconstructed titles must stay same-D consistent and keep the deterministic per-file/per-D tracking code. When creating a final writeback from a source/final-confirmed workbook, recover titles by exact D from that workbook so the original tracking code is preserved.
- Title handling must match task mode. A complete/new/redo workbook must have an explicit title reconstruction step and title diff/fingerprint report. Preserving old titles is allowed only for explicit late-stage repair/writeback or when the user says titles must remain unchanged; in that case the delivery must state that title differentiation is intentionally zero.
- A workbook that only changes T/U while preserving both title and J is not a complete "redo workbook"; it is only a T/U repair or T-first replacement artifact.
- Preserve row identity and unrequested cells. D, G, SKU, row order, variant rows, formulas, and shop helper columns must not drift during T/J/U/title writeback.
- True interleave mode is different from append/refill mode. When the user asks to insert new D groups throughout existing `L0xx + date` sections, form the full old+new ordered union first and recompute final suffixes for every group. Do not preserve old D values by default or only assign identifiers to the new groups. An old D may remain unchanged only when its recomputed ordinal is identical. Apply the resulting `source_D -> final_D` mapping to all physical rows and all D-dependent display/JSON/registry fields, and audit the entire union rather than only the inserted subset.
- Deleted/rejected/不要/死刑/wrong-color images must not return through existing workbook values, approved registries, or source folders.
- Review feedback export must read live DOM/input/textarea values so Chinese comments are preserved even when localStorage or POST saving fails.
- Review feedback export must never destroy the review page. Export buttons must not navigate the current tab, replace the page with JSON, or rely on popup-only previews. Every review page must keep the original cards and user selections available after export and must support DOM-based recovery if download/clipboard fails.
- L042 J special rule: use first-level `黑色` and `绿色` source folders only, match by row `G` + `SKU货号`, reject visually mixed source files, and compose true five-cell grid previews from whole SKU size-chart images unless the user explicitly asks for cutouts.
- L042 T hard rule: the black spiral stakes/nails must keep the original short spiral stake shape and correct quantity feeling. Do not generate long straight pins, fence rods, loose black sticks, outward-facing spikes, or decorative bars. Prefer wide garden-border expanded scenes or fixed-PNG compositing over product redraw when image2 changes the stakes or perforated edging tabs.
- L082 hard T rule: preserve the left-right expandable product function. The product side must not contain hallucinated slide rails, extra tracks, drawer rails, or bottom/side rail hardware; any such candidate is a redo/reject and cannot enter T/U.
- L083 hard T rule: appearance drift is common. Preserve overall proportion, side straight rods, surface metal plate/sheet details, supports, connectors, frame geometry, and visible hardware; prefer fixed-PNG compositing or strict product-reference generation for redo.
- L086 hard material rule: this product group has no white variant. Remove and lock out all white product sources, white product material records, and generated white-product outputs from T/J/candidate/writeback workflows. Later approved registries or workbook values cannot resurrect white L086 images. Do not rely only on path text such as `white`/`白`; if user visual review marks a PNG as white or wrong-color, add that exact source path/source_id to the material rejectlist and feedback lock before any rerun. For J/variant matching, `米杏色`/`杏色` must map to the original wood/walnut source such as `胡桃原木/原色.png`; never fall back to black when beige tokens do not directly match a folder name.
- L095 hard scene rule: hanging/planting basket outputs must rotate balcony, patio, greenhouse, terrace, courtyard wall, porch, raised-bed, garden workbench, and herb-garden scenes. A batch where L095 images share the same generic green garden background or close-up planter composition fails scene differentiation even if the source PNG changes.
- L095 J hard count rule: `2格/2联/2个` and `3格/3联/3个` are visual claims, never nonvisual-G cases. `L095-00` must use the visually confirmed `...\\L095\\sku文件_最终抠图PNG\\2\\2.png` source and `L095-01` must use `...\\L095\\sku文件_最终抠图PNG\\3\\3.png`; a same-D, same-SKU, unique-source, filename, or non-empty-J fallback is forbidden. The release gate must show both sibling rows and their source images side by side, and must reject any count-source mismatch even when SKC preview JSON synchronizes to the wrong J.
- L091 hard T rule: top structure/groove/grid pattern is the failure point. Avoid angle changes, keep strict front-facing or slight perspective, freeze the exact top structure and upper edge, and reject any output that adds/removes/changes top parts. Do not use low-resolution scene screenshots, black-padded images, candles/aromatherapy/contents-heavy references, or sources where the top groove is only partly visible as direct image2 references; they encourage top-structure hallucination. Use a clear product-only reference or fixed-PNG compositing for L091 redos.
- L096 hard T scene rule: folding portable barbecue grill is an outdoor ground/floor-use product. It must stand on its own legs on grass, campsite ground, gravel, patio pavers, courtyard floor, deck boards, terrace floor, or another heat-safe outdoor ground/floor surface. Do not place it on a kitchen counter, indoor surface, ordinary table, picnic table, patio table, balcony table, camp table, workbench, sideboard, shelf, cabinet, or cart as the support. Acceptable scenes include wild camping, lawn picnic, Western family/friends backyard gathering, courtyard/patio outdoor meal prep, RV campsite, garden party, park picnic, terrace/deck floor, and open-air family outdoor dining; props/people may stay in the background and must not touch/block/merge with the product. Prompts should broaden reasonable outdoor usage scenarios, not collapse into one tabletop direction. Because this is a grill, loose contents on/near the grate can be replaced with safe unbranded outdoor-cooking props such as unlit skewers, vegetables, grill tools, folded foil, or picnic prep items, but the grill body, legs, grate/frame, hinges, panels, supports, and silhouette are fixed hardware and must not change. Avoid visible flame, smoke, lit charcoal, alcohol, branded packaging, and unsafe cooking action.
- Do not let a previous round’s approved registry skip a D that appears in the current redo list.
- Never write into the only source workbook. Always copy first.
- Image URL upload fixes must be workbook-wide. Do not deliver a sheet after only fixing one reported D, one T4 URL, or one known bad OSS prefix; full scan and post-scan report are mandatory.
- T4 display fixes must validate the raw workbook line, not a whitespace-splitting regex token. A size-image URL with Chinese text or spaces must be percent-encoded and then HEAD/GET checked before delivery.
- URL display fixes must include a whole-workbook unsafe URL scan after writing the output. `unsafe_url_occurrences_after` must be `0`; a D-based validator returning zero effective rows is not proof that an upload sheet is safe.
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
- Cell-level diff summary for all changed columns, with unchanged protected columns explicitly checked.
