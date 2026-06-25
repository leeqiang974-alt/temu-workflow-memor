# Review Pages, Feedback Locks, And Deletion Lists

## Review Page Design

For large workbooks, do not load all images at once.

Use:

- prefix filter
- D search
- per-D lazy loading
- pagination or collapsible sections
- click-to-zoom images
- delete/reject/restore controls
- exportable JSON feedback list

Show:

- D and prefix
- workbook rows
- title
- variant G
- SKU code
- T image positions
- J row previews
- source PNG/SKU path
- generated output
- prompt/scene/model metadata when AI generated

## Feedback Priority

Persist user feedback as machine-readable JSON:

- `reject_output`: generated image not acceptable, source may still be usable
- `reject_material`: PNG/source image must not be reused
- `redo_first`: T first image must be regenerated
- `too_similar`: regenerate with stronger differentiation
- `wrong_match`: source/variant matching is wrong
- `delete_t_url`: remove a specific T URL
- `delete_j_url`: remove a specific J URL

Priority order:

1. User reject/redo/delete feedback
2. Bad material/source list
3. Current round records
4. Approved registry
5. Existing workbook values

Never let an approved registry override later user feedback.

## Applying Deletes

Do not mutate Excel from browser localStorage alone. Export delete list to JSON, review it, then apply:

- T delete: remove exact URL from every same-D T list if requested.
- J delete: remove or regenerate only affected row URL.
- Preserve T size image unless user explicitly deletes it.
- Revalidate URL count and U after delete.

## Round Workflow

For each round:

1. Save user feedback as a lock JSON.
2. Build a redo plan from feedback.
3. Exclude bad materials.
4. Generate only missing redo tasks.
5. Build review page.
6. Wait for approval before writeback.

If interrupted, resume from records JSON and skip completed OK tasks unless feedback invalidates them.
