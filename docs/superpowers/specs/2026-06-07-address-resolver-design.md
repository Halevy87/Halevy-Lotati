# Address Resolver (Step 5.5) — Design Spec

**Project:** Halevi-Luttati Pre-Contract Real Estate Due Diligence Platform
**Slice:** Step 5.5 — Address Resolver (first slice of PRD v1.1)
**Date:** 2026-06-07
**Status:** Approved — pending implementation plan
**Source:** [PRD-Phase1-Pre-Signing.md](../../PRD-Phase1-Pre-Signing.md) + [PRD_DELTA_v1.0_to_v1.1.md](../../PRD_DELTA_v1.0_to_v1.1.md) (CHANGES 2, 6, 7)
**Builds on:** [2026-06-03-foundation-design.md](2026-06-03-foundation-design.md)

> **Implementation update (2026-06-07):** During the build we discovered hop-2 works
> **token-free** via GovMap's **public GeoServer WMS** (`govmap:layer_parcel_all` at
> `…/api/geoserver/ows/public/`) — a `GetFeatureInfo` at the address point plus
> point-in-polygon selection returns the real gush/chelka (the same layer GovMap's own
> address→gush/chelka tool uses). This **replaces** the token-gated `getSearchResultData`
> hypothesis below. Verified live: `בר יהודה 33, בת ים → גוש 7137 / חלקה 157`. The
> `GOVMAP_API_TOKEN` setting is now **unused** (kept only as a hook if we ever switch to the
> official token-bound API); the manual-entry fallback remains for addresses GovMap can't
> resolve. Sections 1 and 5 below describe the original token approach for historical context.

---

## Context

The v1.1 delta was driven by live validation on a real Bat Yam property. Discovery #1: the
client gives the lawyer only a street **address** (`בר יהודה 33, בת ים, דירה 13`), never the
block/parcel (gush/chelka) that the Land Registry (Taboo, Step 6) requires. A new **Step 5.5
(Address Resolver)** converts address → gush/chelka before Step 6 can run.

This is the **first delta slice** because it is the only one that is free, read-only, and
fully buildable/testable today (proven live — see "Live findings" below). Step 6 (Taboo) is
blocked on real payment + live-portal reverse-engineering; hosting (§0.5) is a deploy task;
Identity Check (Step 5) is a separate module. Each gets its own spec → plan → build cycle.

### Live findings (verified 2026-06-07, from an Israeli IP)

- The reference `docs/Code Examples/address_resolver.py` is **stale**: it loads the old global
  `govmap.api.js` and calls `govmap.searchAndLocate(...lotParcelToAddress)`. GovMap has since
  rewritten that into an ~833 KB app bundle; the old global API no longer exists and the call
  times out. The reference is a design sketch only — not used here beyond intent.
- GovMap's **current** API works and is reachable:
  - **Hop 1 (address → coordinates):** `POST https://www.govmap.gov.il/api/search-service/autocomplete`
    with `{"searchText": "בר יהודה 33 בת ים", "language": "he"}` returns the matched address
    plus a Web-Mercator (EPSG:3857) point. **Works token-free.**
  - **Hop 2 (coordinates → gush/chelka):** the spatial/identify endpoints return
    `{"error":"access denied"}` without authentication. This is the **free GovMap developer
    token** gate (`api.govmap.gov.il`), matching delta Open Question #9 (Ron registers it).
- GovMap's consumer site authenticates via anonymous **session cookies** (`__anon_id`,
  `users-management/me`/`refresh`), distinct from the official token-based developer API.

### Token decision

The free token registration creates an account tied to the **firm's identity** and accepts
GovMap's terms; that belongs to Ron/the firm (delta Open Question #9), not the developer. So:

- We build the resolver **token-ready**: the token is read from a `GOVMAP_API_TOKEN`
  environment variable (unset by default).
- A **manual gush/chelka entry fallback** is always available, so the feature is usable from
  day one even with no token.
- Auto-resolution (hop 2) switches on the moment a token is configured. The whole slice is
  built and tested now via a mockable GovMap client; live hop-2 verification waits on the token.

---

## Confirmed Decisions

- **Scope:** Step 5.5 only, fully wired into `apps/api` + `apps/web`. Identity Check, Taboo,
  payment, and hosting are out of scope (separate slices).
- **Execution model:** **Synchronous** endpoint — the client waits for the result (resolution
  target < 15 s). No Celery/Redis/background jobs introduced for this slice. (The endpoint
  handler is `async def` using `httpx.AsyncClient`; "synchronous" means no job queue / the
  caller gets the result in the response.)
