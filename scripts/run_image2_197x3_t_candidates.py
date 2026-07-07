from __future__ import annotations

import importlib.util
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from luxury_expanded_scene_banks_0616_2 import (
    DEFAULT_LUXURY_EXPANDED_SCENES,
    LUXURY_EXPANDED_SCENE_BANK,
    validate_luxury_scene_banks,
)


BASE_SCRIPT = Path(
    os.environ.get(
        "BASE_IMAGE2_SCRIPT",
        r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\run_0616_2_low_cost_t_candidates.py",
    )
)
OUT = Path(
    os.environ.get(
        "OUT_DIR",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702",
    )
)
WORKBOOK = Path(
    os.environ.get(
        "WORKBOOK",
        r"D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702\0616-2_197_最终回传_硬校验修复_L051060505_C列删第1图_20260702.xlsx",
    )
)
SETS = int(os.environ.get("SETS", "3"))
WORKERS = int(os.environ.get("WORKERS", "3"))
LIMIT = int(os.environ.get("LIMIT", "0"))
MODE = os.environ.get("MODE", "plan")

PLAN_PATH = OUT / "candidate_plan_197x3.json"
RESULTS_PATH = OUT / "candidate_results_197x3.json"
PROGRESS_PATH = OUT / "candidate_progress_197x3.jsonl"


