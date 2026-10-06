import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
root_env = Path(__file__).resolve().parents[2] / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY", "")
STATION_ID = 8118

url = f"https://api.openaq.org/v3/locations/{STATION_ID}"

headers = {}
if API_KEY:
    headers["X-API-Key"] = API_KEY

# Use httpx (from project requirements) or requests or urllib
try:
    import httpx
    response = httpx.get(url, headers=headers, timeout=30)
    status_code = response.status_code
    data = response.json() if status_code == 200 else None
    error_text = response.text
except ImportError:
    try:
        import requests
        response = requests.get(url, headers=headers, timeout=30)
        status_code = response.status_code
        data = response.json() if status_code == 200 else None
        error_text = response.text
    except ImportError:
        import json
        import urllib.request
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status_code = resp.status
                data = json.loads(resp.read().decode())
        except Exception as e:
            status_code = 500
            error_text = str(e)
            data = None

if status_code == 200 and data:
    # OpenAQ returns the location inside the "results" array
    station = data["results"][0]

    latitude = station["coordinates"]["latitude"]
    longitude = station["coordinates"]["longitude"]

    print(f"Station ID: {station['id']}")
    print(f"Station name: {station['name']}")
    print(f"Latitude: {latitude}")
    print(f"Longitude: {longitude}")
    if "sensors" in station:
        print("\nAvailable Sensors:")
        for s in station["sensors"]:
            param = s.get("parameter", {}).get("name", "unknown")
            print(f"  - Sensor ID: {s['id']} | Parameter: {param}")
else:
    print(f"Error: HTTP {status_code}")
    print(error_text)
