"""
SQLAlchemy ORM models for the AI Agriculture Assistant.

All models use SQLite-compatible column types.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database.database import Base


class Farmer(Base):
    """Farmer user account."""
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    village = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    language = Column(String(20), default="English")
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    predictions = relationship("Prediction", back_populates="farmer")
    weather_alerts = relationship("WeatherAlert", back_populates="farmer")


class Prediction(Base):
    """Disease prediction record for a leaf image upload."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    image_url = Column(String(500), nullable=True)
    disease = Column(String(200), nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    farmer = relationship("Farmer", back_populates="predictions")


class WeatherAlert(Base):
    """Weather alert stored for a farmer."""
    __tablename__ = "weather_alerts"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String(50), nullable=True)  # e.g., "rain", "heat", "storm"
    city = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    farmer = relationship("Farmer", back_populates="weather_alerts")


class Recommendation(Base):
    """Static disease treatment recommendations."""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    disease = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    cause = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)
    organic_treatment = Column(Text, nullable=True)
    chemical_treatment = Column(Text, nullable=True)
    prevention = Column(Text, nullable=True)


class MarketPrice(Base):
    """Crop market price record."""
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False, index=True)
    market = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    unit = Column(String(50), default="₹/quintal")
    date = Column(DateTime, default=datetime.utcnow)


class FertilizerRecommendation(Base):
    """Fertilizer recommendation record."""
    __tablename__ = "fertilizer_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False, index=True)
    soil_type = Column(String(100), nullable=False)
    nitrogen = Column(Float, nullable=True)
    phosphorus = Column(Float, nullable=True)
    potassium = Column(Float, nullable=True)
    moisture = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    recommendation = Column(Text, nullable=False)
    quantity = Column(String(100), nullable=True)
    schedule = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
