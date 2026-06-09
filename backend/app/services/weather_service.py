"""
Weather service: fetches weather data from OpenWeatherMap and generates
agricultural alerts based on conditions.
"""
import os
import hashlib
import math
from datetime import datetime
from typing import List, Tuple

import httpx

from app.schemas.schemas import WeatherData, WeatherAlertResponse


OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# ─── City Climate Profiles ────────────────────────────────────────────────────
# Each city gets a realistic base climate. The mock generator adds daily
# variation on top of these baselines so every city feels different.

_CITY_CLIMATE = {
    # South India — hot & humid
    "vijayawada":   {"temp": 34, "hum": 72, "wind": 10, "rain": 0.55, "desc": "Warm and humid with scattered clouds", "icon": "03d", "zone": "tropical_humid"},
    "hyderabad":    {"temp": 36, "hum": 55, "wind": 14, "rain": 0.30, "desc": "Hot and dry with hazy sunshine",       "icon": "01d", "zone": "semi_arid"},
    "chennai":      {"temp": 33, "hum": 80, "wind": 18, "rain": 0.60, "desc": "Humid coastal weather with sea breeze","icon": "04d", "zone": "coastal_humid"},
    "bangalore":    {"temp": 27, "hum": 65, "wind":  8, "rain": 0.40, "desc": "Pleasant weather with light breeze",   "icon": "02d", "zone": "moderate"},
    "kochi":        {"temp": 30, "hum": 85, "wind": 12, "rain": 0.75, "desc": "Heavy tropical humidity with showers", "icon": "10d", "zone": "tropical_wet"},
    "coimbatore":   {"temp": 31, "hum": 60, "wind": 10, "rain": 0.35, "desc": "Warm with partly cloudy skies",       "icon": "02d", "zone": "moderate"},
    "madurai":      {"temp": 35, "hum": 58, "wind":  9, "rain": 0.25, "desc": "Hot and dry with clear skies",         "icon": "01d", "zone": "semi_arid"},
    "visakhapatnam":{"temp": 32, "hum": 78, "wind": 20, "rain": 0.50, "desc": "Coastal winds with overcast skies",    "icon": "04d", "zone": "coastal_humid"},
    "guntur":       {"temp": 35, "hum": 68, "wind": 11, "rain": 0.45, "desc": "Hot with muggy conditions",            "icon": "03d", "zone": "tropical_humid"},
    "tirupati":     {"temp": 33, "hum": 70, "wind":  7, "rain": 0.40, "desc": "Warm with scattered clouds",           "icon": "03d", "zone": "tropical_humid"},

    # North India — seasonal extremes
    "delhi":        {"temp": 42, "hum": 30, "wind": 16, "rain": 0.10, "desc": "Scorching heat with dust haze",        "icon": "01d", "zone": "hot_arid"},
    "jaipur":       {"temp": 41, "hum": 22, "wind": 20, "rain": 0.05, "desc": "Very hot and arid desert conditions",  "icon": "01d", "zone": "desert"},
    "lucknow":      {"temp": 39, "hum": 45, "wind": 12, "rain": 0.20, "desc": "Hot and sticky with hazy sky",         "icon": "50d", "zone": "hot_arid"},
    "chandigarh":   {"temp": 37, "hum": 40, "wind": 10, "rain": 0.25, "desc": "Hot with occasional dry winds",        "icon": "02d", "zone": "hot_arid"},
    "amritsar":     {"temp": 38, "hum": 38, "wind": 14, "rain": 0.15, "desc": "Intense dry heat with clear skies",    "icon": "01d", "zone": "hot_arid"},
    "varanasi":     {"temp": 40, "hum": 50, "wind":  8, "rain": 0.25, "desc": "Extremely hot and oppressive",         "icon": "50d", "zone": "hot_arid"},

    # West India
    "mumbai":       {"temp": 31, "hum": 82, "wind": 22, "rain": 0.80, "desc": "Heavy monsoon humidity with showers",  "icon": "09d", "zone": "coastal_wet"},
    "pune":         {"temp": 29, "hum": 60, "wind": 10, "rain": 0.45, "desc": "Pleasant with light drizzle possible", "icon": "10d", "zone": "moderate"},
    "ahmedabad":    {"temp": 40, "hum": 35, "wind": 18, "rain": 0.08, "desc": "Very hot and dry with clear skies",    "icon": "01d", "zone": "hot_arid"},
    "surat":        {"temp": 34, "hum": 75, "wind": 16, "rain": 0.55, "desc": "Warm and muggy with overcast sky",     "icon": "04d", "zone": "coastal_humid"},

    # East India
    "kolkata":      {"temp": 34, "hum": 78, "wind": 15, "rain": 0.65, "desc": "Hot and sticky with thunderstorms",    "icon": "11d", "zone": "tropical_wet"},
    "bhubaneswar":  {"temp": 35, "hum": 75, "wind": 14, "rain": 0.55, "desc": "Hot with humid coastal influence",     "icon": "04d", "zone": "coastal_humid"},
    "patna":        {"temp": 38, "hum": 55, "wind":  8, "rain": 0.30, "desc": "Oppressive heat with hazy conditions", "icon": "50d", "zone": "hot_arid"},
    "ranchi":       {"temp": 30, "hum": 65, "wind": 10, "rain": 0.50, "desc": "Moderate with occasional showers",     "icon": "10d", "zone": "moderate"},
    "guwahati":     {"temp": 28, "hum": 88, "wind": 12, "rain": 0.85, "desc": "Heavy rain and very high humidity",    "icon": "09d", "zone": "tropical_wet"},

    # Central India
    "nagpur":       {"temp": 42, "hum": 28, "wind": 14, "rain": 0.10, "desc": "Extreme heat, dry orange-city summer", "icon": "01d", "zone": "hot_arid"},
    "indore":       {"temp": 37, "hum": 35, "wind": 12, "rain": 0.20, "desc": "Hot with partly cloudy skies",         "icon": "02d", "zone": "semi_arid"},
    "bhopal":       {"temp": 38, "hum": 40, "wind": 10, "rain": 0.25, "desc": "Hot and dry with hazy sunshine",        "icon": "50d", "zone": "semi_arid"},

    # Hill Stations & NE — cool
    "shimla":       {"temp": 18, "hum": 70, "wind":  8, "rain": 0.50, "desc": "Cool mountain air with mist",          "icon": "50d", "zone": "hill"},
    "darjeeling":   {"temp": 16, "hum": 80, "wind": 10, "rain": 0.65, "desc": "Cool and misty with drizzle",          "icon": "09d", "zone": "hill"},
    "ooty":         {"temp": 17, "hum": 75, "wind":  6, "rain": 0.45, "desc": "Cool and pleasant highland weather",   "icon": "03d", "zone": "hill"},
    "manali":       {"temp": 14, "hum": 60, "wind": 12, "rain": 0.35, "desc": "Cold mountain weather with clear sky", "icon": "02d", "zone": "hill"},
    "srinagar":     {"temp": 20, "hum": 55, "wind": 10, "rain": 0.30, "desc": "Cool valley weather with breeze",      "icon": "02d", "zone": "hill"},
    "shillong":     {"temp": 19, "hum": 82, "wind":  8, "rain": 0.70, "desc": "Cool and wet with continuous drizzle",  "icon": "09d", "zone": "hill"},

    # International examples
    "london":       {"temp": 15, "hum": 75, "wind": 18, "rain": 0.55, "desc": "Cool and overcast with light rain",    "icon": "10d", "zone": "temperate"},
    "dubai":        {"temp": 44, "hum": 20, "wind": 22, "rain": 0.02, "desc": "Extreme desert heat with sand haze",   "icon": "01d", "zone": "desert"},
    "tokyo":        {"temp": 24, "hum": 70, "wind": 12, "rain": 0.40, "desc": "Mild and humid with passing clouds",   "icon": "03d", "zone": "temperate"},
    "new york":     {"temp": 22, "hum": 55, "wind": 16, "rain": 0.30, "desc": "Clear skies with light wind",          "icon": "01d", "zone": "temperate"},
    "beijing":      {"temp": 30, "hum": 50, "wind": 14, "rain": 0.20, "desc": "Warm with occasional smog",            "icon": "50d", "zone": "semi_arid"},
}

