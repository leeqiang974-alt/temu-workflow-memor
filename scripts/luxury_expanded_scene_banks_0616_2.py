from __future__ import annotations

from dataclasses import dataclass


MIN_SCENES_PER_PREFIX = 20

LUXURY_CUES = (
    "unbranded high-end residential styling, natural stone or travertine texture, walnut or oak accents, "
    "plain ceramic decor, brushed metal details, linen or cotton textiles, clean editorial daylight, "
    "premium Temu competitor composition without logos, monograms, readable brand text, screens, fire, candles, alcohol, toys, medicines, or weapons"
)

COMMON_FRAME_RULE = (
    "Camera pulled back; show foreground, midground and background depth. The product must be complete, clear, "
    "realistically supported by the correct surface, with natural contact shadow. The product should occupy about "
    "18-26 percent of image height unless the product lock requires slightly larger inspection scale. Do not make a tight product crop."
)


@dataclass(frozen=True)
class PrefixProfile:
    category: str
    product: str
    fixed: str
    placement: str


SCENE_LANES: dict[str, list[str]] = {
    "garden_border": [
        "luxury villa garden walkway with pale limestone path, clipped grass, layered flower bed and low stone edging",
        "modern courtyard planting strip with travertine pavers, ornamental grasses, charcoal planter wall and deep lawn background",
        "boutique townhouse patio garden with raised soil bed, gravel band, sculptural ceramic planters and clean white exterior wall",
        "premium backyard landscape renovation scene with curved mulch border, manicured lawn and walnut-toned garden bench far behind",
        "architect-designed balcony planter trough scene with matte stone floor, black railing, herbs and city daylight beyond",
        "coastal villa side-yard path with white stucco wall, rosemary beds, pale gravel and soft overcast luxury daylight",
        "contemporary courtyard flower border beside large-format stone tiles, layered shrubs and a quiet water-feature wall far behind",
        "high-end garden supply workbench beside a real flower bed, stone tabletop, linen gloves and unbranded ceramic pots in background",
        "minimal Japanese-inspired courtyard with gravel, mossy planting beds, stepping stones and deep calm negative space",
        "premium nursery garden display lane with potted shrubs, pale stone floor and soft green depth, not a catalog close-up",
        "villa front-yard edging installation with clean soil line, lawn curve, trimmed boxwood and distant entrance path",
        "modern terrace herb-bed border with raised corten-style planter, pale stone deck and glass railing background",
        "Mediterranean courtyard planting bed with limewash wall, terracotta pots, olive greenery and warm but natural daylight",
        "suburban luxury lawn repair scene beside a curved border, stone stepping path and layered garden depth",
        "quiet garden shed exterior with upscale potting table, gravel path, flower bed edge and soft morning light",
        "premium greenhouse exterior planting strip with glass panels, soil bed, stone border and lush but realistic greenery",
        "townhouse roof garden planter border with concrete floor, herb boxes, skyline blur and restrained high-value styling",
        "formal garden sample bed with clipped hedges, pale gravel, broad lawn and product placed low in a real installation context",
        "backyard raised vegetable bed edge scene with cedar planter, stone path, leafy herbs and natural shadows",
        "side-yard luxury landscaping scene with stepping stones, mulch band, wall greenery and a pulled-back editorial composition",
    ],
    "closet_folding": [
        "luxury walk-in closet island with walnut cabinetry, folded cashmere-like neutral sweaters, linen stool and soft skylight",
        "boutique laundry folding counter with stone countertop, pale oak cabinets, linen baskets and deep cabinet background",
        "high-end wardrobe shelf organization scene with matte white shelves, folded shirts, ceramic tray and side daylight",
        "premium apparel prep table in a quiet boutique-style dressing room, travertine floor, neutral garments and clean negative space",
        "modern bedroom wardrobe corner with oak drawers, cream textiles, full-height curtain and calm editorial daylight",
        "compact upscale apartment closet with pale wood shelving, organized shirts and brushed metal rail details in background",
        "linen cabinet folding station with stone counter, stacked towels, ceramic vase and a pulled-back room-scale view",
        "Scandinavian dressing room with light oak bench, soft gray wall, folded garments and deep shelf perspective",
        "boutique hotel wardrobe nook with walnut panels, linen garment bags and product on a correct flat folding surface",
        "minimal laundry room island with white stone top, hidden cabinets, woven baskets and soft window light",
        "open wardrobe drawer scene with premium organizers, folded shirts, oak interior and product not covered by clothing",
        "neutral walk-in closet floor-and-shelf scene with large mirror reflection, linen chair and realistic room depth",
        "family laundry sorting counter with upscale cabinetry, cotton shirts as loose props and soft overcast daylight",
        "dorm closet upgraded like a boutique apartment, pale wood shelf, neutral garments and more surrounding space",
        "modern mudroom folding bench with stone floor, oak hooks, folded sweaters and clean luxury home styling",
        "high-end closet packing station with unbranded travel cubes, linen garment stacks and calm editorial composition",
        "bright wardrobe alcove with warm wood drawers, cream wall panels, natural side light and spacious background",
        "premium laundry cabinet scene with brushed metal handles, stone backsplash and towels placed away from product holes",
        "boutique apparel stockroom table with folded garments, neutral shelves and pulled-back commercial lifestyle framing",
        "soft cream dressing room with linen curtains, pale stone tabletop, folded clothes and product in lower third",
    ],
    "garden_arch": [
        "luxury villa garden path entrance with single black arch on grass, limestone walkway, roses and clipped hedges",
        "boutique courtyard ceremony path with pale stone paving, layered greenery and one arch inserted directly into soil",
        "premium backyard lawn aisle with hydrangea borders, deep garden background and arch standing by original legs only",
        "Mediterranean garden gate scene with limewash wall, terracotta planters and a single black arch without base plates",
        "modern courtyard gravel path with sculptural shrubs, stone border and arch planted into ground, no pedestal",
        "romantic rose garden walkway with restrained floral accents attached only to the existing arch rods",
        "villa patio planter entrance with raised beds, pale pavers and one complete arch, not a second arch or pergola",
        "formal garden photo spot with trimmed hedges, lawn depth and arch legs going directly into grass",
        "coastal courtyard garden with white stucco, olive trees, gravel and single arch centered in a pulled-back scene",
        "premium nursery display row with plants behind, arch on grass or soil and no foot stand",
        "garden wedding lawn corner in natural daylight, arch complete, simple flowers only on original rods and no lights",
        "cottage rose path with brick walkway, leafy background and original black arch geometry preserved",
        "townhouse garden side path with stone border, shrubs and arch lower-center, no bottom board",
        "high-end outdoor decor showroom garden with pale gravel, plants and one black arch, legs inserted in soil",
        "courtyard flower walkway with travertine tiles, green wall and exact arch leg count visible",
        "villa backyard walkway beside manicured lawn, product around one quarter frame height with strong ground contact",
        "garden gate preview scene with muted luxury palette, one arch only and no invented support base",
        "patio planter threshold with cedar boxes, greenery and black arch supported by original legs only",
        "park-style garden display with curved path, shrubs and single arch in broad environmental context",
        "quiet pergola-adjacent courtyard where the product remains a separate single black arch, no merged structure",
    ],
    "fitness_board": [
        "empty boutique gym with dark rubber floor, wall mirror, stone accent wall and no people or body parts",
        "bright premium Pilates studio with oak floor, pale exercise mats, large windows and no demonstration",
        "minimal private training room with gray mat lane, hidden storage wall and clean editorial daylight",
        "garage gym upgraded with polished concrete floor, walnut storage, neutral wall and no person using product",
        "wellness studio with travertine wall, olive-gray mat and soft daylight, product alone on floor",
        "professional fitness studio with mirror depth, black rubber tiles and distant generic equipment only",
        "quiet home workout corner with linen curtain, pale floor, mat and no hands or body parts",
        "premium athletic club training floor with matte black wall, natural side light and spacious negative space",
        "clean physiotherapy-style exercise room without patient, pale wood floor and restrained medical-free decor",
        "modern basement gym with rubber floor, stone-gray walls, storage rack far behind and no human model",
        "high-end yoga studio floor scene without people, product not transformed into a mat",
        "private trainer studio with wide open floor, mirrors and no product-use action",
        "luxury apartment workout alcove with natural window light, oak shelf and rubber mat surface",
        "sports club training bay with neutral props far away, no one touching or blocking product",
        "minimal gray fitness room with deep background layers and exact product silhouette on floor",
        "bright rehabilitation-style exercise area without medical devices, product centered on correct floor surface",
        "premium garage workout bay with daylight door, concrete floor and no hands or feet",
        "clean studio corner with mat, towel in far background and product complete in lower third",
        "dark luxury gym with controlled daylight, no neon lights or screens, product clear on rubber flooring",
        "soft white Pilates room with oak barre far behind, no person and no usage demonstration",
    ],
    "under_shelf": [
        "luxury under-sink kitchen cabinet interior with walnut panels, stone floor base and organized unbranded bottles",
        "premium pantry shelf scene with oak cabinetry, clear jars and telescoping organizer visible under a shelf",
        "high-end bathroom vanity lower cabinet with travertine tile, linen towels and correct cabinet-floor placement",
        "modern kitchen sink-base cabinet with matte white doors, stone backsplash glimpse and no side drawer rails",
        "utility cabinet storage scene with pale oak shelves, neutral cleaning bottles and deep cabinet perspective",
        "closet shelf organizer scene with linen boxes, walnut shelf and left-right expandable width clear",
        "compact apartment kitchen cabinet interior with stone counter above, product front-facing and no extra tracks",
        "laundry cabinet lower shelf with towels and bottles as loose props, realistic support surface",
        "pantry counter lower shelf with spice jars, oak structure and no invented sliding hardware",
        "premium sink cabinet scene with brass-free brushed metal handles, calm daylight and no rail hallucination",
        "walk-in pantry cabinet bay with large-format tile floor and product placed under a shelf",
        "modern vanity storage interior with soft gray palette, folded towels and no drawer slide system",
        "kitchen island lower shelf scene with pale stone and wood, expandable relationship visible",
        "narrow cabinet organization scene with deep background and correct product gravity",
        "high-end utility room cabinet with matte beige panels, product in lower third and no side tracks",
        "cool white pantry shelf scene with ceramic jars, product smaller but inspectable",
        "warm walnut storage cabinet with linen baskets behind and exact shelf/body outline",
        "minimal under-cabinet organization scene with stone floor base and product centered in a pulled-back view",
        "apartment pantry pull-out area with clean shelving but no invented rail hardware on product",
        "soft cream kitchen lower-cabinet scene with deep interior space and visible telescoping function",
    ],
    "kitchen_storage": [
        "luxury kitchen countertop with pale marble backsplash, walnut cabinets and unbranded ceramic bowls",
        "premium pantry sideboard with travertine counter, clear jars, linen runner and soft daylight",
        "boutique coffee station with stone counter, oak shelves, plain ceramic cups and no brand labels",
        "modern appliance corner with matte cabinets, brushed metal accents and deep kitchen background",
        "warm walnut kitchen island scene with ceramic fruit bowl, linen towel and editorial daylight",
        "cool gray marble kitchen counter with glass-front cabinets and restrained high-end styling",
        "compact luxury apartment kitchen with cream cabinets, stone worktop and clean negative space",
        "sideboard organizer scene with oak wall panels, plain tableware and no electronic screens",
        "walk-in pantry shelf scene with ceramic jars, stone counter and product on correct support surface",
        "breakfast station side counter with linen napkins, plain cups and soft window light",
        "matte black and white kitchen corner with crisp natural contrast and no visible brands",
        "boutique home storage nook with travertine tray, ceramic vase and brushed metal bowl",
        "high-end utility counter with pale stone, folded towels and cabinet depth",
        "luxury dining sideboard with neutral tableware, linen runner and oak cabinetry",
        "clean Scandinavian kitchen shelf scene with pale wood, ceramic containers and broad room depth",
        "premium pantry counter with stone backsplash and warm wood shelves, not a tight close-up",
        "modern home appliance station with toaster-like shapes blurred far behind and no readable marks",
        "quiet kitchen prep counter with marble texture, unbranded utensils and product lower third",
        "soft cream kitchen alcove with plain ceramic decor, cotton towel and natural shadows",
        "blue-gray premium kitchen with low saturation, stone counter and deep cabinet perspective",
    ],
    "greenery_fence": [
        "apartment balcony railing privacy screen with artificial greenery panel attached to black railing, stone floor and city daylight beyond",
        "townhouse patio fence decor scene with faux ivy screen on matte metal fence, travertine pavers and deep outdoor garden background",
        "courtyard wall greenery screen with limewash wall, pale gravel, planters and product mounted vertically as privacy decor",
        "villa terrace railing cover scene with artificial leaf fence along glass-and-metal railing, outdoor chairs blurred far behind",
        "garden fence makeover scene with green privacy panel fixed to wooden fence, lawn and flower bed depth",
        "balcony herb corner with faux greenery screen on railing, stone tiles, ceramic pots and realistic apartment outdoor light",
        "modern patio boundary screen scene with artificial vine mat attached to fence, neutral outdoor sofa far behind",
        "rooftop terrace privacy fence with greenery panel, concrete floor, planters and wide urban background",
        "side-yard fence decoration with faux leaf screen clipped to black mesh fence, gravel path and shrubs behind",
        "coastal balcony privacy screen with white wall, black railing, greenery fence and overcast daylight",
        "courtyard cafe-style outdoor divider with artificial greenery panel on freestanding fence, no brand signage",
        "garden pergola side rail scene with green privacy mat secured along railing, stone path and plants",
        "small apartment balcony makeover with faux leaf fence on railing, pale outdoor table and plants far aside",
        "patio planter wall scene with artificial greenery screen behind planters, product mounted flat and complete",
        "modern fence backdrop for outdoor seating with green screen panel, travertine floor and natural shadows",
        "backyard privacy corner with faux ivy fence fixed to wire mesh, lawn edge and pulled-back composition",
        "balcony railing close-to-mid lifestyle scene with greenery screen, stone floor and correct vertical support",
        "villa courtyard gate decor with artificial leaf panel attached to metal fence, plants and path depth",
        "terrace divider screen with faux greenery panel, ceramic planters and safe outdoor home styling",
        "urban balcony fence cover scene with product spanning railing, wide spatial depth and no indoor countertop",
    ],
    "gift_packaging": [
        "boutique gift wrapping table with brown kraft paper bags, linen ribbon rolls, plain tags and warm retail counter background",
        "wedding favor preparation scene with kraft handle bags arranged on a wooden table, neutral flowers and no readable text",
        "small shop checkout counter with plain brown paper gift bags, ceramic display props and soft daylight",
        "holiday packing station at home with kraft bags, cotton twine, blank cards and walnut tabletop",
        "party favor table with brown handle bags in neat rows, linen runner and neutral celebration decor without balloons",
        "craft room packaging desk with kraft shopping bags, scissors kept far aside, paper stack and oak shelves",
        "boutique retail shelf scene with folded kraft bags and finished gift bags on stone counter",
        "market stall prep table with brown paper bags, plain tissue paper and natural daylight, no logos",
        "home bakery packaging station with empty kraft bags, plain ceramic tray and no branded food packaging",
        "wedding welcome table with kraft gift bags, linen cloth and ceramic vase, no readable names",
        "minimal stationery desk with kraft bags, blank labels, twine and clean cream wall background",
        "retail stockroom packing bench with brown paper bags stacked neatly and deep shelf perspective",
        "birthday favor assembly table with kraft bags and plain colored tissue paper, no printed graphics",
        "boutique checkout sideboard with gift bags upright, stone surface and walnut cabinet depth",
        "festival gift prep scene with kraft handle bags, linen ribbon and warm natural window light",
        "handmade goods packing table with brown paper bags, cotton pouch props and no brand marks",
        "ecommerce packing station with kraft bags, blank thank-you cards and neutral home studio styling",
        "coffee-shop style gift counter with kraft bags and plain ceramic cups, no logos or readable text",
        "small retail display table with brown handle bags, folded tissue and brushed metal tray",
        "premium home gift wrapping corner with oak desk, kraft bags and soft overcast catalog realism",
    ],
    "dish_drying": [
        "luxury kitchen sink-side drying area with dish rack beside undermount sink, pale stone counter and clean faucet blurred behind",
        "over-sink dish drying rack scene with product spanning or sitting near sink, walnut cabinets and plates as loose contents",
        "cool gray marble kitchen wet zone with drying rack on drainboard, sink edge visible and natural daylight",
        "compact apartment kitchen sink counter with dish rack correctly placed for draining, plain dishes and no brand labels",
        "warm oak kitchen counter near sink with dish drying rack, ceramic bowls and water-safe surface context",
        "premium pantry-adjacent sink station with drying rack on stone counter, faucet far behind and deep cabinet background",
        "white kitchen sink corner with product on drainboard, tableware arranged without covering hardware",
        "blue-gray kitchen wet counter scene with rack beside sink, brushed metal faucet blurred and no electronic screens",
        "modern galley kitchen sink-side storage scene with dish rack lower third and wet-zone cues",
        "dark luxury kitchen sink area with controlled daylight, product bright enough to inspect rods and tiers",
        "family kitchen after dishwashing scene with rack near sink, neutral plates and broad room depth",
        "Scandinavian kitchen drainboard scene with pale wood, rack complete and correct contact shadow",
        "stone backsplash sink-side organizer scene with drying rack, cups and utensils placed only as loose contents",
        "coastal white kitchen sink counter with dish rack on correct wet surface and natural shadows",
        "premium small kitchen sink bay with rack on counter, folded towel far aside and no tight crop",
        "modern island prep sink scene with drying rack placed beside sink, safe ceramic tableware and no brand marks",
        "utility kitchenette sink-side drying setup with stone counter and product complete in lower-left",
        "soft cream kitchen wet area with drainboard, rack visible and no dry pantry-only setting",
        "minimal kitchen sink shelf scene with dish drying rack, sink basin partly visible and exact structure preserved",
        "morning daylight kitchen sink counter with dish rack, neutral dishes and realistic draining context",
    ],
    "cat_scratcher": [
        "luxury living room pet activity corner with cat scratcher on oak floor, linen sofa far behind and no kitchen counter",
        "modern apartment cat nook with scratcher house on floor, neutral rug nearby and plants safely aside",
        "sunlit window pet corner with cat scratch board on wooden floor, curtain depth and calm home styling",
        "bedroom floor cat rest area with scratcher product complete, walnut furniture and no bed placement on top",
        "home office pet corner with product on floor beside bookshelf, soft daylight and no human touching product",
        "Scandinavian living room floor scene with cat scratcher lower-center, pale wood and clean negative space",
        "warm walnut lounge pet zone with scratcher on rug edge, ceramic planter behind and wide room depth",
        "compact apartment hallway pet corner with scratcher on floor, shoe bench far behind and correct gravity",
        "premium cat play corner with product on floor, neutral wall panels and no toys dominating the product",
        "soft cream living room scene with scratcher house complete, cat optional far behind not blocking product",
        "blue-gray apartment pet area with product on floor and restrained decor",
        "balcony-adjacent indoor pet corner with product on wood floor, plants behind and no outdoor soil",
        "minimal bedroom pet activity nook with scratcher on floor and linen curtain background",
        "family living room corner with product beside sofa, natural contact shadow and no kitchen props",
        "boutique home pet furniture scene with product complete in lower third and wide spatial depth",
        "quiet reading nook with cat scratcher on rug, oak floor and product not transformed into furniture",
        "modern loft pet corner with concrete floor, neutral chair far behind and scratcher structure visible",
        "soft overcast living room floor scene with product centered and no food or tableware props",
        "premium hallway cat rest corner with product on floor, wall art blurred and no readable text",
        "apartment pet zone with scratcher house on wood floor, cozy but clean ecommerce composition",
    ],
    "covered_food_tray": [
        "outdoor picnic table scene with covered divided food tray on wooden table, greenery behind and black handle clearly visible",
        "family dining table prep scene with lidded section tray on linen runner, fruit and snacks as safe loose contents",
        "patio brunch table with covered tray on stone tabletop, plants and outdoor chairs blurred behind",
        "kitchen island meal-prep scene with lidded compartment tray on counter, handle and transparent cover preserved",
        "garden picnic setup with divided tray on blanket-covered low table, no open flame or alcohol",
        "terrace serving table with covered food tray, plain plates and natural daylight, product complete in lower third",
        "warm dining sideboard snack-serving scene with lidded tray, ceramic bowls and no brand packaging",
        "modern balcony snack table with covered tray, railing and plants, safe outdoor daylight",
        "home party prep table with divided covered tray, fruit and pastries as contents, no balloons or text",
        "cool marble kitchen counter with lidded tray, black handle visible and deep cabinet background",
        "wooden breakfast table with covered compartment tray, linen napkins and plain ceramic cups",
        "courtyard tea table with lidded food tray on outdoor surface, greenery and stone floor depth",
        "picnic preparation counter with covered tray, neutral food props and no branded packaging",
        "soft cream dining room side table with tray complete and handle silhouette frozen",
        "coastal patio serving scene with covered tray on pale stone table and safe outdoor decor",
        "family snack station with divided tray on dining table, product not turned into cutting board",
        "premium kitchen prep counter with lidded tray, cover clarity and black handle preserved",
        "backyard table setting with covered tray, ceramic plates far behind and no grill/fire cues",
        "minimal dining table scene with tray on correct tabletop support and product around inspection scale",
        "home buffet sideboard with covered divided tray, natural shadows and no readable labels",
    ],
    "home_repair_tools": [
        "home renovation workbench with stainless putty knives on protective paper, plaster wall repair area blurred behind",
        "wall patching prep scene with scraper set on wooden tool bench, neutral wall and no hazardous chemicals",
        "DIY home repair table with putty knives, plain sanding block far aside and clean workshop daylight",
        "interior wall maintenance scene with scraper tools on drop cloth near wall, product complete and not kitchen props",
        "minimal garage workbench with scraper set, neutral tools in background and no power tools dominating",
        "apartment repair corner with putty knives on stone-look floor cloth, pale wall and natural light",
        "professional painting prep table with scraper set, blank paint tray far aside and no brand labels",
        "home improvement bench with three scraper sizes arranged clearly, wall texture sample behind",
        "utility room repair station with stainless scrapers on work surface, plaster board and clean shadows",
        "wall smoothing job-prep scene with scraper tools on drop sheet, no active person or unsafe blade handling",
        "modern workshop table with scraper set, folded cloth, blank wall panel and cool daylight",
        "renovation corner with putty knives on cardboard protector, wall patch area in background",
        "clean tool organization scene with scraper set on workbench, brushed metal and walnut accents",
        "home repair shelf and bench scene with putty knives lower third, no kitchen counter context",
        "paint-prep workstation with scraper set, neutral plaster sample and no readable packaging",
        "DIY apartment maintenance tabletop with stainless scrapers, plain tools far aside and wall in view",
        "construction-free interior repair scene with scraper set on covered table and soft overcast daylight",
        "premium utility workbench with three putty knives, stone wall sample and safe household setting",
        "wall refinishing prep scene with scraper set on drop cloth, product sizes clear and no food props",
        "home toolbox bench with scraper tools complete, neutral background and realistic repair context",
    ],
    "outdoor_grill": [
        "premium patio outdoor cooking prep scene with stone table, folded grill placed on heat-safe outdoor tabletop, garden seating in background and no active flame",
        "modern courtyard meal-prep area with travertine pavers, wooden outdoor table, folded portable grill on the table and green plants beyond",
        "backyard terrace picnic setup with stone counter, neutral plates far behind, folded barbecue grill on outdoor support surface and no kitchen interior",
        "camp-style garden dining scene with wooden camping table, folded grill placed safely on tabletop, lawn and patio depth in background",
        "villa terrace outdoor dining corner with pale stone floor, linen table runner, folded portable barbecue grill centered on outdoor table",
        "balcony barbecue preparation scene with metal outdoor side table, railing and plants, folded grill visible and not placed on kitchen counter",
        "courtyard picnic table scene with oak outdoor table, folded grill on the table, ceramic plates as distant props and no fire or smoke",
        "garden deck food-prep scene with cedar table, folded portable grill, greenery and wide outdoor spatial depth",
        "modern patio sideboard scene with stone outdoor counter, folded barbecue grill placed on top, no indoor cabinets or kitchen sink",
        "outdoor terrace storage-and-cooking prep scene with brushed metal cart, folded grill on cart surface and garden background",
        "suburban backyard dining table scene with neutral outdoor chairs, folded grill on heat-safe tabletop and bright natural daylight",
        "minimal rooftop terrace meal-prep scene with stone outdoor table, folded grill product in lower third and city greenery blur",
        "Mediterranean patio lunch-prep scene with limewash wall, terracotta planters, folded grill on outdoor table and no open flame",
        "camping picnic preparation scene with wooden table, folded grill complete and clear, tent-like fabric only far blurred in background",
        "garden workbench outdoor cooking prep scene with stone surface, folded grill product, herbs and safe unbranded utensils nearby",
        "coastal terrace outdoor dining scene with white stucco, pale stone tabletop, folded portable barbecue grill and ocean-light ambience",
        "modern balcony meal-prep side table scene with plants, gray railing, folded grill on table and no indoor kitchen cues",
        "patio corner with outdoor cabinet and stone counter, folded grill on counter, product complete with correct legs/frame and no flame",
        "lawn picnic table scene with pulled-back view, folded grill placed on sturdy outdoor table and natural contact shadow",
        "premium outdoor cooking station setup before use, folded barbecue grill on safe table surface, greenery and stone patio depth",
    ],
    "cleaning_set": [
        "luxury laundry room tiled floor with stone-look wall, oak cabinet, linen basket and no messy clutter",
        "premium bathroom utility corner with large-format tile, matte cabinet and product on correct floor surface",
        "modern mudroom cleaning nook with travertine floor, neutral towels and deep cabinet background",
        "high-end utility closet scene with pale oak shelves, plain bottles and natural daylight",
        "clean apartment laundry alcove with stone floor, woven hamper and no electronic screens",
        "warm walnut laundry cabinet scene with linen curtains, folded towels and correct product placement",
        "cool gray bathroom floor scene with vanity in background and restrained spa styling",
        "premium housekeeping corner with cotton mop cloths, stone tile and no brand labels",
        "minimal utility room with matte beige cabinetry, floor drain area and soft daylight",
        "boutique hotel-style bathroom service corner with neutral stone and product complete on floor",
        "bright laundry room side wall with ceramic tile, oak shelves and spacious pulled-back view",
        "modern cleaning closet open door scene with product on tile floor and safe household props",
        "soft cream utility room with linen hamper, stone floor and natural contact shadows",
        "blue-gray laundry cabinet scene with brushed metal handles and no appliance screens",
        "quiet bathroom corner with travertine wall, neutral towel stack and correct gravity",
        "minimal hallway utility nook with stone floor, oak trim and product lower-left",
        "premium washroom storage scene with matte wall, ceramic container and broad room depth",
        "high-end home cleaning station with pale tile, linen basket and product unobstructed",
        "modern laundry sink corner with stone counter and product on floor, no water splash drama",
        "neutral utility cabinet scene with soft overcast daylight and tidy high-value home styling",
    ],
    "pet_mat": [
        "luxury living room pet corner with oak floor, linen sofa far behind and product flat on floor",
        "premium bedroom floor scene with neutral rug nearby, walnut bed frame and pet mat surface fully visible",
        "modern apartment pet area with stone-look floor, plant, linen cushion and no pet covering product",
        "boutique home hallway with pale wood floor, soft daylight and mat placed naturally near wall",
        "calm reading nook with oak floor, linen chair and product unobstructed as a flat mat",
        "minimal pet feeding corner with ceramic bowls far beside product, not on top of it",
        "soft cream living room with woven basket, curtains and product complete on floor",
        "blue-gray apartment corner with clean floor, plant shadow and product surface visible",
        "high-end bedroom pet spot with linen textiles, product flat and not transformed into a bed",
        "modern entryway pet mat scene with stone tile floor and broad spatial depth",
        "warm walnut living room corner with neutral decor and no animal blocking product",
        "premium balcony-adjacent pet resting corner indoors, product on floor, no outdoor soil",
        "quiet home office pet corner with oak floor and product lower third",
        "Scandinavian living room floor scene with pale wood and product surface unobstructed",
        "minimal hallway nook with stone tile, linen wall art and mat flat with clear border",
        "boutique apartment bedroom corner with soft overcast daylight and product not a cushion",
        "neutral lounge floor scene with plants far behind and product rectangular shape exact",
        "modern closet-side pet area with product on floor and visible thickness/binding",
        "premium mudroom pet corner with large tile and product flat near built-in cabinet",
        "soft daylight living room scene with product lower-left and no side walls or bed redesign",
    ],
    "shoe_cabinet": [
        "luxury entryway storage wall with oak cabinetry, stone floor and product standing as a rack/cabinet",
        "modern mudroom shoe organization scene with matte white panels, bench and deep room perspective",
        "premium apartment foyer with travertine tile, walnut console and product front-facing",
        "walk-in closet shoe shelf scene with warm wood, neutral footwear props and product structure unchanged",
        "high-end hallway cabinet scene with brushed metal handles, stone floor and no generic dresser redesign",
        "compact entryway organization nook with oak bench, linen cushion and product lower-right",
        "blue-gray modern foyer with clean wall panels and realistic floor contact",
        "soft cream mudroom with built-in cabinets, product around one quarter frame height",
        "boutique shoe storage corner with pale wood shelves and product not merged with background cabinets",
        "minimal apartment hallway with stone tile, mirror far behind and exact rods/handles visible",
        "warm walnut entry cabinet scene with neutral baskets and no wheels if product has none",
        "premium closet island side scene with product standing near shoe shelves",
        "modern utility entry with matte beige cabinets and product front structure frozen",
        "hotel-style foyer closet with stone floor and product placed naturally by wall",
        "Scandinavian hallway storage scene with oak slats and clear product silhouette",
        "dark luxury entryway with controlled daylight and product hardware still inspectable",
        "bright mudroom cabinet bay with shoes as loose props and no product redesign",
        "small apartment shoe corner with pale stone floor and pulled-back composition",
        "premium wardrobe shoe area with folded umbrellas far away and no brand marks",
        "clean entryway bench scene with cabinet depth and exact flip-door/front details preserved",
    ],
    "mobile_table": [
        "luxury bedside reading corner with linen bed, walnut nightstand and mobile table on floor with caster wheels visible",
        "modern sofa-side work nook with stone side table, oak floor and product support/base complete",
        "premium home office corner with pale rug, walnut desk far behind and adjustable table lower-right",
        "boutique apartment living room with linen sofa, travertine coffee table and caster base visible",
        "minimal bedroom breakfast tray scene without food mess, product on floor beside bed",
        "warm walnut lounge corner with natural daylight and product not converted into generic side table",
        "cool gray studio apartment scene with product near armchair, wheels and X-base clear",
        "soft cream reading nook with curtains, oak floor and rectangular tabletop frozen",
        "modern hospital-free bedside utility scene with linen bedding and exact support pole visible",
        "high-end dorm room study corner with product near chair, correct scale and wheels intact",
        "premium living room side-table scene with product complete in lower third",
        "minimal office lounge with stone wall, product on floor and black knob visible",
        "apartment balcony-adjacent reading area indoors, product on floor not outdoor soil",
        "hotel-style bedroom corner with natural daylight and product structure unchanged",
        "Scandinavian sofa-side scene with pale wood floor and exact caster wheel count",
        "dark luxury lounge with controlled daylight, product bright enough to inspect base",
        "home study side table scene with oak shelf, product lower-left and tabletop exact",
        "neutral nursing-style home bedroom without medical devices, product beside bed",
        "premium compact apartment corner with linen chair and mobile table in realistic use",
        "soft overcast living room scene with deep background and all wheels visible",
    ],
    "drawer_organizer": [
        "luxury front-facing closet shelf scene with walnut panels, product top groove and grid fully visible",
        "premium vanity counter storage scene with pale stone, product strict front view and top structure frozen",
        "modern entryway cabinet organizer scene with cool white daylight and product lower-center",
        "walk-in closet drawer bay with oak interior, product front-facing and upper edge exact",
        "high-end bathroom vanity shelf with stone wall, product front structure clear and no angle drift",
        "soft cream wardrobe scene with linen boxes behind and product around inspection scale",
        "blue-gray closet organizer scene with low saturation and exact transparent door/handle",
        "warm walnut cabinet storage scene with product front view, no invented top parts",
        "minimal dressing room shelf with stone tray, product lower-right and square-grid top visible",
        "boutique apartment cabinet scene with product centered, pulled-back but inspectable",
        "premium pantry drawer organizer scene with matte cabinets and exact top groove",
        "modern closet counter with folded linens far behind, product strict front-facing",
        "dark luxury wardrobe shelf with controlled daylight, top structure bright enough to see",
        "cool marble vanity shelf with product complete and no added upper parts",
        "oak entry cabinet cubby with product on shelf and transparent door frozen",
        "soft overcast closet scene with deep shelf perspective and no rotation",
        "minimal hotel wardrobe nook with product front-facing and exact white frame",
        "warm wood dressing cabinet with product lower-left and black handle unchanged",
        "premium home storage shelf with ceramic decor far aside, product not merged",
        "clean wardrobe island side shelf with product around 22 percent height and top grid intact",
    ],
    "cutting_board": [
        "luxury kitchen sink-side scene with pale marble counter, walnut cabinets and cutting board set near prep area",
        "premium island prep counter with travertine surface, plain ceramic bowl and product holes visible",
        "cool gray marble kitchen with deep cabinet background and exact cutting board hole positions",
        "warm oak breakfast prep scene with linen towel, stone counter and product flat on surface",
        "minimal white kitchen backsplash with natural daylight and product lower-third",
        "dark luxury kitchen counter with controlled daylight and cutting board set complete",
        "Scandinavian kitchen shelf scene with pale wood and product on correct counter",
        "blue-gray apartment kitchen with matte cabinets and no text or brand props",
        "boutique home cooking prep station with ceramic fruit bowl and unbranded utensils",
        "soft cream kitchen alcove with linen cloth and product small but inspectable",
        "modern pantry prep sideboard with stone top and exact board count/hole pattern",
        "luxury sink-side drying area with brushed metal faucet blurred, no water drama",
        "walnut kitchen island corner with natural shadow and product not cropped",
        "coastal white kitchen counter with pale stone and plain ceramic decor",
        "compact apartment prep counter with broad room depth and correct product scale",
        "premium dining-adjacent kitchen sideboard with cutting boards arranged on surface",
        "minimal marble counter close-to-mid scene but still pulled back, product around 24 percent height",
        "cool daylight galley kitchen with product on counter and hole positions frozen",
        "warm wood kitchen shelf background with product clear and no extra boards",
        "high-end home chef prep corner with safe generic props and no logos",
    ],
    "fruit_display": [
        "luxury dining sideboard with travertine top, plain ceramic fruit bowl, linen runner and product as display rack",
        "premium kitchen island fruit display scene with marble counter, walnut cabinets and safe fresh fruit props",
        "boutique cafe-style dessert table at home with unbranded pastries, stone surface and product structure unchanged",
        "modern breakfast counter with ceramic plates, fruit and deep kitchen background",
        "warm wood dining room sideboard with linen runner and product holding neutral fruit",
        "cool gray kitchen counter with glass-front cabinets and product lower-third",
        "soft cream brunch table scene with ceramic bowls, fruit and natural daylight",
        "dark luxury dining sideboard with controlled light and product rods/baskets visible",
        "Scandinavian kitchen shelf scene with pale oak, plain ceramics and product complete",
        "coastal dining counter with white stone, fruit and clean negative space",
        "premium pantry counter with jars blurred behind and product on correct surface",
        "minimal dessert buffet scene with ceramic plates and no brand labels",
        "modern apartment dining nook with stone table and product small but clear",
        "warm walnut breakfast station with fruit, linen and product not transformed",
        "blue-gray marble kitchen scene with low saturation and visible connectors",
        "home cafe sideboard with plain cups, fruit and product lower-left",
        "luxury open kitchen dining area with product on island, wide scene depth",
        "neutral overcast dining shelf scene with product around 22 percent height",
        "soft pastel brunch counter with safe fruit and product hardware frozen",
        "premium tea table scene with ceramic cups and fruit, no logos, no alcohol",
    ],
    "planter": [
        "luxury apartment balcony herb garden with black railing, city daylight, stone floor and product hanging/placed naturally",
        "premium patio planting corner with travertine pavers, olive pots and product cells visible",
        "greenhouse bench scene with seedlings, stone aisle and product as planter/holder, not close-up only",
        "sunny terrace wall garden with limewash wall, clay pots and deep outdoor background",
        "courtyard herb wall scene with climbing greenery, stone wall and product lower-right",
        "modern balcony corner with white wall, terracotta pots and strong color differentiation",
        "porch deck planting scene with cedar floor, neutral outdoor textiles and product complete",
        "backyard raised-bed area with soil, herbs and product near patio edge",
        "garden workbench with seedlings, ceramic pots and product unobstructed",
        "rooftop terrace planter scene with skyline blur, stone surface and natural daylight",
        "Mediterranean patio herb scene with limewash wall, olive greenery and product in lower third",
        "greenhouse aisle with muted glass panels, seedlings and product around 23 percent height",
        "apartment window herb garden with indoor-outdoor balcony depth and no repeated green wall",
        "garden fence planter display with product holder geometry visible",
        "modern courtyard vegetable planter with raised beds and stone walkway",
        "premium balcony rail planter scene with deep city background and cells/box shape frozen",
        "coastal terrace herb corner with white stucco, clay pots and pulled-back composition",
        "backyard potting table scene with soil tray far behind and product not cropped",
        "urban balcony morning scene with stone floor, plants and product complete",
        "designer patio garden nook with travertine, matte planters and safe unbranded props",
    ],
}

