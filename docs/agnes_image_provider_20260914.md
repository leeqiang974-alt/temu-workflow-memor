# Agnes Image Provider Integration (2026-09-14)

## What changed

- Added a secret-safe Agnes image client at `scripts/agnes_image_client.py`.
- Added the YeahF 1999D remaining-23 redo runner at
  `scripts/run_yeahf_1999d_t1_failed23_agnes_20260914.py`.
- Added a same-origin four-image comparison page builder at
  `scripts/build_yeahf_1999d_agnes23_review_20260914.py`.

## Provider contract

- International endpoint: `https://apihub.agnes-ai.com/v1/images/generations`
- Model: `agnes-image-2.5-flash`
- Temu defaults: `size=1K`, `ratio=1:1`
- Image references are sent in `extra_body.image`.
- Image output uses `extra_body.response_format=b64_json`; if the provider returns
  a URL instead, the client downloads it immediately.
- Local key file: `D:\Desktop\api\agnes爱思.txt`. Never print or commit its value.

Official references:

- <https://wiki.agnes-ai.com/en/docs/agnes-image-25-flash.md>
- <https://wiki.agnes-ai.com/en/docs/pricing.md>

## Why

The prior Cangyuan run left 23 provider-level failures. Agnes currently provides
a separate high-quota image-editing channel and supports two-image composition.
The integration preserves the existing 1999D redo contract instead of inventing
a new source strategy.

## Temu safety contract

1. Image 1 is the exact current-workbook T1 and supplies scene/composition only.
2. Image 2 is the exact-D product material and is authoritative for appearance.
3. A human-rejected candidate is negative evidence and must never be submitted.
4. Hash-check both references and the rejected evidence before every request.
5. Run one end-to-end smoke image before a batch larger than five.
6. Keep no more than four Agnes requests in flight for this runner.
7. Provider success is incomplete until the image is decoded, dimension-checked,
   normalized to PNG, saved locally, hashed, and recorded in the manifest.
8. Generation is not approval. Do not apply badges, upload to OSS, or write T/U
   until human review passes.

## Verification

```powershell
python scripts\run_yeahf_1999d_t1_failed23_agnes_20260914.py --preflight
python scripts\run_yeahf_1999d_t1_failed23_agnes_20260914.py --run --workers 4
python scripts\build_yeahf_1999d_agnes23_review_20260914.py
```

The 2026-09-14 run reconciled as `23 submitted -> 23 validated local -> 0 failed`.
The generated candidates were subsequently human-reviewed and rejected `23/23`.

## Human-review correction

The first Agnes batch preserved product appearance reasonably well, but failed the
differentiation objective: scenes, people, camera angle, foreground/background layers,
and depth relationships stayed too close to the old T1. The prompt itself caused much
of this by simultaneously preserving composition/camera/person logic and allowing only
a small crop or safe scene change.

`L082080805` is a permanent product-fusion sentinel. The full old T1 contained a white
pull-out shelf while the exact-D material showed a dark shelf. Agnes rendered both
products together despite role wording. Never rely on prompt-only `scene image` role
separation when references contain conflicting product appearances.

For the next diagnostic:

1. Put the exact-D product image first.
2. Require a measurably new person, setting, camera lane, product position/scale, and
   foreground/midground/background structure.
3. Preserve only equivalent use/task logic, not the original composition or person.
4. If the old T1 product conflicts with exact-D material, do not submit that full T1;
   use a verified scene-only derivative or product-only generation with textual scene
   guidance.
5. Test one non-conflicting D and one conflicting D before any bulk retry.

## V2 product-only redo result

The second 23-D diagnostic used only one submitted image reference per request: the
visually verified exact-D product material. The current-workbook T1 and both earlier
rejected candidates remained hash-recorded evidence, but were not sent to Agnes. The
old T1's useful function was translated into text while every D received an explicit
new setting, person, camera lane, product position, and foreground/midground/background
recipe.

Artifacts:

- Plan builder: `scripts/build_yeahf_1999d_agnes_v2_redo23_plan_20260914.py`
- Runner: `scripts/run_yeahf_1999d_agnes_v2_redo23_20260914.py`
- Review builder: `scripts/build_yeahf_1999d_agnes_v2_review_20260914.py`
- Quiet local server: `scripts/serve_review_quiet.py`

The run reconciled as `23 selected -> 23 validated local -> 0 failed`. All candidates
are still review-only: they have no final badge, no OSS upload, and no workbook
writeback. The review page exposes original T1, exact-D product, rejected V1, and V2
side by side and must show 23 cards / 92 successfully decoded images.

## Concurrency finding

Agnes queue capacity is dynamic and provider-wide. On 2026-09-14:

- eight concurrent requests caused ten HTTP 503 `image queue is full` responses;
- an immediate retry at four workers remained unstable after the saturation event;
- after a 60-second cooldown, two workers completed all eight remaining requests.

Use `--workers 2` as the safe default for this batch. Four workers may be tried only
when the queue is clearly free and with bounded retry/cooldown. Do not use eight as the
default, and do not classify queue-full 503 responses as prompt or product failures.

## V3 four-image correction

Human review approved the V2 direction overall and rejected four exact candidates:

- `L077080826`: product scale/proportion was implausible;
- `L081080846`: an extra stand appeared and the product extended beyond its table;
- `L081080910`: product appearance changed and the frame appeared suspended;
- `L083080809`: the desktop organiser was suspended instead of resting on a surface.

The four V2 files were added to immutable negative evidence and excluded from every V3
request. V3 again submitted only the exact-D product material, but additionally locked
intrinsic proportions, frame occupancy, all-feet/base surface contact, contact shadows,
support-surface boundaries, and no-extra-support rules. Its cast schedule deliberately
rotated a woman in her twenties, a man in his thirties, a woman in her forties, and one
no-person scene so elderly people did not dominate the batch.

The V3 run completed `4 selected -> 4 validated local -> 0 failed`. One item encountered
queue-full 503 responses and succeeded after cooldown at one worker. These candidates
remain blocked from badge, OSS and workbook writeback until the new four-image review is
human-approved.