EXPANDED_SCENE_BANK: dict[str, list[str]] = {
    "L042": [
        "wide expanded villa garden border scene, camera pulled back, flower bed edge and lawn path visible, product occupies 18-24 percent of image height, black spiral stakes shown as the original bundled stakes beside the edging roll, no invented long pins",
        "wide courtyard soil-edge landscaping scene with stone path and low plants, product placed along a real flower-bed border, product around 22 percent height, keep original roll, tabs, holes and black spiral stakes unchanged",
        "wide patio garden corner with raised bed, gravel strip and lawn, product installed only as garden edging, product around 20 percent height, stakes remain original accessory shape and are not rearranged into fence rods",
        "wide balcony planter border scene with soil trough and greenery, product around 24 percent height, exact green/black edging roll preserved, black spiral stakes laid naturally next to it",
        "wide residential front-yard flower-bed scene, natural daylight, product lower-right, product around 19 percent height, no text, no measurement graphic, no extra stakes or altered tabs",
        "wide garden path close-to-ground scene with premium plants and stone edging, product lower-left around 23 percent height, original perforated tabs and hole count frozen",
        "wide lawn repair scene beside a curved flower border, product centered but small, around 21 percent height, original black stakes remain bundled or lightly scattered, not redesigned",
        "wide backyard landscaping scene with mulch bed and clean grass, product around 18 percent height, use scene depth and background garden context, not a tight catalog crop",
        "wide courtyard planting bed with white wall and stone walkway, product around 25 percent height, exact roll geometry and tab pattern preserved",
        "wide outdoor garden-supply scene on a patio table near a flower bed, product around 22 percent height, black spiral stakes kept as original accessories with correct shape",
        "wide suburban garden renovation scene with half-finished flower border, product around 20 percent height, original spiral stakes grouped beside edging, no straight pins",
        "wide cottage garden edge beside brick walkway, product around 22 percent height, roll and perforated tabs preserved, stakes remain short black spiral accessories",
        "wide modern courtyard planter strip with gravel and ornamental grass, product around 21 percent height, no extra holes, no fence-like stake arrangement",
        "wide lawn-and-mulch transition scene with curved border, product lower-right around 23 percent height, black stakes visible but not redesigned",
        "wide outdoor shed workbench scene beside a flower bed, product around 24 percent height, garden context visible, no measurement graphics or text",
        "wide townhouse patio planting bed with pavers and low shrubs, product around 19 percent height, exact roll geometry and tab spacing frozen",
        "wide park-style garden border sample scene, product around 20 percent height, original bundled black spiral stakes placed naturally on soil",
        "wide raised vegetable bed edge scene, product around 22 percent height, product used only as edging, no new support rods or straight stakes",
        "wide side-yard landscaping scene with stepping stones, product around 21 percent height, keep black spiral stakes short and accessory-like",
        "wide nursery garden display scene with plants in background, product around 24 percent height, exact flexible edging roll, holes and tabs preserved",
    ],
    "L043": [
        "wide laundry folding table scene with wardrobe in background, product around 20 percent height, several folded shirts nearby but not covering holes, keep all board holes and small center hole exact",
        "wide bright walk-in closet scene, product on shelf with folded sweaters, product around 18 percent height, rear raised detail and panel seams frozen",
        "wide bedroom closet organization scene with open drawers and neutral textiles, product around 22 percent height, do not turn board into tray or pad",
        "wide home laundry room countertop scene, daylight window, product lower-right around 24 percent height, board outline and holes unchanged",
        "wide dorm wardrobe shelf scene with stacked shirts, product around 20 percent height, realistic scale relative to clothing, no huge board",
        "wide boutique closet packing table scene, product left side around 21 percent height, show environment depth and folded garments, not a close crop",
        "wide minimal white closet scene, product on light wood shelf, product around 19 percent height, rear raised part and small middle hole visible",
        "wide linen cabinet scene with towels and shirts, product center-right around 23 percent height, no redraw of hole positions",
        "wide wardrobe drawer organization scene, product partly on folding surface, product around 22 percent height, exact board hardware and panel seams preserved",
        "wide clean folding station beside closet mirror, product around 18 percent height, strong scene difference from sibling images, no generic plastic tray",
        "wide laundry sorting counter scene with woven baskets in background, product around 21 percent height, board holes and rear raised detail visible",
        "wide Scandinavian wardrobe room scene, product on pale wood folding bench around 19 percent height, realistic clothing scale, no tray transformation",
        "wide linen closet shelf scene with stacked towels, product around 20 percent height, keep small center hole and all panel seams exact",
        "wide apartment bedroom folding corner, product lower-left around 23 percent height, shirts nearby but not covering product structure",
        "wide family laundry room island scene, product center-right around 22 percent height, rear raised edge and holes frozen",
        "wide compact dorm closet scene, product around 20 percent height, gray/white board exact, no oversized scale",
        "wide boutique apparel prep table scene, product around 21 percent height, folded clothing as loose props, board outline unchanged",
        "wide open wardrobe drawer scene, product around 18 percent height, strong depth and varied palette, no generic mat redesign",
        "wide neutral walk-in closet floor-and-shelf scene, product around 22 percent height, holes, seams and raised detail must remain",
        "wide modern laundry cabinet scene with clean countertop, product around 24 percent height, board complete and not cropped",
    ],
    "L047": [
        "wide garden arch scene on grass path, arch legs insert directly into soil/grass, no base plates, no pedestal, no extra feet, product around 26 percent height",
        "wide flower-bed entrance scene, single black arch only, symmetrical legs planted in soil, no base, product around 24 percent height",
        "wide courtyard stone path scene with greenery, arch stands by legs only, no bottom base or platform, product around 23 percent height",
        "wide wedding garden path scene with light flowers attached to existing arch only, no base plates, no second arch, product around 25 percent height",
        "wide patio lawn border scene, arch lower-center, legs go into grass, no invented support base, product around 22 percent height",
        "wide villa backyard walkway, single black arch on soil, equal left/right leg count, no base, product around 24 percent height",
        "wide garden gate decoration scene, product complete and centered, no bottom board or foot stand, product around 23 percent height",
        "wide gravel garden path scene, arch legs inserted into ground, no base plates, flowers optional only on original rods",
        "wide rose garden entrance scene, one black arch, product around 26 percent height, no extra rods or duplicate arches",
        "wide balcony garden display scene with planter boxes, arch supported by original legs only, no pedestal or base",
        "wide backyard lawn ceremony path, one black arch, legs inserted into grass, no base plate, product around 24 percent height",
        "wide courtyard flower walkway with stone border, arch complete and single, no pedestal, product around 23 percent height",
        "wide villa garden side path with shrubs, arch legs go directly into soil, no bottom board, product around 25 percent height",
        "wide garden gate preview scene with gravel and greenery, single black arch, equal support legs, product around 22 percent height",
        "wide patio planter entrance scene, arch planted in soil boxes, no foot stand, product around 24 percent height",
        "wide outdoor wedding lawn with simple floral accents, flowers attached only to existing arch rods, no second arch or base",
        "wide cottage rose path scene, arch lower-center, original legs only, no invented feet, product around 25 percent height",
        "wide garden nursery display row, arch on grass/soil, no base plates or platforms, product around 23 percent height",
        "wide courtyard pergola-adjacent scene, black arch remains separate single product, no extra rods, no base, product around 22 percent height",
        "wide park garden photo spot scene, one black arch with original leg count, no pedestal, product around 24 percent height",
    ],
    "L063": [
        "wide empty boutique gym scene, dark rubber floor and wall mirrors, no people or body parts, product on floor around 24 percent height, exact board outline and holes frozen",
        "wide bright professional fitness studio, wood floor and exercise mat, no people, product lower-left around 22 percent height, keep handles, slots and accessories exact",
        "wide garage gym with concrete floor and neutral wall, no people, product around 25 percent height, use contact shadow only, do not redraw board",
        "wide wellness studio with stone wall and olive-gray mat, no people, product center-right around 23 percent height, accessories visible but unchanged",
        "wide minimal white training room, pale floor, distant gym equipment only, no demonstration, product around 26 percent height",
        "wide home workout corner on rubber mat, no person, no hands, product around 24 percent height, exact surface pattern preserved",
        "wide premium Pilates studio with clean mat area, no people, product around 22 percent height, board stays flat and complete",
        "wide training room with storage rack far behind, no person using product, product lower-right around 25 percent height",
        "wide neutral fitness studio with side daylight, no human model, product around 23 percent height, no invented rails or pedals",
        "wide empty exercise area with mat and towel in background only, product around 24 percent height, fixed PNG-like fidelity",
        "wide compact home gym corner with rubber tiles, no person, product around 23 percent height, exact board holes, handles and accessories preserved",
        "wide professional training room with wall bars far behind, no people, product lower-right around 22 percent height, no product-use action",
        "wide bright Pilates studio with mirrors and wood floor, no people, product around 24 percent height, fixed board silhouette",
        "wide neutral basement gym scene, no human body parts, product around 25 percent height, rails and holes unchanged",
        "wide empty physiotherapy-style exercise room, no patient, product around 22 percent height, exact board surface pattern",
        "wide premium athletic studio with gray mat lane, no people, product center-left around 23 percent height, no accessory redesign",
        "wide home workout storage corner with dumbbells far in background, no person, product around 24 percent height, do not merge with props",
        "wide clean yoga studio floor scene, no people, product around 21 percent height, product remains the same fitness board not a yoga mat",
        "wide sports club training floor, no people, product around 25 percent height, exact handles, pedals and bands frozen",
        "wide empty garage workout bay with daylight door, no people, product around 23 percent height, fixed cutout-like fidelity",
    ],
    "L082": [
        "wide under-sink kitchen cabinet scene, product shows left-right expandable function under cabinet, no side drawer rails, product around 24 percent height",
        "wide pantry shelf organization scene, telescoping left-right structure visible, no extra tracks or side rails, product around 22 percent height",
        "wide bathroom vanity under-cabinet scene, product placed on cabinet floor, extendable width visible, product around 23 percent height",
        "wide kitchen sink-side lower cabinet scene, product front-facing, no sliding rail hardware on side, product around 24 percent height",
        "wide utility cabinet storage scene with bottles as loose contents, product around 22 percent height, shelf/body outline frozen",
        "wide closet shelf organizer scene, product lower-center, left-right extension shown, no drawer mechanism invented",
        "wide modern kitchen cabinet interior, product around 25 percent height, support surfaces realistic, no side/bottom rail hallucination",
        "wide laundry cabinet storage scene, product in cabinet, telescoping relation clear, no extra tracks",
        "wide compact apartment kitchen cabinet scene, product around 23 percent height, front structure preserved",
        "wide pantry counter lower shelf scene, product around 22 percent height, left and right extension visible and believable",
        "wide pull-out under-cabinet organizer scene, product around 24 percent height, left-right extension visible, no side rails invented",
        "wide kitchen lower-shelf scene with spice bottles as loose contents, product around 22 percent height, no drawer slides on sides",
        "wide sink base cabinet scene with cleaning bottles, product center-right around 23 percent height, telescoping relationship clear",
        "wide apartment pantry cabinet interior, product around 21 percent height, exact shelf/body outline and support surfaces",
        "wide bathroom storage cabinet scene with towels in background, product around 22 percent height, no side tracks or bottom rails",
        "wide utility room cabinet floor scene, product lower-left around 24 percent height, expandable width shown front-facing",
        "wide kitchen island lower shelf scene, product around 23 percent height, no generic drawer redesign",
        "wide narrow cabinet organization scene, product around 22 percent height, left-right sliding extension visible without extra hardware",
        "wide modern pantry pull-out area, product around 24 percent height, frame and shelf silhouette frozen",
        "wide under-stove cabinet storage scene, product around 21 percent height, no rail hardware beyond original product",
    ],
    "L086": [
        "wide kitchen countertop organizer scene, black/walnut or beige-wood product only, no white product material, product around 24 percent height",
        "wide pantry counter scene with small appliances far behind, no white rack, product around 23 percent height, drawers/baskets and top board unchanged",
        "wide coffee station sideboard scene, product lower-right, no white product, product around 22 percent height, front grid and side frame frozen",
        "wide closet storage counter scene, product around 24 percent height, use original non-white material only, no industrial shelf merging",
        "wide modern kitchen island background, product on counter around 23 percent height, black/walnut/beige-wood product only, never white",
        "wide appliance station scene with toaster far behind, product around 22 percent height, no white variant, exact two drawer/basket units preserved",
        "wide pantry shelf scene, product center-left, no white material, product around 24 percent height, legs and vertical supports frozen",
        "wide home sideboard storage scene, product around 23 percent height, avoid industrial workshop references, no white rack",
        "wide compact kitchen storage scene, product around 25 percent height, original non-white product color only",
        "wide utility cabinet countertop scene, product around 22 percent height, no white source or white generated product allowed",
        "wide warm walnut pantry sideboard scene, product around 23 percent height, black/walnut/beige-wood only, exact drawer/basket units",
        "wide cool gray kitchen countertop scene with appliance station far behind, product around 22 percent height, no white rack",
        "wide small apartment coffee bar scene, product lower-left around 24 percent height, non-white product only, front grid frozen",
        "wide breakfast station side counter scene, product around 23 percent height, no industrial shelving merge, no white material",
        "wide walk-in pantry shelf scene with jars as loose contents, product around 22 percent height, original non-white rack preserved",
        "wide home appliance corner with microwave far behind, product center-right around 24 percent height, no white variant",
        "wide kitchen storage nook with wood cabinets, product around 23 percent height, legs, supports and top board exact",
        "wide closet utility shelf scene, product around 22 percent height, black/walnut/beige-wood material only",
        "wide sideboard organizer scene with bowls and cups as loose props, product around 24 percent height, drawer faces unchanged",
        "wide premium pantry counter scene with stone backsplash, product around 23 percent height, no white generated product",
    ],
    "L095": [
        "wide balcony planter scene with railing and city daylight, product around 22 percent height, hanging/planter structure clear, green plants varied",
        "wide garden patio planting corner, stone floor and outdoor plants, product around 23 percent height, not the same generic garden background",
        "wide greenhouse bench scene with soil bags and seedlings in background, product around 24 percent height, product structure unchanged",
        "wide sunny terrace scene with wall-mounted planter area, product around 22 percent height, clear 2/3-grid planter specification",
        "wide courtyard wall garden scene with climbing greenery, product lower-left around 23 percent height, waterproof planting box visible",
        "wide apartment balcony herb garden scene, product around 24 percent height, railing and pots visible, no repeated stock background",
        "wide outdoor porch planting scene with wooden deck, product around 22 percent height, planter cells and frame frozen",
        "wide backyard raised-bed scene, product near patio edge around 23 percent height, natural soil/greenery context",
        "wide modern balcony corner with white wall and terracotta pots, product around 24 percent height, strong color difference from sibling images",
        "wide garden workbench scene with seedlings and hand tools far away, product around 22 percent height, no text or logo, structure preserved",
        "wide herb balcony scene with black railing and morning light, product around 23 percent height, planter cells visible and distinct",
        "wide courtyard herb wall scene with stone wall and vines, product lower-right around 22 percent height, no repeated green backdrop",
        "wide greenhouse aisle scene with seedlings and misty daylight, product around 24 percent height, frame and hanging structure clear",
        "wide rooftop terrace planter scene with city background, product around 22 percent height, varied palette and real support surface",
        "wide porch corner with wooden bench and potted herbs, product around 23 percent height, cells and waterproof box shape frozen",
        "wide backyard potting table scene with soil tray in background, product around 24 percent height, no close-up-only composition",
        "wide apartment window herb garden scene, product around 22 percent height, bright indoor-outdoor balcony context",
        "wide garden fence planter display scene, product around 23 percent height, hanging/holder structure visible and unchanged",
        "wide Mediterranean patio planting scene with clay pots and white wall, product around 24 percent height, strong color change from sibling scenes",
        "wide modern terrace vegetable planter scene with raised-bed context, product around 22 percent height, grid/box specification preserved",
    ],
}


