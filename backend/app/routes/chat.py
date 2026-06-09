"""
AI Agriculture Chatbot routes.

Provides a knowledge-based chatbot that answers agricultural questions
about diseases, fertilizers, weather, irrigation, and crop management.
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Farmer
from app.services.auth_service import get_current_farmer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Chat Assistant"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for sending a chat message."""
    message: str = Field(..., min_length=1, max_length=2000)
    language: Optional[str] = "English"


class ChatResponse(BaseModel):
    """Response body for a chat message."""
    question: str
    answer: str
    language: str
    timestamp: str


class ChatHistoryItem(BaseModel):
    """A single chat history entry."""
    id: int
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Knowledge Base ──────────────────────────────────────────────────────────

KNOWLEDGE_BASE = {
    "yellow leaves": {
        "en": "Yellow leaves can be caused by:\n1. **Nitrogen deficiency** — Apply urea or ammonium sulfate\n2. **Overwatering** — Reduce irrigation frequency\n3. **Iron deficiency** — Apply ferrous sulfate as foliar spray\n4. **Early disease infection** — Check for spots or patterns\n5. **Root damage** — Check for root rot or nematodes\n\n💡 **Tip:** Get a soil test to identify the exact nutrient deficiency.",
        "hi": "पीली पत्तियों के कारण:\n1. नाइट्रोजन की कमी — यूरिया लगाएं\n2. अधिक पानी — सिंचाई कम करें\n3. लोहे की कमी — फेरस सल्फेट स्प्रे करें\n4. रोग संक्रमण — पत्तियों पर धब्बे देखें\n5. जड़ क्षति — जड़ सड़न की जांच करें",
        "te": "పసుపు ఆకులు కారణాలు:\n1. నత్రజని లోపం — యూరియా వేయండి\n2. ఎక్కువ నీరు — నీటిపారుదల తగ్గించండి\n3. ఇనుము లోపం — ఫెర్రస్ సల్ఫేట్ స్ప్రే చేయండి\n4. వ్యాధి సోకడం — మచ్చలు తనిఖీ చేయండి",
    },
    "pest control": {
        "en": "Integrated Pest Management (IPM) tips:\n1. **Biological control** — Use neem oil, Trichoderma, Pseudomonas\n2. **Cultural practices** — Crop rotation, trap crops, clean cultivation\n3. **Mechanical methods** — Yellow sticky traps, light traps, hand picking\n4. **Chemical control (last resort)** — Use recommended pesticides at correct dosage\n\n⚠️ Always observe the waiting period before harvest after pesticide application.",
    },
    "irrigation": {
        "en": "Irrigation best practices:\n1. **Drip irrigation** — 90% water efficiency, best for vegetables\n2. **Sprinkler irrigation** — Good for field crops, 70-80% efficiency\n3. **Furrow irrigation** — Traditional, 50-60% efficiency\n4. **Timing** — Water early morning or late evening to minimize evaporation\n5. **Frequency** — Depends on crop stage, soil type, and weather\n\n💧 **Rule of thumb:** Sandy soil needs more frequent, lighter watering. Clay soil needs less frequent, deeper watering.",
    },
    "soil health": {
        "en": "Improving soil health:\n1. **Organic matter** — Add compost, farmyard manure, vermicompost\n2. **Green manuring** — Grow and plough in legumes like dhaincha, sunhemp\n3. **Crop rotation** — Alternate cereals with legumes\n4. **Mulching** — Use crop residue or organic mulch\n5. **Minimum tillage** — Reduce soil disturbance\n6. **Soil testing** — Test every 2-3 years for nutrient status\n\n🌱 Healthy soil = Healthy crops = Higher yields",
    },
    "organic farming": {
        "en": "Organic farming essentials:\n1. **Fertilizers** — Compost, vermicompost, biofertilizers (Rhizobium, Azotobacter)\n2. **Pest control** — Neem oil, Bt spray, pheromone traps, beneficial insects\n3. **Weed management** — Mulching, hand weeding, cover crops\n4. **Certification** — Contact local organic certification bodies\n5. **Market** — Organic produce sells at 20-50% premium\n\n✅ Transition period from conventional to organic is typically 2-3 years.",
    },
    "harvest": {
        "en": "Harvesting tips:\n1. **Timing** — Harvest at correct maturity stage for best quality\n2. **Morning harvest** — Vegetables taste better when harvested in cool hours\n3. **Tools** — Use clean, sharp tools to avoid damage\n4. **Post-harvest** — Sort, grade, and store properly to reduce losses\n5. **Storage** — Keep in cool, dry, well-ventilated place\n\n📦 Post-harvest losses in India are 25-30%. Proper handling can reduce this significantly.",
    },
    "tomato": {
        "en": "Tomato growing guide:\n1. **Season** — Rabi (Oct-Feb) and Kharif (Jun-Sep)\n2. **Spacing** — 60cm × 45cm\n3. **Fertilizer** — NPK 10:26:26 as basal, Urea top-dress at 30 & 60 days\n4. **Irrigation** — Drip irrigation every 2-3 days\n5. **Common diseases** — Early blight, late blight, leaf curl virus\n6. **Yield** — 20-25 tonnes/acre with good management\n\n🍅 Staking tomato plants improves air circulation and reduces disease.",
    },
    "rice": {
        "en": "Rice cultivation tips:\n1. **Nursery** — 20-25 days old seedlings for transplanting\n2. **Spacing** — 20cm × 15cm (SRI method: 25cm × 25cm)\n3. **Water management** — Maintain 2-3cm standing water during vegetative stage\n4. **Fertilizer** — Apply nitrogen in 3 splits (basal, tillering, panicle)\n5. **Common issues** — Blast, brown spot, BPH (Brown Plant Hopper)\n\n🌾 System of Rice Intensification (SRI) can increase yield by 20-50% with less water.",
    },
    "weather": {
        "en": "Weather-based farming decisions:\n1. **Before rain** — Avoid pesticide spraying, complete harvesting of mature crops\n2. **During drought** — Use mulching, reduce plant density, irrigate wisely\n3. **High temperature** — Provide shade, increase irrigation, harvest early morning\n4. **Cold wave** — Cover nurseries, irrigate to prevent frost damage\n5. **Monsoon** — Prepare drainage channels, watch for fungal diseases\n\n🌤️ Check weather forecasts daily through our Weather module!",
    },
    "market": {
        "en": "Getting best market prices:\n1. **Timing** — Sell when prices are high (check our Market module)\n2. **Grading** — Sort produce by size and quality for better rates\n3. **Direct selling** — Farmer markets, FPOs eliminate middlemen\n4. **Value addition** — Processing (drying, pickling) increases value\n5. **Storage** — Cold storage for perishables to sell during off-season\n\n📊 Use our Market Price Tracking feature to monitor daily prices!",
    },
}

