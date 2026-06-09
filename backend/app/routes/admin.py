"""
Admin Routes — AGENTAI
Simple admin panel to view live database users and stats.
Protected by a secret admin key set in environment variables.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database.database import get_db
from app.models.models import Farmer, Prediction, WeatherAlert, MarketPrice, FertilizerRecommendation

router = APIRouter(prefix="/admin", tags=["Admin"])

# Admin secret key — set ADMIN_KEY in your Render environment variables
ADMIN_KEY = os.getenv("ADMIN_KEY", "agentai-admin-2024")


def verify_admin(key: str = Query(..., description="Admin secret key")):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True


@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin),
):
    """List all registered users with their activity summary."""
    farmers = db.query(Farmer).order_by(Farmer.created_at.desc()).all()

    result = []
    for f in farmers:
        pred_count = db.query(func.count(Prediction.id)).filter(
            Prediction.farmer_id == f.id
        ).scalar()

        alert_count = db.query(func.count(WeatherAlert.id)).filter(
            WeatherAlert.farmer_id == f.id
        ).scalar()

        result.append({
            "id": f.id,
            "name": f.name,
            "phone": f.phone,
            "village": f.village,
            "district": f.district,
            "state": f.state,
            "language": f.language,
            "joined": str(f.created_at)[:19],
            "predictions": pred_count,
            "weather_alerts": alert_count,
        })

    return {
        "total_users": len(result),
        "users": result,
    }


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin),
):
    """Overall database statistics."""

    total_users = db.query(func.count(Farmer.id)).scalar()
    total_predictions = db.query(func.count(Prediction.id)).scalar()
    total_weather = db.query(func.count(WeatherAlert.id)).scalar()
    total_market = db.query(func.count(MarketPrice.id)).scalar()

    # Most recent user
    latest = db.query(Farmer).order_by(Farmer.created_at.desc()).first()

    # Most common disease
    top_disease = (
        db.query(Prediction.disease, func.count(Prediction.id).label("count"))
        .group_by(Prediction.disease)
        .order_by(func.count(Prediction.id).desc())
        .first()
    )

    return {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "total_weather_alerts": total_weather,
        "total_market_prices": total_market,
        "latest_user": {
            "name": latest.name,
            "phone": latest.phone,
            "joined": str(latest.created_at)[:19],
        } if latest else None,
        "most_common_disease": {
            "disease": top_disease[0],
            "count": top_disease[1],
        } if top_disease else None,
    }


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin),
):
    """Get full details for a specific user including all their activity."""
    farmer = db.query(Farmer).filter(Farmer.id == user_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="User not found")

    predictions = (
        db.query(Prediction)
        .filter(Prediction.farmer_id == user_id)
        .order_by(Prediction.created_at.desc())
        .all()
    )

    alerts = (
        db.query(WeatherAlert)
        .filter(WeatherAlert.farmer_id == user_id)
        .order_by(WeatherAlert.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "user": {
            "id": farmer.id,
            "name": farmer.name,
            "phone": farmer.phone,
            "village": farmer.village,
            "district": farmer.district,
            "state": farmer.state,
            "language": farmer.language,
            "joined": str(farmer.created_at)[:19],
        },
        "predictions": [
            {
                "disease": p.disease,
                "confidence": p.confidence,
                "date": str(p.created_at)[:19],
            }
            for p in predictions
        ],
        "weather_alerts": [
            {
                "city": a.city,
                "type": a.alert_type,
                "message": a.message,
                "date": str(a.created_at)[:10],
            }
            for a in alerts
        ],
    }
