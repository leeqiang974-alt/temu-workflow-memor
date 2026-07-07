# 20260707 192 Redo17 V2 Plan After Claude Block

- Created: 2026-07-07T21:04:58
- Refreshed: 2026-07-07T21:07:42
- Feedback lock: `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_full_print_20260707\feedback_lock_20260707_192_interactive_redo17_enriched_v2.json`
- Source allocation: `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_full_print_20260707\redo17_newpng_source_allocation_plan_v2_after_claude_block_20260707.json`
- Scene bank: `C:\Users\Administrator\Documents\temu自动化\scripts\luxury_expanded_scene_banks_0616_2.py`
- Summary: {'feedback_items': 17, 'redo_items': 17, 'prefixes': ['L043', 'L082', 'L085', 'L091', 'L096'], 'new_source_changed_count': 17, 'sku_fallback_count': 0}

## Claude Block Fixes
- excluded same-prefix old_source_id from new source allocation
- created enriched feedback lock with L096 forbidden terms and whitelist
- added L043 audit tags and explicit hole visibility checks
- updated L096 scene prompt to require at least 3 outdoor cues
- reran scene bank validation
- refreshed L096 runtime prompts to use positive outdoor cues instead of repeating indoor/kitchen forbidden terms

## Rules
- L043: L043-AUDIT required. New source not in failed prefix source list. Product 34-40% frame height. Do not mirror, rotate, or redraw. Preserve exact hole count, all large holes, small center hole, rear raised detail, front raised detail, panel seams, material and thin thickness. Clothing nearby but never covering holes.
- L082: Do not mirror, rotate, or flip. Preserve left-right telescoping orientation horizontally and front-facing. No side rails, drawer tracks, or invented hardware.
- L085: Scene must be home repair, wall patching, paint-prep, drop cloth, or utility workbench. Preserve three scraper sizes, metal blades, handles and straight edges.
- L091: Front-facing or very slight perspective only. Product 30-36% frame height. Use closet shelf, vanity shelf, entry cabinet or storage cubby. Preserve top groove/grid, upper edge, drawer face, black handle, white frame.
- L096: superseded by the 2026-07-07 ground/floor-use correction. Every prompt must show a real outdoor use context and the folded portable grill must stand on its own legs on grass, campsite ground, gravel, patio pavers, courtyard floor, deck boards, terrace floor, or another heat-safe outdoor ground/floor surface. Do not support it on tabletop/workbench/cart/counter/shelf/cabinet surfaces. Rotate wild camping, lawn picnic, Western family/friends backyard gathering, courtyard/patio outdoor meal prep, RV campsite, garden party, park picnic, terrace/deck floor, and open-air family outdoor dining scenes.

## Items
- L043060501__set1__redo_newpng2: `L043_NEW_0001` -> `L043_NEW_0004`, source `kept_0023_0023_L043_NEW_0004_kept.png`, risk critical, feedback `不要这个png，重新用别的png来重做`
- L043060502__set1__redo_newpng2: `L043_NEW_0003` -> `L043_NEW_0007`, source `kept_0026_0026_L043_NEW_0007_kept.png`, risk critical, feedback `产品错误，重做`
- L043060503__set1__redo_newpng2: `L043_NEW_0005` -> `L043_NEW_0008`, source `kept_0027_0027_L043_NEW_0008_kept.png`, risk critical, feedback `产品中间有个小孔洞，丢失了`
- L043060504__set1__redo_newpng2: `L043_NEW_0006` -> `L043_NEW_0020`, source `kept_0029_0029_L043_NEW_0020_kept.png`, risk critical, feedback `脑子有病，产品的孔洞数量不对`
- L043060506__set1__redo_newpng2: `L043_NEW_0011` -> `L043_NEW_0025`, source `kept_0030_0030_L043_NEW_0025_kept.png`, risk critical, feedback ``
- L043060508__set1__redo_newpng2: `L043_NEW_0030` -> `L043_NEW_0033`, source `kept_0032_0032_L043_NEW_0033_kept.png`, risk critical, feedback `产品外观严重错误`
- L082060504__set1__redo_newpng2: `L082_NEW_0011` -> `L082_NEW_0009`, source `kept_0143_0143_L082_NEW_0009_kept.png`, risk high, feedback `产品的方向错了`
- L082060506__set1__redo_newpng2: `L082_NEW_0002` -> `L082_NEW_0010`, source `kept_0144_0144_L082_NEW_0010_kept.png`, risk high, feedback ``
- L082060507__set1__redo_newpng2: `L082_NEW_0006` -> `L082_NEW_0012`, source `kept_0146_0146_L082_NEW_0012_kept.png`, risk high, feedback `产品的方向错了`
- L085060503__set1__redo_newpng2: `L085_T_0032` -> `L085_T_0001`, source `kept_0157_0157_L085_T_0001_kept.png`, risk high, feedback `场景错误`
- L085060505__set1__redo_newpng2: `L085_T_0009` -> `L085_T_0010`, source `kept_0159_0159_L085_T_0010_kept.png`, risk high, feedback `场景错误`
- L091060502__set1__redo_newpng2: `L091_T_0015` -> `L091_T_0002`, source `kept_0182_0182_L091_T_0002_kept.png`, risk high, feedback `产品在场景中的比例不对，不符合产品的使用场景`
- L096060501__set1__redo_newpng2: `L096_T_0001` -> `L096_RAW_CLEAN_01`, source `L096_RAW_CLEAN_01.png`, risk critical, feedback ``
- L096060502__set1__redo_newpng2: `L096_T_0006` -> `L096_RAW_CLEAN_02`, source `L096_RAW_CLEAN_02.png`, risk critical, feedback ``
- L096060504__set1__redo_newpng2: `L096_T_0013` -> `L096_RAW_CLEAN_03`, source `L096_RAW_CLEAN_03.png`, risk critical, feedback ``
- L096060505__set1__redo_newpng2: `L096_T_0020` -> `L096_RAW_CLEAN_04`, source `L096_RAW_CLEAN_04.png`, risk critical, feedback ``
- L096060506__set1__redo_newpng2: `L096_T_0001` -> `L096_RAW_CLEAN_05`, source `L096_RAW_CLEAN_05.png`, risk critical, feedback ``
