from __future__ import annotations

import json
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui")

PRODUCT_RULES = {
    "L042": {
        "identity": "black garden edging fence panels with small nail stakes; preserve the exact PNG product structure, panel count, panel spacing, stake shape, stake length, panel profile, edge detail and connection style",
        "allowed": "garden patio, grass edge, stone path, flower bed border, courtyard landscaping",
        "forbid": "do not change nail count, nail length, panel profile, panel spacing, hinge or connection details; do not reconstruct it as a different fence, flower bed wall, continuous border, decorative barrier, wooden edging, plastic wall, or newly imagined garden enclosure",
    },
    "L043": {
        "identity": "folding clothes stacking board; preserve board holes, the small center hole, raised rear structure and panel outline",
        "allowed": "laundry room, wardrobe, closet shelf, folding table with folded clothes",
        "forbid": "do not alter hole shape, remove the small hole, exaggerate or delete the rear raised part",
    },
    "L047": {
        "identity": "outdoor black metal garden arch frame, arched iron structure for decoration and garden entrances; preserve the exact black arched frame silhouette, rod thickness, side supports, base geometry, and metal structure from the PNG",
        "allowed": "realistic seaside path, green lawn, church garden entrance, flower bed, courtyard path, outdoor ceremony arch scene; flowers, vines or flowing fabric may decorate the arch without hiding the black frame",
        "forbid": "do not invent a new arch shape; do not add a second foreground arch or duplicate arch frame; do not turn it into a toy, cartoon, children illustration, plastic object, wooden gate, full building, or random fence; do not delete the arch curve or alter the black metal frame structure",
    },
    "L048": {
        "identity": "green artificial leaf privacy decoration panel for fences; preserve leaf panel texture and decorative greenery character",
        "allowed": "balcony fence, garden wall, patio privacy screen, indoor decor wall",
        "forbid": "avoid treating it as real live plants or flower bouquet; do not change it into unrelated foliage product",
    },
    "L051": {
        "identity": "flat kraft paper bags sold as a quantity pack; show a stack or bundle to imply quantity, include visual cue of 50 pieces without adding risky text; preserve the original flat paper-bag handle shape, opening direction and upright/front-facing orientation if visible",
        "allowed": "boutique packing table, gift packing scene, retail shelf, home storage drawer",
        "forbid": "do not imply only one bag; do not hide or remove the bag handles on the visible front bags; do not flip the bag direction away from the reference; do not turn handles into circular ring handles, rope loops, handbag handles, plastic rings or metal rings; no brand logos or printed words",
    },
    "L058": {
        "identity": "rotating mop bucket set with bucket, spinner basket, mop pole and mop head; preserve bucket shape, pole position, spinner structure and all major parts",
        "allowed": "laundry room floor, bathroom cleaning corner, utility room, kitchen cleaning corner",
        "forbid": "do not redesign the bucket, pole, spinner, mop head, water area or internal structure; do not change the mop cloth or mop head into black, dark charcoal, dirty black fabric or unrelated dark material; preserve the original light mop cloth color and texture from the reference",
    },
    "L063": {
        "identity": "fitness-related household product; product appearance should follow the dimension reference and formed product photos; preserve all visible details",
        "allowed": "realistic home gym room, fitness room, exercise mat area, real apartment workout corner with natural daylight",
        "forbid": "do not reconstruct product details or change outer shape; do not place it in unrelated counter display scenes when a fitness scene is requested",
    },
    "L068": {
        "identity": "household rack/shelf product; preserve rack structure, supports, tiers and outline; replace contents only when safe",
        "allowed": "kitchen countertop, dining sideboard, sink side counter, organized home shelf",
        "forbid": "do not change rack structure or number of tiers",
    },
    "L076": {
        "identity": "pet mat cushion with flat surface material matching references; avoid black anti-slip bottom image if not true product",
        "allowed": "living room floor, bedroom pet corner, window-side pet mat area",
        "forbid": "do not invent black anti-slip bottom, headrest, extra cushion parts, comfort medical claims or new structure",
    },
    "L078": {
        "identity": "high-risk product where internal plate/tray structure must remain accurate; preserve tray and plate structure exactly",
        "allowed": "dessert table, dining table, clean kitchen counter with safe dry food props",
        "forbid": "do not expand, redraw, hallucinate or redesign the outside appearance or the structure inside the plate/tray; do not change product outline",
    },
    "L082": {
        "identity": "extendable organizer; preserve visible product structure and extension mechanism with minimum risk",
        "allowed": "cabinet organizer, drawer storage, kitchen shelf scene",
        "forbid": "do not invent extra side rails, sliding rail parts, tracks, drawer slides, metal runners or extension hardware; do not alter extension direction, drawer/organizer form, supports, surface color or rails",
    },
    "L091": {
        "identity": "storage product with four-square groove detail on top; preserve upper detail especially for top view; keep the same reference viewing angle to avoid hallucinating the top structure",
        "allowed": "desk organizer, vanity counter, shelf organization scene",
        "forbid": "do not change the camera angle or rotate the product; do not add any new block, lid, handle, raised part, decoration, object or extra piece on the top; do not remove or alter the four-square groove detail on top",
    },
    "L092": {
        "identity": "cutting board with one flat oval hole and two round holes; preserve hole count, shape and positions",
        "allowed": "kitchen counter, sink side prep area, wood countertop, clean food prep scene",
        "forbid": "do not change hole shape, hole number or hole placement",
    },
    "L094": {
        "identity": "fruit tray or layered fruit plate; preserve tray structure while changing fruit contents safely",
        "allowed": "dining table, kitchen island, sideboard with fruit and plain desserts",
        "forbid": "do not drift into generic storage rack; do not change tray tiers or structure",
    },
    "L095": {
        "identity": "basket/planter product; preserve basket structure while varying flowers or plants inside",
        "allowed": "garden, balcony planter, patio decor, window greenery",
        "forbid": "do not change basket structure or turn it into unrelated flowerpot",
    },
    "L096": {
        "identity": "household product with specific reference details; preserve product structure and avoid hallucinated changes",
        "allowed": "safe home use scene, warm household context, clean organization scene",
        "forbid": "do not invent parts, delete details or redesign visible product body",
    },
    "L087": {
        "identity": "household organizer product; preserve exact product exterior, frame shape, color, proportions, visible surfaces and structural details from the PNG",
        "allowed": "safe kitchen, dining sideboard, home organization scene with warm natural daylight",
        "forbid": "do not change the product exterior, color, frame geometry, surface material, number of parts or visible structure; do not redraw it into a different organizer",
    },
}

