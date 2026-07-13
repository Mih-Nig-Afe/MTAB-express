# Mela Express backend — starter scaffold

Matches the architecture doc: FastAPI + PostgreSQL + Telegram bot + Chapa.

## What's here
- `app/models.py` — core schema: branches, staff, customers, parcels, status history, payments
- `app/routers/parcels.py` — intake, tracking lookup, status transitions (+ notification trigger)
- `app/routers/payments.py` — cash collection, Chapa checkout initiation, Chapa webhook handler
- `app/services/chapa.py` — checkout + verification + webhook signature check
- `app/services/notifications.py` — Telegram message sending, one template per status
- `app/bot/bot.py` — customer-facing Telegram bot (thin, calls the API, no business logic)

## What's intentionally left as a TODO
- Auth on staff-facing endpoints (currently `created_by`/`changed_by` are passed as plain
  query params — replace with a real auth dependency before this touches real branches)
- `POST /api/customers/link` referenced by the bot but not yet implemented
- Alembic migration setup (`alembic init` + first revision from `app/models.py`)
- Background task queue for notification sends (currently awaited inline — fine for a pilot,
  not fine once Telegram rate limits or slow requests start blocking parcel creation)
- Rate limiting on `/api/parcels/track/{code}` before this is public-facing

## Running locally
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in real values
3. Spin up PostgreSQL (`docker run -e POSTGRES_USER=mela -e POSTGRES_PASSWORD=mela -e POSTGRES_DB=mela_express -p 5432:5432 postgres:16`)
4. `alembic upgrade head` (once migrations are set up) or `Base.metadata.create_all` for a quick local start
5. `uvicorn app.main:app --reload`
6. In a separate process: `python -m app.bot.bot`
