# Foundation Slice — Design Spec

**Project:** Halevi-Luttati Pre-Contract Real Estate Due Diligence Platform
**Slice:** Foundation (Sprint 0)
**Date:** 2026-06-03
**Status:** Approved — ready for implementation planning
**Source PRD:** [PRD-Phase1-Pre-Signing.md](../../PRD-Phase1-Pre-Signing.md)

---

## Context & Decomposition

The PRD describes a full multi-subsystem platform (10 step modules, scrapers, AI,
document generation, auth, calendar). It is too large for a single implementation
plan, so it is decomposed slice-by-slice, following the PRD's own roadmap (§12) and
build-order rationale (Appendix B). Each slice gets its own spec → plan → build cycle:

| Order | Slice | Notes |
|------|-------|-------|
| **0** | **Foundation** (this spec) | Scaffolding, RTL, base models, dashboard + case CRUD |
| 1 | Step 5 — Identity & risk check (5 scrapers) | Highest ROI, zero-auth, de-risks scraping |
| 2 | Step 2 — Client intake form | Prerequisite for steps 3/6/7/9 |
| 3 | Step 3 — Document generation + tax calculator | |
| 4 | Steps 6+7 — Taboo + condo (digital signature) | Hardest integration |
| 5 | Step 8 — AI contract review | Highest-value AI feature |
| 6 | Steps 4, 9, 10 — Municipal, addenda, signing + polish | |

## Confirmed Decisions

- **Build target:** Solo developer.
- **Architecture:** Approach A — polyglot monorepo (`apps/web` Next.js + `apps/api` FastAPI).
- **Dev environment:** Local-first with Docker (`docker-compose` for Postgres + Redis).
  Cloud deploy (Vercel / Fly.io / Neon / R2) deferred to a later slice.
- **Auth:** Deferred entirely for this stage. No magic link / 2FA. Seed dev users so cases
  have a `primary_lawyer_id`; a `TODO: auth` dependency stub makes the later swap one line.

## Non-Negotiable Constraint (PRD §0)

The product is **Hebrew-first, RTL**. Foundation establishes this from day one:
HTML `dir="rtl" lang="he"`, all UI strings in `messages/he.json` (next-intl), Hebrew
fonts with Hebrew subset, Tailwind logical properties, RTL-validated shadcn/ui.
Hebrew copy is sourced from the approved demo (`docs/halevi_luttati_demo.html`) —
never machine-translated.

---

## 1. Repo Structure & Tooling

```
Halevy-Lotati/
├── apps/
│   ├── web/                  # Next.js 14 (App Router), TypeScript, Tailwind
│   │   ├── messages/he.json  # ALL Hebrew UI strings (next-intl)
│   │   ├── src/app/          # dir="rtl" lang="he" at root
│   │   ├── src/components/   # shadcn/ui (RTL-validated), feature components
│   │   ├── src/lib/          # api client (TanStack Query), zod schemas
│   │   └── tests/            # Vitest + Playwright
│   └── api/                  # FastAPI, Python 3.11+
│       ├── app/models/       # SQLAlchemy models
│       ├── app/schemas/      # Pydantic (mirror frontend Zod)
│       ├── app/routers/      # cases, parties, activity, health
│       ├── app/core/         # config, db session, seed
│       ├── alembic/          # migrations
│       └── tests/            # pytest
├── docker-compose.yml        # postgres:15 + redis:7 (redis idle until Step 5)
├── docs/                     # PRD + specs
└── .github/workflows/ci.yml  # lint + test both apps
```

Monorepo with two independently-deployable apps. Redis is present in compose so it is
ready for Celery later, but **Foundation has no background jobs**.

## 2. Data Models (Foundation subset)

Built now (per PRD §8). Remaining tables arrive with their slices.

- **User** — minimal; no auth. Seed 2 dev users (Ron, Lev) so cases have a
  `primary_lawyer_id`.
- **Case** — full model per PRD, **including all per-step JSONB columns**
  (`intake_data`, `tax_calculation`, `municipal_check`, `identity_checks`,
  `taboo_data`, `condo_data`, `contract_review`, `addenda_checklist`), created
  **nullable** so later slices fill them in without a migration churn. Computed
  `red_flags_count` and `completion_percentage`.