- **Mechanism:** GovMap's current API over plain `httpx` REST (no browser in the API process).
  Hop 1 is token-free (proven); hop 2 uses `GOVMAP_API_TOKEN`. A short spike at implementation
  start pins the exact hop-2 endpoint with a real token; Playwright is a fallback only if REST
  proves insufficient.
- **Trigger:** Manual (a button on Case Detail). Auto-trigger on intake completion is deferred
  — the intake step (Step 2) does not exist yet.

---

## 1. Resolution Service — `app/services/govmap.py`

A single, mockable unit with one public coroutine:

```python
async def resolve(city: str, street: str, number: str) -> AddressResolutionResult
```

`AddressResolutionResult` (plain dataclass / Pydantic model) carries:
`status`, `reason` (set when `failed`), `gush`, `chelka`, `coordinates` (`{x, y}` EPSG:3857),
`candidates` (for multi-candidate), `method` (`"rest"` / `"manual"`), `raw_response`,
`resolution_time_ms`, `error`.

Internal flow:
1. **Hop 1** — `httpx` POST to the autocomplete endpoint; parse the best address match → point.
   Token-free.
2. **Hop 2** — `httpx` call to the official parcel/identify endpoint with `GOVMAP_API_TOKEN`,
   passing the point → gush/chelka. If `GOVMAP_API_TOKEN` is unset, **short-circuit** to
   `failed` with `reason="token_not_configured"` (do not call hop 2).
3. Validate resolved gush/chelka are numeric and in a plausible range.

All network I/O goes through one thin HTTP layer so tests mock it. No GovMap call is made in
unit tests.

**Status values (canonical — the delta uses these inconsistently; this set is authoritative):**

| Status | Meaning |
|--------|---------|
| `auto_resolved` | GovMap returned a single gush/chelka. |
| `multi_candidate` | GovMap returned several; lawyer picks one (or enters manually). |
| `manual_entry` | Lawyer entered gush/chelka by hand (result of the PATCH endpoint). |
| `failed` | Resolution did not produce a result. `reason` ∈ {`token_not_configured`, `govmap_error`, `not_found`, `invalid_result`}. |

The frontend offers manual entry whenever the status is `failed` or `multi_candidate`, or
before any attempt has been made.

## 2. Data Model

### New table `AddressResolution` (delta CHANGE 6)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| case_id | UUID FK → cases | |
| city / street / number | str | inputs actually used |
| apartment_number_claimed | str? | client's claim, e.g. "13" |
| status | str | one of the four status values |
| resolved_gush / resolved_chelka | str? | |
| resolved_tat_chelka | str? | stays null until Step 6 |
| coordinates | JSONB? | `{x, y}` in EPSG:3857 |
| method | str | `rest` / `manual` |
| raw_response | JSONB? | full GovMap payload, for debugging |
| resolution_time_ms | int | |
| resolved_at | timestamptz | server default now |
| resolved_by_user_id | UUID? FK → users | null if automatic |

One row **per attempt** (audit + retry analysis).

### `Case` additions (delta CHANGE 6)

`resolved_gush`, `resolved_chelka`, `resolved_tat_chelka`, `apartment_number_claimed` (str?),
`property_coordinates` (JSONB?).

### `Case` change — block/parcel become nullable

Foundation made `block`/`parcel` `nullable=False` and required in `CaseCreate`. The delta's
premise (address-first) contradicts this. Change: `Case.block` and `Case.parcel` → **nullable**;
`CaseCreate.block`/`parcel` → **optional**. On successful resolution, populate `resolved_*` and
**mirror into `block`/`parcel` only when they are empty**, so existing reads (dashboard,
deal-details card) keep working unchanged.

### Migration

One Alembic migration: create `address_resolution`, add the 5 `Case` columns, alter
`block`/`parcel` to nullable.

## 3. API (delta CHANGE 7)

All under the existing `/api/cases` router; auth uses the current stub.

| Method | Path | Behavior |
|--------|------|----------|
| POST | `/api/cases/{id}/resolve-address` | Body optional `{street?, number?, apartment_number_claimed?}`; missing street/number are parsed from `case.property_address`, city from `case.property_city`. Runs the resolver synchronously, writes an `AddressResolution` row + an `Activity`, updates the `Case`, returns the row. **Returns 200 even when `status=failed`/`manual_entry_required`** — failure is an expected outcome, not a server error. 404 if the case is missing. |
| GET | `/api/cases/{id}/address-resolution` | Latest `AddressResolution` for the case; 404 if none yet. |
| PATCH | `/api/cases/{id}/address-resolution/manual` | Body `{gush, chelka, tat_chelka?}`. Lawyer manual entry → creates a row with `method=manual`, `status=manual_entry`; updates `Case`; writes `Activity`. |

