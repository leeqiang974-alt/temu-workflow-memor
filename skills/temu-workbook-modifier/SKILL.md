---
name: temu-workbook-modifier
description: Top-level modification workflow for Temu/店小秘/Xuanxshop Excel workbooks. Use whenever a user supplies a Temu product workbook and asks to inspect, repair, rebuild, differentiate, rekey D values, change titles/descriptions/prices/categories/attributes/J/T/U/SKC/SKU fields, prepare an upload copy, or make a final submission workbook. Declares task mode and change scope first, applies exact-D and row-variant linkage rules, creates review evidence, and hands the candidate to the independent release gate; it never self-certifies.
---

# Temu Workbook Modifier

This is the top-level **construction guide**. It decides what must be changed and how linked fields move together. It never decides that its own output is upload-ready.

Always read the project `AGENTS.md` before acting. Then use the smallest relevant installed domain skills for image generation, T1 reference editing, OSS, or browser work.

## Mandatory start

1. Preserve the supplied workbook. Make a new candidate copy.
2. Inspect all sheets and resolve columns by normalized header names, never fixed letters alone.
3. Build a baseline manifest: source path/SHA-256, sheet/header count, physical row count, exact-D count, D-to-row map, active L0xx families, image delimiters, JSON columns, and existing formulas/styles.
4. Declare one task mode and an explicit changed/protected-column scope before writing.
5. If the user asks for a new/redo/final/full workbook, default to `full-rebuild`; never silently narrow it to T-only or one-column repair.

Read [task modes and scope](references/task-modes.md) for the declaration contract.

## Construction sequence

1. **Model identity**: exact `D` is the product group; each physical row is a variant identity `D + G + SKU货号`.
2. **Plan dependencies**: expand every requested field into its linked-field closure before editing. Read [linked fields](references/linked-fields.md).
3. **Resolve authority**: record the source/reference for every changed fact. Folder names, non-empty URLs, same-L0xx values, and synchronized JSON are not visual or semantic proof.
4. **Transform once**: apply a deterministic source-to-candidate mapping. Never run broad text replacement across JSON.
5. **Re-import and compare**: verify actual saved values, formulas/styles, allowed changes, protected zero-drift, and same-D consistency.
6. **Create review artifacts**: image or high-risk semantic changes require exact-D/row review evidence and machine-readable decisions.
7. **Hand off**: produce candidate workbook + scope declaration + source-to-output manifest + changed-cell diff + review records. Invoke `$temu-release-gate` independently for any claim involving final, upload, submit, OSS writeback, or registry replacement.

## Core invariants

- Same exact D must have one group-level title, description, T carousel, U, category/product attributes, and other declared group fields.
- J is row-level and requires exact positive lineage for `D + G + SKU`; `SKC属性.previewImgUrls` must equal that row's J, but equality alone is not visual proof.
- D changes require parsed updates to every D-dependent display/JSON/registry field declared by policy. Preserve historical extCode only for an explicitly identified already-uploaded-record mode.
- G is a real variant fact. Preserve color/count/size/material/set semantics; do not turn it into scene marketing text. When G changes, update E, SKU spec JSON and J/SKC linkage together.
- T parsers split both commas and CR/LF. T has at most 10 URLs; U equals T1; protected T4 remains the size-image slot.
- Category ID and product-attribute `templatePid` must come from certified reference evidence or the category registry, never a guessed neighboring L0xx. A non-empty product-attribute JSON must contain at least one `templatePid`; empty lists are invalid unless the certified category policy explicitly allows attribute-free products.
- Product descriptions may contain valid rich HTML/image URLs. Do not rewrite them merely because they are not plain Chinese text.
- 店小秘 upload copies keep the current header structure but clear `来源url`, `所属店铺`, `创建时间`, and `更新时间` data cells.
- X `外包装图片` uses the workbook's own universal majority OSS package image. Do not hard-code a historical batch URL or retain `kwcdn`.
- Price changes require an explicit SKU/source-price map and multiplier/rounding rule; audit every physical row after re-import.
- Titles/fingerprints follow the current batch mode and global registry. Same-D title must match; different D title bodies cannot be generic duplicates disguised by fingerprints.
- Never overwrite the only source workbook; never write temporary provider URLs or local paths into final cells.

Read [workbook contract](references/workbook-contract.md) for the complete field and batch rules. Read [project memory map](references/project-memory-map.md) to route special L0xx, image, plugin, and historical rules without copying stale logic into a new script.

## Image boundary

- Generated images are candidates until human review.
- Current-workbook T1 is the exact-D reference when the active batch declares that contract; T4 or J cannot replace it as scene anchor.
- Paid async work uses a resumable submit → poll → immediate download → decode/dimension → SHA-256 manifest loop and explicit user approval for retries.
- A required `THIS IS THE PRODUCT` inset/badge is a post-approval finalization stage. Unbadged T1 approval does not satisfy badge completion.
- OSS upload and workbook T/U writeback happen only after the independent gate has the required human and coverage evidence.

## Completion language

Call the output **candidate**, **review-ready**, or **technically validated** until `$temu-release-gate` issues a current certificate for the exact final workbook hash. Never call a generator's own audit “release PASS”.

## Required outputs

- Immutable source manifest and task-scope declaration.
- Exact-D / physical-row transformation manifest.
- Candidate workbook copy.
- Re-imported changed-cell diff with allowed and protected changes separated.
- Review HTML/JSON and rejection locks when visual work exists.
- Machine audit reports requested by the release gate.
