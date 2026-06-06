# Address Resolver (Step 5.5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve an Israeli street address into block/parcel (gush/chelka) via GovMap's current API, fully wired into the backend and Case Detail UI, with a manual-entry fallback that works before the GovMap token exists.

**Architecture:** A synchronous backend service (`app/services/govmap.py`) does the proven two-hop lookup — address → coordinates (token-free) then coordinates → gush/chelka (token-gated). Three endpoints on the `/api/cases` router run it synchronously, persist each attempt in a new `AddressResolution` table, update the `Case`, and log an `Activity`. A Case Detail sidebar card triggers resolution and offers manual entry. `Case.block`/`parcel` become nullable (address-first).

**Tech Stack:** FastAPI, SQLAlchemy 2 (`Mapped`/`mapped_column`), Alembic, Pydantic 2, `httpx` (sync `Client` + `MockTransport` for tests), pytest; Next.js 14, TanStack Query, next-intl, Vitest.

**Spec:** [docs/superpowers/specs/2026-06-07-address-resolver-design.md](../specs/2026-06-07-address-resolver-design.md)

**Conventions:** Enums stored as `String` columns. Activity model maps attribute `activity_metadata` → column `"metadata"`. Backend tests build schema via `Base.metadata.create_all` against `halevy_test` (not Alembic). Run backend commands from `apps/api` with the venv active; frontend from `apps/web`. Ruff line-length 100.

---

## File Structure

**Backend (`apps/api`)**
- Create `app/services/__init__.py`, `app/services/govmap.py` — the resolver (one responsibility: address→gush/chelka).
- Create `app/models/address_resolution.py` — the `AddressResolution` table.
- Create `app/schemas/address_resolution.py` — request/response schemas.
- Create `app/routers/address_resolution.py` — the 3 endpoints.
- Create `alembic/versions/<rev>_address_resolver.py` — migration.
- Create tests: `tests/test_govmap_service.py`, `tests/test_address_resolution.py`.
- Modify `app/core/config.py` (token setting), `app/models/case.py` (5 fields + nullable block/parcel), `app/models/__init__.py` (export new model), `app/schemas/case.py` (optional/nullable + resolved fields), `app/routers/cases.py` (expose `_get_case_or_404` import), `app/main.py` (register router), `pyproject.toml` (move `httpx` to runtime deps).

**Frontend (`apps/web`)**
- Create `src/components/address-resolution-card.tsx`, `src/components/address-resolution-card.test.tsx`.
- Modify `src/lib/types.ts`, `src/lib/api.ts`, `src/lib/schemas.ts`, `src/components/case-detail.tsx`, `src/components/new-case-modal.tsx`, `messages/he.json`.

---

## Task 1: GovMap token setting + httpx as runtime dep

**Files:**
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/pyproject.toml`

- [ ] **Step 1: Add the token setting**

In `app/core/config.py`, add inside `Settings` (after `cors_origins`):

```python
    # GovMap official developer API token (free; registered by the firm). Empty = hop 2
    # (coordinates→gush/chelka) is skipped and resolution falls back to manual entry.
    govmap_api_token: str = ""
```

- [ ] **Step 2: Make httpx a runtime dependency**

In `pyproject.toml`, add `"httpx>=0.27",` to `[project.dependencies]` (it is currently only under `dev`). Leave it in `dev` too (harmless) or remove from dev — either is fine.

- [ ] **Step 3: Verify config imports**

Run: `cd apps/api && source .venv/bin/activate && python -c "from app.core.config import settings; print(repr(settings.govmap_api_token))"`
Expected: prints `''`

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/core/config.py apps/api/pyproject.toml
git commit -m "feat(api): add GOVMAP_API_TOKEN setting; httpx as runtime dep"
```

---

## Task 2: GovMap resolver service

**Files:**
- Create: `apps/api/app/services/__init__.py`
- Create: `apps/api/app/services/govmap.py`
- Test: `apps/api/tests/test_govmap_service.py`

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/test_govmap_service.py`:

```python
import httpx
import pytest

from app.core.config import settings
from app.services import govmap


def _mock(handler):
    return httpx.MockTransport(handler)


def test_auto_resolved_with_token(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        if "autocomplete" in str(request.url):
            return httpx.Response(200, json={"results": [
                {"type": "address", "shape": "POINT(3867584.08 3764952.86)"}
            ]})
        return httpx.Response(200, json={"results": [{"text": "גוש 7136 חלקה 142"}]})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "auto_resolved"
    assert res.gush == "7136"
    assert res.chelka == "142"
    assert res.coordinates == {"x": 3867584.08, "y": 3764952.86}
    assert res.method == "rest"


def test_token_not_configured_short_circuits(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [
            {"type": "address", "shape": "POINT(1.0 2.0)"}
        ]})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "failed"
    assert res.reason == "token_not_configured"
    assert res.coordinates == {"x": 1.0, "y": 2.0}
    assert res.gush is None