# Zone-based fallbacks for unknown cities
_ZONE_DEFAULTS = {
    "tropical_humid": {"temp": 33, "hum": 72, "wind": 10, "rain": 0.50, "desc": "Warm tropical conditions",       "icon": "03d"},
    "tropical_wet":   {"temp": 30, "hum": 85, "wind": 14, "rain": 0.75, "desc": "Hot and wet tropical weather",    "icon": "09d"},
    "semi_arid":      {"temp": 36, "hum": 40, "wind": 14, "rain": 0.20, "desc": "Hot and dry with hazy sky",       "icon": "02d"},
    "hot_arid":       {"temp": 40, "hum": 30, "wind": 16, "rain": 0.10, "desc": "Very hot and dry",                "icon": "01d"},
    "coastal_humid":  {"temp": 31, "hum": 78, "wind": 18, "rain": 0.55, "desc": "Warm coastal humidity",           "icon": "04d"},
    "coastal_wet":    {"temp": 30, "hum": 82, "wind": 20, "rain": 0.70, "desc": "Coastal monsoon conditions",      "icon": "09d"},
    "moderate":       {"temp": 28, "hum": 60, "wind": 10, "rain": 0.40, "desc": "Pleasant moderate weather",       "icon": "02d"},
    "hill":           {"temp": 18, "hum": 72, "wind":  8, "rain": 0.50, "desc": "Cool highland conditions",        "icon": "50d"},
    "temperate":      {"temp": 20, "hum": 60, "wind": 14, "rain": 0.35, "desc": "Mild temperate weather",          "icon": "03d"},
    "desert":         {"temp": 42, "hum": 18, "wind": 22, "rain": 0.03, "desc": "Extreme arid desert heat",        "icon": "01d"},
}