DEFAULT_EXPANDED_SCENES = [
    "wide expanded lifestyle scene with real room depth, camera pulled back, product around 20 percent of image height, lower-left placement, safe unbranded props",
    "wide expanded lifestyle scene, product center-right around 24 percent height, deeper background perspective and natural daylight",
    "wide expanded realistic use scene, product lower-right around 22 percent height, strong contact shadow and non-templated background",
    "wide expanded premium home scene, product around 25 percent height, visible surrounding space and varied color palette",
    "wide expanded catalog lifestyle scene, product around 21 percent height, believable support surface and larger environment",
    "wide expanded practical use scene, product around 23 percent height, different room scale and prop arrangement",
    "wide expanded natural daylight scene, product around 20 percent height, more negative space and realistic depth",
    "wide expanded high-value scene, product around 24 percent height, safe household props and no repeated background pattern",
    "wide expanded scene with product on correct support surface, product around 22 percent height, different placement and camera distance",
    "wide expanded ecommerce lifestyle scene, product around 23 percent height, distinct color palette and composition from sibling images",
    "wide expanded home-use scene with product lower-left around 21 percent height, room or outdoor depth clearly visible, safe unbranded props",
    "wide expanded premium scene with product center-left around 24 percent height, different surface material and natural side light",
    "wide expanded practical-use scene with product lower-right around 20 percent height, realistic surroundings and contact shadow",
    "wide expanded lifestyle scene with product mid-frame around 23 percent height, varied background architecture and color palette",
    "wide expanded scene with pulled-back camera and product around 22 percent height, no tight crop, no repeated generic backdrop",
    "wide expanded product-in-use environment, product around 25 percent height, support surface and gravity obvious",
    "wide expanded safe household scene with product around 21 percent height, foreground/background depth and varied props",
    "wide expanded high-value environment, product around 24 percent height, different composition and lighting from sibling images",
    "wide expanded category-correct scene, product around 22 percent height, clear surrounding space and non-template background",
    "wide expanded realistic ecommerce scene, product around 23 percent height, visible context, believable scale and contact shadow",
]

