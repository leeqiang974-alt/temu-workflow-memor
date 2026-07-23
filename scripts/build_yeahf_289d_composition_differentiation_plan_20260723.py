"""Build the approved 289-D Cangyuan reference-edit redo plan.

This plan keeps the previously verified original manuscript reference for each D,
but forces material composition differentiation. It never submits paid tasks.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


WORKSPACE = Path(r"C:\Users\Administrator\Documents\temu自动化")
SOURCE_PLAN = (
    WORKSPACE
    / "outputs"
    / "yeahf_merged_d_0721"
    / "YeahF_2000D_苍猿T1原稿参考任务清单_20260723.json"
)
OUTPUT_PLAN = (
    WORKSPACE
    / "outputs"
    / "yeahf_merged_d_0721"
    / "YeahF_2000D_289D_按L0xx构图差异化重做任务清单_20260723.json"
)
OUTPUT_MD = (
    WORKSPACE
    / "outputs"
    / "yeahf_merged_d_0721"
    / "YeahF_2000D_289D_按L0xx构图差异化规则_20260723.md"
)


LANES = [
    {
        "id": "wide_left",
        "instruction": (
            "Create a substantially wider scene than the source. The complete product "
            "should occupy about 24-30% of the square frame and sit in the left third, "
            "with believable new environment visible on the right and behind it."
        ),
        "mirror": False,
    },
    {
        "id": "wide_right_mirror",
        "instruction": (
            "Create a substantially wider scene than the source. The complete product "
            "should occupy about 26-32% of the square frame and sit in the right third. "
            "When the family mirror rule permits, horizontally mirror the whole product "
            "as one rigid object while preserving every part and functional relationship."
        ),
        "mirror": True,
    },
    {
        "id": "medium_lower_left",
        "instruction": (
            "Use a medium-wide composition with the complete product at about 34-40% of "
            "the frame, positioned lower-left. Add clear foreground and background depth "
            "that did not exist in the source crop."
        ),
        "mirror": False,
    },
    {
        "id": "medium_upper_right_mirror",
        "instruction": (
            "Use a medium-wide composition with the complete product at about 32-38% of "
            "the frame, offset toward the upper-right with generous negative space. When "
            "permitted, horizontally mirror the complete product without changing geometry."
        ),
        "mirror": True,
    },
    {
        "id": "closer_left",
        "instruction": (
            "Use a clearly closer crop than the source while keeping the entire product "
            "visible and uncropped. Let it occupy about 46-54% of the frame, offset left, "
            "with a newly staged but uncluttered environment."
        ),
        "mirror": False,
    },
    {
        "id": "closer_right_mirror",
        "instruction": (
            "Use a clearly closer crop than the source while keeping the entire product "
            "visible and uncropped. Let it occupy about 44-52% of the frame, offset right. "
            "When permitted, horizontally mirror the whole product as a rigid unit."
        ),
        "mirror": True,
    },
    {
        "id": "deep_center",
        "instruction": (
            "Place the complete product near the center at about 30-36% of the frame, but "
            "create much stronger front-to-back scene depth, a different camera distance, "
            "and different surrounding architecture or landscape from the source."
        ),
        "mirror": False,
    },
    {
        "id": "asymmetric_negative_space",
        "instruction": (
            "Recompose with the complete product at about 36-44% of the frame and strong "
            "asymmetric negative space on the opposite side. Change camera distance, crop, "
            "background depth, lighting direction, and environmental palette together."
        ),
        "mirror": False,
    },
]


NO_MIRROR = {
    "L043",  # fragile folding-board geometry and holes/seams are immutable
    "L047",  # ground insertion/support relationship is the primary lock
    "L058",  # preserve the complete black/red bucket orientation
    "L082",  # left/right expandable direction lock
    "L088",  # offset stepped baskets/rods/supports must not swap sides
    "L089",  # preserve rack hardware orientation
    "L091",  # front/slight-perspective product lock
}


FAMILY_RULES = {
    "L043": (
        "FAMILY LOCK L043: this is a fragile folding board. Preserve the exact visible "
        "board region, scale relationship, angle, color, holes including the small center "
        "hole, raised detail, seams, count and every variant-specific feature. Change only "
        "camera distance, crop, background, non-occluding person styling and palette."
    ),
    "L047": (
        "FAMILY LOCK L047: preserve the exact arch/trellis structure and insert its legs "
        "directly into the ground in every environment; the product must insert directly into "
        "the ground. Remove and forbid any circular, "
        "square, cross-shaped, pedestal or freestanding base. Do not invent feet."
    ),
    "L058": (
        "FAMILY LOCK L058: retain the complete black-and-red mop bucket as the focal "
        "product, including every visible compartment, handle, wringer and support. Never "
        "crop away or recolor the product."
    ),
    "L077": (
        "FAMILY VARIATION L077: replace the pet with a visibly different believable breed, "
        "coat color and pose. Keep one pet naturally using the product, but do not let the "
        "animal cover, merge with or deform the product boundary."
    ),
    "L082": (
        "FAMILY LOCK L082: preserve the exact left-right expansion direction and all "
        "hardware. No horizontal mirror, no swapped sides and no altered extension count."
    ),
    "L083": (
        "FAMILY VARIATION L083: preserve all rack hardware. Replace stored objects with a "
        "different coordinated household assortment. If cabinetry is visible, change only "
        "the surrounding cabinet/counter color, finish and door style, never the product."
    ),
    "L088": (
        "FAMILY VARIATION L088: preserve the exact offset stepped baskets, rods, supports, "
        "feet, tier count and product color. Replace the items stored on the rack with a "
        "different realistic coordinated assortment. Change surrounding cabinet/counter "
        "finish where present, never the rack body."
    ),
    "L089": (
        "FAMILY VARIATION L089: preserve the exact rack frame, tier count, rods, feet and "
        "product color. Replace the displayed/stored products with a different realistic "
        "assortment. Change surrounding cabinet/counter appearance where present, never "
        "the rack itself."
    ),
    "L091": (
        "FAMILY LOCK L091: retain the approved front or slight-perspective product view. "
        "Do not mirror, rotate to a new side, change count, or alter structural geometry."
    ),
    "L095": (
        "FAMILY VARIATION L095: replace the flowers/plants with clearly different species, "
        "colors and arrangement. Preserve the exact planter/basket structure, quantity, "
        "size relationship, mounting/support and product color."
    ),
}


GENERIC_ENVIRONMENT_RULE = (
    "If the source scene contains a lower cabinet, cupboard, console or countertop, "
    "differentiate the surrounding furniture by changing its finish, color, panel style "
    "and handle style only. The sale product is not furniture and must remain unchanged."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_prompt(record: dict, lane: dict) -> str:
    prefix = str(record["l0xx"])
    source_d = str(record["source_D"])
    mirror_allowed = lane["mirror"] and prefix not in NO_MIRROR
    lane_text = lane["instruction"]
    if lane["mirror"] and not mirror_allowed:
        lane_text = lane_text.replace(
            "When the family mirror rule permits, horizontally mirror the whole product "
            "as one rigid object while preserving every part and functional relationship.",
            "Do not mirror the product; create the differentiation through framing, "
            "position, scene expansion and camera distance.",
        ).replace(
            "When permitted, horizontally mirror the complete product without changing geometry.",
            "Do not mirror the product; use position, negative space and camera distance instead.",
        ).replace(
            "When permitted, horizontally mirror the whole product as a rigid unit.",
            "Do not mirror the product; use crop, position and scene depth instead.",
        )

    pieces = [
        "MODE: reference_edit.",
        (
            f"SOURCE: the inspected approved original manuscript reference {source_d}; "
            "never use any generated candidate or output image as a reference."
        ),
        (
            "PRODUCT TRUTH IS IMMUTABLE: preserve the exact complete product silhouette, "
            "boundary, color, material, count, hardware, tier/compartment count, supports, "
            "contact points and useful task logic. Keep any useful person performing the "
            "same or equivalent product-related task."
        ),
        (
            "MANDATORY MATERIAL DIFFERENTIATION: this must be a re-staged composition, not "
            "a near-copy or micro-edit. Change framing scale, product position, camera "
            "distance, scene depth, environmental palette, lighting direction, and at "
            "least two safe background materials/props."
        ),
        lane_text,
        FAMILY_RULES.get(prefix, ""),
        GENERIC_ENVIRONMENT_RULE,
        (
            "Do not add, remove, redraw or redesign product parts. Do not let people, pets "
            "or props occlude the product. No text, logo, watermark, inset, collage, border, "
            "badge or product color/count drift. Photorealistic premium ecommerce image, "
            "square 1024x1024."
        ),
    ]
    return " ".join(piece for piece in pieces if piece)


def main() -> None:
    source = json.loads(SOURCE_PLAN.read_text(encoding="utf-8"))
    records = source["records"]
    if len(records) != 289 or len({r["target_D"] for r in records}) != 289:
        raise RuntimeError("source plan must contain exactly 289 unique target D values")

    prefix_ordinals: Counter[str] = Counter()
    new_records = []
    reference_hash_failures = []
    for record in records:
        prefix = str(record["l0xx"])
        index = prefix_ordinals[prefix]
        prefix_ordinals[prefix] += 1
        lane = LANES[index % len(LANES)]
        reference = Path(record["reference_image"])
        actual_sha = sha256_file(reference)
        if actual_sha != record.get("reference_sha256"):
            reference_hash_failures.append(
                {
                    "D": record["target_D"],
                    "path": str(reference),
                    "expected": record.get("reference_sha256"),
                    "actual": actual_sha,
                }
            )
        item = dict(record)
        item["prompt_version"] = "yeahf-289d-composition-differentiation/v1"
        item["composition_lane"] = lane["id"]
        item["horizontal_mirror_requested"] = bool(lane["mirror"])
        item["horizontal_mirror_allowed"] = bool(
            lane["mirror"] and prefix not in NO_MIRROR
        )
        item["family_rule"] = FAMILY_RULES.get(prefix, "generic-product-truth-lock")
        item["prompt"] = build_prompt(record, lane)
        new_records.append(item)

    if reference_hash_failures:
        raise RuntimeError(
            "original reference hash gate failed: "
            + json.dumps(reference_hash_failures, ensure_ascii=False)
        )

    payload = {
        "schema": "yeahf-289d-composition-differentiation-plan/v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_plan": str(SOURCE_PLAN),
        "source_plan_sha256": sha256_file(SOURCE_PLAN),
        "count": len(new_records),
        "reference_mode": "approved-original-manuscript-only",
        "generated_reference_forbidden": True,
        "paid_submission_authorized": True,
        "workbook_writeback": "blocked_until_full_visual_review",
        "global_rules": {
            "material_differentiation_required": True,
            "composition_dimensions": [
                "zoom/framing",
                "product position",
                "camera distance",
                "scene depth",
                "environment palette/materials",
                "lighting direction",
                "safe horizontal mirror when family permits",
            ],
            "no_mirror_prefixes": sorted(NO_MIRROR),
            "family_rules": FAMILY_RULES,
        },
        "records": new_records,
    }
    OUTPUT_PLAN.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    counts = Counter(r["l0xx"] for r in new_records)
    lanes = Counter(r["composition_lane"] for r in new_records)
    mirror_count = sum(r["horizontal_mirror_allowed"] for r in new_records)
    lines = [
        "# YeahF 289D 构图差异化重做规则",
        "",
        f"- 计划数：{len(new_records)}",
        "- 参考图：仅使用逐 D 已核验原稿；生成图区永久禁止作为参考。",
        "- 强制差异化：扩景/缩景、产品位置、相机距离、空间纵深、环境材质与色调、光向。",
        f"- 安全水平镜像：{mirror_count} 个 D；高风险产品族禁用镜像。",
        "- 写表：全量视觉审核前禁止。",
        "",
        "## L0xx 数量",
        "",
    ]
    lines.extend(f"- {prefix}: {counts[prefix]}" for prefix in sorted(counts))
    lines.extend(["", "## 构图通道", ""])
    lines.extend(f"- {lane}: {lanes[lane]}" for lane in sorted(lanes))
    lines.extend(["", "## 专项规则", ""])
    lines.extend(f"- {prefix}: {rule}" for prefix, rule in sorted(FAMILY_RULES.items()))
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "output_plan": str(OUTPUT_PLAN),
                "output_md": str(OUTPUT_MD),
                "count": len(new_records),
                "prefix_counts": dict(sorted(counts.items())),
                "lane_counts": dict(sorted(lanes.items())),
                "mirror_allowed": mirror_count,
                "reference_hash_failures": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