def _city_hash(city: str) -> float:
    """Return a deterministic 0.0-1.0 float from a city name (daily variation)."""
    today = datetime.now().strftime("%Y-%m-%d")
    digest = hashlib.md5(f"{city.lower().strip()}-{today}".encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _generate_mock_weather(city: str) -> WeatherData:
    """
    Generate realistic, location-specific weather data.
    Uses city climate profiles with daily pseudo-random variation.
    """
    key = city.lower().strip()
    profile = _CITY_CLIMATE.get(key)

    if not profile:
        # Unknown city → generate from city name hash for uniqueness
        h = _city_hash(city)
        # Pick a zone based on the hash
        zones = list(_ZONE_DEFAULTS.keys())
        zone = zones[int(h * len(zones)) % len(zones)]
        profile = {**_ZONE_DEFAULTS[zone], "zone": zone}

    # Add daily variation using hash (±3°C temp, ±10% humidity, etc.)
    h = _city_hash(city)
    variation = (h - 0.5) * 2  # Range: -1.0 to +1.0

    temp = round(profile["temp"] + variation * 3, 1)
    humidity = max(5, min(99, int(profile["hum"] + variation * 10)))
    wind = max(0, round(profile["wind"] + variation * 5, 1))
    rain = max(0.0, min(1.0, round(profile["rain"] + variation * 0.15, 2)))

    # Pick description — sometimes override based on computed values
    desc = profile["desc"]
    icon = profile["icon"]
    if temp > 42:
        desc = f"Extreme heat wave conditions in {city}"
        icon = "01d"
    elif temp < 8:
        desc = f"Very cold conditions with possible frost in {city}"
        icon = "13d"
    elif rain > 0.8:
        desc = f"Heavy rainfall expected in {city}"
        icon = "09d"

    return WeatherData(
        city=city,
        temperature=temp,
        humidity=humidity,
        description=desc,
        wind_speed=wind,
        rain_probability=rain,
        icon=icon,
    )


async def fetch_weather(city: str) -> WeatherData:
    """
    Fetch current weather from OpenWeatherMap for a given city.
    Falls back to mock data if no API key is configured or API call fails.
    """
    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY.startswith("your-"):
        # Return location-aware mock data for development / demo
        return _generate_mock_weather(city)

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPENWEATHER_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        weather_main = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})
        rain = data.get("rain", {})

        return WeatherData(
            city=data.get("name", city),
            temperature=main.get("temp", 0),
            humidity=main.get("humidity", 0),
            description=weather_main.get("description", ""),
            wind_speed=wind.get("speed", 0),
            rain_probability=rain.get("1h", 0) if rain else 0,
            icon=weather_main.get("icon", ""),
        )
    except Exception:
        # Fall back to mock data if API fails
        return _generate_mock_weather(city)


