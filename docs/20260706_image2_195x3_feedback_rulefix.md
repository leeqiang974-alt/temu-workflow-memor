# 2026-07-06 image2 195x3 feedback rulefix

Context:

- Batch: `store_newskill_image2_195x3_t_candidates_20260705`
- Review page: `0616_2_image2_195x3_t_candidates_decision_review`
- User feedback exported at `2026-07-06T01:58:44.021Z`

Findings:

- L042 was not using a single PNG, but image2 still redrew the edging/stakes. The prompt did not strongly preserve black spiral stakes and still allowed tight product redraw.
- L043 used multiple source PNGs, but scenes and product compositions remained too similar and image2 frequently changed board structure.
- L063 and L082 had limited but non-zero source pools; prompt-level expansion was too generic.
- L086 white-product contamination came from visual source feedback, not a filename/path token. The bad source was:
  `kept_0147_0147_L086_NEW_0001_kept.png` / `L086_NEW_0001`.
- L095 scenes were too similar because the previous prompt only asked for generic variation instead of a concrete scene bank.

Locked fixes:

- Added `L086_NEW_0001` to the local material rejectlist after user visual feedback.
- `scripts/run_image2_197x3_t_candidates.py` now filters feedback-locked bad sources before planning.
- The same script now assigns concrete expanded-scene lanes from 20-scene banks for high-risk prefixes including L042, L043, L047, L063, L082, L086, and L095.
- Preflight now fails if any active custom or default expanded-scene bank has fewer than 20 concrete prompts.
- Prompt append no longer relies on vague text such as "different scene mood"; it injects the concrete expanded scene directive.
- Skills now require 20 concrete expanded-scene prompts per L0xx before bulk generation when expansion/differentiation is requested.

Verification:

- Plan-only output: `store_newskill_image2_195x3_t_candidates_rulefix_plan_20260706`
- Target candidates: 585
- Missing source: 0
- L086 bad source hits after fix: 0
- Placeholder/old generic scene hits after fix: 0
- Focus prefixes L042, L043, L063, L082, L086, and L095 all have concrete expanded-scene lanes, with 20-prompt banks after the follow-up rule change.