DEFAULT_RESPONSE = {
    "en": "I'm your AI Agriculture Assistant! 🌱 I can help with:\n\n• **Plant diseases** — Ask about yellow leaves, spots, wilting\n• **Pest control** — Natural and chemical pest management\n• **Fertilizers** — What to apply and when\n• **Irrigation** — Best watering practices\n• **Soil health** — Improving your soil\n• **Crop guides** — Tomato, rice, potato, corn, cotton\n• **Weather advice** — Farming decisions based on weather\n• **Market tips** — Getting best prices for your produce\n• **Organic farming** — Transitioning to organic\n\nTry asking: \"Why are my tomato leaves turning yellow?\" or \"How to control pests naturally?\"",
    "hi": "मैं आपका AI कृषि सहायक हूँ! 🌱 मैं इन विषयों में मदद कर सकता हूँ:\n\n• पौधों के रोग\n• कीट नियंत्रण\n• उर्वरक सिफारिशें\n• सिंचाई\n• मिट्टी स्वास्थ्य\n• फसल मार्गदर्शन\n\nपूछें: \"मेरे टमाटर की पत्तियाँ पीली क्यों हो रही हैं?\"",
    "te": "నేను మీ AI వ్యవసాయ సహాయకుడిని! 🌱 నేను సహాయం చేయగలను:\n\n• మొక్కల వ్యాధులు\n• పురుగుల నియంత్రణ\n• ఎరువుల సిఫార్సులు\n• నీటిపారుదల\n• నేల ఆరోగ్యం\n• పంట మార్గదర్శకత్వం\n\nఅడగండి: \"నా టమాటా ఆకులు ఎందుకు పసుపు రంగులోకి మారుతున్నాయి?\"",
}


