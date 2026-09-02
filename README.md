# MTAB Express

Inter-city parcel operations for Ethiopia: intake, scan checkpoints, linehaul manifests, cash and Chapa payments, waybills, and live customer tracking — in **English** and **Amharic**.

Branding is env-driven (`BRAND_NAME`, `TRACKING_PREFIX`, …). Change those variables to white-label the platform; do not hardcode a product name in app code.

| Surface | URL |
|---------|-----|
| Operator dashboard | [mtab-dashboard.vercel.app](https://mtab-dashboard.vercel.app) |
| Public tracking + Mini App | [mtab-public.vercel.app](https://mtab-public.vercel.app) |
| API | [api-production-7e857.up.railway.app](https://api-production-7e857.up.railway.app) · [OpenAPI `/docs`](https://api-production-7e857.up.railway.app/docs) |
| Telegram | [@mela_express_bot](https://t.me/mela_express_bot) (display name **MTAB Express**) |
| Source | [Mih-Nig-Afe/MTAB-express](https://github.com/Mih-Nig-Afe/MTAB-express) |

Demo staff login (seeded, change in production): phone `+251900000000` / password `admin123`.

---

## What it does

**Staff (dashboard)**  
Register parcels, print thermal waybills, scan at counters and airports, batch parcels onto manifests, collect cash, reconcile drawers, and watch network KPIs. Roles: admin, manager, operator, driver.

**Customers**  
Track by code on the web, pay pending fees with Chapa, confirm receipt, and use the same flows inside Telegram (bot + Mini App). Status changes notify the linked phone.

**Ops**  
Branch-scoped RBAC, OTP proof of delivery, air-leg / ETA, pickup aging, and bilingual UI (`EN` / `አማርኛ`).

---

## Architecture

```
                    ┌─────────────────┐     ┌──────────────────┐
  Staff browsers ──►│  Dashboard      │     │  Public portal   │◄── customers / Mini App
                    │  Next.js :3010  │     │  Next.js :3011   │
                    └────────┬────────┘     └────────┬─────────┘
                             │  /api                 │
                             ▼                       ▼
                    ┌─────────────────────────────────────────┐
                    │  FastAPI  (Railway / Docker :8001)       │
                    │  JWT auth · scan · manifests · Chapa     │
                    └───────┬──────────────┬──────────────────┘
                            │              │
                 ┌──────────▼──┐    ┌──────▼──────┐    ┌────────────┐
                 │ PostgreSQL  │    │    Redis    │    │ Telegram   │
                 └─────────────┘    │  Celery     │    │ bot worker │
                                    └─────────────┘    └────────────┘
```

| Piece | Stack |
|-------|--------|
| API, bot, workers | Python 3.12, FastAPI, SQLAlchemy, Alembic, Celery |
| Dashboard & public | Next.js 15, React 19, Tailwind, i18next |
| Data | PostgreSQL 16, Redis 7 |
| Payments | Chapa (card/mobile) + cash at counter |
| Hosting | API/bot/workers on **Railway**; frontends on **Vercel** |

---

## Repository layout

```
config/branding.ts              Shared brand helpers (imported as @brand)
mela-express-backend/           FastAPI, Telegram bot, Celery
mela-express-dashboard/         Staff console
mela-express-public/            Tracking site + Telegram Mini App
docker-compose.dev.yml          Local stack (hot reload)
docs/                           Deployment, Railway, Vercel
```

Deeper tree: [`FOLDER_STRUCTURE.md`](FOLDER_STRUCTURE.md).

---

## Branding

Set once; APIs and UIs read the same values. Frontends can also `GET /public/brand` if `NEXT_PUBLIC_*` is omitted.

| Variable | Role |
|----------|------|
| `BRAND_NAME` / `NEXT_PUBLIC_BRAND_NAME` | Display name (e.g. MTAB Express) |
| `BRAND_SHORT` / `NEXT_PUBLIC_BRAND_SHORT` | Short label |
| `TRACKING_PREFIX` | Tracking codes (`MTAB-HW-000482`) |
| `SMS_SENDER_ID` | SMS sender |
| `TELEGRAM_BOT_USERNAME` | `t.me` links and Chapa return URLs (no `@`) |
| `PUBLIC_PORTAL_URL` | Customer site (QR on stickers, Mini App) |
| `APP_BASE_URL` | Public API origin |

Full list: [`.env.example`](.env.example).

---

## Local development

**Requirements:** Docker Desktop, Node 24 (for running Next outside Compose), Python 3.12 if you work on the API without Docker.

```bash
git clone https://github.com/Mih-Nig-Afe/MTAB-express.git
cd MTAB-express
cp .env.example .env
# At minimum: JWT_SECRET_KEY, TELEGRAM_BOT_TOKEN (bot), CHAPA_* (payments)

docker compose -f docker-compose.dev.yml up --build
```

| Service | Host port |
|---------|-----------|
| API | [http://localhost:8001](http://localhost:8001) · docs at `/docs` |
| Dashboard | [http://localhost:3010](http://localhost:3010) |
| Public portal | [http://localhost:3011](http://localhost:3011) |
| Postgres | `localhost:5433` |
| Redis | `localhost:6381` |

API start script seeds an admin if missing. Optional sample parcels: `SEED_SAMPLE=1` on the API container.

Without Compose (API only):

```bash
cd mela-express-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# DATABASE_URL pointing at Postgres 16
alembic upgrade head
python scripts/seed_branches.py
python scripts/seed_admin.py
uvicorn app.main:app --reload --port 8000
```

Dashboard / public:

```bash
cd mela-express-dashboard   # or mela-express-public
npm ci
echo 'NEXT_PUBLIC_API_URL=http://localhost:8001/api' >> .env.local
npm run dev
```

---

## Languages

Staff and customers pick **EN** or **አማርኛ**. Preference is stored in the browser (`mela_lang` / `mela_public_lang`). Locale JSON lives under each app’s `src/locales/{en,am}/`. Keep English and Amharic keys in parity when you add copy.

---

## Deployment

| Environment | Branch | What ships |
|-------------|--------|------------|
| Staging | `staging` | Vercel preview/staging apps |
| Production | `production` | Live dashboard + public |
| Integration | `develop` | Feature PRs |

```
feature/*  →  develop  →  staging  →  production
```

- **Frontends:** Vercel projects `mtab-dashboard` (root `mela-express-dashboard`) and `mtab-public` (root `mela-express-public`). Required: `NEXT_PUBLIC_API_URL` (include `/api`). Optional: `NEXT_PUBLIC_BRAND_*`.
- **Backend:** Railway services `api`, `bot`, `worker`, `beat` + Postgres + Redis. See [`docs/RAILWAY.md`](docs/RAILWAY.md).
- **CORS:** `CORS_ORIGINS` on the API must include both Vercel origins.

More: [`docs/deployment.md`](docs/deployment.md), [`docs/VERCEL.md`](docs/VERCEL.md).

Health check: `GET /health`.

---

## Tests & CI

```bash
cd mela-express-backend
pip install -r requirements-dev.txt
pytest
```

GitHub Actions (`.github/workflows/ci.yml`) runs backend tests on PRs. Vercel workflows deploy on push to `staging` / `production`.

---

## Security notes

- Never commit `.env`, tokens, or `credentials.json`.
- Rotate the seeded `admin123` password before real traffic.
- JWT, Chapa webhook secret, and Telegram token are production secrets — set them only in Railway/Vercel.
- Public tracking is rate-limited; staff APIs require JWT and role checks.

---

## Further reading

- [`docs/RAILWAY.md`](docs/RAILWAY.md) — API, bot, Celery on Railway  
- [`docs/VERCEL.md`](docs/VERCEL.md) — frontend projects and env  
- [`docs/deployment.md`](docs/deployment.md) — branch model  
- [`FOLDER_STRUCTURE.md`](FOLDER_STRUCTURE.md) — file map  
