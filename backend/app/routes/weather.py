"""
Weather routes: get current weather and agricultural alerts for a city.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Farmer, WeatherAlert
from app.schemas.schemas import WeatherResponse
from app.services.auth_service import get_current_farmer
from app.services.weather_service import fetch_weather, generate_agricultural_alerts

router = APIRouter(tags=["Weather"])


@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    city: str = Query(..., description="City name, e.g. 'Vijayawada'"),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Fetch current weather for a city and return intelligent agricultural
    alerts based on the conditions.
    """
    try:
        weather_data = await fetch_weather(city)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch weather data: {str(e)}",
        )

    alerts = generate_agricultural_alerts(weather_data)

    # Store alerts in database for the farmer's history
    for alert in alerts:
        db_alert = WeatherAlert(
            farmer_id=current_farmer.id,
            message=alert.message,
            alert_type=alert.alert_type,
            city=city,
        )
        db.add(db_alert)
    db.commit()

    return WeatherResponse(current=weather_data, alerts=alerts)
