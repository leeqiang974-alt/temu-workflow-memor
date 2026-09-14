"""Build the second Agnes 23-D plan after the full human rejection.

V2 submits only the exact-D product reference. The old T1 remains hashed
planning evidence but is never sent, preventing scene copying and product fusion.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(
    r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810"
    r"\t1_cangyuan_current_workbook_t1"
)
SOURCE_PLAN = ROOT / "YeahF_1999D_T1人工驳回105D_双参考重做计划_20260813.json"
REJECTION_LOCK = ROOT / "outcome_library" / "human_rejected" / "agnes_20260914_23D_human_rejection_lock.json"
OUT = ROOT / "human_redo23_agnes_v2_20260914" / "agnes_v2_redo23_plan.json"


SCENES = {
    "L043080812": "a bright hotel-laundry folding counter, low three-quarter left camera, a middle-aged man in a navy overshirt arranging three countable stacks of five boards, blurred wicker hamper foreground, exact boards and hands midground, deep linen shelves and window background",
    "L043080829": "a premium walk-in wardrobe island, high oblique right camera, an older woman in a sage cardigan sorting three countable stacks of five boards, blurred folded sweater foreground, product stacks midground, deep wardrobe rails and doorway background",
    "L043080832": "a spacious utility-room table, eye-level diagonal camera through a doorway, a young man in a beige apron using one board while fourteen matching boards remain in two clearly countable stacks, soft laundry basket foreground, product midground, washer wall and sunlit corridor background",
    "L043080878": "a boutique bedroom dressing bench, near-product wide-angle from the right, a different woman with short hair and blue work shirt folding a garment, three countable stacks of five boards visible, linen foreground, product and hands midground, bed and wardrobe in deep background",
    "L043080881": "a modern dry-cleaning preparation studio, lower eye-level front-left camera, an older man in a charcoal apron presenting one board beside two stacks of seven matching boards, blurred fabric roll foreground, all fifteen boards midground, long workroom depth and shelves background",
    "L058080888": "a large premium mudroom with stone floor, low side camera near the floor, a different adult man in dark green work clothes actively wringing and pushing the exact mop system, wet-floor reflection foreground, bucket and hands midground, open glass door and garden depth background",
    "L072080808": "a luxury dressing-room entrance, high three-quarter right camera, a different older woman in a rust cardigan placing a folded scarf into the exact drawer unit, blurred bench edge foreground, product and hands midground, wardrobe corridor and window background",
    "L076080806": "a sunlit living room photographed low at pet-eye level from the side, a different adult man kneeling to smooth the exact pet mat while a medium dog settles onto it, blurred toy foreground, mat and dog midground, sofa and garden doors in deep background",
    "L077080826": "a refined reading nook shot from a higher diagonal rear-left angle, a different woman in a green sweater offering a toy through the exact cat-house opening, blurred table edge foreground, product and cat midground, bookcase and window background",
    "L081080810": "a premium breakfast island, low three-quarter right camera, a different adult male home barista in a blue shirt pulling the exact front basket and organising coffee packets, blurred cup and linen foreground, product and hands midground, walnut kitchen and window depth background",
    "L081080846": "a hotel-suite coffee station, high oblique left camera, a different older woman in a burgundy blouse sliding the exact basket outward, blurred tray foreground, product midground, lounge and curtain layers in the background",
    "L081080851": "a deep pantry coffee nook, eye-level side camera through an open cabinet door, a different young man in a cream apron loading cups into the exact basket, cabinet edge foreground, product midground, stone backsplash and distant dining room background",
    "L081080883": "a bright sunroom beverage console, low front-left wide-angle camera, a different older man in a linen shirt reaching into the exact basket, blurred glass carafe foreground, product midground, plants and terrace doors far behind",
    "L081080887": "a dark walnut home-office refreshment bar, high three-quarter right camera, a different woman with short grey hair arranging tea packets in the exact basket, blurred notebook foreground, product midground, shelves and doorway depth background",
    "L081080901": "a marble kitchen peninsula viewed from a low side angle, a different young woman in a terracotta apron pulling the exact basket with one hand, soft fruit bowl foreground, product midground, long galley kitchen and window background",
    "L081080910": "a boutique guesthouse breakfast room, eye-level telephoto view through a foreground chair, a different adult man in a light grey cardigan organising supplies in the exact basket, product midground, layered tables and arched window background",
    "L082080805": "a completely new lower kitchen cabinet scene, low three-quarter side camera, a different adult woman kneeling and pulling the single exact dark telescopic tray outward while arranging dishes, cabinet-door edge and linen foreground, exact tray and hands midground, deep refined pantry background",
    "L083080809": "a luxury vanity cabinet viewed from a high diagonal left angle, a different woman in a navy robe sliding the exact two-level organiser outward, blurred towel foreground, product and bottles midground, mirror and doorway background",
    "L087080803": "a premium under-sink cabinet shot low from inside the open door toward the room, a different adult man kneeling and reaching into the exact two-tier basket, cabinet hinge foreground, product midground, kitchen island and window far behind",
    "L091080901": "a spacious walk-in closet island viewed from a low three-quarter right angle, a different older woman in a teal blouse opening the middle mesh-front drawer, blurred handbag foreground, exact unit and hands midground, hanging clothes and doorway background",
    "L091080943": "a boutique bedroom storage corner photographed from a high oblique left angle, a different young man in a brown overshirt loading folded linen into the bottom drawer, bed edge foreground, exact drawer unit midground, window and wardrobe depth background",
    "L092080811": "a chef-style stone kitchen island from a low three-quarter left camera, a different middle-aged woman in a dark blue apron holding the smallest of exactly three cutting boards, herb leaves foreground, all three boards midground, stove wall and window far behind",
    "L095080823": "a rooftop terrace garden shot from a low corner wide-angle, a completely different older couple planting herbs in the exact raised planter, blurred watering can foreground, planter and hands midground, seating, glass rail and mountain depth background",
}


FAMILY_LOCKS = {
    "L043": "Exactly fifteen identical white perforated folding boards must be physically visible and countable; arrange them as three stacks of five or one active board plus two stacks of seven. Do not reduce the set to one or two boards.",
    "L058": "Preserve the exact bucket, wringer, mop heads, handles, colours, component count and proportions from the product reference. Do not substitute the blue product from any prior scene.",
    "L072": "Preserve the exact drawer count, black fabric body, handles, top rails, feet and proportions.",
    "L076": "Preserve the exact pet-mat outline, thickness, grey texture and edge construction; the dog and room may change.",
    "L077": "Preserve the exact wooden cat-house body, openings, scratching surfaces, holes, edges and proportions.",
    "L081": "Preserve the exact black metal frame, wood top, pull-out wire-basket structure, rails, legs, proportions and colour. Coffee machines and loose contents are props, not product structure.",
    "L082": "Exactly one dark charcoal telescopic pull-out tray system. Preserve the split expansion seam, slotted surface, side rails, front edges and proportions. Absolutely no white shelf, second tray, overlap or fused product.",
    "L083": "Preserve the exact upper wire basket, lower solid caddy, rods, supports, connectors, handles and proportions.",
    "L087": "Preserve the exact two-tier black basket body, frame, rails, handles, spacing and proportions.",
    "L091": "Preserve the exact white drawer-unit body, three mesh-front drawers, handles, top structure, recess pattern and proportions.",
    "L092": "Exactly three cutting boards, matching the three sizes and handle openings in the reference. Never show a fourth board.",
    "L095": "Preserve the exact raised planter body, woven panel pattern, leg count, height, rectangular proportions and colour.",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> None:
    source = json.loads(SOURCE_PLAN.read_text(encoding="utf-8-sig"))
    lock = json.loads(REJECTION_LOCK.read_text(encoding="utf-8-sig"))
    locked = {row["D"]: row for row in lock["records"]}
    if set(locked) != set(SCENES):
        raise RuntimeError("Scene plan must cover the exact 23 human-rejected D values")
    source_by_d = {row["target_D"]: row for row in source["records"]}
    records = []
    for d_value in sorted(SCENES):
        old = source_by_d[d_value]
        product = Path(old["product_material"])
        old_scene = Path(old["scene_anchor"])
        first_negative = Path(old["negative_candidate"])
        agnes_negative = Path(locked[d_value]["candidate_path"])
        for path in (product, old_scene, first_negative, agnes_negative):
            if not path.is_file():
                raise FileNotFoundError(path)
        l0xx = d_value[:4]
        prompt = f"""MODE: product-only high-differentiation lifestyle reconstruction. The single input image is the absolute and only visual authority for the sale product. {FAMILY_LOCKS[l0xx]} Create {SCENES[d_value]}. This must be a genuinely new photograph, not a close edit of any old T1. Mandatory differences: new setting/layout, new adult person identity and face, new clothing, new pose and placement, new camera angle and height, new product position and scale, new foreground/midground/background layering, new palette, new lighting direction and new props. Keep only a believable equivalent product-use task. The exact product must remain unobstructed and physically supported with realistic contact, gravity and shadows. Exactly one sale-product set unless the product lock explicitly states a pack count. No readable text, measurement marks, badges, inset circles, logos, watermarks, duplicated or fused products, extra parts, changed colour, changed count, warped hardware or copied old-scene composition. Square 1:1 polished realistic premium ecommerce photograph."""
        records.append({
            "D": d_value,
            "L0xx": l0xx,
            "G": old.get("G", ""),
            "SKU": old.get("SKU", ""),
            "submitted_images": [{
                "order": 1,
                "role": "absolute_exact_D_product_identity",
                "path": str(product),
                "sha256": sha256(product),
            }],
            "planning_evidence_not_submitted": [{
                "role": "old_T1_context_only_forbidden_as_pixel_reference",
                "path": str(old_scene),
                "sha256": sha256(old_scene),
            }],
            "negative_evidence_not_submitted": [
                {"path": str(first_negative), "sha256": sha256(first_negative)},
                {"path": str(agnes_negative), "sha256": sha256(agnes_negative)},
            ],
            "scene_recipe": SCENES[d_value],
            "product_lock": FAMILY_LOCKS[l0xx],
            "prompt": prompt,
            "status": "planned_user_authorized_redo_20260914",
            "review_status": "pending_generation",
            "writeback": "BLOCK_until_human_review_badge_OSS_release_gate",
        })
    payload = {
        "schema": "yeahf-1999d-agnes-v2-product-only-redo23/v1",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "authorization": "user_authorized_new_23_and_concurrency_test_20260914",
        "provider": "Agnes AI",
        "model": "agnes-image-2.5-flash",
        "size": "1K",
        "ratio": "1:1",
        "max_in_flight": 8,
        "record_count": len(records),
        "all_old_T1_not_submitted": True,
        "all_prior_rejected_candidates_not_submitted": True,
        "records": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"plan": str(OUT), "records": len(records), "reference_count_each": 1}, ensure_ascii=False))


if __name__ == "__main__":
    main()

