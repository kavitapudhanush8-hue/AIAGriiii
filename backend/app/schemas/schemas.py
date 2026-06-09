"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ─── Authentication ───────────────────────────────────────────────────────────

class FarmerRegister(BaseModel):
    """Request body for farmer registration."""
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    language: Optional[str] = "English"


class FarmerLogin(BaseModel):
    """Request body for farmer login."""
    phone: str
    password: str


class FarmerProfile(BaseModel):
    """Response body for farmer profile."""
    id: int
    name: str
    phone: str
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    language: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FarmerUpdate(BaseModel):
    """Request body for updating farmer profile."""
    name: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    language: Optional[str] = None


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


# ─── Disease Prediction ──────────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    """Response body for a disease prediction."""
    id: int
    disease: str
    confidence: float
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Response body for a disease treatment recommendation."""
    disease: str
    description: Optional[str] = None
    cause: Optional[str] = None
    symptoms: Optional[str] = None
    organic_treatment: Optional[str] = None
    chemical_treatment: Optional[str] = None
    prevention: Optional[str] = None

    class Config:
        from_attributes = True


class PredictionWithRecommendation(BaseModel):
    """Combined prediction result with treatment recommendation."""
    prediction: PredictionResponse
    recommendation: Optional[RecommendationResponse] = None


# ─── Weather ──────────────────────────────────────────────────────────────────

class WeatherData(BaseModel):
    """Current weather data response."""
    city: str
    temperature: float
    humidity: int
    description: str
    wind_speed: float
    rain_probability: Optional[float] = None
    icon: Optional[str] = None


class WeatherAlertResponse(BaseModel):
    """Agricultural alert based on weather conditions."""
    alert_type: str
    message: str
    severity: str  # "info", "warning", "danger"


class WeatherResponse(BaseModel):
    """Full weather response including current data and alerts."""
    current: WeatherData
    alerts: List[WeatherAlertResponse]


# ─── Fertilizer Recommendation ───────────────────────────────────────────────

class FertilizerRequest(BaseModel):
    """Request body for fertilizer recommendation."""
    crop: str = Field(..., description="Crop type e.g. 'Tomato', 'Rice', 'Cotton'")
    soil_type: str = Field(..., description="Soil type e.g. 'Loamy', 'Sandy', 'Clay', 'Black'")
    nitrogen: Optional[float] = Field(None, ge=0, le=200, description="Nitrogen level (kg/ha)")
    phosphorus: Optional[float] = Field(None, ge=0, le=200, description="Phosphorus level (kg/ha)")
    potassium: Optional[float] = Field(None, ge=0, le=200, description="Potassium level (kg/ha)")
    moisture: Optional[float] = Field(None, ge=0, le=100, description="Soil moisture %")
    temperature: Optional[float] = Field(None, description="Temperature °C")


class FertilizerResponse(BaseModel):
    """Response body for fertilizer recommendation."""
    crop: str
    soil_type: str
    recommended_fertilizer: str
    quantity: str
    schedule: str
    tips: List[str]

    class Config:
        from_attributes = True


# ─── Market Price ─────────────────────────────────────────────────────────────

class MarketPriceResponse(BaseModel):
    """Single market price entry."""
    id: int
    crop: str
    market: str
    price: float
    unit: str
    date: datetime

    class Config:
        from_attributes = True


class MarketPriceTrend(BaseModel):
    """Market price trend analysis."""
    crop: str
    market: str
    current_price: float
    previous_price: Optional[float] = None
    change_percent: Optional[float] = None
    trend: str  # "up", "down", "stable"
    prices: List[MarketPriceResponse]


class MarketPriceCreate(BaseModel):
    """Request body for adding a market price entry."""
    crop: str = Field(..., description="Crop name e.g. 'Tomato', 'Rice'")
    market: str = Field(..., description="Market name e.g. 'Vijayawada', 'Guntur'")
    price: float = Field(..., gt=0, description="Price in ₹/quintal")
    unit: str = Field(default="₹/quintal")
