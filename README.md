# Halevi-Luttati — Pre-Contract Real Estate Due Diligence Platform

Hebrew-first (RTL) platform for an Israeli law firm. See [docs/](docs/) for the PRD and
design specs. This repo currently implements the **Foundation** slice
([spec](docs/superpowers/specs/2026-06-03-foundation-design.md)).

> ⚠️ **Foundation is local-dev only.** It has no auth and stores Israeli IDs in
> plaintext. Use **synthetic/fake IDs only** — never real client PII. Real PII handling
> is blocked until the security/auth slice.

## Structure

```
apps/web   # Next.js 14 frontend (Hebrew/RTL)
apps/api   # FastAPI backend
docs/      # PRD + design specs
```

## Quick start

```bash
# 1. Start Postgres + Redis (Postgres is exposed on host port 5544)
docker compose up -d

# 2. Backend
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
python -m app.core.seed          # seed dev users (fake)
uvicorn app.main:app --reload    # http://localhost:8000  (docs at /docs)

# 3. Frontend (separate terminal)
cd apps/web
npm install
npm run dev                      # http://localhost:3000
```

## Tests

```bash
cd apps/api && pytest                 # backend
cd apps/web && npm test               # frontend unit (Vitest)
cd apps/web && npm run test:e2e       # Playwright RTL matrix
```
