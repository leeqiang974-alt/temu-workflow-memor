# Evidence contract

## Universal evidence

- Frozen candidate workbook hash and frozen policy hash.
- Confirmed task scope and execution receipt.
- Re-imported workbook integrity audit.
- Changed-cell diff: allowed changes, dependency closure and protected zero-drift.
- Negative/rejection locks.
- Category/product-attribute audit.
- URL/OSS and 店小秘 upload-compatibility audit when applicable.

## Conditional evidence

- `j_audit`: every physical row with D, G, SKU, inspected source, generated/local J, durable URL, SKC preview equality and visual decision.
- `t1_approval`: every exact D candidate and human decision.
- `badge_approval`: qualitative human approval of final badge placement/style.
- `badge_coverage_audit`: every exact D with source hash, final badged hash, required label/status, human approval reference, OSS URL and workbook T1/U linkage.
- Price audit: all used SKU codes resolved from supplied source table and exact multiplier/rounding.
- Title/fingerprint audit: same-D consistency, cross-D body duplication, trailing code shape, global registry collision/ambiguity.
- Special-L0xx sentinels from current project policy.

## Evidence integrity

Every evidence file and every approved asset is hashed. Evaluation must recheck current bytes. Evidence produced for another workbook hash, another policy hash, another D mapping, or another batch is invalid.

## Certificate

The certificate binds batch ID, final workbook path/hash, frozen source/policy hashes, evidence states and issue time. Upload and registry adapters must revalidate it immediately before acting.