PREFIX_PROFILES: dict[str, PrefixProfile] = {
    "L042": PrefixProfile("garden_border", "garden edging strip with bundled black spiral stakes", "edging strip or roll, fixing tabs, hole pattern, roll geometry and short black spiral stakes", "on soil, grass, gravel, flower-bed edge or patio planter border only"),
    "L043": PrefixProfile("closet_folding", "folding clothes stacking board", "flat board outline, all holes, small center hole, rear raised detail, panel seams, thickness and material", "on a closet shelf, laundry counter or folding table near folded clothes"),
    "L047": PrefixProfile("garden_arch", "single black garden arch", "one arch only, original rods, leg geometry and ground-inserted supports; no base plates", "inserted into soil, grass, planter bed or garden path ground"),
    "L048": PrefixProfile("greenery_fence", "artificial greenery privacy fence screen", "leaf panel grid, vine coverage, fence-screen shape, color, connector points and flexible sheet silhouette", "attached vertically to balcony railing, patio fence, courtyard wall, garden fence or terrace divider only"),
    "L051": PrefixProfile("gift_packaging", "brown kraft paper gift bags with handles", "bag body, handle loops, kraft paper material, quantity feeling, folded edges and upright/open bag silhouettes", "on a gift wrapping table, boutique retail counter, party favor table or packaging workstation only"),
    "L058": PrefixProfile("cleaning_set", "bucket and mop cleaning set", "bucket, mop pole, basket, handle, quantity and proportions", "on bathroom, laundry, mudroom or utility room floor"),
    "L063": PrefixProfile("fitness_board", "fitness board or exercise training product", "board outline, holes, handles, pedals, bands, rails, surface pattern and accessories", "on gym floor, exercise mat, training room floor or rubber tile"),
    "L068": PrefixProfile("dish_drying", "kitchen dish drying rack for sink-side use", "rack body, tiers, cover/top detail, rods, tray, supports, length relationship and color", "beside or over a kitchen sink, on a drainboard, wet counter or sink-side support surface only"),
    "L071": PrefixProfile("mobile_table", "mobile adjustable table", "rectangular tabletop, vertical support, adjustment knob, X-shaped base and caster wheels", "standing on floor beside bed, sofa, chair or desk"),
    "L072": PrefixProfile("shoe_cabinet", "flip-door shoe cabinet rack", "silver rods, black connector rings, flip-door fronts, handles and no-wheel structure", "standing on entryway, mudroom, closet or hallway floor"),
    "L074": PrefixProfile("dish_drying", "three-tier kitchen dish drying rack with drain tray", "three tiers, drain tray, rods, shelf spacing, utensil/tableware zones, supports, color and outline", "beside a kitchen sink, on a drainboard or wet countertop only"),
    "L075": PrefixProfile("dish_drying", "two-tier large-capacity dish drying rack", "two-tier rack body, drain tray, detachable structure, rods, frame, supports and visible hardware", "over or beside a kitchen sink, on a wet countertop or drainboard only"),
    "L076": PrefixProfile("pet_mat", "flat gray plush pet mat", "flat rectangular mat, gray plush surface, white edge binding, thickness and no side walls", "flat on living room, bedroom, hallway or mudroom floor"),
    "L077": PrefixProfile("cat_scratcher", "multi-layer cat scratcher and cat house", "corrugated scratch board texture, layered cat house body, ventilation slots, openings, edges, color and silhouette", "on living room, bedroom, hallway, home office or pet-corner floor only"),
    "L078": PrefixProfile("covered_food_tray", "covered divided picnic or serving tray", "six compartments, transparent lid, black top handle, tray body, proportions and food-safe serving shape", "on dining table, kitchen prep counter, outdoor picnic table, patio table or serving sideboard only"),
    "L081": PrefixProfile("kitchen_storage", "storage shelf or rack", "shelf/rack proportions, panels, rods, supports, edges and color", "on a home storage shelf, pantry sideboard or cabinet"),
    "L082": PrefixProfile("under_shelf", "left-right expandable under-shelf organizer", "telescoping function, shelf/body outline, front structure and support surfaces; no side rails or drawer slides", "inside under-sink cabinet, pantry shelf, vanity cabinet or storage cabinet"),
    "L083": PrefixProfile("under_shelf", "sliding under-sink cabinet storage rack", "overall proportion, side straight rods, sliding basket/plate details, supports, connectors and frame geometry", "inside or under a sink cabinet, vanity cabinet, lower cabinet or enclosed storage bay only"),
    "L085": PrefixProfile("home_repair_tools", "three-piece stainless wall putty scraper set", "three scraper sizes, metal blades, handles, straight edges, proportions and tool-set quantity", "on a home repair workbench, wall patching prep table, drop cloth or utility tool bench only"),
    "L086": PrefixProfile("kitchen_storage", "non-white kitchen or storage rack", "two drawer/basket units, front grid or transparent face, top board, vertical supports, side frame, legs and non-white material", "on kitchen counter, pantry sideboard, coffee station or closet storage counter; never white"),
    "L087": PrefixProfile("under_shelf", "two-tier under-sink metal storage rack", "two-tier frame, basket/shelf structure, width-height relationship, visible rods, supports and proportions", "inside a sink-base cabinet, vanity lower cabinet, utility cabinet or under-shelf storage bay only"),
    "L088": PrefixProfile("fruit_display", "offset stepped fruit basket rack", "offset basket layout, long bottom basket, upper baskets, support rods, side rods, feet, color and connectors", "on kitchen island, dining sideboard or pantry counter"),
    "L089": PrefixProfile("kitchen_storage", "home storage rack", "product appearance, frame, compartments, rods, supports and structure", "on realistic counter, cabinet, pantry or shelf surface"),
    "L090": PrefixProfile("kitchen_storage", "household organizer", "organizer frame, shelves, rods, supports, panels and silhouette", "on kitchen, pantry, utility or closet support surface"),
    "L091": PrefixProfile("drawer_organizer", "drawer organizer with top grid structure", "front view, drawer surface, transparent door, black handle, white frame, exact top groove and square-grid pattern", "front-facing on closet shelf, vanity counter, entry cabinet or storage shelf"),
    "L092": PrefixProfile("cutting_board", "cutting board set", "board count, hole count, hole positions, shape, color and surface structure", "on kitchen counter, sink side, prep island or pantry sideboard"),
    "L094": PrefixProfile("fruit_display", "fruit bowl or tiered fruit stand", "bamboo stand, white ceramic bowls, screws, rods and tier structure", "on kitchen island, dining table, sideboard or pantry counter"),
    "L095": PrefixProfile("planter", "hanging or planting basket", "basket/frame/planter body, grid or cells, hanging/holder geometry and waterproof box shape", "on balcony, patio, terrace, greenhouse, fence, wall garden or planting workbench"),
    "L096": PrefixProfile("outdoor_grill", "folding portable barbecue grill", "folding grill body, frame, legs, grate, hinge/locking structure, panels, supports, color and product silhouette", "on an outdoor patio table, terrace table, picnic table, garden workbench, outdoor cart or heat-safe outdoor prep surface only; never on an indoor kitchen counter"),
}


