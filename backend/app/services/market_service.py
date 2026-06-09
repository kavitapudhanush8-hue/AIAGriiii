"""
Market price service — seed data and trend analysis.

Provides market price management with sample Indian agricultural
market data and trend analysis capabilities.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.models import MarketPrice
from app.schemas.schemas import MarketPriceResponse, MarketPriceTrend


# ─── Sample Market Data (seeded on first run) ────────────────────────────────

SEED_DATA = [
    # Tomato prices across markets
    {"crop": "Tomato", "market": "Vijayawada", "price": 2200, "days_ago": 0},
    {"crop": "Tomato", "market": "Vijayawada", "price": 2000, "days_ago": 1},
    {"crop": "Tomato", "market": "Vijayawada", "price": 1800, "days_ago": 2},
    {"crop": "Tomato", "market": "Vijayawada", "price": 1950, "days_ago": 3},
    {"crop": "Tomato", "market": "Vijayawada", "price": 2100, "days_ago": 5},
    {"crop": "Tomato", "market": "Guntur", "price": 2350, "days_ago": 0},
    {"crop": "Tomato", "market": "Guntur", "price": 2100, "days_ago": 1},
    {"crop": "Tomato", "market": "Guntur", "price": 2050, "days_ago": 2},
    {"crop": "Tomato", "market": "Hyderabad", "price": 2500, "days_ago": 0},
    {"crop": "Tomato", "market": "Hyderabad", "price": 2300, "days_ago": 1},
    {"crop": "Tomato", "market": "Hyderabad", "price": 2400, "days_ago": 2},

    # Rice prices
    {"crop": "Rice", "market": "Vijayawada", "price": 2800, "days_ago": 0},
    {"crop": "Rice", "market": "Vijayawada", "price": 2750, "days_ago": 1},
    {"crop": "Rice", "market": "Vijayawada", "price": 2700, "days_ago": 2},
    {"crop": "Rice", "market": "Vijayawada", "price": 2650, "days_ago": 4},
    {"crop": "Rice", "market": "Guntur", "price": 2900, "days_ago": 0},
    {"crop": "Rice", "market": "Guntur", "price": 2850, "days_ago": 1},
    {"crop": "Rice", "market": "Hyderabad", "price": 3000, "days_ago": 0},
    {"crop": "Rice", "market": "Hyderabad", "price": 2950, "days_ago": 1},

    # Potato prices
    {"crop": "Potato", "market": "Vijayawada", "price": 1800, "days_ago": 0},
    {"crop": "Potato", "market": "Vijayawada", "price": 1900, "days_ago": 1},
    {"crop": "Potato", "market": "Vijayawada", "price": 1850, "days_ago": 2},
    {"crop": "Potato", "market": "Hyderabad", "price": 2000, "days_ago": 0},
    {"crop": "Potato", "market": "Hyderabad", "price": 2050, "days_ago": 1},

    # Corn prices
    {"crop": "Corn", "market": "Vijayawada", "price": 2100, "days_ago": 0},
    {"crop": "Corn", "market": "Vijayawada", "price": 2050, "days_ago": 1},
    {"crop": "Corn", "market": "Vijayawada", "price": 2000, "days_ago": 3},
    {"crop": "Corn", "market": "Guntur", "price": 2200, "days_ago": 0},
    {"crop": "Corn", "market": "Guntur", "price": 2150, "days_ago": 1},

    # Cotton prices
    {"crop": "Cotton", "market": "Guntur", "price": 6500, "days_ago": 0},
    {"crop": "Cotton", "market": "Guntur", "price": 6400, "days_ago": 1},
    {"crop": "Cotton", "market": "Guntur", "price": 6300, "days_ago": 2},
    {"crop": "Cotton", "market": "Guntur", "price": 6200, "days_ago": 4},
    {"crop": "Cotton", "market": "Hyderabad", "price": 6600, "days_ago": 0},
    {"crop": "Cotton", "market": "Hyderabad", "price": 6550, "days_ago": 1},

    # Onion prices
    {"crop": "Onion", "market": "Vijayawada", "price": 1500, "days_ago": 0},
    {"crop": "Onion", "market": "Vijayawada", "price": 1600, "days_ago": 1},
    {"crop": "Onion", "market": "Vijayawada", "price": 1700, "days_ago": 2},
    {"crop": "Onion", "market": "Hyderabad", "price": 1650, "days_ago": 0},
    {"crop": "Onion", "market": "Hyderabad", "price": 1700, "days_ago": 1},

    # Chilli prices
    {"crop": "Chilli", "market": "Guntur", "price": 12000, "days_ago": 0},
    {"crop": "Chilli", "market": "Guntur", "price": 11500, "days_ago": 1},
    {"crop": "Chilli", "market": "Guntur", "price": 11000, "days_ago": 3},
    {"crop": "Chilli", "market": "Guntur", "price": 10500, "days_ago": 5},
]


def seed_market_data(db: Session) -> int:
    """
    Seed the market_prices table with sample data if it is empty.
    Returns the number of rows inserted.
    """
    existing_count = db.query(MarketPrice).count()
    if existing_count > 0:
        return 0  # Already seeded

    now = datetime.utcnow()
    count = 0
    for entry in SEED_DATA:
        record = MarketPrice(
            crop=entry["crop"],
            market=entry["market"],
            price=entry["price"],
            unit="₹/quintal",
            date=now - timedelta(days=entry["days_ago"]),
        )
        db.add(record)
        count += 1

    db.commit()
    return count


def get_market_prices(
    db: Session,
    crop: Optional[str] = None,
    market: Optional[str] = None,
    limit: int = 50,
) -> List[MarketPrice]:
    """Fetch market prices with optional filters."""
    query = db.query(MarketPrice)

    if crop:
        query = query.filter(MarketPrice.crop == crop)
    if market:
        query = query.filter(MarketPrice.market == market)

    return query.order_by(MarketPrice.date.desc()).limit(limit).all()


def get_price_trend(
    db: Session,
    crop: str,
    market: str,
) -> MarketPriceTrend:
    """Compute price trend for a specific crop in a specific market."""
    prices = (
        db.query(MarketPrice)
        .filter(MarketPrice.crop == crop, MarketPrice.market == market)
        .order_by(MarketPrice.date.desc())
        .limit(30)
        .all()
    )

    if not prices:
        return MarketPriceTrend(
            crop=crop,
            market=market,
            current_price=0,
            trend="unknown",
            prices=[],
        )

    current_price = prices[0].price
    previous_price = prices[1].price if len(prices) > 1 else None

    if previous_price:
        change = ((current_price - previous_price) / previous_price) * 100
        change_percent = round(change, 2)
        if change > 1:
            trend = "up"
        elif change < -1:
            trend = "down"
        else:
            trend = "stable"
    else:
        change_percent = None
        trend = "stable"

    price_responses = [
        MarketPriceResponse(
            id=p.id,
            crop=p.crop,
            market=p.market,
            price=p.price,
            unit=p.unit or "₹/quintal",
            date=p.date,
        )
        for p in prices
    ]

    return MarketPriceTrend(
        crop=crop,
        market=market,
        current_price=current_price,
        previous_price=previous_price,
        change_percent=change_percent,
        trend=trend,
        prices=price_responses,
    )
