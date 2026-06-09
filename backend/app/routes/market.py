"""
Market price routes: view prices, get trends, add new price entries.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Farmer, MarketPrice
from app.schemas.schemas import (
    MarketPriceResponse,
    MarketPriceTrend,
    MarketPriceCreate,
)
from app.services.auth_service import get_current_farmer
from app.services.market_service import (
    get_market_prices,
    get_price_trend,
    seed_market_data,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Market Prices"])


@router.get("/market-prices", response_model=List[MarketPriceResponse])
def list_market_prices(
    crop: Optional[str] = Query(None, description="Filter by crop name"),
    market: Optional[str] = Query(None, description="Filter by market name"),
    limit: int = Query(50, ge=1, le=200),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Get current market prices. Optionally filter by crop and/or market.
    """
    # Auto-seed sample data on first access
    seed_market_data(db)

    prices = get_market_prices(db, crop=crop, market=market, limit=limit)
    return prices


@router.get("/market-prices/trend", response_model=MarketPriceTrend)
def market_price_trend(
    crop: str = Query(..., description="Crop name e.g. 'Tomato'"),
    market: str = Query(..., description="Market name e.g. 'Vijayawada'"),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Get price trend analysis for a specific crop in a specific market.
    Returns current price, previous price, percentage change, and trend direction.
    """
    # Auto-seed sample data on first access
    seed_market_data(db)

    trend = get_price_trend(db, crop=crop, market=market)
    if trend.current_price == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for {crop} in {market}",
        )
    return trend


@router.post("/market-prices", response_model=MarketPriceResponse, status_code=status.HTTP_201_CREATED)
def add_market_price(
    payload: MarketPriceCreate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Add a new market price entry. Useful for community-sourced price data.
    """
    record = MarketPrice(
        crop=payload.crop,
        market=payload.market,
        price=payload.price,
        unit=payload.unit,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info("New price entry: %s at %s = %s", payload.crop, payload.market, payload.price)
    return record


@router.get("/market-prices/crops", response_model=List[str])
def list_available_crops(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Get list of all crops with price data."""
    seed_market_data(db)
    results = db.query(MarketPrice.crop).distinct().all()
    return [r[0] for r in results]


@router.get("/market-prices/markets", response_model=List[str])
def list_available_markets(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Get list of all markets with price data."""
    seed_market_data(db)
    results = db.query(MarketPrice.market).distinct().all()
    return [r[0] for r in results]
