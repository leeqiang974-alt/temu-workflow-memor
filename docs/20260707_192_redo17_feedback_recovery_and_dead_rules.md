# 2026-07-07 192 redo17 feedback recovery and dead rules

## Recovery artifact

- Review page: `http://127.0.0.1:8793/0616_2_image2_192_redo17_v2_review.html`
- Recovery method: read live DOM state from `.card[data-id]`, active `button[data-decision]`, and matching feedback textarea values. Do not press the destructive export button again.
- Saved local lock: `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_redo17_v2_newpng_promptfix_20260707\recovered_feedback_from_dom_20260707.json`
- Recovered count: 17 items, 13 redo, 4 keep.

## Recovered decisions

| candidate | decision | feedback |
|---|---|---|
| `L043060501__set1__redo_newpng2` | redo | 产品严重错误 |
| `L043060502__set1__redo_newpng2` | redo | 产品严重错误 |
| `L043060503__set1__redo_newpng2` | redo | 都说了，不要这个png，删掉这个png，以后彻底不用。找别的素材做。 |
| `L043060504__set1__redo_newpng2` | keep |  |
| `L043060506__set1__redo_newpng2` | keep |  |
| `L043060508__set1__redo_newpng2` | redo | 产品严重错误 |
| `L082060504__set1__redo_newpng2` | redo | 这个明显是上下两层，太ai了 |
| `L082060506__set1__redo_newpng2` | redo | 这个也是上下两层，太ai了 |
| `L082060507__set1__redo_newpng2` | keep |  |
| `L085060503__set1__redo_newpng2` | keep |  |
| `L085060505__set1__redo_newpng2` | redo | 产品错误 |
| `L091060502__set1__redo_newpng2` | redo | 产品顶部结构错误 |
| `L096060501__set1__redo_newpng2` | redo | 场景还是不对 |
| `L096060502__set1__redo_newpng2` | redo | 场景还是不对 |
| `L096060504__set1__redo_newpng2` | redo | 场景还是不对 |
| `L096060505__set1__redo_newpng2` | redo | 场景还是不对 |
| `L096060506__set1__redo_newpng2` | redo | 场景还是不对 |

## Dead rules added

1. Review feedback export must be non-destructive. It must not navigate the current tab, replace the page with JSON, or rely on `window.open()` popup previews. Export must keep the review cards, button states, and typed comments available after export.
2. Future review pages must read live DOM/button/textarea state, download JSON, optionally copy to clipboard, and optionally show an inline preview. If the export fails, DOM recovery remains valid.
3. L043 is a critical high-failure product. Do not continue free-redrawing after repeated structure failures. If feedback says `不要这个png` or `删掉这个png`, lock out that exact `source_png/source_id` and choose a different approved source or fixed-PNG/scene-only compositing.
4. L096 folding portable barbecue grill must stand on its own legs on outdoor ground/floor: grass, campsite ground, gravel, patio pavers, courtyard floor, deck boards, or terrace floor. Do not place it on kitchen counters, indoor surfaces, ordinary tables, picnic tables, patio tables, balcony tables, camp tables, workbenches, carts, shelves, cabinets, or sideboards as the support.
5. L096 scene prompts must broaden realistic outdoor use cases: wild camping, lawn picnic, Western family/friends backyard gathering, courtyard/patio outdoor meal prep, RV campsite, garden party, park picnic, terrace/deck floor, and open-air family outdoor dining.