def build_luxury_prompt(prefix: str, scene: str, index: int) -> str:
    profile = PREFIX_PROFILES[prefix]
    palette = [
        "cool white marble and pale oak",
        "blue-gray stone and brushed metal",
        "warm walnut and cream linen",
        "dark charcoal luxury with controlled daylight",
        "soft cream travertine and ceramic",
        "fresh green natural outdoor palette",
        "black-white modern contrast",
        "neutral overcast catalog realism",
    ][index % 8]
    position = [
        "lower-left",
        "center-right",
        "lower-right",
        "center-left",
        "lower-center",
    ][index % 5]
    scale = [18, 19, 20, 21, 22, 23, 24, 25, 26][index % 9]
    return (
        f"Expanded luxury lifestyle scene for {prefix}: {scene}. "
        f"Use the input product image as the exact {profile.product} reference; preserve {profile.fixed}. "
        f"Place it only {profile.placement}. Composition lane: product at {position}, about {scale} percent of image height, "
        f"complete and inspectable while the wider environment takes most of the frame. "
        f"Luxury scene cues: {LUXURY_CUES}. Color palette lane: {palette}; avoid repeating the same palette across sibling images. "
        f"{COMMON_FRAME_RULE} No readable text, no logos, no branded luxury goods, no monogram patterns, no electronics screens, "
        f"no fire, no candles, no alcohol, no toys, no medicines, no weapons. Square 1:1 premium ecommerce image."
    )


