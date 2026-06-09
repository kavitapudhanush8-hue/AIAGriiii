"""
Fertilizer recommendation routes.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Farmer, FertilizerRecommendation
from app.schemas.schemas import FertilizerRequest, FertilizerResponse
from app.services.auth_service import get_current_farmer
from app.services.fertilizer_service import get_fertilizer_recommendation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Fertilizer Recommendation"])


@router.post("/fertilizer/recommend", response_model=FertilizerResponse)
def recommend_fertilizer(
    payload: FertilizerRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Get fertilizer recommendation based on crop type, soil type, and
    optional nutrient levels. The recommendation is saved to the
    farmer's history.
    """
    result = get_fertilizer_recommendation(payload)

    # Save to database for history
    db_rec = FertilizerRecommendation(
        crop=result.crop,
        soil_type=result.soil_type,
        nitrogen=payload.nitrogen,
        phosphorus=payload.phosphorus,
        potassium=payload.potassium,
        moisture=payload.moisture,
        temperature=payload.temperature,
        recommendation=result.recommended_fertilizer,
        quantity=result.quantity,
        schedule=result.schedule,
    )
    db.add(db_rec)
    db.commit()

    logger.info("Fertilizer recommendation for %s on %s soil", result.crop, result.soil_type)
    return result
