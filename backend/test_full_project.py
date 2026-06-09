"""
Comprehensive Test Suite for AI Agriculture Assistant
Tests all API endpoints end-to-end against the running server.
"""
import requests
import json
import os
import io
from PIL import Image

BASE_URL = "http://localhost:8000"

# ─── Formatting helpers ──────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = 0
failed = 0


def section(title):
    print(f"\n{'='*70}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{'='*70}")


def test(name, condition, response=None):
    global passed, failed
    if condition:
        passed += 1
        print(f"  {GREEN}✓ PASS{RESET}  {name}")
    else:
        failed += 1
        detail = ""
        if response is not None:
            try:
                detail = f" → {response.status_code}: {response.text[:200]}"
            except:
                detail = f" → {response}"
        print(f"  {RED}✗ FAIL{RESET}  {name}{detail}")


def pretty_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1: Health Check
# ═══════════════════════════════════════════════════════════════════════════════
section("1. HEALTH CHECK")

r = requests.get(f"{BASE_URL}/")
test("Health endpoint returns 200", r.status_code == 200, r)
data = r.json()
test("Status is healthy", data.get("status") == "healthy", r)
test("App name present", "Agriculture" in data.get("app", ""), r)
test("Version present", "1.0.0" in data.get("version", ""), r)
test("All 6 modules listed", len(data.get("modules", [])) == 6, r)
print(f"\n  {YELLOW}Response:{RESET}")
print(f"  {pretty_json(data)}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2: User Registration
# ═══════════════════════════════════════════════════════════════════════════════
section("2. FARMER REGISTRATION")

register_data = {
    "name": "Ravi Kumar",
    "phone": "9876543210",
    "password": "farmer123",
    "village": "Gudivada",
    "district": "Krishna",
    "state": "Andhra Pradesh",
    "language": "Telugu"
}

r = requests.post(f"{BASE_URL}/auth/register", json=register_data)
test("Registration returns 201", r.status_code == 201, r)
farmer = r.json()
test("Farmer name matches", farmer.get("name") == "Ravi Kumar", r)
test("Farmer phone matches", farmer.get("phone") == "9876543210", r)
test("Farmer village matches", farmer.get("village") == "Gudivada", r)
test("Farmer has ID", farmer.get("id") is not None, r)
test("Created_at timestamp present", farmer.get("created_at") is not None, r)
print(f"\n  {YELLOW}Registered Farmer:{RESET}")
print(f"  {pretty_json(farmer)}")

# Test duplicate registration
r_dup = requests.post(f"{BASE_URL}/auth/register", json=register_data)
test("Duplicate phone rejected (400)", r_dup.status_code == 400, r_dup)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3: User Login & JWT
# ═══════════════════════════════════════════════════════════════════════════════
section("3. FARMER LOGIN & JWT AUTHENTICATION")

login_data = {"phone": "9876543210", "password": "farmer123"}
r = requests.post(f"{BASE_URL}/auth/login", json=login_data)
test("Login returns 200", r.status_code == 200, r)
token_data = r.json()
test("Access token present", "access_token" in token_data, r)
test("Token type is bearer", token_data.get("token_type") == "bearer", r)

TOKEN = token_data.get("access_token", "")
AUTH_HEADERS = {"Authorization": f"Bearer {TOKEN}"}
print(f"\n  {YELLOW}JWT Token (first 50 chars):{RESET}")
print(f"  {TOKEN[:50]}...")

# Test wrong password
r_wrong = requests.post(f"{BASE_URL}/auth/login", json={"phone": "9876543210", "password": "wrong"})
test("Wrong password rejected (401)", r_wrong.status_code == 401, r_wrong)

# Test non-existent user
r_nouser = requests.post(f"{BASE_URL}/auth/login", json={"phone": "0000000000", "password": "test"})
test("Non-existent user rejected (401)", r_nouser.status_code == 401, r_nouser)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4: Profile Management
# ═══════════════════════════════════════════════════════════════════════════════
section("4. FARMER PROFILE MANAGEMENT")

r = requests.get(f"{BASE_URL}/auth/profile", headers=AUTH_HEADERS)
test("Get profile returns 200", r.status_code == 200, r)
profile = r.json()
test("Profile name matches", profile.get("name") == "Ravi Kumar", r)
test("Profile language is Telugu", profile.get("language") == "Telugu", r)
print(f"\n  {YELLOW}Profile:{RESET}")
print(f"  {pretty_json(profile)}")

# Update profile
update_data = {"name": "Ravi Kumar Reddy", "village": "Vijayawada"}
r = requests.put(f"{BASE_URL}/auth/profile", headers=AUTH_HEADERS, json=update_data)
test("Update profile returns 200", r.status_code == 200, r)
updated = r.json()
test("Name updated", updated.get("name") == "Ravi Kumar Reddy", r)
test("Village updated", updated.get("village") == "Vijayawada", r)
print(f"\n  {YELLOW}Updated Profile:{RESET}")
print(f"  {pretty_json(updated)}")

# Test unauthorized access
r_noauth = requests.get(f"{BASE_URL}/auth/profile")
test("Unauthorized access rejected (401)", r_noauth.status_code in [401, 403], r_noauth)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 5: Disease Prediction (Image Upload)
# ═══════════════════════════════════════════════════════════════════════════════
section("5. DISEASE PREDICTION (Image Upload & AI)")

# Create a test image (green leaf-like)
img = Image.new("RGB", (224, 224), color=(34, 139, 34))
img_buffer = io.BytesIO()
img.save(img_buffer, format="JPEG")
img_buffer.seek(0)

r = requests.post(
    f"{BASE_URL}/predict",
    headers=AUTH_HEADERS,
    files={"file": ("test_leaf.jpg", img_buffer, "image/jpeg")},
)
test("Prediction returns 200", r.status_code == 200, r)
pred_result = r.json()
test("Prediction object present", "prediction" in pred_result, r)
prediction = pred_result.get("prediction", {})
test("Disease name present", prediction.get("disease") is not None, r)
test("Confidence score present", prediction.get("confidence") is not None, r)
test("Confidence > 0", prediction.get("confidence", 0) > 0, r)
test("Image URL saved", prediction.get("image_url") is not None, r)
test("Prediction ID assigned", prediction.get("id") is not None, r)

# Check recommendation
recommendation = pred_result.get("recommendation")
if recommendation:
    test("Recommendation has disease name", recommendation.get("disease") is not None, r)
    print(f"\n  {YELLOW}Recommendation:{RESET}")
    print(f"  {pretty_json(recommendation)}")
else:
    print(f"  {YELLOW}(No recommendation for mock disease — expected){RESET}")

print(f"\n  {YELLOW}Prediction Result:{RESET}")
print(f"  Disease: {prediction.get('disease')}")
print(f"  Confidence: {prediction.get('confidence')}%")
print(f"  Image: {prediction.get('image_url')}")

# Upload a second image for history testing
img2 = Image.new("RGB", (224, 224), color=(139, 69, 19))
img_buffer2 = io.BytesIO()
img2.save(img_buffer2, format="JPEG")
img_buffer2.seek(0)
r2 = requests.post(
    f"{BASE_URL}/predict",
    headers=AUTH_HEADERS,
    files={"file": ("test_leaf2.jpg", img_buffer2, "image/jpeg")},
)
test("Second prediction returns 200", r2.status_code == 200, r2)

# Test prediction history
r_hist = requests.get(f"{BASE_URL}/predict/history", headers=AUTH_HEADERS)
test("Prediction history returns 200", r_hist.status_code == 200, r_hist)
history = r_hist.json()
test("History has >= 2 entries", len(history) >= 2, r_hist)
print(f"\n  {YELLOW}Prediction History ({len(history)} entries):{RESET}")
for h in history:
    print(f"    • {h.get('disease')} ({h.get('confidence')}%) — {h.get('created_at')}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 6: Disease Recommendation Lookup
# ═══════════════════════════════════════════════════════════════════════════════
section("6. DISEASE RECOMMENDATION LOOKUP")

# Test with a known disease from disease_info.json
known_diseases = [
    "Tomato - Early Blight",
    "Tomato - Late Blight",
    "Potato - Early Blight",
    "Corn - Common Rust",
]

for disease in known_diseases:
    r = requests.get(f"{BASE_URL}/recommendation/{disease}")
    if r.status_code == 200:
        rec = r.json()
        test(f"Recommendation for '{disease}' found", True, r)
        if disease == known_diseases[0]:
            print(f"\n  {YELLOW}Sample Recommendation ({disease}):{RESET}")
            print(f"  {pretty_json(rec)}")
    else:
        test(f"Recommendation for '{disease}' found", False, r)

# Test unknown disease
r_unknown = requests.get(f"{BASE_URL}/recommendation/UnknownDisease123")
test("Unknown disease returns 404", r_unknown.status_code == 404, r_unknown)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 7: Weather Alerts
# ═══════════════════════════════════════════════════════════════════════════════
section("7. WEATHER ALERTS & FORECASTING")

cities = ["Vijayawada", "Hyderabad", "Delhi", "Shimla", "Mumbai"]
for city in cities:
    r = requests.get(f"{BASE_URL}/weather?city={city}", headers=AUTH_HEADERS)
    test(f"Weather for {city} returns 200", r.status_code == 200, r)
    weather = r.json()
    current = weather.get("current", {})
    alerts = weather.get("alerts", [])
    
    print(f"\n  {YELLOW}🌤️  {city}:{RESET}")
    print(f"    Temperature: {current.get('temperature')}°C")
    print(f"    Humidity: {current.get('humidity')}%")
    print(f"    Wind: {current.get('wind_speed')} km/h")
    print(f"    Rain Prob: {current.get('rain_probability')}")
    print(f"    Description: {current.get('description')}")
    for alert in alerts:
        severity_colors = {"info": GREEN, "warning": YELLOW, "danger": RED}
        color = severity_colors.get(alert.get("severity"), "")
        print(f"    {color}⚠ [{alert.get('severity').upper()}] {alert.get('message')}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 8: Fertilizer Recommendations
# ═══════════════════════════════════════════════════════════════════════════════
section("8. FERTILIZER RECOMMENDATIONS")

fert_tests = [
    {"crop": "Tomato", "soil_type": "Loamy"},
    {"crop": "Rice", "soil_type": "Clay", "nitrogen": 20, "phosphorus": 15, "moisture": 20},
    {"crop": "Cotton", "soil_type": "Black", "temperature": 42},
    {"crop": "Potato", "soil_type": "Sandy"},
]

for ft in fert_tests:
    r = requests.post(f"{BASE_URL}/fertilizer/recommend", headers=AUTH_HEADERS, json=ft)
    test(f"Fertilizer for {ft['crop']} on {ft['soil_type']} soil", r.status_code == 200, r)
    result = r.json()
    print(f"\n  {YELLOW}🌱 {ft['crop']} on {ft['soil_type']} soil:{RESET}")
    print(f"    Fertilizer: {result.get('recommended_fertilizer')}")
    print(f"    Quantity: {result.get('quantity')}")
    print(f"    Schedule: {result.get('schedule')}")
    tips = result.get("tips", [])
    for tip in tips[:3]:
        print(f"    💡 {tip}")
    if len(tips) > 3:
        print(f"    ... and {len(tips)-3} more tips")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 9: Market Prices
# ═══════════════════════════════════════════════════════════════════════════════
section("9. MARKET PRICE TRACKING")

# List all crops
r = requests.get(f"{BASE_URL}/market-prices/crops", headers=AUTH_HEADERS)
test("List crops returns 200", r.status_code == 200, r)
crops = r.json()
test("Multiple crops available", len(crops) >= 3, r)
print(f"\n  {YELLOW}Available Crops:{RESET} {', '.join(crops)}")

# List all markets
r = requests.get(f"{BASE_URL}/market-prices/markets", headers=AUTH_HEADERS)
test("List markets returns 200", r.status_code == 200, r)
markets = r.json()
test("Multiple markets available", len(markets) >= 2, r)
print(f"  {YELLOW}Available Markets:{RESET} {', '.join(markets)}")

# Get all prices
r = requests.get(f"{BASE_URL}/market-prices", headers=AUTH_HEADERS)
test("Get all prices returns 200", r.status_code == 200, r)
all_prices = r.json()
test("Multiple price entries", len(all_prices) >= 10, r)
print(f"  {YELLOW}Total price entries:{RESET} {len(all_prices)}")

# Filter by crop
r = requests.get(f"{BASE_URL}/market-prices?crop=Tomato", headers=AUTH_HEADERS)
test("Filter by Tomato works", r.status_code == 200, r)
tomato_prices = r.json()
test("All filtered entries are Tomato", all(p["crop"] == "Tomato" for p in tomato_prices), r)

# Price trend
r = requests.get(f"{BASE_URL}/market-prices/trend?crop=Tomato&market=Vijayawada", headers=AUTH_HEADERS)
test("Price trend returns 200", r.status_code == 200, r)
trend = r.json()
test("Trend has current price", trend.get("current_price", 0) > 0, r)
test("Trend direction present", trend.get("trend") in ["up", "down", "stable"], r)
print(f"\n  {YELLOW}📊 Tomato Price Trend (Vijayawada):{RESET}")
print(f"    Current: ₹{trend.get('current_price')}/quintal")
print(f"    Previous: ₹{trend.get('previous_price')}/quintal")
print(f"    Change: {trend.get('change_percent')}%")
print(f"    Trend: {'📈' if trend.get('trend') == 'up' else '📉' if trend.get('trend') == 'down' else '➡️'} {trend.get('trend').upper()}")

# Add new price
new_price = {"crop": "Groundnut", "market": "Kurnool", "price": 5500, "unit": "₹/quintal"}
r = requests.post(f"{BASE_URL}/market-prices", headers=AUTH_HEADERS, json=new_price)
test("Add new price entry returns 201", r.status_code == 201, r)
print(f"\n  {YELLOW}Added new price:{RESET} Groundnut @ ₹5500/quintal in Kurnool")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 10: AI Chat Assistant
# ═══════════════════════════════════════════════════════════════════════════════
section("10. AI CHAT ASSISTANT")

# Get suggestions
r = requests.get(f"{BASE_URL}/chat/suggestions")
test("Chat suggestions returns 200", r.status_code == 200, r)
suggestions = r.json().get("suggestions", [])
test("Multiple suggestions available", len(suggestions) >= 5, r)
print(f"\n  {YELLOW}Suggested Questions:{RESET}")
for s in suggestions[:5]:
    print(f"    • {s}")

# Test various chat queries
chat_tests = [
    {"message": "Why are my tomato leaves turning yellow?", "language": "English"},
    {"message": "How to control pests naturally?", "language": "English"},
    {"message": "Best irrigation method for vegetables?", "language": "English"},
    {"message": "Tomato growing guide", "language": "English"},
    {"message": "How to get best market prices?", "language": "English"},
    {"message": "मेरे टमाटर की पत्तियाँ पीली क्यों हो रही हैं?", "language": "Hindi"},
]

for ct in chat_tests:
    r = requests.post(f"{BASE_URL}/chat", headers=AUTH_HEADERS, json=ct)
    test(f"Chat: '{ct['message'][:40]}...' ({ct['language']})", r.status_code == 200, r)
    chat_resp = r.json()
    answer = chat_resp.get("answer", "")
    # Show first chat response in full
    if ct == chat_tests[0]:
        print(f"\n  {YELLOW}💬 Q: {ct['message']}{RESET}")
        print(f"  {YELLOW}🤖 A:{RESET}")
        for line in answer.split("\n")[:8]:
            print(f"     {line}")
        if len(answer.split("\n")) > 8:
            print(f"     ... (truncated)")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 11: Swagger API Documentation
# ═══════════════════════════════════════════════════════════════════════════════
section("11. API DOCUMENTATION (Swagger)")

r = requests.get(f"{BASE_URL}/openapi.json")
test("OpenAPI schema available", r.status_code == 200, r)
schema = r.json()
paths = list(schema.get("paths", {}).keys())
test("Multiple API paths documented", len(paths) >= 10, r)
print(f"\n  {YELLOW}Documented API Endpoints:{RESET}")
for path in sorted(paths):
    methods = list(schema["paths"][path].keys())
    for m in methods:
        summary = schema["paths"][path][m].get("summary", "")
        print(f"    {m.upper():6s} {path:35s} — {summary}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 12: Frontend Web App
# ═══════════════════════════════════════════════════════════════════════════════
section("12. FRONTEND WEB APP")

r = requests.get(f"{BASE_URL}/app/")
test("Frontend served at /app/", r.status_code == 200, r)
test("HTML content returned", "html" in r.text.lower()[:500], r)
test("Has page title", "<title>" in r.text.lower(), r)
print(f"  {YELLOW}Frontend served at:{RESET} {BASE_URL}/app/")


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print(f"{BOLD}{CYAN}  TEST SUMMARY{RESET}")
print(f"{'='*70}")
total = passed + failed
print(f"  Total Tests:  {total}")
print(f"  {GREEN}Passed:     {passed}{RESET}")
print(f"  {RED}Failed:     {failed}{RESET}")
pct = (passed / total * 100) if total > 0 else 0
color = GREEN if pct >= 90 else YELLOW if pct >= 70 else RED
print(f"  {color}Pass Rate:  {pct:.1f}%{RESET}")

if failed == 0:
    print(f"\n  {GREEN}{BOLD}🎉 ALL TESTS PASSED! The project is fully working!{RESET}")
else:
    print(f"\n  {YELLOW}{BOLD}⚠️  Some tests failed. Check details above.{RESET}")

print(f"\n{'='*70}")
print(f"{BOLD}  📋 PROJECT ENDPOINTS SUMMARY{RESET}")
print(f"{'='*70}")
print(f"  🏠 Health Check:      GET  {BASE_URL}/")
print(f"  📝 Register:          POST {BASE_URL}/auth/register")
print(f"  🔐 Login:             POST {BASE_URL}/auth/login")
print(f"  👤 Profile:           GET  {BASE_URL}/auth/profile")
print(f"  ✏️  Update Profile:    PUT  {BASE_URL}/auth/profile")
print(f"  🔬 Predict Disease:   POST {BASE_URL}/predict")
print(f"  📜 Prediction History:GET  {BASE_URL}/predict/history")
print(f"  💊 Recommendation:    GET  {BASE_URL}/recommendation/{{disease}}")
print(f"  🌤️  Weather:          GET  {BASE_URL}/weather?city={{city}}")
print(f"  🌱 Fertilizer:        POST {BASE_URL}/fertilizer/recommend")
print(f"  📊 Market Prices:     GET  {BASE_URL}/market-prices")
print(f"  📈 Price Trend:       GET  {BASE_URL}/market-prices/trend")
print(f"  🆕 Add Price:         POST {BASE_URL}/market-prices")
print(f"  🌾 Crops List:        GET  {BASE_URL}/market-prices/crops")
print(f"  🏪 Markets List:      GET  {BASE_URL}/market-prices/markets")
print(f"  💬 Chat:              POST {BASE_URL}/chat")
print(f"  ❓ Chat Suggestions:  GET  {BASE_URL}/chat/suggestions")
print(f"  📖 Swagger UI:        GET  {BASE_URL}/docs")
print(f"  🌐 Web Frontend:      GET  {BASE_URL}/app/")
print(f"{'='*70}")
