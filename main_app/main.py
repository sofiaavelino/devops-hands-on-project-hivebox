from fastapi import FastAPI, HTTPException
import httpx
from datetime import datetime, timezone, timedelta

app = FastAPI()

SENSEBOX_URL = "https://api.opensensemap.org/boxes"
APP_VERSION_FILE = "../version.txt"
CACHE_TTL = timedelta(minutes=5)

# In-memory cache
CACHE_VALUE = None
CACHE_TIME = None


async def fetch_boxes(params):
    """Function fetching data from opensensemap."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(SENSEBOX_URL, params=params)
        response.raise_for_status()
        return response.json()

'''async def fetch_last_measurement(sensor_id):
    url = f"https://api.opensensemap.org/sensors/{sensor_id}/data?limit=1"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None
            return data[0]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Sensor does not exist or has no data → skip
                return None
            raise  # re-raise other errors'''

def compute_average_temperature(boxes):
    """Function computing average temperature from data."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)

    temps = []

    for box in boxes:
        for sensor in box.get("sensors", []):
            #if sensor.get("type") != "temperature":
            #   continue

            unit = sensor.get("unit")

            if not isinstance(unit, str):
                continue

            if "°C" not in unit:
                continue

            last = sensor.get("lastMeasurement")
            print(last)

            if not isinstance(last, dict):
                continue

            ts_raw = last.get("createdAt")
            val_raw = last.get("value")

            if not ts_raw or not val_raw:
                continue

            try:
                ts = datetime.fromisoformat(
                    ts_raw.replace("Z", "+00:00")
                )
                value = float(val_raw)
            except (ValueError, TypeError):
                continue

            if ts >= cutoff:
                temps.append(value)

    if not temps:
        return None

    return sum(temps) / len(temps), len(temps)


@app.get("/temperature")
async def get_temperature():
    """Function obtaining average_temperature in past hour."""
    global CACHE_VALUE, CACHE_TIME

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)

    # Serve from cache if valid
    if CACHE_VALUE and CACHE_TIME:
        if now - CACHE_TIME < CACHE_TTL:
            return CACHE_VALUE
        
    params = {
        "date": f"{cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")},{now.strftime("%Y-%m-%dT%H:%M:%SZ")}",
        "phenomenon": "Temperatur",
        "bbox": "-10,35,30,60"
    }
        
    boxes = await fetch_boxes(params)
    result = compute_average_temperature(boxes)

    if result is None:
        raise HTTPException(
            status_code=503,
            detail="No temperature data from the last hour"
        )

    avg_temp, count = result

    response = {
        "average_temperature": round(avg_temp, 2),
        "unit": "°C",
        "measurements_used": count,
        "time_window_minutes": 60
    }

    CACHE_VALUE = response
    CACHE_TIME = now

    return response


@app.get("/version")
def get_version():
    """Function printing python version."""
    with open(APP_VERSION_FILE, encoding="utf-8") as f:
        return {"version": f.read().strip()}