New Pydantic schemas: `ResolveAddressRequest`, `ManualResolutionRequest`, `AddressResolutionOut`.

### Activity logging

Resolution writes an `Activity` with a Hebrew description (e.g. `"כתובת נפתרה לגוש/חלקה"` on
success, `"פתרון כתובת נכשל"` on failure, `"גוש/חלקה הוזנו ידנית"` on manual). Reuses existing
`ActivityType` values (`scraping_completed` / `scraping_failed` / `note_added`).

## 4. Frontend (`apps/web`)

### Case Detail — new "Address Resolution" sidebar card

A card (`address-resolution-card.tsx`) in the right sidebar of Case Detail, above deal-details:
- Shows current resolved גוש/חלקה (or `לא נפתר` / "not resolved").
- **"פתרון כתובת" button** → `POST /resolve-address` (TanStack Query mutation), shows a spinner
  while running.
- On `auto_resolved`: show gush/chelka + coordinates/confidence.
- On `failed` / `manual_entry_required` / `multi_candidate`: show the message and an inline
  **manual-entry form** (גוש / חלקה / תת-חלקה inputs) → `PATCH .../manual`. For multi-candidate,
  list the candidates.
- After success, invalidate the case query so deal-details reflects the resolved block/parcel.

All Hebrew strings added to `messages/he.json` under an `addressResolution` key. RTL via the
existing logical-property conventions.

### New Case modal

`block` / `parcel` inputs become **optional** (address-first creation). No other change.

## 5. Error Handling

| Situation | Behavior |
|-----------|----------|
| GovMap timeout / network error | Save `failed` row (`reason=govmap_error`); endpoint 200; card shows message + manual entry. |
| `GOVMAP_API_TOKEN` unset | Resolver short-circuits hop 2 → `failed` (`reason=token_not_configured`) with a clear "token not configured" message. Manual entry works. **This is the default state pre-token.** |
| GovMap returns no match | `failed` (`reason=not_found`). |
| Multiple candidates | `multi_candidate`; candidates listed; lawyer picks/enters. |
| Resolved gush/chelka invalid (non-numeric / implausible) | `failed` (`reason=invalid_result`). |

No path raises a 5xx for an expected resolution outcome.

## 6. Testing (TDD)

- **Backend unit** — `resolve()` with a **mocked GovMap HTTP layer**: success, multi-candidate,
  GovMap-error→failed, token-unset→manual_entry_required, invalid-gush→failed. No live calls.
- **Backend API** — ephemeral Postgres: POST (success via mocked service, failure), GET
  (present / 404), PATCH manual; assert `AddressResolution` rows, `Case` field updates,
  `Activity` entries, and block/parcel mirroring.
- **Migration** — applies cleanly on a fresh DB; `block`/`parcel` nullable verified.
- **Live integration (opt-in, skipped in CI)** — hits real GovMap for hop 1 (address →
  coordinates), proving the live path token-free. Hop-2 live assertion runs only if
  `GOVMAP_API_TOKEN` is set.
- **Frontend (Vitest)** — the resolution card across states: unresolved / resolving / resolved /
  failed / manual-entry / multi-candidate.

## Out of Scope (this slice)

Taboo extract fetch (Step 6); tat-chelka discovery (stays null until Step 6); background jobs /
Celery; auto-trigger on intake completion (Step 2 not built); push notifications / payment;
Kamatera / production deploy (§0.5); Playwright (fallback only, not built unless REST is shown
insufficient during the hop-2 spike); registering the GovMap token (Ron's task).

## Acceptance Criteria

- With no token: lawyer opens a case, clicks "פתרון כתובת", sees a clear
  `failed (token_not_configured)` message, enters gush/chelka manually, and it persists on the
  case and shows in deal-details. All Hebrew renders RTL.
- With `GOVMAP_API_TOKEN` set (or in the opt-in live test): entering the Bat Yam address
  resolves to a real gush/chelka within 15 s and persists.
- A case can be created with **no** block/parcel (address only).
- Each resolution attempt creates an `AddressResolution` row and an `Activity`; failures are
  recorded, never silently dropped.
- No real client PII used (Foundation PII rule still applies — synthetic IDs only, local dev).
- Both test suites green in CI (live GovMap test skipped there).