def _find_best_match(message: str) -> str:
    """Find the best matching knowledge base entry for a user message."""
    msg_lower = message.lower()
    best_key = None
    best_score = 0

    # Keyword matching
    # Keyword matching with weights
    keyword_map = {
        "yellow leaves": {"keywords": ["yellow", "yellowing", "पीली", "పసుపు"], "weight": 2},
        "pest control": {"keywords": ["pest", "insect", "bug", "कीट", "పురుగు", "aphid", "whitefly"], "weight": 1},
        "irrigation": {"keywords": ["water", "irrigation", "drip", "सिंचाई", "నీటిపారుదల", "watering"], "weight": 1},
        "soil health": {"keywords": ["soil", "मिट्टी", "నేల", "compost", "organic matter"], "weight": 1},
        "organic farming": {"keywords": ["organic", "जैविक", "సేంద్రీయ", "natural farming"], "weight": 1.5},
        "harvest": {"keywords": ["harvest", "storage", "post-harvest", "कटाई", "పంట కోత"], "weight": 1},
        "tomato": {"keywords": ["tomato", "टमाटर", "టమాటా"], "weight": 2},
        "rice": {"keywords": ["rice", "paddy", "चावल", "धान", "వరి"], "weight": 2},
        "weather": {"keywords": ["weather", "rain", "temperature", "मौसम", "వాతావరణం"], "weight": 1},
        "market": {"keywords": ["market", "price", "sell", "बाजार", "మార్కెట్", "rate"], "weight": 1},
    }

    for key, data in keyword_map.items():
        score = sum(data["weight"] for kw in data["keywords"] if kw in msg_lower)
        if score > best_score:
            best_score = score
            best_key = key

    return best_key


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI agriculture chatbot.
    Supports English, Hindi, and Telugu.
    """
    lang_code = "en"
    if payload.language and payload.language.lower() in ["hindi", "hi"]:
        lang_code = "hi"
    elif payload.language and payload.language.lower() in ["telugu", "te"]:
        lang_code = "te"

    # Find matching knowledge base entry
    match_key = _find_best_match(payload.message)

    if match_key and match_key in KNOWLEDGE_BASE:
        entry = KNOWLEDGE_BASE[match_key]
        answer = entry.get(lang_code, entry.get("en", ""))
    else:
        answer = DEFAULT_RESPONSE.get(lang_code, DEFAULT_RESPONSE["en"])

    logger.info("Chat query from farmer %d: %s", current_farmer.id, payload.message[:80])

    return ChatResponse(
        question=payload.message,
        answer=answer,
        language=payload.language or "English",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/chat/suggestions")
def chat_suggestions():
    """Get suggested questions for the chatbot."""
    return {
        "suggestions": [
            "Why are my tomato leaves turning yellow?",
            "How to control pests naturally?",
            "Best irrigation method for vegetables?",
            "How to improve soil health?",
            "Tomato growing guide",
            "Rice cultivation tips",
            "How to get best market prices?",
            "What to do before rain?",
            "How to start organic farming?",
            "When and how to harvest crops?",
        ]
    }
