import hashlib
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DB_PATH = BASE_DIR / "weather_cache.db"

MAX_LOCATION_LENGTH = 100

CONDITIONS = [
    "Sunny",
    "Partly Cloudy",
    "Cloudy",
    "Light Rain",
    "Thunderstorms",
    "Snowy",
    "Windy",
    "Foggy",
]

app = FastAPI(title="Weather Forecast Demo")


def init_db() -> None:
    """Create the cache table if it does not exist yet."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS forecast_cache (
                location TEXT PRIMARY KEY,
                temperature REAL NOT NULL,
                condition TEXT NOT NULL,
                humidity INTEGER NOT NULL,
                wind REAL NOT NULL
            )
            """
        )
        conn.commit()


init_db()


def generate_forecast(location: str) -> dict:
    """Build a deterministic simulated forecast from the location name.

    The same location always yields the same values because the numbers are
    derived from a hash of the normalized location string.
    """
    normalized = location.strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).digest()

    temperature = round(-10 + (digest[0] / 255) * 45, 1)
    condition = CONDITIONS[digest[1] % len(CONDITIONS)]
    humidity = 30 + (digest[2] % 61)
    wind = round((digest[3] / 255) * 40, 1)

    return {
        "location": location.strip(),
        "temperature": temperature,
        "condition": condition,
        "humidity": humidity,
        "wind": wind,
    }


def get_cached(location: str) -> dict | None:
    """Return a cached forecast for the location, or None if not cached."""
    key = location.strip().lower()
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT temperature, condition, humidity, wind "
            "FROM forecast_cache WHERE location = ?",
            (key,),
        ).fetchone()
    if row is None:
        return None
    return {
        "location": location.strip(),
        "temperature": row[0],
        "condition": row[1],
        "humidity": row[2],
        "wind": row[3],
    }


def store_cache(forecast: dict) -> None:
    """Persist a forecast so repeat lookups can reuse it."""
    key = forecast["location"].strip().lower()
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO forecast_cache "
            "(location, temperature, condition, humidity, wind) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                key,
                forecast["temperature"],
                forecast["condition"],
                forecast["humidity"],
                forecast["wind"],
            ),
        )
        conn.commit()


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/forecast")
def forecast(location: str = Query(default="")):
    cleaned = location.strip()
    if not cleaned:
        return JSONResponse(
            status_code=400,
            content={"error": "Please provide a location or city name."},
        )
    if len(cleaned) > MAX_LOCATION_LENGTH:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Location must be {MAX_LOCATION_LENGTH} characters or fewer."
            },
        )

    cached = get_cached(cleaned)
    if cached is not None:
        result = dict(cached)
        result["cached"] = True
    else:
        result = generate_forecast(cleaned)
        store_cache(result)
        result["cached"] = False

    result["simulated"] = True
    result["disclaimer"] = "Simulated demo forecast - not real weather data."
    return result