def build_scene_bank(prefixes: list[str] | None = None) -> dict[str, list[str]]:
    selected = prefixes or sorted(PREFIX_PROFILES)
    bank: dict[str, list[str]] = {}
    for prefix in selected:
        profile = PREFIX_PROFILES[prefix]
        lanes = SCENE_LANES[profile.category]
        bank[prefix] = [build_luxury_prompt(prefix, scene, idx) for idx, scene in enumerate(lanes[:MIN_SCENES_PER_PREFIX])]
    return bank


LUXURY_EXPANDED_SCENE_BANK = build_scene_bank()

DEFAULT_LUXURY_EXPANDED_SCENES = [
    (
        f"Expanded luxury lifestyle scene: {scene}. Use the product image as exact product reference; preserve all visible hardware, "
        f"color, silhouette, supports and proportions. Product placed on a realistic support surface, about {18 + (idx % 9)} percent of image height, "
        f"with a pulled-back room-scale view. Luxury cues: {LUXURY_CUES}. {COMMON_FRAME_RULE} Square 1:1 premium ecommerce image."
    )
    for idx, scene in enumerate(SCENE_LANES["kitchen_storage"][:MIN_SCENES_PER_PREFIX])
]


def validate_luxury_scene_banks(prefixes: list[str] | None = None) -> dict[str, int]:
    bank = build_scene_bank(prefixes)
    counts = {prefix: len(prompts) for prefix, prompts in bank.items()}
    short = {prefix: count for prefix, count in counts.items() if count < MIN_SCENES_PER_PREFIX}
    if len(DEFAULT_LUXURY_EXPANDED_SCENES) < MIN_SCENES_PER_PREFIX:
        short["DEFAULT"] = len(DEFAULT_LUXURY_EXPANDED_SCENES)
    if short:
        raise RuntimeError(f"luxury scene bank too short: {short}")
    vague_hits = []
    banned_generic = ("different scene mood", "set_1_scene_lane", "generic background")
    for prefix, prompts in bank.items():
        for idx, prompt in enumerate(prompts):
            lower = prompt.lower()
            if any(token in lower for token in banned_generic):
                vague_hits.append((prefix, idx + 1))
            if "luxury scene cues" not in lower or "product at" not in lower or "percent of image height" not in lower:
                vague_hits.append((prefix, idx + 1))
    if vague_hits:
        raise RuntimeError(f"luxury scene prompts missing detail: {vague_hits[:20]}")
    return counts


if __name__ == "__main__":
    import json

    print(json.dumps(validate_luxury_scene_banks(), ensure_ascii=False, indent=2))
