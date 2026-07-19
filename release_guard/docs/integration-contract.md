# Production integration contract

This is the finite handoff contract for existing conversational Temu workflows.
The existing generator may remain responsible for workbook/image work; it must
call these boundaries in order.

## Required sequence

1. `init(batch_id, immutable_input_workbook)` creates the freeze.
2. `ConversationAdapter.record_suggestion(...)` records the chat message hash and structured scope.
3. The operator explicitly confirms with `CONFIRM <proposal_id>`.
4. `execute_confirmed(...)` runs the existing generator and writes an execution receipt.
5. The workflow writes the T1/angle human approvals, row-level J manifest, 54-column audit, negative-lock audit, and re-import diff.
6. `require_release(...)` is the only permitted final-workbook handoff.
7. `require_index_registration(...)` is the only permitted plugin-index handoff.

## Prohibited shortcuts

- A chat sentence is not an approval.
- A non-empty J/T/U value is not evidence.
- A synchronized AC value is not visual proof.
- A successful generator exit code is not a release decision.
- A certificate copied from another batch is invalid.
- Existing registry state cannot replace current-batch evidence.

## Integration ownership

The business workflow owns image generation, workbook writeback, OSS upload,
and review UI. Release Guard owns the immutable freeze, evidence hashes,
state decision, certificate, and plugin-facing validation. The current 398
workbook is intentionally outside this contract's write scope.
