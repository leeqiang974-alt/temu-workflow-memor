# Workbook contract

## Identity levels

- Workbook: immutable source hash and one candidate lineage.
- Product group: exact D.
- Physical variant row: row number + D + G + SKU货号.
- Product family: L0xx; useful for routing, never sufficient provenance.

## Baseline checks

- Sheet names, dimensions, normalized headers, formulas/styles and merged/table objects.
- Effective row count and exact-D count.
- Duplicate/blank identifiers and same-D row membership.
- JSON parseability for product, SPU, SKC and SKU fields.
- Image URL delimiter/count/domain/accessibility inventory.
- Existing category/attribute mapping and special batch policies.

## Writeback checks

- Saved file is re-imported.
- Row order/identity preserved unless the declared mode explicitly rebuilds it.
- Changed cells equal the transformation manifest.
- Protected cells have zero drift.
- Same-D group fields are consistent.
- Row-level J/SKC linkage is exact and separately backed by visual lineage.
- T≤10, U=T1, T4 preserved as required size slot.
- Category/product attributes pass certified-reference audit.
- Upload-only fields are empty only in the upload copy.
- Unsafe/truncated image URLs and known forbidden domains are zero.

## Historical/high-risk rules

Read project `AGENTS.md` for current sentinels and batch exceptions. Important examples include L095 2-vs-3 J count lineage, L043 quantity/color, L086 no-white material, L091 top structure, L096 ground-supported outdoor grill, L082 rail hallucination, L083 hardware fidelity, and L058 required functional carousel image. These are release blockers when active, not prompt suggestions.

## Differentiation

Differentiate title body, fingerprint, description text where authorized, T1 scene/composition, and other carousel material without changing product truth. Same-L0xx siblings should vary meaningful non-product dimensions. G may stay the same when it is the same real variant fact; a new D can still differ through title, description, images, scene and product grouping.

