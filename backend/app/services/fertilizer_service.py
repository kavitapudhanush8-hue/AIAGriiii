"""
Fertilizer recommendation service — rule-based engine.

Provides fertilizer recommendations based on crop type, soil type,
and nutrient levels. Uses a curated knowledge base of Indian agricultural
best practices.
"""
from typing import List, Dict, Optional
from app.schemas.schemas import FertilizerRequest, FertilizerResponse


# ─── Fertilizer Knowledge Base ────────────────────────────────────────────────

FERTILIZER_DB: Dict[str, Dict[str, dict]] = {
    "Tomato": {
        "Loamy": {
            "fertilizer": "NPK 10:26:26",
            "quantity": "20 kg per acre",
            "schedule": "Apply basal dose before transplanting. Top-dress with Urea (46-0-0) at 25 kg/acre at 30 and 60 days after transplanting.",
            "tips": [
                "Add well-decomposed farmyard manure (10 tonnes/acre) before planting",
                "Apply micronutrients (Zinc, Boron) as foliar spray at flowering",
                "Split nitrogen application into 3 doses for best results",
                "Avoid excess nitrogen to prevent leaf curl and delayed fruiting",
            ],
        },
        "Sandy": {
            "fertilizer": "NPK 12:32:16 + Urea",
            "quantity": "25 kg NPK + 15 kg Urea per acre",
            "schedule": "Apply NPK as basal. Split Urea into 3 equal doses at 20, 40, and 60 days after transplanting.",
            "tips": [
                "Sandy soils lose nutrients quickly — use split applications",
                "Add organic matter to improve water and nutrient retention",
                "Consider drip fertigation for better nutrient delivery",
                "Apply potash through water-soluble fertilizers",
            ],
        },
        "Clay": {
            "fertilizer": "DAP (18:46:0) + MOP (0:0:60)",
            "quantity": "15 kg DAP + 10 kg MOP per acre",
            "schedule": "Apply entire DAP and half MOP as basal. Remaining MOP at 45 days after transplanting.",
            "tips": [
                "Clay soils retain nutrients well — reduce total fertilizer amount",
                "Ensure proper drainage before applying fertilizers",
                "Avoid waterlogging after fertilizer application",
                "Use gypsum to improve clay soil structure",
            ],
        },
        "Black": {
            "fertilizer": "NPK 10:26:26 + Neem-coated Urea",
            "quantity": "18 kg NPK + 20 kg Neem Urea per acre",
            "schedule": "Apply NPK as basal dose. Apply Neem Urea in 2 splits at 30 and 60 days.",
            "tips": [
                "Black soil (Vertisol) is naturally rich in potassium",
                "Focus on phosphorus and nitrogen supplementation",
                "Neem-coated urea reduces nitrogen loss from black soils",
                "Add zinc sulphate (10 kg/acre) to address zinc deficiency",
            ],
        },
    },
    "Rice": {
        "Loamy": {
            "fertilizer": "NPK 20:20:0 + Urea + MOP",
            "quantity": "25 kg NPK + 30 kg Urea + 10 kg MOP per acre",
            "schedule": "Apply NPK and half Urea at transplanting. Remaining Urea at tillering (25 days) and panicle initiation (50 days). MOP at panicle initiation.",
            "tips": [
                "Apply zinc sulphate (10 kg/acre) in zinc-deficient soils",
                "Use leaf color chart (LCC) to optimize nitrogen timing",
                "Maintain 2-3 cm standing water during fertilizer application",
                "Drain field before harvest for better grain quality",
            ],
        },
        "Clay": {
            "fertilizer": "DAP + Urea + MOP",
            "quantity": "20 kg DAP + 25 kg Urea + 8 kg MOP per acre",
            "schedule": "Apply DAP at transplanting. Urea in 3 splits. MOP at panicle initiation.",
            "tips": [
                "Clay soils in paddy fields retain nutrients well",
                "Reduce total urea by 10-15% compared to sandy soils",
                "Apply fertilizer on moist (not flooded) soil for best absorption",
                "Consider green manuring with dhaincha before rice season",
            ],
        },
        "Sandy": {
            "fertilizer": "NPK 15:15:15 + Urea",
            "quantity": "30 kg NPK + 35 kg Urea per acre",
            "schedule": "Frequent small doses needed. Apply NPK at planting, Urea in 4 splits at 15-day intervals.",
            "tips": [
                "Sandy soils need frequent, smaller fertilizer applications",
                "Apply organic manure generously to improve nutrient retention",
                "Drip irrigation with fertigation is ideal for sandy paddy soils",
                "Monitor water levels carefully as sandy soils drain fast",
            ],
        },
        "Black": {
            "fertilizer": "Urea + SSP (Single Super Phosphate)",
            "quantity": "30 kg Urea + 50 kg SSP per acre",
            "schedule": "Apply SSP as basal. Urea in 3 splits at planting, tillering, and panicle initiation.",
            "tips": [
                "Black soils are naturally rich in potassium — skip potash",
                "Focus on nitrogen and phosphorus supplementation",
                "Apply sulphur through SSP to address sulphur deficiency",
                "Use Azolla as biofertilizer to supplement nitrogen",
            ],
        },
    },
    "Potato": {
        "Loamy": {
            "fertilizer": "NPK 10:26:26 + Urea",
            "quantity": "30 kg NPK + 25 kg Urea per acre",
            "schedule": "Apply full NPK and half Urea at planting. Remaining Urea at earthing up (30 days).",
            "tips": [
                "Potatoes need high potassium for good tuber quality",
                "Apply farmyard manure (15 tonnes/acre) well before planting",
                "Avoid fresh manure as it causes scab disease",
                "Maintain soil pH between 5.5 and 6.5 for best results",
            ],
        },
        "Sandy": {
            "fertilizer": "NPK 12:32:16 + Urea + MOP",
            "quantity": "25 kg NPK + 20 kg Urea + 15 kg MOP per acre",
            "schedule": "Apply NPK and MOP at planting. Urea in 2 splits at 20 and 40 days.",
            "tips": [
                "Sandy soils are ideal for potato — good drainage prevents rot",
                "Use split fertilizer applications due to quick nutrient leaching",
                "Apply sulphate of potash instead of muriate for better quality",
                "Maintain adequate moisture without waterlogging",
            ],
        },
    },
    "Corn": {
        "Loamy": {
            "fertilizer": "DAP + Urea + MOP",
            "quantity": "25 kg DAP + 40 kg Urea + 10 kg MOP per acre",
            "schedule": "Apply DAP and MOP at sowing. Urea in 3 splits: sowing, knee-high (25 days), and tasseling (50 days).",
            "tips": [
                "Corn is a heavy nitrogen feeder — never skip nitrogen doses",
                "Apply zinc sulphate (10 kg/acre) to prevent zinc deficiency",
                "Earthing up at knee-high stage improves fertilizer efficiency",
                "Use intercropping with legumes to fix nitrogen naturally",
            ],
        },
        "Black": {
            "fertilizer": "Urea + SSP",
            "quantity": "35 kg Urea + 50 kg SSP per acre",
            "schedule": "Apply SSP at sowing. Urea in 3 splits at sowing, 25 days, and 50 days.",
            "tips": [
                "Black soils provide good potash — focus on N and P",
                "Corn in black soil needs good drainage for root development",
                "Apply farmyard manure (8-10 tonnes/acre) before sowing",
                "Monitor for zinc and iron deficiency symptoms",
            ],
        },
    },
    "Cotton": {
        "Black": {
            "fertilizer": "NPK 10:26:26 + Urea",
            "quantity": "20 kg NPK + 30 kg Urea per acre",
            "schedule": "Apply NPK at sowing. Urea in 3 splits: sowing, squaring (35 days), and flowering (60 days).",
            "tips": [
                "Cotton in black soil needs careful nitrogen management",
                "Excess nitrogen causes excessive vegetative growth",
                "Apply boron as foliar spray to prevent flower/boll drop",
                "Use potash to improve fiber quality and boll weight",
            ],
        },
        "Loamy": {
            "fertilizer": "DAP + Urea + MOP",
            "quantity": "15 kg DAP + 25 kg Urea + 10 kg MOP per acre",
            "schedule": "Apply DAP and half MOP at sowing. Urea in 2-3 splits. Remaining MOP at flowering.",
            "tips": [
                "Balanced NPK is crucial for cotton yield and fiber quality",
                "Apply magnesium sulphate if leaves show interveinal chlorosis",
                "Avoid late-season nitrogen to promote boll maturity",
                "Use neem cake (100 kg/acre) to improve soil health",
            ],
        },
    },
}

