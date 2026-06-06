"""Address → gush/chelka resolver via GovMap's public API.

Two hops, both token-free (the same calls GovMap's own public map makes):
  1. address → coordinates   — POST search-service/autocomplete → POINT(x y) in EPSG:3857
  2. coordinates → gush/chelka — WMS GetFeatureInfo on the public parcel layer
     (govmap:layer_parcel_all), then point-in-polygon to pick the containing parcel.

This uses GovMap's public GeoServer WMS (the same layer the map renders), so no API token
is required. All network I/O goes through one httpx.Client so tests inject httpx.MockTransport.
"""

import re
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

AUTOCOMPLETE_URL = "https://www.govmap.gov.il/api/search-service/autocomplete"
WMS_URL = "https://www.govmap.gov.il/api/geoserver/ows/public/"
PARCEL_LAYER = "govmap:layer_parcel_all"

# GovMap serves these from an Israeli-fronted CDN; a browser-like UA + Referer is expected.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.govmap.gov.il/",
}
_POINT_RE = re.compile(r"POINT\(\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s*\)")
_TIMEOUT = 15.0
# Half-width (metres, EPSG:3857) of the GetFeatureInfo query box centred on the address point.
_QUERY_HALF_M = 60.0


@dataclass
class AddressResolutionResult:
    status: str  # auto_resolved | multi_candidate | manual_entry | failed
    method: str = "rest"
    reason: Optional[str] = None  # govmap_error | not_found | invalid_result
    gush: Optional[str] = None
    chelka: Optional[str] = None
    coordinates: Optional[dict] = None  # {"x": float, "y": float} in EPSG:3857
    candidates: list[dict] = field(default_factory=list)  # [{"gush","chelka"}]
    raw_response: Optional[dict] = None
    resolution_time_ms: int = 0
    error: Optional[str] = None


def _extract_point(shape: str) -> Optional[dict]:
    m = _POINT_RE.search(shape or "")
    if not m:
        return None
    try:
        return {"x": float(m.group(1)), "y": float(m.group(2))}
    except ValueError:
        return None


def _point_in_ring(x: float, y: float, ring: list) -> bool:
    """Ray-casting point-in-polygon for a single ring of [x, y] pairs."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _geom_contains(geom: Optional[dict], x: float, y: float) -> bool:
    if not geom:
        return False
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []
    polys = [coords] if gtype == "Polygon" else coords if gtype == "MultiPolygon" else []
    for poly in polys:
        if poly and _point_in_ring(x, y, poly[0]):
            return True
    return False


def _parse_parcel_features(data: dict) -> list[dict]:
    """Map a WMS GeoJSON FeatureCollection to [{gush, chelka, geometry}]."""
    out = []
    for f in data.get("features", []):
        props = f.get("properties", {})
        gush = props.get("gush_num")
        chelka = props.get("parcel")
        if gush is None or chelka is None:
            continue
        out.append({"gush": str(gush), "chelka": str(chelka), "geometry": f.get("geometry")})
    return out


def _valid_id(value: Optional[str]) -> bool:
    # Numeric and within a generous plausibility bound; widen if real data exceeds it.
    return bool(value) and value.isdigit() and 0 < int(value) < 1_000_000


def _query_parcels(client: httpx.Client, point: dict) -> dict:
    """WMS GetFeatureInfo for the parcel layer at the given point (EPSG:3857)."""
    x, y = point["x"], point["y"]
    h = _QUERY_HALF_M
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": PARCEL_LAYER,
        "QUERY_LAYERS": PARCEL_LAYER,
        "CRS": "EPSG:3857",
        "BBOX": f"{x - h},{y - h},{x + h},{y + h}",
        "WIDTH": "256",
        "HEIGHT": "256",
        "I": "128",
        "J": "128",
        "INFO_FORMAT": "application/json",
        "FEATURE_COUNT": "20",
    }
    r = client.get(WMS_URL, params=params, headers=_HEADERS)
    r.raise_for_status()
    return r.json()


def resolve(
    city: str,
    street: str,
    number: str,
    *,
    transport: Optional[httpx.BaseTransport] = None,
) -> AddressResolutionResult:
    start = time.monotonic()

    def ms() -> int:
        return int((time.monotonic() - start) * 1000)

    full_address = " ".join(p for p in (street, number, city) if p)
    try:
        with httpx.Client(timeout=_TIMEOUT, transport=transport) as client:
            # Hop 1: address → coordinates
            r1 = client.post(
                AUTOCOMPLETE_URL,
                json={"searchText": full_address, "language": "he"},
                headers=_HEADERS,
            )
            r1.raise_for_status()
            data1 = r1.json()
            addresses = [x for x in data1.get("results", []) if x.get("type") == "address"]
            if not addresses:
                return AddressResolutionResult(
                    status="failed", reason="not_found", raw_response=data1, resolution_time_ms=ms()
                )
            point = _extract_point(addresses[0].get("shape", ""))
            if point is None:
                return AddressResolutionResult(
                    status="failed", reason="not_found", raw_response=data1, resolution_time_ms=ms()
                )

            # Hop 2: coordinates → gush/chelka (public WMS parcel layer)
            data2 = _query_parcels(client, point)
            features = _parse_parcel_features(data2)
            if not features:
                return AddressResolutionResult(
                    status="failed", reason="not_found",
                    coordinates=point, resolution_time_ms=ms(),
                )

            # Prefer parcels whose polygon actually contains the address point; if the
            # geocoded point sits on a boundary and none "contain" it, fall back to all hits.
            containing = [f for f in features if _geom_contains(f["geometry"], point["x"], point["y"])]
            picked = containing or features

            # De-duplicate by (gush, chelka).
            seen, uniq = set(), []
            for f in picked:
                key = (f["gush"], f["chelka"])
                if key not in seen:
                    seen.add(key)
                    uniq.append({"gush": f["gush"], "chelka": f["chelka"]})

            if len(uniq) == 1:
                gush, chelka = uniq[0]["gush"], uniq[0]["chelka"]
                if not (_valid_id(gush) and _valid_id(chelka)):
                    return AddressResolutionResult(
                        status="failed", reason="invalid_result",
                        coordinates=point, resolution_time_ms=ms(),
                    )
                return AddressResolutionResult(
                    status="auto_resolved", gush=gush, chelka=chelka,
                    coordinates=point, resolution_time_ms=ms(),
                )
            return AddressResolutionResult(
                status="multi_candidate", coordinates=point,
                candidates=uniq, resolution_time_ms=ms(),
            )
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return AddressResolutionResult(
            status="failed", reason="govmap_error", error=str(exc), resolution_time_ms=ms()
        )