GENERIC_RULE = {
    "identity": "household product; preserve product silhouette, color, material, structural parts and visible functional details",
    "allowed": "safe realistic home lifestyle scene with warm high-value styling",
    "forbid": "do not add, delete, deform or redesign product parts",
}

SAFE_VALUE_STYLE = (
    "Use high-value but safe unbranded styling: warm natural light, premium home interior or outdoor lifestyle setting, "
    "plain ceramic, stone, wood, linen, greenery, clean spatial depth, realistic shadows, commercial photography. "
    "Luxury-inspired but non-infringing visual cues are allowed: marble surfaces, brushed metal accents, boutique hotel styling, "
    "minimal leather-like trays, premium gift wrap textures, elegant flowers, soft editorial lighting and upscale home decor. "
    "Do not use or imitate any brand logo, monogram pattern, recognizable luxury brand packaging, protected character, trademarked product shape, "
    "designer handbag silhouette, branded watch, branded jewelry, printed brand text, or counterfeit-like item. "
    "No logos, no brand packaging, no text, no electronic screens, no fire, no candles, no alcohol, no toys, no medicines, no weapons."
)

REPLACEABLE_CONTENTS_STYLE = (
    "For racks, shelves, trays, baskets, boxes, cabinet organizers and storage products, use loose removable contents as a controlled differentiation axis. "
    "The product body is fixed hardware: keep frame, rods, shelves, tiers, hooks, handles, holes, rails, baskets, legs, supports, wheels, color, outline and silhouette unchanged. "
    "Only replace loose contents placed on or inside the product with category-safe unbranded items such as plain plates, bowls, cups, utensils, towels, files, fruit, artificial flowers, greenery or small household props. "
    "Replacement contents must not cover, merge with, hide, replace, or redesign the product hardware. "
    "If a visible object might be part of the product itself, treat it as fixed hardware and do not replace it."
)

