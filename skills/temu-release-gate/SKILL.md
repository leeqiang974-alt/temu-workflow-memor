---
name: temu-release-gate
description: Independent top-level audit and hard-stop workflow for Temu/店小秘/Xuanxshop workbooks and image batches. Use whenever a candidate is described as final, complete, upload-ready, submit-ready, OSS-ready, approved, certified, or ready to replace a registry workbook, and after any broad workbook rebuild. It independently recomputes evidence from the exact final workbook and blocks writeback, upload, delivery, or registry use when any required structural, linkage, visual, badge, URL, category, diff, or human-review evidence is missing.
---

# Temu Release Gate

This skill is the independent **inspection and shutdown authority**. It does not generate images, modify product content, repair cells, upload assets, or approve its own evidence.

The construction workflow may submit evidence, but cannot declare PASS. The gate reads the exact candidate again, recomputes checks, records immutable evidence hashes, and issues a certificate only when every required evidence item is PASS.

## Non-bypassable boundary

- Generator success, non-empty cells, URL equality, same-D inheritance, file/folder names, and an ad-hoc “audit passed” report are not release proof.
- Human approval and machine integrity are separate evidence classes; neither substitutes for the other.
- Candidate T1 approval and final badge completion are separate stages.
- `UNKNOWN`, `CHECK`, missing evidence, stale evidence, changed hashes, or missing certificate means `BLOCK`.
- A later workbook change invalidates evidence tied to the earlier hash.
- Registry replacement requires a current certificate for the exact workbook bytes.

## Gate order

1. Freeze exact candidate path, SHA-256, policy SHA-256, mode, scope and source lineage.
2. Validate scope/diff: allowed changes are complete; protected cells have zero drift; candidate is re-imported.
3. Validate workbook structure and field linkage independently.
4. Validate semantic/reference evidence: category attributes, price source, title fingerprint registry, special L0xx sentinels.
5. Validate row-level J positive lineage and human visual decisions.
6. Validate exact-D T1 reference/candidate decisions and negative locks.
7. If badges are required, validate the full chain for every exact D: approved unbadged source → final badged local hash → human badge approval → durable OSS URL → workbook T1/U equality.
8. Validate all image URLs, T count, U=T1, protected T4, 店小秘 upload fields and OSS durability.
9. Re-evaluate every evidence source hash, issue the release certificate, and only then permit delivery/upload/registry handoff.

Read [evidence contract](references/evidence-contract.md) and [status language](references/status-language.md).

## Machine implementation

Use the project `release_guard` package. Its policy file is the only required-evidence list; code must read it dynamically. Use append-only evidence history and never edit a prior PASS record in place.

Typical boundary:

```powershell
python -m release_guard.cli --root <guard-root> init <batch-id> <candidate.xlsx>
python -m release_guard.cli --root <guard-root> status <batch-id>
python -m release_guard.cli --root <guard-root> certify <batch-id> <candidate.xlsx>
```

Evidence commands and schemas are documented in the project `release_guard/docs/` directory. The audit system must remain separate from workbook writers and OSS uploaders.

## Required independent outputs

- Gate status with reasons for every missing/non-PASS item.
- Evidence ledger containing exact source paths and hashes.
- Full blocker list by D/row/cell, not only counts.
- Release certificate for the exact final workbook hash, or an explicit BLOCK result.
- Registry handoff record only after certificate revalidation.

## Special rule: visual evidence

Every physical J row and every exact-D final T1 requiring human judgment must have an explicit decision. “Batch approve current page” is a valid human action only when the review UI records each visible D as an individual decision; it cannot approve records outside that page. Rejected and unreviewed items remain blockers.

## Special rule: badge coverage

Do not infer a badge from filename, OSS prefix, prompt, URL, or a few samples. Exact-D coverage, local hashes, required label/style decision, human approval, durable URL and workbook linkage are mandatory. One missing D blocks the entire final release.

