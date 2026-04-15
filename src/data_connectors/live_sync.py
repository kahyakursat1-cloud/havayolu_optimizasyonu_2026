"""External data connectors.

Fetches real aircraft traffic from OpenSky Network, weather from
Open-Meteo, and METAR strings from NOAA. Features circuit breakers
and offline fallbacks for production stability.
"""
import os
import random
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict

import requests
import pybreaker

logger = logging.getLogger(__name__)

OPENSKY_URL = "https://opensky-network.org/api/states/all"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
NOAA_METAR_URL = "https://aviationweather.gov/api/data/metar"

AIRPORT_COORDS = {
    "IST": (41.2753, 28.7519),
    "ESB": (40.1281, 32.9951),
    "ADB": (38.2924, 27.1568),
    "AYT": (36.8987, 30.8005),
    "LHR": (51.4700, -0.4543),
    "JFK": (40.6413, -73.7781),
    "CDG": (49.0097, 2.5479),
    "DXB": (25.2532, 55.3657),
}

DEFAULT_TR_BBOX = (35.0, 25.0, 43.0, 45.0)

# Circuit Breakers: Fail after 5 consecutive errors, reset after 60s
opensky_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)
weather_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)
noaa_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

class _TTLCache:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._store: dict = {}

    def get(self, key):
        entry = self._store.get(key)
        if not entry:
            return None
        value, expires = entry
        if time.time() > expires:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key, value):
        self._store[key] = (value, time.time() + self.ttl)


class ExternalDataConnector:
    """Live traffic + weather connector with circuit breakers and offline fallback."""

    def __init__(self, enabled: Optional[bool] = None, timeout: float = 4.0):
        if enabled is None:
            enabled = os.environ.get("LIVE_SYNC_ENABLED", "0") == "1"
        self.enabled = enabled
        self.timeout = timeout
        self._traffic_cache = _TTLCache(ttl_seconds=60)
        self._weather_cache = _TTLCache(ttl_seconds=600)
        self._noaa_cache = _TTLCache(ttl_seconds=900)

    @noaa_breaker
    def fetch_noaa_metar(self, airport_code: str = "IST") -> Optional[str]:
        """Fetch raw METAR string from NOAA."""
        cached = self._noaa_cache.get(airport_code)
        if cached:
            return cached

        if self.enabled:
            try:
                resp = requests.get(
                    NOAA_METAR_URL,
                    params={"ids": airport_code, "format": "json"},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0:
                    metar = data[0].get("rawOb")
                    self._noaa_cache.set(airport_code, metar)
                    return metar
            except Exception as exc:
                logger.warning("NOAA METAR fetch failed for %s: %s", airport_code, exc)
                raise exc # Trigger circuit breaker
        return None

    @weather_breaker
    def _fetch_meteo_raw(self, airport_code: str) -> dict:
        coords = AIRPORT_COORDS.get(airport_code)
        if not coords:
            raise ValueError(f"unknown airport: {airport_code}")
        lat, lon = coords
        resp = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,wind_speed_10m,wind_direction_10m,visibility,pressure_msl",
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("current", {})

    def fetch_real_metar(self, airport_code: str = "IST") -> dict:
        """Fetch current weather metrics from Open-Meteo. Returns fallback on failure."""
        cached = self._weather_cache.get(airport_code)
        if cached:
            return cached

        if self.enabled and airport_code in AIRPORT_COORDS:
            try:
                current = self._fetch_meteo_raw(airport_code)
                visibility = int(current.get("visibility", 9999) or 9999)
                result = {
                    "airport": airport_code,
                    "temperature_c": current.get("temperature_2m"),
                    "wind_speed_kt": current.get("wind_speed_10m"),
                    "wind_dir_deg": current.get("wind_direction_10m"),
                    "visibility_m": visibility,
                    "pressure_hpa": current.get("pressure_msl"),
                    "condition": "VFR" if visibility > 5000 else "IFR",
                    "is_real_data": True,
                    "source": "open-meteo",
                }
                self._weather_cache.set(airport_code, result)
                return result
            except Exception as exc:
                logger.warning("Weather fetch failed for %s: %s", airport_code, exc)

        return self._fallback_weather(airport_code)

    @opensky_breaker
    def _fetch_opensky_raw(self, bbox) -> list:
        min_lat, min_lon, max_lat, max_lon = bbox
        resp = requests.get(
            OPENSKY_URL,
            params={"lamin": min_lat, "lomin": min_lon, "lamax": max_lat, "lomax": max_lon},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return (resp.json() or {}).get("states") or []

    def fetch_opensky_traffic(self, bbox=DEFAULT_TR_BBOX) -> dict:
        """Fetch live aircraft states from OpenSky. Returns fallback on failure."""
        cache_key = tuple(bbox)
        cached = self._traffic_cache.get(cache_key)
        if cached:
            return cached

        if self.enabled:
            try:
                states = self._fetch_opensky_raw(bbox)
                result = {
                    "active_icao_count": len(states),
                    "region": "TR-Airspace" if bbox == DEFAULT_TR_BBOX else "custom",
                    "sync_status": "Success",
                    "is_real_data": True,
                    "source": "opensky",
                }
                self._traffic_cache.set(cache_key, result)
                return result
            except Exception as exc:
                logger.warning("OpenSky fetch failed: %s", exc)

        return self._fallback_traffic(bbox)

    def sync_all(self) -> dict:
        """Synchronize all streams."""
        return {
            "weather": self.fetch_real_metar("IST"),
            "traffic": self.fetch_opensky_traffic(),
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    @staticmethod
    def _fallback_weather(airport_code: str) -> dict:
        visibility = random.randint(5000, 9999)
        temp = random.randint(15, 30)
        return {
            "airport": airport_code,
            "metar": f"{airport_code} 131700Z 24010KT {visibility} FEW030 {temp}/12 Q1013",
            "condition": "VFR" if visibility > 5000 else "IFR",
            "is_real_data": False,
            "source": "fallback",
        }

    @staticmethod
    def _fallback_traffic(bbox) -> dict:
        return {
            "active_icao_count": random.randint(150, 450),
            "region": "TR-Airspace" if bbox == DEFAULT_TR_BBOX else "custom",
            "sync_status": "Success (Offline Fallback)",
            "is_real_data": False,
            "source": "fallback",
        }

market_intel = ExternalDataConnector()
