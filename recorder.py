import requests
import pandas as pd
import os
from datetime import datetime
import pytz

API_KEY  = os.environ["IQAIR_API_KEY"]
CSV_FILE = "dhaka_air_quality.csv"
BST      = pytz.timezone("Asia/Dhaka")

def aqi_category(aqi):
    if aqi <= 50:    return "Good"
    elif aqi <= 100: return "Moderate"
    elif aqi <= 150: return "Unhealthy for Sensitive Groups"
    elif aqi <= 200: return "Unhealthy"
    elif aqi <= 300: return "Very Unhealthy"
    else:            return "Hazardous"

def who_status(pm25):
    if not pm25: return "N/A"
    return f"{pm25 / 5:.1f}x WHO limit"

now = datetime.now(BST)
print(f"Recording — {now.strftime('%Y-%m-%d %H:%M')} BST")

url    = "http://api.airvisual.com/v2/city"
params = {
    "city":    "Dhaka",
    "state":   "Dhaka",
    "country": "Bangladesh",
    "key":     API_KEY
}

raw = requests.get(url, params=params, timeout=10).json()

if raw["status"] == "success":
    pollution = raw["data"]["current"]["pollution"]
    weather   = raw["data"]["current"]["weather"]

    aqi  = pollution.get("aqius", None)
    pm25 = pollution.get("p2", {}).get("conc", None)
    pm10 = pollution.get("p1", {}).get("conc", None)

    record = {
        "date":            now.strftime("%Y-%m-%d"),
        "time_bst":        now.strftime("%H:%M"),
        "day_of_week":     now.strftime("%A"),
        "session":         "Morning" if now.hour < 12 else "Afternoon" if now.hour < 18 else "Night",
        "city":            "Dhaka",
        "aqi":             aqi,
        "aqi_category":    aqi_category(aqi) if aqi else "N/A",
        "pm25_ugm3":       pm25,
        "pm10_ugm3":       pm10,
        "who_pm25_status": who_status(pm25),
        "main_pollutant":  pollution.get("mainus", "N/A"),
        "temperature_c":   weather.get("tp", None),
        "humidity_pct":    weather.get("hu", None),
        "wind_speed_ms":   weather.get("ws", None),
        "wind_direction":  weather.get("wd", None),
    }

    df_new = pd.DataFrame([record])
    if os.path.exists(CSV_FILE):
        df_existing = pd.read_csv(CSV_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_csv(CSV_FILE, index=False)
    print(f"✅ AQI: {aqi} ({aqi_category(aqi)}) | PM2.5: {pm25} µg/m³ | Temp: {weather.get('tp')}°C")
    print(f"📊 Total rows: {len(df_combined)}")
else:
    print(f"❌ Error: {raw.get('status')}")
