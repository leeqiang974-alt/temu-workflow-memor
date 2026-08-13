# Status language

Use these terms precisely:

- `candidate`: modified output; no release claim.
- `review-ready`: review page/assets are complete enough for human decisions.
- `technically validated`: stated machine checks passed; visual and release evidence may still be missing.
- `human-approved`: specified review decisions exist; does not imply writeback/URL/structure correctness.
- `BLOCK`: at least one required evidence item is missing, stale, CHECK, UNKNOWN or failed.
- `CERTIFIED`: independent gate passed for the exact final workbook hash.
- `upload-ready` / `submit-ready`: allowed only when the exact deliverable is CERTIFIED and any external adapter revalidation passes.

Never collapse technical lineage, JSON synchronization, visual review and final certificate into one green count.