def generate_agricultural_alerts(weather: WeatherData) -> List[WeatherAlertResponse]:
    """
    Generate context-aware agricultural alerts based on current weather.
    These alerts help farmers make better decisions.
    """
    alerts: List[WeatherAlertResponse] = []

    # ── Rain Alerts ───────────────────────────────────────────────────────
    if weather.rain_probability and weather.rain_probability > 0.5:
        alerts.append(WeatherAlertResponse(
            alert_type="rain",
            message=(
                f"Heavy rain expected in {weather.city}. "
                "Avoid spraying pesticides today. Consider covering nursery beds."
            ),
            severity="warning",
        ))
    elif weather.rain_probability and weather.rain_probability > 0.2:
        alerts.append(WeatherAlertResponse(
            alert_type="rain",
            message=(
                f"Light rain possible in {weather.city}. "
                "Postpone fertilizer application if possible."
            ),
            severity="info",
        ))

    # ── Temperature Alerts ────────────────────────────────────────────────
    if weather.temperature > 40:
        alerts.append(WeatherAlertResponse(
            alert_type="heat",
            message=(
                f"Extreme heat ({weather.temperature}°C) in {weather.city}. "
                "Increase irrigation frequency. Provide shade for young plants."
            ),
            severity="danger",
        ))
    elif weather.temperature > 35:
        alerts.append(WeatherAlertResponse(
            alert_type="heat",
            message=(
                f"High temperature ({weather.temperature}°C) detected. "
                "Water crops during early morning or evening."
            ),
            severity="warning",
        ))
    elif weather.temperature < 10:
        alerts.append(WeatherAlertResponse(
            alert_type="cold",
            message=(
                f"Low temperature ({weather.temperature}°C) in {weather.city}. "
                "Protect frost-sensitive crops with mulch or covers."
            ),
            severity="warning",
        ))

    # ── Wind Alerts ───────────────────────────────────────────────────────
    if weather.wind_speed > 30:
        alerts.append(WeatherAlertResponse(
            alert_type="storm",
            message=(
                f"Strong winds ({weather.wind_speed} km/h) expected. "
                "Secure crop supports and stakes. Avoid open-field spraying."
            ),
            severity="danger",
        ))

    # ── Humidity Alerts ───────────────────────────────────────────────────
    if weather.humidity > 85:
        alerts.append(WeatherAlertResponse(
            alert_type="humidity",
            message=(
                f"Very high humidity ({weather.humidity}%) in {weather.city}. "
                "Risk of fungal diseases is elevated. Monitor crops closely."
            ),
            severity="warning",
        ))

    # If no specific alerts, provide a general positive message
    if not alerts:
        alerts.append(WeatherAlertResponse(
            alert_type="info",
            message=f"Weather in {weather.city} looks favourable for farming today.",
            severity="info",
        ))

    return alerts