# Default fallback recommendation
DEFAULT_RECOMMENDATION = {
    "fertilizer": "NPK 10:26:26 (Balanced)",
    "quantity": "20 kg per acre",
    "schedule": "Apply as basal dose before sowing/transplanting. Top-dress with Urea at 30 and 60 days.",
    "tips": [
        "Get soil tested for precise fertilizer recommendation",
        "Apply well-decomposed organic manure before chemical fertilizers",
        "Follow split application method for nitrogen fertilizers",
        "Maintain optimal soil moisture during fertilizer application",
    ],
}


def get_fertilizer_recommendation(request: FertilizerRequest) -> FertilizerResponse:
    """
    Get fertilizer recommendation based on crop and soil type.
    Uses a curated rule-based knowledge base.
    """
    crop = request.crop.strip().title()
    soil = request.soil_type.strip().title()

    # Look up recommendation
    crop_data = FERTILIZER_DB.get(crop, {})
    rec = crop_data.get(soil, None)

    if rec is None:
        # Try first available soil type for the crop
        if crop_data:
            first_soil = next(iter(crop_data))
            rec = crop_data[first_soil]
        else:
            rec = DEFAULT_RECOMMENDATION

    tips = list(rec["tips"])

    # Add nutrient-specific tips based on input levels
    if request.nitrogen is not None and request.nitrogen < 30:
        tips.append(f"⚠️ Low nitrogen ({request.nitrogen} kg/ha) — increase Urea application by 20%")
    if request.phosphorus is not None and request.phosphorus < 20:
        tips.append(f"⚠️ Low phosphorus ({request.phosphorus} kg/ha) — apply extra DAP or SSP")
    if request.potassium is not None and request.potassium < 20:
        tips.append(f"⚠️ Low potassium ({request.potassium} kg/ha) — add MOP or sulphate of potash")
    if request.moisture is not None and request.moisture < 25:
        tips.append("⚠️ Low soil moisture — irrigate before applying fertilizers")
    if request.temperature is not None and request.temperature > 40:
        tips.append("⚠️ High temperature — avoid mid-day fertilizer application. Apply in early morning.")

    return FertilizerResponse(
        crop=crop,
        soil_type=soil,
        recommended_fertilizer=rec["fertilizer"],
        quantity=rec["quantity"],
        schedule=rec["schedule"],
        tips=tips,
    )