EXPANDED_SCENE_BANK.update(LUXURY_EXPANDED_SCENE_BANK)
DEFAULT_EXPANDED_SCENES = DEFAULT_LUXURY_EXPANDED_SCENES


PREFIX_HARD_LOCK_APPEND = {
    "L042": "L042 hard lock: the black spiral stakes/nails must keep the original short spiral stake shape and correct quantity feeling; do not create long straight pins, fence rods, loose black sticks, outward-facing spikes, or decorative bars. Prefer wider garden context over tight product redraw.",
    "L043": "L043 hard lock: if the board holes, small center hole, rear raised detail, panel seams, or realistic scale cannot be preserved, this candidate is invalid. Do not make all L043 scenes a similar close laundry crop; use the wide expanded scene lane.",
    "L047": "L047 hard lock: no bottom base, no base plate, no pedestal, no platform, no extra feet. The arch legs insert directly into soil, grass, gravel, or planter ground.",
    "L063": "L063 hard lock: no people, no hands, no body parts, no exercise demonstration. Keep the exact fitness board as a fixed cutout-like product on the floor or mat.",
    "L082": "L082 hard lock: show the left-right expandable/telescoping function; do not add side rails, drawer rails, bottom tracks, or any slide hardware not present in the source.",
    "L086": "L086 hard lock: this group has no white product. Never use or generate a white rack/shelf/product; use only black, walnut, original wood, or beige-wood/non-white material from approved sources.",
    "L095": "L095 hard lock: rotate balcony, patio, greenhouse, terrace, courtyard, porch, and garden workbench scenes; do not repeat the same generic garden/green backdrop across the prefix.",
}


