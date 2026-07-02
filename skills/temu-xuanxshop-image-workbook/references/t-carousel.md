# T Carousel, First Image, U, And Size Image

## First Carousel Image

Default unit: one first image per unique exact D.

For every row with the same D:

- T first URL must be the same.
- U must equal T first URL.
- Existing T URLs should be preserved unless user requests replacement/reorder.

## Insert Behavior

Default writeback:

1. New approved first image
2. Existing T URLs after exact delete/reject locks are applied
3. Deduplicate while preserving order
4. Force a valid size image into position 4 when required
5. Cap at 10 URLs

Do not delete useful existing images unless the user provided a delete list or reorder rule.

## Common Reorder Rule

If user says “第五第六张图放前面2、3位，2、3的图片放5、6，第四始终保持不变”, write:

1. New generated first image
2. Original 5th
3. Original 6th
4. Original 4th size image
5. Original 2nd
6. Original 3rd
7. Original 1st
8. Original 7th onward

Deduplicate and cap at 10.

## Size Image

If the fourth image is locked as dimensions/size chart:

- Detect a valid size image using filename/URL/title clues such as `尺寸`, `size`, or `尺码`.
- Preserve it at T[4] when valid.
- If user feedback deletes T[4], locate another valid size image and place it at T[4].
- If no valid size image remains, block final delivery and report the D/rows.
- In review pages label it as `第4张尺寸图`.
- Validate position 4 after writeback.

## Approved Registry

An approved registry can reduce repeated generation cost, but only if:

- D is not in current redo list.
- Output is not later rejected by user.
- Material PNG is not in bad-material/reject list.
- It is not too similar to another accepted same-prefix image unless user allows it.

User feedback lock has higher priority than approved registry.
