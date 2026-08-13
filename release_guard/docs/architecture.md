# Release Guard contract

## State machine

`UNKNOWN` is the initial state for a new batch. Each evidence record is independently `UNKNOWN`, `CHECK`, `BLOCK`, or `PASS`. The batch profile is frozen at initialization; required evidence is read dynamically from `policy/v1.json`. A certifiable batch becomes `PASS` only when every profile-required record is `PASS`, the frozen input workbook and policy hashes are unchanged, and approved image hashes still match. `audit-only` is intentionally non-certifiable. Any missing, stale, malformed, or conflicting evidence makes the batch `BLOCK`.

```
init/freeze -> evidence attestations -> evaluate -> certify -> validate_for_index
     |              any non-PASS              |             |
     +--------------------> BLOCK <------------+-------------+
```

## Evidence contracts

- `t1_approval` and `badge_approval`: `decision=APPROVED`, human `approver`, batch and policy hashes, and a non-empty `asset_paths` map of local asset path to SHA-256.
- `badge_coverage_audit`: exact workbook-D coverage with one final badged local asset and SHA-256 per D; `badge_status=applied` and the required label must be explicit. A generic badge approval or URL path does not satisfy coverage.
- `j_audit`: `physical_rows` plus one row record for every physical row. Each record contains exact `D`, `G`, `SKU`, `source_path`, `generated_asset`, `oss_url`, and `AC_previewImgUrls`; AC must equal the written OSS URL. L095-00 and L095-01 source suffixes are hard-coded policy sentinels.
- `cell_audit`: `column_count=54`, and every listed cell has `status=PASS`.
- `negative_locks`: machine-readable active locks; a lock with `appears_in_output=true` blocks.
- `writeback_diff`: `reimport_verified=true`, no protected-cell changes, and no failures.

Profiles split `audit-only`, `targeted-repair`, `full-rebuild`, `upload-finalization`, and `already-uploaded-record-repair`; they prevent a one-field repair from requiring irrelevant paid-image evidence while keeping broad rebuilds under full visual/badge gates. The SQLite database is the durable state ledger. JSON records under `batches/<batch_id>/` are evidence snapshots for independent review. The release certificate records both the frozen input hash and the exact final output hash. The plugin-facing adapter rechecks the certificate, current state, policy hash, frozen hash, output existence, and output hash immediately before an external index transaction.

## Security boundary

This directory has no OSS uploader, XLSX writer, plugin mutator, or automatic human approval. Those integrations must supply evidence and call the adapter; they must not bypass it. Existing workbooks, images, scripts, and outputs remain outside this implementation's write scope.