def test_address_not_found(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    res = govmap.resolve("עיר", "רחוב", "1", transport=_mock(handler))
    assert res.status == "failed"
    assert res.reason == "not_found"


def test_multi_candidate(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        if "autocomplete" in str(request.url):
            return httpx.Response(200, json={"results": [
                {"type": "address", "shape": "POINT(1.0 2.0)"}
            ]})
        return httpx.Response(200, json={"results": [
            {"text": "גוש 7136 חלקה 142"}, {"text": "גוש 7136 חלקה 143"}
        ]})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "multi_candidate"
    assert len(res.candidates) == 2


def test_govmap_http_error(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "failed"
    assert res.reason == "govmap_error"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && source .venv/bin/activate && pytest tests/test_govmap_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services'`

- [ ] **Step 3: Create the service package and module**

Create `apps/api/app/services/__init__.py` (empty file).

Create `apps/api/app/services/govmap.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_govmap_service.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Lint and commit**

```bash
ruff check app/services/govmap.py tests/test_govmap_service.py
git add apps/api/app/services apps/api/tests/test_govmap_service.py
git commit -m "feat(api): GovMap address resolver service (two-hop, token-ready)"
```

---

## Task 3: AddressResolution model + Case field changes

**Files:**
- Create: `apps/api/app/models/address_resolution.py`
- Modify: `apps/api/app/models/case.py`
- Modify: `apps/api/app/models/__init__.py`

- [ ] **Step 1: Create the model**

Create `apps/api/app/models/address_resolution.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AddressResolution(Base):
    """One address→gush/chelka resolution attempt (audit + retry history). Step 5.5."""

    __tablename__ = "address_resolution"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    # Inputs actually used
    city: Mapped[str] = mapped_column(String, nullable=False)
    street: Mapped[str] = mapped_column(String, nullable=False)
    number: Mapped[str] = mapped_column(String, nullable=False)
    apartment_number_claimed: Mapped[str | None] = mapped_column(String, nullable=True)
    # Outputs
    status: Mapped[str] = mapped_column(String, nullable=False)
    resolved_gush: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_chelka: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_tat_chelka: Mapped[str | None] = mapped_column(String, nullable=True)
    coordinates: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Metadata
    method: Mapped[str] = mapped_column(String, nullable=False, default="rest")
    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolution_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
```

- [ ] **Step 2: Add Case fields and make block/parcel nullable**

In `app/models/case.py`, change the `block` and `parcel` columns to nullable:

```python
    block: Mapped[str | None] = mapped_column(String, nullable=True)  # gush
    parcel: Mapped[str | None] = mapped_column(String, nullable=True)  # chelka
```

Then add these after the `property_city` column:

```python
    # Resolved property identifiers (Step 5.5 — Address Resolver)
    resolved_gush: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_chelka: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_tat_chelka: Mapped[str | None] = mapped_column(String, nullable=True)
    apartment_number_claimed: Mapped[str | None] = mapped_column(String, nullable=True)
    property_coordinates: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

- [ ] **Step 3: Export the model**

In `app/models/__init__.py`, add an import so `Base.metadata` and Alembic autogenerate see it. Match the existing import style in that file, e.g. add:

```python
from app.models.address_resolution import AddressResolution  # noqa: F401
```

- [ ] **Step 4: Verify metadata builds**

Run: `cd apps/api && source .venv/bin/activate && python -c "from app.models import AddressResolution; from app.core.db import Base; print('address_resolution' in Base.metadata.tables)"`
Expected: prints `True`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/models/address_resolution.py apps/api/app/models/case.py apps/api/app/models/__init__.py
git commit -m "feat(api): AddressResolution model + Case resolved fields; block/parcel nullable"
```

---

## Task 4: Pydantic schemas

**Files:**
- Create: `apps/api/app/schemas/address_resolution.py`
- Modify: `apps/api/app/schemas/case.py`

- [ ] **Step 1: Create address-resolution schemas**

Create `apps/api/app/schemas/address_resolution.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResolveAddressRequest(BaseModel):
    # All optional: missing street/number are parsed from the case's property_address.
    street: str | None = None
    number: str | None = None
    apartment_number_claimed: str | None = None


class ManualResolutionRequest(BaseModel):
    gush: str
    chelka: str
    tat_chelka: str | None = None


class AddressResolutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    city: str
    street: str
    number: str
    apartment_number_claimed: str | None
    status: str
    resolved_gush: str | None
    resolved_chelka: str | None
    resolved_tat_chelka: str | None
    coordinates: dict | None
    method: str
    resolution_time_ms: int
    resolved_at: datetime
```

- [ ] **Step 2: Update Case schemas**

In `app/schemas/case.py`:

In `CaseCreate`, change `block`/`parcel` to optional:

```python
    block: str | None = None
    parcel: str | None = None
```

In `CaseDetail`, change `block`/`parcel` to nullable and add resolved fields:

```python
class CaseDetail(CaseListItem):
    block: str | None
    parcel: str | None
    sub_parcel: str | None
    resolved_gush: str | None = None
    resolved_chelka: str | None = None
    resolved_tat_chelka: str | None = None
    apartment_number_claimed: str | None = None
    property_coordinates: dict | None = None
    deal_value_ils: int | None
    counterparty_lawyer_name: str | None
    counterparty_lawyer_phone: str | None
    signing_scheduled_at: datetime | None
    handover_scheduled_at: datetime | None
    parties: list[PartyOut] = []
    activities: list[ActivityOut] = []
```

Leave `CaseUpdate.block`/`parcel` as already-optional `str | None` (no change).

- [ ] **Step 3: Verify schemas import**

Run: `cd apps/api && source .venv/bin/activate && python -c "from app.schemas.address_resolution import AddressResolutionOut, ResolveAddressRequest, ManualResolutionRequest; from app.schemas.case import CaseDetail; print('ok')"`
Expected: prints `ok`

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/schemas/address_resolution.py apps/api/app/schemas/case.py
git commit -m "feat(api): address-resolution schemas; Case block/parcel optional + resolved fields"
```

---

## Task 5: API endpoints + activity logging

**Files:**
- Create: `apps/api/app/routers/address_resolution.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_address_resolution.py`

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/test_address_resolution.py`:

```python
import uuid

import pytest

from app.services import govmap


def _case_payload(**overrides):
    payload = {
        "deal_type": "purchase",
        "property_address": "בר יהודה 33",
        "property_city": "בת ים",
        "primary_client": {
            "role": "buyer",
            "full_name": "ישראל ישראלי",
            "israeli_id": "000000018",
        },
    }
    payload.update(overrides)
    return payload


def _make_case(client) -> str:
    return client.post("/api/cases", json=_case_payload()).json()["id"]


def test_create_case_without_block_parcel(client):
    resp = client.post("/api/cases", json=_case_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["block"] is None
    assert body["parcel"] is None


def test_resolve_auto_resolved(client, monkeypatch):
    def fake_resolve(city, street, number, **kwargs):
        return govmap.AddressResolutionResult(
            status="auto_resolved", gush="7136", chelka="142",
            coordinates={"x": 1.0, "y": 2.0}, resolution_time_ms=12,
        )

    monkeypatch.setattr(govmap, "resolve", fake_resolve)
    cid = _make_case(client)

    resp = client.post(f"/api/cases/{cid}/resolve-address", json={})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "auto_resolved"
    assert body["resolved_gush"] == "7136"

    case = client.get(f"/api/cases/{cid}").json()
    assert case["resolved_gush"] == "7136"
    assert case["resolved_chelka"] == "142"
    assert case["block"] == "7136"  # mirrored into empty block
    assert case["property_coordinates"] == {"x": 1.0, "y": 2.0}

    activity = client.get(f"/api/cases/{cid}/activity").json()
    assert any(a["type"] == "scraping_completed" for a in activity)


def test_resolve_failed_token_not_configured(client, monkeypatch):
    def fake_resolve(city, street, number, **kwargs):
        return govmap.AddressResolutionResult(
            status="failed", reason="token_not_configured", coordinates={"x": 1.0, "y": 2.0}
        )

    monkeypatch.setattr(govmap, "resolve", fake_resolve)
    cid = _make_case(client)

    resp = client.post(f"/api/cases/{cid}/resolve-address", json={})
    assert resp.status_code == 200  # expected outcome, not a server error
    assert resp.json()["status"] == "failed"

    activity = client.get(f"/api/cases/{cid}/activity").json()
    assert any(a["type"] == "scraping_failed" for a in activity)


def test_get_address_resolution_404_then_latest(client, monkeypatch):
    cid = _make_case(client)
    assert client.get(f"/api/cases/{cid}/address-resolution").status_code == 404

    def fake_resolve(city, street, number, **kwargs):
        return govmap.AddressResolutionResult(status="failed", reason="not_found")

    monkeypatch.setattr(govmap, "resolve", fake_resolve)
    client.post(f"/api/cases/{cid}/resolve-address", json={})
    got = client.get(f"/api/cases/{cid}/address-resolution")
    assert got.status_code == 200
    assert got.json()["status"] == "failed"


def test_manual_resolution(client):
    cid = _make_case(client)
    resp = client.patch(
        f"/api/cases/{cid}/address-resolution/manual",
        json={"gush": "7136", "chelka": "142", "tat_chelka": "13"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "manual_entry"
    assert body["method"] == "manual"
    assert body["resolved_tat_chelka"] == "13"

    case = client.get(f"/api/cases/{cid}").json()
    assert case["resolved_gush"] == "7136"
    assert case["block"] == "7136"
    assert case["sub_parcel"] == "13"

    activity = client.get(f"/api/cases/{cid}/activity").json()
    assert any(a["type"] == "note_added" for a in activity)


def test_resolve_missing_case_404(client):
    assert client.post(f"/api/cases/{uuid.uuid4()}/resolve-address", json={}).status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && source .venv/bin/activate && pytest tests/test_address_resolution.py -v`
Expected: FAIL — 404 on `/resolve-address` (route not registered) / endpoints missing.

- [ ] **Step 3: Create the router**

Create `apps/api/app/routers/address_resolution.py`:

```python
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.activity import Activity
from app.models.address_resolution import AddressResolution
from app.models.case import Case
from app.models.enums import ActivityType
from app.schemas.address_resolution import (
    AddressResolutionOut,
    ManualResolutionRequest,
    ResolveAddressRequest,
)
from app.services import govmap

router = APIRouter(prefix="/api/cases", tags=["address-resolution"])

_ADDR_RE = re.compile(r"^(.*?)[\s,]*(\d+)\s*$")


def _get_case_or_404(db: Session, case_id: uuid.UUID) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _split_address(address: str) -> tuple[str, str]:
    """Best-effort split of a free-text address into (street, number)."""
    m = _ADDR_RE.match((address or "").strip())
    if m:
        return m.group(1).strip(), m.group(2)
    return (address or "").strip(), ""


@router.post("/{case_id}/resolve-address", response_model=AddressResolutionOut)
def resolve_address(
    case_id: uuid.UUID, payload: ResolveAddressRequest, db: Session = Depends(get_db)
) -> AddressResolution:
    case = _get_case_or_404(db, case_id)

    street, number = payload.street, payload.number
    if not street or not number:
        parsed_street, parsed_number = _split_address(case.property_address)
        street = street or parsed_street
        number = number or parsed_number

    result = govmap.resolve(case.property_city, street, number)

    row = AddressResolution(
        case_id=case.id,
        city=case.property_city,
        street=street,
        number=number,
        apartment_number_claimed=payload.apartment_number_claimed,
        status=result.status,
        resolved_gush=result.gush,
        resolved_chelka=result.chelka,
        coordinates=result.coordinates,
        method=result.method,
        raw_response=result.raw_response,
        resolution_time_ms=result.resolution_time_ms,
    )
    db.add(row)

    if payload.apartment_number_claimed:
        case.apartment_number_claimed = payload.apartment_number_claimed

    if result.status == "auto_resolved":
        case.resolved_gush = result.gush
        case.resolved_chelka = result.chelka
        case.property_coordinates = result.coordinates
        if not case.block:
            case.block = result.gush
        if not case.parcel:
            case.parcel = result.chelka
        db.add(Activity(
            case_id=case.id,
            type=ActivityType.scraping_completed,
            description="כתובת נפתרה לגוש/חלקה",  # "Address resolved to block/parcel"
            activity_metadata={"gush": result.gush, "chelka": result.chelka},
        ))
    else:
        db.add(Activity(
            case_id=case.id,
            type=ActivityType.scraping_failed,
            description="פתרון כתובת נכשל",  # "Address resolution failed"
            activity_metadata={"status": result.status, "reason": result.reason},
        ))

    db.commit()
    db.refresh(row)
    return row


@router.get("/{case_id}/address-resolution", response_model=AddressResolutionOut)
def get_address_resolution(
    case_id: uuid.UUID, db: Session = Depends(get_db)
) -> AddressResolution:
    _get_case_or_404(db, case_id)
    row = (
        db.query(AddressResolution)
        .filter(AddressResolution.case_id == case_id)
        .order_by(AddressResolution.resolved_at.desc())
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="No address resolution yet")
    return row


@router.patch("/{case_id}/address-resolution/manual", response_model=AddressResolutionOut)
def manual_resolution(
    case_id: uuid.UUID, payload: ManualResolutionRequest, db: Session = Depends(get_db)
) -> AddressResolution:
    case = _get_case_or_404(db, case_id)

    row = AddressResolution(
        case_id=case.id,
        city=case.property_city,
        street="",
        number="",
        status="manual_entry",
        method="manual",
        resolved_gush=payload.gush,
        resolved_chelka=payload.chelka,
        resolved_tat_chelka=payload.tat_chelka,
    )
    db.add(row)

    case.resolved_gush = payload.gush
    case.resolved_chelka = payload.chelka
    case.resolved_tat_chelka = payload.tat_chelka
    if not case.block:
        case.block = payload.gush
    if not case.parcel:
        case.parcel = payload.chelka
    if payload.tat_chelka and not case.sub_parcel:
        case.sub_parcel = payload.tat_chelka

    db.add(Activity(
        case_id=case.id,
        type=ActivityType.note_added,
        description="גוש/חלקה הוזנו ידנית",  # "Block/parcel entered manually"
        activity_metadata={"gush": payload.gush, "chelka": payload.chelka},
    ))

    db.commit()
    db.refresh(row)
    return row
```

- [ ] **Step 4: Register the router**

In `app/main.py`, add to the imports line:

```python
from app.routers import activity, address_resolution, cases, health, parties
```

And after `app.include_router(activity.router)`:

```python
app.include_router(address_resolution.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_address_resolution.py -v`
Expected: PASS (7 tests)

- [ ] **Step 6: Run the full backend suite (no regressions)**

Run: `pytest -v`
Expected: PASS — all prior tests (incl. `test_create_case_validation_error_returns_422`, which still 422s because `property_address`/`property_city` remain required) plus the new ones.

- [ ] **Step 7: Lint and commit**

```bash
ruff check app/routers/address_resolution.py app/main.py tests/test_address_resolution.py
git add apps/api/app/routers/address_resolution.py apps/api/app/main.py apps/api/tests/test_address_resolution.py
git commit -m "feat(api): address-resolution endpoints (resolve/get/manual) + activity logging"
```

---

## Task 6: Alembic migration

**Files:**
- Create: `apps/api/alembic/versions/<rev>_address_resolver.py` (filename generated by Alembic)

- [ ] **Step 1: Generate a blank revision**

Run: `cd apps/api && source .venv/bin/activate && alembic revision -m "address resolver"`
Expected: prints the path of a new file under `alembic/versions/`. Open it.

- [ ] **Step 2: Fill in upgrade/downgrade**

Replace the `upgrade()` and `downgrade()` bodies in the generated file with:

```python
def upgrade() -> None:
    op.create_table(
        "address_resolution",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("street", sa.String(), nullable=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("apartment_number_claimed", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("resolved_gush", sa.String(), nullable=True),
        sa.Column("resolved_chelka", sa.String(), nullable=True),
        sa.Column("resolved_tat_chelka", sa.String(), nullable=True),
        sa.Column("coordinates", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("resolution_time_ms", sa.Integer(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("cases", sa.Column("resolved_gush", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("resolved_chelka", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("resolved_tat_chelka", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("apartment_number_claimed", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("property_coordinates", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.alter_column("cases", "block", existing_type=sa.String(), nullable=True)
    op.alter_column("cases", "parcel", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.alter_column("cases", "parcel", existing_type=sa.String(), nullable=False)
    op.alter_column("cases", "block", existing_type=sa.String(), nullable=False)
    op.drop_column("cases", "property_coordinates")
    op.drop_column("cases", "apartment_number_claimed")
    op.drop_column("cases", "resolved_tat_chelka")
    op.drop_column("cases", "resolved_chelka")
    op.drop_column("cases", "resolved_gush")
    op.drop_table("address_resolution")
```

Ensure the imports at the top of the file include:

```python
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
```

(`down_revision` is pre-filled by Alembic to the previous head — leave it.)

- [ ] **Step 3: Apply the migration to the dev DB**

Run: `alembic upgrade head`
Expected: `INFO ... Running upgrade ... address resolver`, no error.

- [ ] **Step 4: Verify the schema**

Run: `python -c "from app.core.db import engine; from sqlalchemy import inspect; i=inspect(engine); print('address_resolution' in i.get_table_names()); print([c['name'] for c in i.get_columns('cases') if c['name'] in ('resolved_gush','property_coordinates')]); print([c for c in i.get_columns('cases') if c['name']=='block'][0]['nullable'])"`
Expected: `True`, then `['resolved_gush', 'property_coordinates']`, then `True`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/alembic/versions/
git commit -m "feat(api): migration for address_resolution table + Case fields"
```

---

## Task 7: Frontend types + API client

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/api.ts`

- [ ] **Step 1: Add types**

In `src/lib/types.ts`:

Change `CaseDetail`'s `block`/`parcel` to nullable and add resolved fields:

```typescript
export interface CaseDetail extends CaseListItem {
  block: string | null;
  parcel: string | null;
  sub_parcel: string | null;
  resolved_gush: string | null;
  resolved_chelka: string | null;
  resolved_tat_chelka: string | null;
  apartment_number_claimed: string | null;
  property_coordinates: Record<string, number> | null;
  deal_value_ils: number | null;
  counterparty_lawyer_name: string | null;
  counterparty_lawyer_phone: string | null;
  signing_scheduled_at: string | null;
  handover_scheduled_at: string | null;
  parties: Party[];
  activities: Activity[];
}
```

Make `CreateCaseInput`'s `block`/`parcel` optional:

```typescript
export interface CreateCaseInput {
  deal_type: DealType;
  block?: string | null;
  parcel?: string | null;
  sub_parcel?: string | null;
  property_address: string;
  property_city: string;
  counterparty_lawyer_name?: string | null;
  primary_client?: {
    role: "buyer";
    full_name: string;
    israeli_id: string;
    phone?: string | null;
    email?: string | null;
  };
}
```

Append the new interfaces:

```typescript
export type AddressResolutionStatus =
  | "auto_resolved"
  | "multi_candidate"
  | "manual_entry"
  | "failed";

export interface AddressResolution {
  id: string;
  case_id: string;
  city: string;
  street: string;
  number: string;
  apartment_number_claimed: string | null;
  status: AddressResolutionStatus;
  resolved_gush: string | null;
  resolved_chelka: string | null;
  resolved_tat_chelka: string | null;
  coordinates: Record<string, number> | null;
  method: string;
  resolution_time_ms: number;
  resolved_at: string;
}

export interface ManualResolutionInput {
  gush: string;
  chelka: string;
  tat_chelka?: string | null;
}
```

- [ ] **Step 2: Add API client methods**

In `src/lib/api.ts`, add the import:

```typescript
import type {
  AddressResolution,
  CaseDetail,
  CaseList,
  CreateCaseInput,
  ManualResolutionInput,
} from "./types";
```

Add to the `api` object (after `createCase`):

```typescript
  resolveAddress: (id: string) =>
    request<AddressResolution>(`/api/cases/${id}/resolve-address`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  getAddressResolution: async (id: string): Promise<AddressResolution | null> => {
    const res = await fetch(`${BASE_URL}/api/cases/${id}/address-resolution`, {
      headers: { "content-type": "application/json" },
    });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return (await res.json()) as AddressResolution;
  },
  manualResolution: (id: string, input: ManualResolutionInput) =>
    request<AddressResolution>(`/api/cases/${id}/address-resolution/manual`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),
```

- [ ] **Step 3: Type-check**

Run: `cd apps/web && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/lib/types.ts apps/web/src/lib/api.ts
git commit -m "feat(web): address-resolution types + API client methods"
```

---

## Task 8: Hebrew strings

**Files:**
- Modify: `apps/web/messages/he.json`

- [ ] **Step 1: Add the addressResolution block**

In `messages/he.json`, add a new top-level key after the `"case"` object (keep valid JSON — add a comma after the `case` block's closing brace):

```json
  "addressResolution": {
    "title": "פתרון כתובת",
    "resolveButton": "פתרון כתובת לגוש/חלקה",
    "resolving": "מאתר...",
    "notResolved": "טרם נפתר",
    "resolved": "גוש {gush} / חלקה {chelka}",
    "coordinates": "קואורדינטות",
    "failed": "פתרון אוטומטי נכשל — נא להזין ידנית",
    "tokenMissing": "טוקן GovMap לא הוגדר — נא להזין גוש/חלקה ידנית",
    "multiCandidate": "נמצאו מספר התאמות — נא לבחור או להזין ידנית",
    "manualTitle": "הזנה ידנית",
    "gush": "גוש",
    "chelka": "חלקה",
    "tatChelka": "תת חלקה",
    "save": "שמירה",
    "manualSaved": "גוש/חלקה נשמרו"
  }
```

- [ ] **Step 2: Validate JSON**

Run: `cd apps/web && node -e "JSON.parse(require('fs').readFileSync('messages/he.json','utf8')); console.log('valid json')"`
Expected: prints `valid json`

- [ ] **Step 3: Commit**

```bash
git add apps/web/messages/he.json
git commit -m "feat(web): Hebrew strings for address resolution"
```

---

## Task 9: Address Resolution card + Case Detail + New Case modal

**Files:**
- Create: `apps/web/src/components/address-resolution-card.tsx`
- Test: `apps/web/src/components/address-resolution-card.test.tsx`
- Modify: `apps/web/src/components/case-detail.tsx`
- Modify: `apps/web/src/lib/schemas.ts`

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/components/address-resolution-card.test.tsx`:

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import messages from "../../messages/he.json";
import { AddressResolutionCard } from "./address-resolution-card";

vi.mock("@/lib/api", () => ({
  api: {
    getAddressResolution: vi.fn().mockResolvedValue(null),
    resolveAddress: vi.fn(),
    manualResolution: vi.fn(),
  },
}));

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <NextIntlClientProvider locale="he" messages={messages}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

describe("AddressResolutionCard", () => {
  it("shows the not-resolved state and a resolve button when no resolution exists", async () => {
    wrap(<AddressResolutionCard caseId="abc" />);
    expect(await screen.findByText("טרם נפתר")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "פתרון כתובת לגוש/חלקה" }),
    ).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd apps/web && npx vitest run src/components/address-resolution-card.test.tsx`
Expected: FAIL — cannot resolve `./address-resolution-card`.

- [ ] **Step 3: Create the card component**

Create `apps/web/src/components/address-resolution-card.tsx`:

```tsx
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { Card } from "@/components/ui";
import { api } from "@/lib/api";

export function AddressResolutionCard({ caseId }: { caseId: string }) {
  const t = useTranslations("addressResolution");
  const queryClient = useQueryClient();
  const [gush, setGush] = useState("");
  const [chelka, setChelka] = useState("");
  const [tatChelka, setTatChelka] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["address-resolution", caseId],
    queryFn: () => api.getAddressResolution(caseId),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["address-resolution", caseId] });
    queryClient.invalidateQueries({ queryKey: ["case", caseId] });
  };

  const resolveMutation = useMutation({
    mutationFn: () => api.resolveAddress(caseId),
    onSuccess: invalidate,
  });

  const manualMutation = useMutation({
    mutationFn: () => api.manualResolution(caseId, { gush, chelka, tat_chelka: tatChelka || null }),
    onSuccess: invalidate,
  });

  const resolved = data && (data.status === "auto_resolved" || data.status === "manual_entry");
  const showManual = !resolved;

  return (
    <Card>
      <h3 className="mb-3 font-medium">{t("title")}</h3>

      {isLoading ? (
        <p className="text-sm text-ink/40">…</p>
      ) : resolved ? (
        <p className="bidi-isolate text-sm">
          {t("resolved", { gush: data!.resolved_gush ?? "", chelka: data!.resolved_chelka ?? "" })}
          {data!.resolved_tat_chelka ? ` / ${data!.resolved_tat_chelka}` : ""}
        </p>
      ) : (
        <p className="text-sm text-ink/50">{t("notResolved")}</p>
      )}

      {data?.status === "failed" && (
        <p className="mt-1 text-xs text-red-600">{t("failed")}</p>
      )}
      {data?.status === "multi_candidate" && (
        <p className="mt-1 text-xs text-gold">{t("multiCandidate")}</p>
      )}

      <button
        onClick={() => resolveMutation.mutate()}
        disabled={resolveMutation.isPending}
        className="mt-3 rounded-lg bg-burgundy px-4 py-2 text-sm font-medium text-white hover:bg-burgundy/90 disabled:opacity-50"
      >
        {resolveMutation.isPending ? t("resolving") : t("resolveButton")}
      </button>

      {showManual && (
        <div className="mt-4 border-t border-ink/10 pt-3">
          <h4 className="mb-2 text-sm font-medium">{t("manualTitle")}</h4>
          <div className="grid grid-cols-3 gap-2">
            <input
              aria-label={t("gush")}
              placeholder={t("gush")}
              value={gush}
              onChange={(e) => setGush(e.target.value)}
              className="rounded-lg border border-ink/15 px-2 py-1 text-sm outline-none focus:border-burgundy"
            />
            <input
              aria-label={t("chelka")}
              placeholder={t("chelka")}
              value={chelka}
              onChange={(e) => setChelka(e.target.value)}
              className="rounded-lg border border-ink/15 px-2 py-1 text-sm outline-none focus:border-burgundy"
            />
            <input
              aria-label={t("tatChelka")}
              placeholder={t("tatChelka")}
              value={tatChelka}
              onChange={(e) => setTatChelka(e.target.value)}
              className="rounded-lg border border-ink/15 px-2 py-1 text-sm outline-none focus:border-burgundy"
            />
          </div>
          <button
            onClick={() => manualMutation.mutate()}
            disabled={!gush || !chelka || manualMutation.isPending}
            className="mt-2 rounded-lg border border-ink/15 px-4 py-1.5 text-sm hover:border-burgundy disabled:opacity-50"
          >
            {t("save")}
          </button>
        </div>
      )}
    </Card>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd apps/web && npx vitest run src/components/address-resolution-card.test.tsx`
Expected: PASS (1 test).

- [ ] **Step 5: Wire the card into Case Detail**

In `src/components/case-detail.tsx`, add the import near the other component imports:

```tsx
import { AddressResolutionCard } from "@/components/address-resolution-card";
```

In the sidebar `<div className="space-y-4">`, add the card as the **first** child (before the red-flags `Card`):

```tsx
          <AddressResolutionCard caseId={caseId} />
```

- [ ] **Step 6: Make block/parcel optional in the New Case form schema**

In `src/lib/schemas.ts`, change:

```typescript
  block: z.string().optional(),
  parcel: z.string().optional(),
```

The modal already sends `block: values.block` / `parcel: values.parcel`; with the field optional these may be `undefined`, which the backend accepts. No modal change needed for correctness. (The inputs remain visible as optional fields.)

- [ ] **Step 7: Type-check + run the full frontend unit suite**

Run: `cd apps/web && npx tsc --noEmit && npx vitest run`
Expected: no type errors; all Vitest tests pass (existing + the new card test).

- [ ] **Step 8: Commit**

```bash
git add apps/web/src/components/address-resolution-card.tsx apps/web/src/components/address-resolution-card.test.tsx apps/web/src/components/case-detail.tsx apps/web/src/lib/schemas.ts
git commit -m "feat(web): address resolution card on Case Detail; optional block/parcel in new-case form"
```

---

## Task 10: Full verification, live hop-1 smoke, finish

**Files:** none (verification + optional manual check)

- [ ] **Step 1: Backend — full suite + lint**

Run: `cd apps/api && source .venv/bin/activate && pytest -v && ruff check .`
Expected: all tests pass; ruff clean.

- [ ] **Step 2: Frontend — lint, types, unit, build**

Run: `cd apps/web && npm run lint && npx tsc --noEmit && npx vitest run && npm run build`
Expected: lint clean, no type errors, tests pass, build compiles.

- [ ] **Step 3: Live end-to-end smoke (manual, optional)**

With Postgres up and the migration applied, start the API (`uvicorn app.main:app --reload`) and frontend (`npm run dev`). Create a case at `http://localhost:3000` with address `בר יהודה 33` / city `בת ים` and **no** block/parcel. Open it, click **"פתרון כתובת לגוש/חלקה"**. With no `GOVMAP_API_TOKEN` set, expect the `failed`/manual message; enter `7136` / `142` manually and confirm it persists and shows in deal-details. (When the firm's token is later set via `GOVMAP_API_TOKEN`, re-run to confirm auto-resolution and, if needed, adjust the hop-2 parser in `govmap.py` to the live response shape.)

- [ ] **Step 4: Final review against the spec**

Confirm acceptance criteria from the spec are met: case creatable without block/parcel; resolution attempt always writes an `AddressResolution` row + `Activity`; manual fallback works token-free; Hebrew renders RTL; both suites green.

- [ ] **Step 5: Finish the branch**

Use the `superpowers:finishing-a-development-branch` skill to decide merge/PR.

---

## Self-Review notes

- **Spec coverage:** service (Task 2) ↔ §1; model + Case fields + nullable block/parcel (Tasks 3, 6) ↔ §2; endpoints + activity (Task 5) ↔ §3; card + New Case (Task 9) ↔ §4; error/status handling (Tasks 2, 5, 9) ↔ §5/§status-table; tests (Tasks 2, 5, 9) ↔ §6; live hop-1 + token note (Task 10) ↔ Context/Acceptance.
- **Status set:** `auto_resolved` / `multi_candidate` / `manual_entry` / `failed`(+`reason`) used consistently across service, endpoints, types, and card.
- **Type consistency:** `AddressResolutionResult` fields (service) ↔ `AddressResolution` columns (model) ↔ `AddressResolutionOut` (schema) ↔ `AddressResolution` (TS) align. `resolve(city, street, number, *, transport)` signature is used identically in tests and the router (router omits `transport`, using the real client).
- **No placeholders:** hop-2 endpoint/shape is concrete and tested via mocks; the only deferred item is confirming the live hop-2 shape once a token exists (an explicit verification step, not a code gap) — token-absent behavior is fully defined.
