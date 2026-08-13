# Task modes and scope declaration

Declare one mode before changing cells. Save it as JSON beside the candidate.

## Modes

### `audit-only`

Read and report. No workbook mutation and no upload-ready claim.

### `targeted-repair`

The user explicitly limits the repair, for example price, X, category/attributes, or T/U. Only declared columns and their dependency closure may change. Every other cell is protected.

### `full-rebuild`

Use for “new workbook”, “redo”, “differentiate”, “rekey all D”, “full modify”, or equivalent broad wording. Scope includes D mapping, title/fingerprint, description, J and row lineage, T1 and non-T1 carousel, U, T4, variant/SKC/SKU linkage, category/attributes, prices when supplied, upload fields, and final review evidence. A preserved field must be explicitly justified and audited.

### `upload-finalization`

Use only after construction and human reviews. Apply approved badge/inset, upload durable assets, write exact OSS URLs into T/U/J/JSON, create 店小秘-compatible copy, run independent release gate, and issue certificate.

### `already-uploaded-record-repair`

Repair an existing marketplace record. Historical SKC extCode or cargo association may be preserved. Never reuse this exception for a not-yet-uploaded workbook.

## Scope JSON

```json
{
  "schema": "temu-workbook-change-scope/v1",
  "mode": "targeted-repair",
  "source_workbook": "D:/path/source.xlsx",
  "source_sha256": "...",
  "candidate_workbook": "D:/path/candidate.xlsx",
  "candidate_sha256": "...",
  "requested_changes": ["申报价格"],
  "linked_changes": [],
  "allowed_changed_headers": ["申报价格"],
  "observed_changed_headers": ["申报价格"],
  "protected_headers": ["* except allowed_changed_headers"],
  "protected_changed": [],
  "linked_failures": [],
  "reimport_verified": true,
  "identity_policy": "preserve row order + D + G + SKU",
  "skc_extcode_policy": "preserve|equals_D|already_uploaded",
  "price_rule": {"source": "D:/path/prices.txt", "multiplier": 2.5},
  "image_policy": null,
  "user_authority": "message/reference"
}
```

The changed-column list is not permission to break linked invariants. If a requested change needs linked changes, expand the scope before editing and state why.
