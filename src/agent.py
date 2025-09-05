# src/agent.py
import os, math, requests
from typing import List, Dict

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    import math as m
    phi1, phi2 = m.radians(lat1), m.radians(lat2)
    dphi = m.radians(lat2 - lat1)
    dl = m.radians(lon2 - lon1)
    a = m.sin(dphi/2)**2 + m.cos(phi1)*m.cos(phi2)*m.sin(dl/2)**2
    return 2*R*m.asin(m.sqrt(a))

def google_places_nearby(query: str, lat: float, lon: float, radius_m: int, key: str) -> List[Dict]:
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "location": f"{lat},{lon}", "radius": radius_m, "key": key}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = []
    for item in data.get("results", []):
        loc = item.get("geometry", {}).get("location", {})
        out.append({
            "name": item.get("name"),
            "address": item.get("formatted_address"),
            "lat": loc.get("lat"),
            "lon": loc.get("lng"),
            "rating": item.get("rating"),
            "types": item.get("types"),
        })
    return out

def osm_overpass_shops(center=(12.9698, 77.7499), radius_m=6000) -> List[Dict]:
    lat, lon = center
    around = f"(around:{radius_m},{lat},{lon})"
    overpass = f"""
    [out:json];
    (
      node[shop~"garden|agricultural|farm|hardware|general"]{around};
      node[name~"seed|nursery|agri|agriculture|papaya", i]{around};
    );
    out center 50;
    """
    r = requests.post("https://overpass-api.de/api/interpreter", data=overpass, timeout=30)
    r.raise_for_status()
    data = r.json()
    out = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        out.append({
            "name": tags.get("name"),
            "address": tags.get("addr:full") or tags.get("addr:street"),
            "lat": el.get("lat"),
            "lon": el.get("lon"),
            "tags": tags,
        })
    return out

def find_seed_stores_near_whitefield() -> List[Dict]:
    key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    if key:
        results = google_places_nearby(
            "papaya seed store near Whitefield Bangalore",
            12.9698, 77.7499, 6000, key
        )
        if results:
            return results[:10]
    return osm_overpass_shops()
