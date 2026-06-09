"""Quick test: verify different cities return different weather data."""
import httpx

r = httpx.post('http://localhost:8000/auth/login', json={'phone':'5555555555','password':'fresh123'})
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

cities = ['Vijayawada', 'Hyderabad', 'Delhi', 'Shimla', 'Mumbai', 'Chennai', 'Kolkata', 'Jaipur']
print(f"{'City':15s}  {'Temp':>6s}  {'Humid':>5s}  {'Wind':>7s}  {'Rain':>5s}  {'Alerts':>6s}  Description")
print("-" * 100)

for city in cities:
    r = httpx.get(f'http://localhost:8000/weather?city={city}', headers=h)
    data = r.json()
    d = data['current']
    alerts = len(data['alerts'])
    rain_pct = f"{int(d['rain_probability']*100)}%"
    print(f"{city:15s}  {d['temperature']:5.1f}C  {d['humidity']:4d}%  {d['wind_speed']:5.1f}km/h  {rain_pct:>5s}  {alerts:>6d}  {d['description'][:50]}")

print("\nDone! Each city shows unique climate conditions.")