- **Party** — buyer / seller / guarantor / spouse on a case. `israeli_id` column present;
  application-layer encryption hook deferred to the security/auth slice.
- **Activity** — audit log. Foundation writes `case_opened` and `note_added`.
- **Document** — table created; upload/download endpoints deferred (no R2 storage yet).

Enums per PRD: `CaseStatus`, `ActivityType`, `DocumentType`. One Alembic migration
covers all Foundation tables.

**Decision (confirmed):** keep all step-JSONB columns in the Case model now rather than
adding them per-slice — avoids repeated migrations and keeps the central entity stable.

## 3. Backend API (FastAPI)

Only the non-step endpoints from PRD §9:

```
GET    /api/health
GET    /api/cases?status=&page=
POST   /api/cases                      → creates case, writes case_opened activity
GET    /api/cases/:id                  → CaseDetail (parties, activity)
PATCH  /api/cases/:id
DELETE /api/cases/:id
GET    /api/cases/:id/activity
GET    /api/cases/:id/parties
POST   /api/cases/:id/parties
PATCH  /api/cases/:id/parties/:pid
```

- No auth middleware yet — a `TODO: auth` FastAPI dependency stub so it is a one-line swap.
- Case number auto-generated, format `YYYY-NNNN`.
- Pydantic schemas mirror the frontend Zod schemas.
- Validation errors return 422 with field-level detail (PRD §9 conventions).

## 4. Frontend (Next.js, Hebrew/RTL)

PRD §0 applied from day one:

- `<html dir="rtl" lang="he">`; **next-intl**, all strings in `messages/he.json` seeded
  from the approved demo copy.
- Fonts: **Frank Ruhl Libre** (display) + **Heebo** (body), Hebrew subset. Palette per
  §10: ink `#1a1d23`, paper `#fafaf7`, burgundy `#8b1538`, gold `#a67c2e`.
- Tailwind with **logical properties** (`ms-/me-/ps-/pe-`). shadcn/ui installed and
  RTL-checked.
- Data layer: TanStack Query + typed API client; React Hook Form + Zod for forms.

**Screens:**
- **Dashboard** (§10.1) — 4 KPI cards (active cases, checks this week, needs attention,
  signings this week), active-cases table (case number, address, client, status badge,
  X/10 progress bar, next action), "+ New Case" button.
- **New Case modal** (§10.2) — deal type, block/parcel/sub-parcel, address, client
  name + Israeli ID + phone + email, counterparty lawyer → `POST /api/cases`.
- **Case Detail shell** (§10.3) — header (case ID, address, client, counterparty, key
  dates, phase pill), clickable 10-segment timeline, 10 collapsible step cards rendered
  as **placeholders**, right sidebar (red flags / deal summary / activity feed).

**Decision (confirmed):** the full Case Detail shell is included in Foundation so each
later slice only fills in its own step card, rather than restructuring the page.

## 5. Testing & CI

TDD throughout (superpowers discipline — tests before implementation).

- **Backend:** pytest against an ephemeral Postgres; API tests for every CRUD path,
  case-number generation, and activity logging.
- **Frontend:** Vitest + Testing Library for components; one Playwright e2e that loads
  the dashboard and asserts RTL rendering, run on Chromium + WebKit (covers the
  Safari / iOS concern from §0).
- **CI:** GitHub Actions runs ruff + pytest (api) and lint + vitest + playwright (web)
  on push.

## Explicitly Out of Scope (Foundation)

Auth / 2FA, background jobs / Celery, any of the 10 step *logic*, document upload /
storage (R2), email / WhatsApp, cloud deployment. Each is a later slice.

## Acceptance Criteria

- `docker-compose up` starts Postgres + Redis; both apps run locally.
- A dev user can open the dashboard (Hebrew UI), create a case via the modal (Hebrew
  form), and see it in the dashboard table.
- Case detail page renders with the 10-step timeline and placeholder step cards.
- All Hebrew text renders correctly RTL on Chromium and WebKit.
- CI green: both test suites pass on push.
