"""
Geocoder: ambil koordinat akurat dari Google Maps Geocoding API.
Dijalankan SEKALI saat bot startup, hasilnya di-cache ke geocache.json.
"""

import os
import json
import time
import logging
import requests

logger = logging.getLogger(__name__)
CACHE_FILE = "geocache.json"
GMAPS_KEY = os.environ.get("GMAPS_API_KEY")


def geocode_name(name: str) -> tuple[float, float] | None:
    """Geocode satu nama lokasi → (lat, lon) atau None jika gagal."""
    url = "https://api.distancematrix.ai/maps/api/geocode/json"
    # Tambah konteks Jakarta supaya hasil lebih akurat
    query = f"{name}, Jakarta, Indonesia"
    params = {"address": query, "key": GMAPS_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get("status") == "OK" and data.get("result"):
            loc = data["result"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
        else:
            logger.warning(f"Geocode gagal untuk '{name}': {data.get('status')}")
            return None
    except Exception as e:
        logger.error(f"Error geocode '{name}': {e}")
        return None


def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def build_geocached_locations(locations_raw: dict) -> dict:
    """
    Terima LOCATIONS mentah {slot: [(name, lat, lon), ...]},
    kembalikan dict sama tapi koordinat sudah diverifikasi Google Maps.
    Kalau nama sudah ada di cache → pakai cache, tidak hit API lagi.
    """
    if not GMAPS_KEY:
        logger.warning("GMAPS_API_KEY tidak ditemukan, pakai koordinat fallback.")
        return locations_raw

    cache = load_cache()
    result = {}
    updated = False

    for slot, items in locations_raw.items():
        result[slot] = []
        for name, fallback_lat, fallback_lon in items:
            if name in cache:
                lat, lon = cache[name]
            else:
                logger.info(f"Geocoding: {name}")
                coords = geocode_name(name)
                if coords:
                    lat, lon = coords
                    cache[name] = [lat, lon]
                    updated = True
                else:
                    # Fallback ke koordinat estimasi
                    lat, lon = fallback_lat, fallback_lon
                    logger.warning(f"Pakai koordinat fallback untuk: {name}")
                time.sleep(0.1)  # Hindari rate limit

            result[slot].append((name, lat, lon))

    if updated:
        save_cache(cache)
        logger.info(f"Cache geocode disimpan ke {CACHE_FILE}")

    return result
