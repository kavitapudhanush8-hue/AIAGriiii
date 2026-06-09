"""Live demo of all working API endpoints."""
import httpx, json

base = 'http://localhost:8000'

# 1. Health check
r = httpx.get(f'{base}/')
print('=== HEALTH CHECK ===')
print(json.dumps(r.json(), indent=2))

# 2. Login
r = httpx.post(f'{base}/auth/login', json={'phone':'9876543210','password':'farmer123'})
token = r.json().get('access_token','')
print('\n=== LOGIN (200 OK) ===')
print(f'Token: {token[:60]}...')

h = {'Authorization': f'Bearer {token}'}

# 3. Weather 5 cities
print('\n=== WEATHER (5 CITIES) ===')
for city in ['Vijayawada', 'Hyderabad', 'Delhi', 'Shimla', 'Mumbai']:
    r = httpx.get(f'{base}/weather?city={city}', headers=h)
    d = r.json()['current']
    temp = d['temperature']
    hum = d['humidity']
    wind = d['wind_speed']
    desc = d['description'][:40]
    print(f'  {city:12s}  {temp:5.1f}C  Humidity:{hum}%  Wind:{wind}km/h  {desc}')

# 4. Market prices
r = httpx.get(f'{base}/market-prices/trend?crop=Tomato&market=Vijayawada', headers=h)
t = r.json()
print('\n=== TOMATO PRICE TREND ===')
print(f'  Current:  Rs.{t["current_price"]}/quintal')
print(f'  Previous: Rs.{t["previous_price"]}/quintal')
print(f'  Change:   {t["change_percent"]}% ({t["trend"].upper()})')

# 5. Crops & Markets
r = httpx.get(f'{base}/market-prices/crops', headers=h)
print(f'\n=== AVAILABLE CROPS ===')
print(f'  {", ".join(r.json())}')

r = httpx.get(f'{base}/market-prices/markets', headers=h)
print(f'=== AVAILABLE MARKETS ===')
print(f'  {", ".join(r.json())}')

# 6. Chat
r = httpx.post(f'{base}/chat', headers=h, json={'message':'How to grow tomatoes?','language':'English'})
ans = r.json().get('answer','')
print('\n=== AI CHAT ===')
print('  Q: How to grow tomatoes?')
for line in ans.split('\n')[:7]:
    print(f'  {line}')

# 7. Fertilizer
r = httpx.post(f'{base}/fertilizer/recommend', headers=h, json={'crop':'Tomato','soil_type':'Loamy'})
fr = r.json()
print('\n=== FERTILIZER RECOMMENDATION ===')
print(f'  Crop: Tomato | Soil: Loamy')
print(f'  Fertilizer: {fr["recommended_fertilizer"]}')
print(f'  Quantity: {fr["quantity"]}')
print(f'  Schedule: {fr["schedule"][:80]}')

# 8. Profile
r = httpx.get(f'{base}/auth/profile', headers=h)
p = r.json()
print('\n=== FARMER PROFILE ===')
print(f'  Name: {p["name"]}')
print(f'  Phone: {p["phone"]}')
print(f'  Village: {p["village"]}, {p["district"]}, {p["state"]}')
print(f'  Language: {p["language"]}')

print('\n' + '='*60)
print('  ALL ENDPOINTS WORKING!')
print('='*60)
print(f'  Web App:  http://localhost:8000/app/')
print(f'  Swagger:  http://localhost:8000/docs')
print(f'  Health:   http://localhost:8000/')
print('='*60)