REALISTIC_USAGE_CONTEXT_STYLE = (
    "Place the product only in a realistic usage context that matches its actual function, weight, support surface, gravity and buyer use case. "
    "The product must sit, stand, hang, lean or attach exactly where this category would naturally be used. "
    "Do not put products in visually attractive but physically absurd contexts: no barbecue grill on a bed, no heavy rack floating on fabric, no garden arch on a sofa, no pet mat on a kitchen counter, no kitchen storage on bedroom bedding. "
    "Match the contact surface: floor products on floor, grass or tile; countertop products on counters, tables or shelves; wall/fence products attached to walls, fences or railings; outdoor garden products on lawn, path, patio or flower bed; cleaning products on bathroom, laundry or utility floors. "
    "If the product needs support or attachment, show believable support and natural contact shadows."
)

USAGE_CONTEXT_BY_PREFIX = {
    "L042": "Use a garden, lawn edge, flower bed, stone path or patio border scene; never place garden edging on bed, sofa, kitchen counter or indoor closet.",
    "L047": "Use an outdoor lawn, garden path, patio, seaside grass path, courtyard or ceremony entrance; the arch must stand on ground, not on furniture or fabric.",
    "L048": "Use balcony fence, garden fence, patio privacy screen, railing or decor wall; show it attached to a vertical support.",
    "L058": "Use bathroom, laundry room, utility room or tiled cleaning floor; never place mop bucket on bed, dining table, sofa or wardrobe shelf.",
    "L063": "Use real home gym, fitness studio, exercise mat or workout floor; never place fitness product on kitchen counter, bed or dining table.",
    "L076": "Use living room floor, bedroom floor, rug or pet corner; never put pet mat on counter, shelf, sink or tabletop.",
    "L077": "Use floor-level pet area, living room rug or bedroom pet corner; keep pet-use context believable.",
    "L092": "Use kitchen counter, sink side or food prep area; do not place cutting board in bedroom, bathroom or grass.",
}


def rule_for(prefix: str) -> dict:
    return PRODUCT_RULES.get(prefix, GENERIC_RULE)


def build_seedream_product_fusion_prompt(prefix: str, d_value: str, scene_hint: str = "", variation_hint: str = "") -> str:
    rule = rule_for(prefix)
    scene = scene_hint or rule["allowed"]
    integration_rule = (
        "For this product, treat the input PNG as a fixed product layer to be blended into the new scene. "
        "Keep the exact same product angle, orientation, outline, top view relationship and visible structure from the PNG. "
        "Only adjust scene background, natural lighting, contact shadow, color matching and placement; do not create a new perspective or rotate the product. "
        if prefix in {"L042", "L047", "L078", "L082", "L087", "L091"}
        else
        "You may adjust natural lighting, contact shadow, perspective feeling, scene interaction and scale so the product belongs in the environment, "
    )
    return (
        "Use the input transparent PNG as the primary product reference and generate a new realistic ecommerce first-carousel image. "
        "The product should look naturally integrated into the scene, not pasted on top. "
        "Preserve the exact product identity and structure: "
        f"{rule['identity']}. "
        f"{integration_rule}"
        "but do not freely redesign the product. "
        f"Scene direction: {scene}. "
        f"{REALISTIC_USAGE_CONTEXT_STYLE} "
        f"{USAGE_CONTEXT_BY_PREFIX.get(prefix, '')} "
        f"{SAFE_VALUE_STYLE} "
        f"{REPLACEABLE_CONTENTS_STYLE} "
        f"Hard restrictions: {rule['forbid']}. "
        "The product must remain complete, clear, commercially attractive, realistic, and recognizable. "
        "Square composition, 800x800-ready, product occupies about 28-42 percent of image height unless the scene needs a wider view. "
        f"Product code: {d_value}. Variation: {variation_hint or 'use a distinct composition, lighting and placement from other images of the same product family'}."
    )


def main() -> None:
    samples = {
        "L047060509": build_seedream_product_fusion_prompt(
            "L047",
            "L047060509",
            "realistic seaside grass path with a black metal arch frame decorated lightly with vines, premium outdoor ceremony atmosphere",
            "avoid cartoon style, use photographic realism and keep the arch frame visible",
        )
    }
    out = BASE / "outputs" / "product_specific_seedream_prompts" / "prompt_samples.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "samples": samples}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
