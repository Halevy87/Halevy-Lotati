# Foundation Slice — Implementation Status

**Status:** ✅ Implemented and verified locally
**Date:** 2026-06-03
**Spec:** [superpowers/specs/2026-06-03-foundation-design.md](superpowers/specs/2026-06-03-foundation-design.md)

The Foundation (Sprint 0) slice of the [PRD](PRD-Phase1-Pre-Signing.md) is built. It is
the scaffold every later slice (Steps 1–10) sits on.

> ⚠️ **Foundation is local-dev only.** No auth. Israeli IDs are stored in plaintext —
> use **synthetic/fake IDs only**, never real client PII. Real PII handling is blocked
> until the security/auth slice (encryption + key management).

## What was built

### Backend — `apps/api` (FastAPI + SQLAlchemy + Alembic)
- **Models:** `User`, `Case` (all per-step JSONB columns, nullable), `Party`, `Activity`,
  `Document`, plus enums (`CaseStatus`, `DealType`, `PartyRole`, `ActivityType`, …).
- **Endpoints:**
  - `GET /api/health`
  - `GET/POST /api/cases`, `GET/PATCH/DELETE /api/cases/{id}`
  - `GET/POST /api/cases/{id}/parties`, `PATCH /api/cases/{id}/parties/{pid}`
  - `GET /api/cases/{id}/activity`
- Auto-generated case numbers (`YYYY-NNNN`), `case_opened` activity logging.
- `app/core/auth.py` — auth **stub** (returns seeded dev user); one-line swap when the
  real magic-link + 2FA slice lands.
- Alembic initial migration; `app/core/seed.py` seeds 2 fake dev users.

### Frontend — `apps/web` (Next.js 14 App Router, Hebrew-first RTL)
- `<html dir="rtl" lang="he">`, **next-intl** with all strings in `messages/he.json`
  (Hebrew-only, no locale routing).
- Fonts: **Frank Ruhl Libre** (display) + **Heebo** (body), Hebrew subset. Palette per
  PRD §10 (ink/paper/burgundy/gold). Tailwind logical properties.
- **Screens:** Dashboard (4 KPI cards + active-cases table), New Case modal
  (React Hook Form + Zod), Case Detail shell (10-segment timeline + 10 placeholder step
  cards + sidebar: red flags / deal details / activity).
- Data layer: TanStack Query + typed API client (`src/lib/api.ts`).

### Infra
- `docker-compose.yml` — Postgres (host port **5544**, to avoid a native Postgres on
  5432) + Redis (idle until Step 5).
- `.github/workflows/ci.yml` — CI for both apps (ruff + pytest; lint + vitest + build +
  Playwright).

## Verification (commands actually run)

| Check | Result |
|-------|--------|
| Backend `pytest` | **10 passed** |
| Live API smoke (health / create / list) | 200 / 201 / 200, Hebrew preserved |
| Alembic migrate + seed | 6 tables, 2 dev users |
| `ruff check` | No issues |
| Frontend Vitest | **4 passed** |
| `next build` | Compiled + type-checked, 4 routes |
| Playwright RTL e2e | **PASS (4)** — Chrome, Safari, Mobile Safari iOS, Android Chrome |

## Still pending
- **Ron native-Hebrew review gate** (per spec §0) — a human sign-off on the Hebrew copy
  before screens are considered shippable.

## Run it locally

```bash
docker compose up -d                      # Postgres (5544) + Redis

cd apps/api && python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" && alembic upgrade head && python -m app.core.seed
uvicorn app.main:app --reload             # http://localhost:8000  (docs at /docs)

cd apps/web && npm install && npm run dev  # http://localhost:3000
```

## Repository & push status

All Foundation work is committed locally on `master`. As of this session the branch is
ahead of `origin/master` and **not yet pushed**, blocked by two independent issues:

1. **Local deny rule** — `~/.claude/settings.json` contains
   `"deny": ["Bash(git push)", "Bash(git push:*)"]`, which prevents the agent from
   running `git push`. (Resolve by removing the rule, or push manually.)
2. **GitHub access** — the active GitHub identity (`Pipl-Barr`, forced by the
   `GITHUB_TOKEN` env var) lacks write access to `Halevy87/Halevy-Lotati` and gets
   `403 Forbidden`. Resolve by adding `Pipl-Barr` as a collaborator, switching to an
   account with write access, or forking + PR.

To push manually once access is sorted:

```bash
git push origin master
```

## Next slice
**Step 5 — Identity & risk check** (5 government-site scrapers). Highest ROI, zero-auth,
de-risks the scraping infrastructure (PRD Appendix B).
