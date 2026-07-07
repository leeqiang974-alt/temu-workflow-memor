# 192 redo17 新 PNG + 场景纠偏执行计划

- 创建时间: 2026-07-07T20:56:24
- GitHub 分支/提交: `codex/l096-outdoor-grill-scene-lock-20260707` / `0785b5a Harden redo scene locks for 192 image batch`
- 反馈锁: `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_full_print_20260707\feedback_lock_20260707_192_interactive_redo17.json`
- PNG 分配: `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_192_full_print_20260707\redo17_newpng_source_allocation_plan.json`
- 场景库: `C:\Users\Administrator\Documents\temu自动化\scripts\luxury_expanded_scene_banks_0616_2.py`
- redo 数: 17；SKU fallback: 0

## 硬规则
- No modification based on the wrong generated image; use a different clean product PNG and avoid the user-described error.
- Before generation, Claude/NVIDIA must review feedback list, source PNG allocation, scene prompts, product locks, and GitHub memory evidence.
- L096 must be clearly outdoor use context only; ban kitchen/counter/sink/cabinet/appliance/pantry/sideboard/cooking-station wording.
- L043 must be treated as high-risk/critical: new PNG, no mirror/rotate/redraw, larger inspection scale, exact holes and small center hole preserved.
- All outputs are candidates only; user review decides keep/redo/reject. Deleted/wrong images must not enter writeback.

## Prefix 锁
- L043: Do not edit failed image. Use new clean PNG. Do not mirror, rotate, or redraw. Front/top-front view. Preserve exact hole count, all large holes, small center hole, rear raised detail, panel seams, thin board thickness. Clothing nearby only; never cover holes.
- L082: Do not mirror, rotate, or flip. Preserve left-right telescoping orientation horizontally and front-facing. No side rails, drawer tracks, or invented hardware.
- L085: Scene must be home repair, wall patching, paint-prep, drop cloth, or utility workbench. Preserve three scraper sizes, metal blades, handles and straight edges.
- L091: Front-facing or very slight perspective only. Product 30-36% frame height. Use closet shelf, vanity shelf, entry cabinet or storage cubby. Preserve top groove/grid, upper edge, drawer face, black handle, white frame.
- L096: superseded by the 2026-07-07 ground/floor-use correction. Folding portable grill must stand on its own legs on grass, campsite ground, gravel, patio pavers, courtyard floor, deck boards, terrace floor, or another heat-safe outdoor ground/floor surface. Do not use tabletop/workbench/cart/counter/shelf/cabinet support. Rotate wild camping, lawn picnic, Western family/friends backyard gathering, courtyard/patio outdoor meal prep, RV campsite, garden party, park picnic, terrace/deck floor, and open-air family outdoor dining scenes.

## 明细
- L043060501__set1__redo_newpng1: old `L043_NEW_0001` -> new `L043_NEW_0007`; feedback `不要这个png，重新用别的png来重做`; scene #1; risk critical
- L043060502__set1__redo_newpng1: old `L043_NEW_0003` -> new `L043_NEW_0043`; feedback `产品错误，重做`; scene #2; risk critical
- L043060503__set1__redo_newpng1: old `L043_NEW_0005` -> new `L043_NEW_0004`; feedback `产品中间有个小孔洞，丢失了`; scene #3; risk critical
- L043060504__set1__redo_newpng1: old `L043_NEW_0006` -> new `L043_NEW_0008`; feedback `脑子有病，产品的孔洞数量不对`; scene #4; risk critical
- L043060506__set1__redo_newpng1: old `L043_NEW_0011` -> new `L043_NEW_0030`; feedback ``; scene #5; risk critical
- L043060508__set1__redo_newpng1: old `L043_NEW_0030` -> new `L043_NEW_0005`; feedback `产品外观严重错误`; scene #6; risk critical
- L082060504__set1__redo_newpng1: old `L082_NEW_0011` -> new `L082_NEW_0010`; feedback `产品的方向错了`; scene #1; risk high
- L082060506__set1__redo_newpng1: old `L082_NEW_0002` -> new `L082_NEW_0009`; feedback ``; scene #2; risk high
- L082060507__set1__redo_newpng1: old `L082_NEW_0006` -> new `L082_NEW_0011`; feedback `产品的方向错了`; scene #3; risk high
- L085060503__set1__redo_newpng1: old `L085_T_0032` -> new `L085_T_0029`; feedback `场景错误`; scene #1; risk high
- L085060505__set1__redo_newpng1: old `L085_T_0009` -> new `L085_T_0019`; feedback `场景错误`; scene #2; risk high
- L091060502__set1__redo_newpng1: old `L091_T_0015` -> new `L091_T_0017`; feedback `产品在场景中的比例不对，不符合产品的使用场景`; scene #1; risk high
- L096060501__set1__redo_newpng1: old `L096_T_0001` -> new `L096_T_0020`; feedback ``; scene #1; risk critical
- L096060502__set1__redo_newpng1: old `L096_T_0006` -> new `L096_T_0008`; feedback ``; scene #2; risk critical
- L096060504__set1__redo_newpng1: old `L096_T_0013` -> new `L096_T_0006`; feedback ``; scene #3; risk critical
- L096060505__set1__redo_newpng1: old `L096_T_0020` -> new `L096_T_0001`; feedback ``; scene #4; risk critical
- L096060506__set1__redo_newpng1: old `L096_T_0001` -> new `L096_T_0008`; feedback ``; scene #5; risk critical
