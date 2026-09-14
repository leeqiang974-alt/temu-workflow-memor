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
The generated candidates remain `pending_human_review`.

