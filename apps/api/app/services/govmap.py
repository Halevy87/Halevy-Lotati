"""Address → gush/chelka resolver via GovMap's current API.

Two hops:
  1. address → coordinates  — POST search-service/autocomplete (token-free, proven live)
  2. coordinates → gush/chelka — token-gated parcel identify

Hop-2 endpoint path and response shape are the current hypothesis; confirm/adjust the
parser against the live API once GOVMAP_API_TOKEN is set (see plan Task 10). With no token
(the default), hop 2 is never called and resolution returns failed/token_not_configured.
All network I/O goes through one httpx.Client so tests inject httpx.MockTransport.
"""

import re
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.core.config import settings

AUTOCOMPLETE_URL = "https://www.govmap.gov.il/api/search-service/autocomplete"
PARCEL_IDENTIFY_URL = "https://www.govmap.gov.il/api/layers-catalog/identify"

_POINT_RE = re.compile(r"POINT\(\s*([-\d.]+)\s+([-\d.]+)\s*\)")
_PARCEL_RE = re.compile(r"גוש\s*(\d+)\s*חלקה\s*(\d+)")
_TIMEOUT = 15.0


@dataclass
class AddressResolutionResult:
    status: str  # auto_resolved | multi_candidate | manual_entry | failed
    method: str = "rest"
    reason: Optional[str] = None  # token_not_configured | govmap_error | not_found | invalid_result
    gush: Optional[str] = None
    chelka: Optional[str] = None
    coordinates: Optional[dict] = None  # {"x": float, "y": float} in EPSG:3857
    candidates: list = field(default_factory=list)  # [{"gush","chelka"}]
    raw_response: Optional[dict] = None
    resolution_time_ms: int = 0
    error: Optional[str] = None


def _extract_point(shape: str) -> Optional[dict]:
    m = _POINT_RE.search(shape or "")
    if not m:
        return None
    return {"x": float(m.group(1)), "y": float(m.group(2))}


def _parse_parcels(data: dict) -> list[dict]:
    parcels = []
    for item in data.get("results", []):
        m = _PARCEL_RE.search(item.get("text", ""))
        if m:
            parcels.append({"gush": m.group(1), "chelka": m.group(2)})
    return parcels


def _valid_id(value: Optional[str]) -> bool:
    return bool(value) and value.isdigit() and 0 < int(value) < 100000


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

    full_address = f"{street} {number} {city}".strip()
    try:
        with httpx.Client(timeout=_TIMEOUT, transport=transport) as client:
            # Hop 1: address → coordinates (token-free)
            r1 = client.post(AUTOCOMPLETE_URL, json={"searchText": full_address, "language": "he"})
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

            # Hop 2: coordinates → gush/chelka (token-gated)
            if not settings.govmap_api_token:
                return AddressResolutionResult(
                    status="failed", reason="token_not_configured",
                    coordinates=point, resolution_time_ms=ms(),
                )
            r2 = client.post(
                PARCEL_IDENTIFY_URL,
                json={"x": point["x"], "y": point["y"], "layers": ["PARCEL_ALL"]},
                headers={"Authorization": f"Bearer {settings.govmap_api_token}"},
            )
            r2.raise_for_status()
            data2 = r2.json()
            parcels = _parse_parcels(data2)
            if not parcels:
                return AddressResolutionResult(
                    status="failed", reason="not_found",
                    coordinates=point, raw_response=data2, resolution_time_ms=ms(),
                )
            if len(parcels) > 1:
                return AddressResolutionResult(
                    status="multi_candidate", coordinates=point,
                    candidates=parcels, raw_response=data2, resolution_time_ms=ms(),
                )
            gush, chelka = parcels[0]["gush"], parcels[0]["chelka"]
            if not (_valid_id(gush) and _valid_id(chelka)):
                return AddressResolutionResult(
                    status="failed", reason="invalid_result",
                    coordinates=point, raw_response=data2, resolution_time_ms=ms(),
                )
            return AddressResolutionResult(
                status="auto_resolved", gush=gush, chelka=chelka,
                coordinates=point, raw_response=data2, resolution_time_ms=ms(),
            )
    except httpx.HTTPError as exc:
        return AddressResolutionResult(
            status="failed", reason="govmap_error", error=str(exc), resolution_time_ms=ms()
        )
