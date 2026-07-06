# 2026-07-06 Seedream Fallback From 195x3 Redo JSON45

Context:

- Source review: `0616_2_image2_195x3_redo_json45_20260706_review`
- User feedback export: `C:\Users\Administrator\.codex\attachments\5e987ad8-7e2b-4c27-ba4f-047e3eb03947\pasted-text.txt`
- Output folder: `D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_195x3_redo_json45_feedback_20260706`

Rules applied:

- Only explicit `redo` decisions from the image2 redo_json45 review entered Seedream.
- Explicit `keep` decisions stayed keep and were not rerun.
- Seedream was allowed because these were reviewed image2/APIMart failures.
- Redo prompts kept first-generation restrictions, including Chinese feedback, product locks, safe Temu props, and no workbook writeback.
- Expanded-scene prompt rule was strengthened for this fallback: pulled-back room/garden/cabinet depth, front/mid/background layers, real support surface, and product usually about `14-22%` image height.
- Old `28-42%` product-close prompt ratio was not present.

Target count:

- Total Seedream fallback targets: `13`
- Prefix counts: `L042=1`, `L043=9`, `L081=1`, `L082=1`, `L091=1`

Important locks:

- `L043_NEW_0008` was discarded because user feedback said `产品外观错误，丢弃这个png`.
- `L043_NEW_0008` was added to the local material rejectlist and was not selected in the Seedream source plan.
- L042 prompt locks short black spiral stakes/nails and blocks long pins, fence rods, loose sticks, decorative bars, and separated fence-like stakes.
- L043 prompt locks board outline, holes, small center hole, rear raised detail, panel seams, thickness, and realistic scale.
- L082 prompt locks left-right expandable function and blocks side rails, drawer rails, bottom tracks, and metal runners.
- L091 prompt locks front-facing top groove/grid/top structure.

Claude/NVIDIA gates:

- Initial path-only and long self-contained prompts were blocked or unusable; the final compact gate passed.
- Pre-run gate: `D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_195x3_redo_json45_feedback_20260706\claude_nvidia_seedream_195x3_redo_json45_review_v6_20260706.md`
- Local gate command passed with `artifact_count=3`.

Execution:

- Script: `scripts\run_seedream_195x3_redo_json45_from_feedback.py`
- Results: `D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_195x3_redo_json45_feedback_20260706\seedream_fallback_results.json`
- Review HTML: `D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_195x3_redo_json45_feedback_20260706\0616_2_seedream_from_195x3_redo_json45_feedback_13_review.html`

Verification:

- Results total: `13`
- OK: `13`
- Errors: `0`
- Missing result files: `0`
- Review HTML image tags: `39`
- Non-empty image src: `39`
- Missing HTML image files: `0`

This batch is only a local review artifact. It is not approved for workbook writeback until the user reviews and exports decisions from the review page.