MIN_SCENES_PER_PREFIX = 20


def validate_scene_banks() -> None:
    validate_luxury_scene_banks(sorted(EXPANDED_SCENE_BANK))
    short = {
        prefix: len(scenes)
        for prefix, scenes in EXPANDED_SCENE_BANK.items()
        if len(scenes) < MIN_SCENES_PER_PREFIX
    }
    if len(DEFAULT_EXPANDED_SCENES) < MIN_SCENES_PER_PREFIX:
        short["DEFAULT"] = len(DEFAULT_EXPANDED_SCENES)
    if short:
        detail = ", ".join(f"{prefix}:{count}" for prefix, count in sorted(short.items()))
        raise RuntimeError(f"Expanded scene bank must have at least {MIN_SCENES_PER_PREFIX} scenes per prefix; short banks: {detail}")


def load_base_module():
    os.environ["WORKBOOK"] = str(WORKBOOK)
    os.environ["OUT_DIR"] = str(OUT)
    spec = importlib.util.spec_from_file_location("image2_base_0616_2", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base image2 script: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["image2_base_0616_2"] = module
    spec.loader.exec_module(module)
    module.OUT = OUT
    module.GENERATED = OUT / "generated"
    module.PLAN_PATH = OUT / "base_candidate_plan.json"
    module.RESULTS_PATH = OUT / "base_candidate_results.json"
    module.PROGRESS_PATH = OUT / "base_candidate_progress.jsonl"
    return module


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def load_feedback_bad_sources() -> set[str]:
    paths: list[Path] = []
    env_path = os.environ.get("MATERIAL_FEEDBACK_LOCK")
    if env_path:
        paths.append(Path(env_path))
    paths.extend(sorted(OUT.glob("feedback_lock*_*.json")))

    bad: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        data = load_json(path, {})
        for source in (data.get("bad_sources") or {}).values():
            values = source if isinstance(source, list) else [source]
            for value in values:
                if value:
                    text = str(value)
                    bad.update({text, Path(text).name, Path(text).stem})
        for item in (data.get("feedback") or {}).values():
            if item.get("reject_material") and item.get("source_png"):
                text = str(item["source_png"])
                bad.update({text, Path(text).name, Path(text).stem})
    return bad


def wrap_source_filter(module):
    bad_sources = load_feedback_bad_sources()
    if not bad_sources:
        return

    original_list_sources = module.list_sources

    def list_sources(prefix: str):
        records = original_list_sources(prefix)
        filtered = []
        for record in records:
            haystack = " ".join(
                str(record.get(key) or "")
                for key in ("source_id", "material_id", "source_path", "library_path", "library_rel", "path")
            )
            path = record.get("path")
            if path:
                haystack += f" {Path(path).name} {Path(path).stem}"
            if any(token and token in haystack for token in bad_sources):
                continue
            filtered.append(record)
        if prefix == "L086":
            filtered = [
                record
                for record in filtered
                if not re.search(
                    r"白|white|纯白",
                    " ".join(
                        str(record.get(key) or "")
                        for key in ("source_id", "material_id", "source_path", "library_path", "library_rel", "path")
                    ),
                    re.I,
                )
            ]
        return filtered

    module.list_sources = list_sources


def expanded_scene_for(item: dict, prefix_index: int) -> str:
    prefix = item.get("prefix") or ""
    scenes = EXPANDED_SCENE_BANK.get(prefix) or DEFAULT_EXPANDED_SCENES
    scene_index = prefix_index % len(scenes)
    return scenes[scene_index]


def build_expanded_plan(module) -> list[dict]:
    by_set: dict[int, list[dict]] = {}
    original_shift = os.environ.get("SOURCE_SHIFT")
    for set_no in range(1, SETS + 1):
        os.environ["SOURCE_SHIFT"] = str(set_no - 1)
        by_set[set_no] = module.build_plan()
    if original_shift is None:
        os.environ.pop("SOURCE_SHIFT", None)
    else:
        os.environ["SOURCE_SHIFT"] = original_shift

    expanded: list[dict] = []
    prefix_index: defaultdict[str, int] = defaultdict(int)
    for set_no, plan in by_set.items():
        for item in plan:
            original_d = item["d"]
            candidate_id = f"{original_d}__set{set_no}"
            item = dict(item)
            item["original_d"] = original_d
            item["candidate_id"] = candidate_id
            item["d"] = candidate_id
            item["set_no"] = set_no
            item["run_type"] = "image2_197x3_candidate_pool"
            item["scene_lane"] = expanded_scene_for(item, prefix_index[item["prefix"]])
            item["color_lane"] = f"set_{set_no}_color_lane"
            item["composition_lane"] = f"set_{set_no}_composition_lane"
            hard_lock = PREFIX_HARD_LOCK_APPEND.get(item["prefix"], "")
            item["prompt_append"] = (
                f"This is candidate set {set_no} of {SETS} for exact D {original_d}. "
                "It is a spare candidate pool for future replacement, not an immediate workbook writeback. "
                "Use the assigned expanded-scene lane and source PNG rotation to make this candidate visibly different from sibling images for the same exact D and same L0xx. "
                f"Expanded scene directive: {item['scene_lane']}. "
                "Use a camera-pulled-back expanded lifestyle scene with real spatial depth; avoid tight product-only catalog crops unless the product-specific lock requires strict front view. "
                f"{hard_lock} "
                "Do not reuse any deleted/rejected/wrong-color image and do not imitate old all_sku_tfirst or Ali single-SKU outputs."
            )
            prefix_index[item["prefix"]] += 1
            expanded.append(item)

    save_json(PLAN_PATH, expanded)
    write_plan_summary(expanded)
    return expanded


def write_plan_summary(items: list[dict]) -> None:
    prefix_counts = Counter(item["prefix"] for item in items)
    source_counts = Counter((item["prefix"], item.get("source_id") or "") for item in items)
    rows = [
        "# 197 D x 3 image2 candidate plan",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- workbook: `{WORKBOOK}`",
        f"- output: `{OUT}`",
        f"- target_candidates: {len(items)}",
        f"- unique_original_d: {len(set(item['original_d'] for item in items))}",
        f"- sets: {SETS}",
        f"- provider/model: APIMart / gpt-image-2",
        f"- purpose: spare T-first candidate pool for future replacement, no workbook writeback",
        "",
        "## Prefix Counts",
        "",
        "| prefix | candidates |",
        "|---|---:|",
    ]
    for prefix in sorted(prefix_counts):
        rows.append(f"| {prefix} | {prefix_counts[prefix]} |")
    rows.extend(["", "## Source Rotation Sample", "", "| prefix | source_id | uses |", "|---|---|---:|"])
    for (prefix, source_id), count in sorted(source_counts.items())[:200]:
        rows.append(f"| {prefix} | {str(source_id).replace('|','/')} | {count} |")
    (OUT / "candidate_plan_197x3.md").write_text("\n".join(rows), encoding="utf-8")


def wrap_prompt_builder(module):
    original_build_prompt = module.build_prompt

    def build_prompt(item: dict, index_in_prefix: int, prefix_total: int) -> str:
        prompt = original_build_prompt(item, index_in_prefix, prefix_total)
        append = item.get("prompt_append")
        if append:
            prompt = f"{prompt} {append}"
        return prompt

    module.build_prompt = build_prompt


def existing_candidates() -> set[str]:
    done = set()
    for item in load_json(RESULTS_PATH, []):
        if item.get("candidate_id") and item.get("local_path") and Path(item["local_path"]).exists():
            done.add(item["candidate_id"])
    return done


def run_candidates(module, items: list[dict]) -> list[dict]:
    prefix_totals = Counter(item["prefix"] for item in items)
    prefix_seen = defaultdict(int)
    done = existing_candidates()
    queue = []
    for item in items:
        index = prefix_seen[item["prefix"]]
        prefix_seen[item["prefix"]] += 1
        if item["candidate_id"] in done:
            continue
        if not item.get("source_png"):
            continue
        queue.append((item, index, prefix_totals[item["prefix"]]))
    if LIMIT > 0:
        queue = queue[:LIMIT]

    results = load_json(RESULTS_PATH, [])
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(module.apimart_submit, item, index, total): item for item, index, total in queue}
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                result["status"] = result.get("status") or "ok"
            except Exception as error:
                result = {
                    "provider": "APIMart",
                    "model": "gpt-image-2",
                    "status": "error",
                    "error": str(error),
                    "d": item["candidate_id"],
                    "prefix": item["prefix"],
                    "rows": item.get("rows", []),
                    "source_png": item.get("source_png"),
                    "cost_usd_est": 0,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            result["candidate_id"] = item["candidate_id"]
            result["original_d"] = item["original_d"]
            result["set_no"] = item["set_no"]
            result["run_type"] = "image2_197x3_candidate_pool"
            result["scene_lane"] = item.get("scene_lane")
            result["color_lane"] = item.get("color_lane")
            result["composition_lane"] = item.get("composition_lane")
            results.append(result)
            with PROGRESS_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            save_json(RESULTS_PATH, results)
            print(
                f"{result.get('status')} {item['candidate_id']} {result.get('elapsed_sec','-')}s {result.get('error','')[:160]}",
                flush=True,
            )
    return results


def _escape(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _url_for_local_path(value: str | None) -> str:
    if not value:
        return ""
    path = Path(value)
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path

    mappings = [
        (OUT.resolve(), f"/outputs/{OUT.name}"),
        (Path(r"C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs").resolve(), "/outputs"),
    ]
    for root, prefix in mappings:
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            continue
        return prefix + "/" + quote(rel.as_posix(), safe="/")
    return ""


def _load_success_results() -> list[dict]:
    results = load_json(RESULTS_PATH, [])
    success = []
    for item in results:
        local_path = item.get("local_path")
        if item.get("status") == "ok" and local_path and Path(local_path).exists():
            success.append(item)
    return success


def build_review(module=None) -> Path:
    results = _load_success_results()
    by_d: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        by_d[item.get("original_d") or item.get("d") or item.get("candidate_id")].append(item)
    for items in by_d.values():
        items.sort(key=lambda item: (int(item.get("set_no") or 0), item.get("candidate_id") or ""))

    prefix_counts = Counter((d or "")[:4] for d in by_d)
    generated_counts = Counter((item.get("original_d") or item.get("d") or "")[:4] for item in results)
    stats_rows = "\n".join(
        f"<tr><td>{_escape(prefix)}</td><td>{prefix_counts[prefix]}</td><td>{generated_counts[prefix]}</td></tr>"
        for prefix in sorted(prefix_counts)
    )

    cards = []
    for original_d in sorted(by_d):
        items = by_d[original_d]
        first = items[0]
        source_url = _url_for_local_path(first.get("source_png"))
        set_figures = []
        for item in items:
            candidate_id = item.get("candidate_id") or item.get("d") or original_d
            image_url = _url_for_local_path(item.get("local_path"))
            prompt = item.get("prompt") or ""
            set_no = item.get("set_no") or "?"
            set_figures.append(
                f"""
                <section class="candidate" data-candidate="{_escape(candidate_id)}">
                  <figure>
                    <img class="zoomable generated" src="{_escape(image_url)}" loading="lazy" alt="{_escape(candidate_id)}">
                    <figcaption>set{_escape(set_no)} · {_escape(candidate_id)}</figcaption>
                  </figure>
                  <div class="actions">
                    <button onclick="mark('{_escape(candidate_id)}','keep')">保留</button>
                    <button onclick="mark('{_escape(candidate_id)}','redo')">重做</button>
                    <button onclick="mark('{_escape(candidate_id)}','reject')">不要</button>
                    <input id="fb-{_escape(candidate_id)}" placeholder="反馈：错误点/可保留原因">
                    <span class="status" id="st-{_escape(candidate_id)}">未筛选</span>
                  </div>
                  <details><summary>prompt</summary><pre>{_escape(prompt)}</pre></details>
                </section>
                """
            )
        cards.append(
            f"""
            <article class="card" data-d="{_escape(original_d)}" data-prefix="{_escape(first.get('prefix'))}">
              <div class="meta"><b>{_escape(first.get('prefix'))}</b> · {_escape(original_d)} · rows {_escape(','.join(map(str, first.get('rows') or [])))} · source {_escape(first.get('source_kind'))}:{_escape(first.get('source_id'))}</div>
              <div class="compare">
                <figure class="source">
                  <img src="{_escape(source_url)}" loading="lazy" alt="source PNG">
                  <figcaption>source PNG</figcaption>
                </figure>
                <div class="sets">{''.join(set_figures)}</div>
              </div>
            </article>
            """
        )

    target = OUT / "0616_2_image2_197x3_t_candidates_review.html"
    legacy_target = OUT / "0616_2_low_cost_t_candidates_review.html"
    generated_at = datetime.now().isoformat(timespec="seconds")
    body = "\n".join(cards)
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>0616-2 image2 197x3 T首图候选复核</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;margin:0;background:#f6f4ef;color:#1f2933}}
header{{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #ddd;padding:12px 18px;box-shadow:0 2px 10px rgba(0,0,0,.06)}}
.wrap{{padding:16px;max-width:1680px;margin:auto}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;margin:0 0 18px 0;padding:12px;box-shadow:0 1px 4px rgba(0,0,0,.04)}}
.meta{{font-size:14px;margin-bottom:10px;color:#374151}}
.compare{{display:grid;grid-template-columns:260px 1fr;gap:14px;align-items:start}}
.sets{{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:12px}}
figure{{margin:0;background:#fafafa;border:1px solid #e5e7eb;border-radius:6px;padding:8px;text-align:center}}
figure img{{max-width:100%;height:240px;object-fit:contain;background:#fff;border-radius:4px}}
.source img{{height:260px}}
figcaption{{font-size:12px;color:#4b5563;margin-top:6px;word-break:break-all}}
.candidate{{border:1px solid #e5e7eb;border-radius:6px;padding:8px;background:#fcfcfd}}
.candidate.keep{{border-color:#16a34a;background:#f0fdf4}}
.candidate.redo{{border-color:#f59e0b;background:#fffbeb}}
.candidate.reject{{border-color:#ef4444;background:#fef2f2}}
.actions{{display:flex;gap:6px;margin-top:8px;align-items:center;flex-wrap:wrap}}
button{{border:0;border-radius:6px;padding:6px 10px;background:#7c3aed;color:white;cursor:pointer}}
button:nth-child(2){{background:#f59e0b}} button:nth-child(3){{background:#ef4444}}
button.active{{outline:3px solid rgba(37,99,235,.35);box-shadow:0 0 0 2px #fff inset}}
input{{flex:1;min-width:160px;padding:6px;border:1px solid #ddd;border-radius:6px}}
.status{{font-size:12px;font-weight:700;color:#6b7280;min-width:52px}}
details{{margin-top:8px}} pre{{white-space:pre-wrap;font-size:11px;max-height:160px;overflow:auto;background:#111827;color:#f9fafb;padding:8px;border-radius:6px}}
table{{border-collapse:collapse}} th,td{{border:1px solid #ddd;padding:4px 8px;font-size:12px}}
#exportBox{{width:100%;height:180px;margin-top:10px}}
#modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.72);z-index:999;align-items:center;justify-content:center}}
#modal img{{max-width:94vw;max-height:94vh;background:#fff}}
@media(max-width:1100px){{.compare{{grid-template-columns:1fr}}.sets{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header>
  <h2>0616-2 image2 197x3 T首图候选复核</h2>
  <div>generated_at: {_escape(generated_at)} · unique D: {len(by_d)} · candidates: {len(results)} · sets: {SETS}</div>
  <p>这是备用候选池，不代表已通过，不自动写回表格。每个 D 显示 source PNG + set1/set2/set3。</p>
  <button onclick="exportFeedback()">导出筛选JSON</button>
  <button onclick="clearFeedback()">清空本页筛选</button>
  <button onclick="window.scrollTo({{top:0,behavior:'smooth'}})">回顶部</button>
  <details><summary>按L0xx统计</summary><table><tr><th>L0xx</th><th>D数</th><th>候选数</th></tr>{stats_rows}</table></details>
  <textarea id="exportBox" placeholder="导出的反馈 JSON 会出现在这里"></textarea>
</header>
<main class="wrap">{body}</main>
<div id="modal" onclick="this.style.display='none'"><img id="modalImg"></div>
<script>
const REVIEW='0616_2_image2_197x3_t_candidates_review';
let feedback = safeLoadFeedback();
function storageGet(key) {{
  try {{
    if (window.localStorage) return window.localStorage.getItem(key);
  }} catch (err) {{}}
  return null;
}}
function storageSet(key, value) {{
  try {{
    if (window.localStorage) window.localStorage.setItem(key, value);
  }} catch (err) {{}}
}}
function storageRemove(key) {{
  try {{
    if (window.localStorage) window.localStorage.removeItem(key);
  }} catch (err) {{}}
}}
function safeLoadFeedback() {{
  try {{
    return JSON.parse(storageGet(REVIEW + ':feedback') || '{{}}');
  }} catch (err) {{
    return {{}};
  }}
}}
window.liveFeedbackValue = function liveFeedbackValue(id) {{
  const el = document.getElementById('fb-' + id);
  return el ? el.value : '';
}};
function paintDecision(id, decision) {{
  const input = document.getElementById('fb-' + id);
  const section = document.querySelector('[data-candidate="' + CSS.escape(id) + '"]');
  const status = document.getElementById('st-' + id);
  if (input) input.style.borderColor = decision === 'keep' ? '#16a34a' : (decision === 'redo' ? '#f59e0b' : '#ef4444');
  if (section) {{
    section.classList.remove('keep', 'redo', 'reject');
    section.classList.add(decision);
    section.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
    const index = decision === 'keep' ? 0 : (decision === 'redo' ? 1 : 2);
    const btn = section.querySelectorAll('button')[index];
    if (btn) btn.classList.add('active');
  }}
  if (status) {{
    status.textContent = decision === 'keep' ? '已保留' : (decision === 'redo' ? '已重做' : '已不要');
    status.style.color = decision === 'keep' ? '#16a34a' : (decision === 'redo' ? '#d97706' : '#dc2626');
  }}
}}
window.mark = function mark(id, decision) {{
  feedback[id] = {{decision, feedback: window.liveFeedbackValue(id), ts: new Date().toISOString()}};
  storageSet(REVIEW + ':feedback', JSON.stringify(feedback));
  paintDecision(id, decision);
}};
window.exportFeedback = function exportFeedback() {{
  Object.keys(feedback).forEach(id => feedback[id].feedback = window.liveFeedbackValue(id) || feedback[id].feedback || '');
  const data = {{review: REVIEW, exported_at: new Date().toISOString(), feedback}};
  document.getElementById('exportBox').value = JSON.stringify(data, null, 2);
  navigator.clipboard && navigator.clipboard.writeText(document.getElementById('exportBox').value).catch(()=>{{}});
}};
window.clearFeedback = function clearFeedback() {{
  if (!confirm('清空本页筛选反馈？')) return;
  feedback = {{}};
  storageRemove(REVIEW + ':feedback');
  document.querySelectorAll('.candidate').forEach(el => el.classList.remove('keep', 'redo', 'reject'));
  document.querySelectorAll('button.active').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.status').forEach(el => {{el.textContent='未筛选'; el.style.color='#6b7280';}});
  document.querySelectorAll('input[id^="fb-"]').forEach(el => {{el.value=''; el.style.borderColor='#ddd';}});
}};
document.querySelectorAll('.zoomable').forEach(img => img.addEventListener('click', () => {{
  document.getElementById('modalImg').src = img.src;
  document.getElementById('modal').style.display = 'flex';
}}));
Object.entries(feedback).forEach(([id, item]) => {{
  const input = document.getElementById('fb-' + id);
  if (input) {{
    input.value = item.feedback || '';
    paintDecision(id, item.decision);
  }}
}});
</script>
</body>
</html>"""
    target.write_text(page, encoding="utf-8")
    legacy_target.write_text(page, encoding="utf-8")
    return target


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    validate_scene_banks()
    module = load_base_module()
    wrap_source_filter(module)
    wrap_prompt_builder(module)
    items = build_expanded_plan(module)
    missing_source = sum(1 for item in items if not item.get("source_png"))
    summary = {
        "mode": MODE,
        "workbook": str(WORKBOOK),
        "out": str(OUT),
        "sets": SETS,
        "target_candidates": len(items),
        "unique_original_d": len(set(item["original_d"] for item in items)),
        "missing_source": missing_source,
        "workers": WORKERS,
        "limit": LIMIT,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    if MODE == "run":
        run_candidates(module, items)
    review = build_review(module)
    print(f"REVIEW={review}", flush=True)


if __name__ == "__main__":
    main()
