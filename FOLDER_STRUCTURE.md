# Mela Express — Production Folder Structure

> **Note on `src/` vs `app/`**
> The backend uses `app/` as its Python package root — this is the standard FastAPI/Python convention (not `src/`). The two Next.js projects (`mela-express-dashboard/` and `mela-express-public/`) both use `src/` as their TypeScript source root, which is the standard Next.js App Router convention.

```
mela-express/                             # Repo root
│
├── .github/
│   └── workflows/
│       ├── ci.yml                        # Run tests + lint on every PR
│       └── deploy.yml                    # Deploy to VPS on push to main
│
├── .gitignore                            # Root gitignore (Python, Node, env, macOS, Docker)
│
├── docker/
│   ├── nginx/
│   │   ├── nginx.conf                    # Reverse proxy config
│   │   └── sites-available/
│   │       └── mela-express.conf         # Server block: API + dashboard + Certbot
│   └── postgres/
│       └── init.sql                      # Enum type definitions (run before first migration)
│
├── docker-compose.yml                    # Production: api, bot, worker, beat, db, redis, nginx
├── docker-compose.dev.yml                # Dev overrides: hot reload, no Nginx
├── .env.example                          # Template — copy to .env, never commit .env
│
│
├── mela-express-backend/                 # Python backend (FastAPI)
│   ├── .gitignore                        # Backend-scoped: venv, __pycache__, .coverage
│   ├── Dockerfile
│   ├── requirements.txt                  # Production dependencies (pinned)
│   ├── requirements-dev.txt              # pytest, hypothesis, httpx, ruff, mypy
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/                     # Migration scripts (never edit manually)
│   │       ├── 0001_initial_schema.py
│   │       └── 0002_add_proof_of_delivery.py
│   │
│   └── app/                              # Python package root (FastAPI convention = app/, not src/)
│       ├── __init__.py
│       ├── main.py                       # FastAPI app factory, router registration
│       ├── config.py                     # Pydantic Settings — all env vars here
│       ├── database.py                   # Async engine, session factory, Base
│       ├── models.py                     # SQLAlchemy ORM models
│       ├── schemas.py                    # Pydantic request/response schemas
│       ├── dependencies.py               # get_current_user, require_roles, get_db
│       ├── exceptions.py                 # Custom exception classes + handlers
│       │
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── auth.py                   # POST /api/auth/login, /refresh
│       │   ├── customers.py              # POST /api/customers/link, GET /me/parcels
│       │   ├── parcels.py                # CRUD + status update + tracking + waybill
│       │   ├── payments.py               # Cash collect, Chapa initiate + webhook
│       │   ├── manifests.py              # Transfer manifest CRUD + bulk receive
│       │   ├── branches.py               # Branch CRUD (admin)
│       │   ├── staff.py                  # Staff CRUD (admin/manager)
│       │   └── reports.py                # Cash reconciliation, performance, overrides
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── chapa.py                  # initiate_checkout, verify_transaction, verify_signature
│       │   ├── notifications.py          # notify_status_change, notify_payment_confirmed
│       │   ├── pdf.py                    # render_waybill_html, generate_pdf_bytes (WeasyPrint)
│       │   ├── storage.py                # S3/R2 upload, signed URL generation
│       │   └── sms.py                    # SMS gateway integration
│       │
│       ├── workers/
│       │   ├── __init__.py
│       │   ├── celery_app.py             # Celery app factory
│       │   ├── notification_tasks.py     # send_telegram_notification, send_sms_notification
│       │   ├── payment_tasks.py          # retry_failed_webhook
│       │   ├── pdf_tasks.py              # generate_waybill_pdf task
│       │   ├── alert_tasks.py            # check_transit_delays, daily_manager_digest
│       │   └── beat_schedule.py          # Celery beat periodic task definitions
│       │
│       ├── core/                         # Pure Python — zero FastAPI/SQLAlchemy imports
│       │   ├── __init__.py
│       │   ├── state_machine.py          # ALLOWED_TRANSITIONS, validate_transition()
│       │   ├── tracking_code.py          # generate_tracking_code()
│       │   ├── security.py               # JWT encode/decode, bcrypt hashing
│       │   └── pagination.py             # Generic offset pagination helper
│       │
│       └── bot/
│           ├── __init__.py
│           ├── bot.py                    # Application builder, handler registration
│           ├── messages.py               # All message templates (English + future i18n)
│           └── handlers/
│               ├── __init__.py
│               ├── start.py              # /start, contact sharing
│               ├── track.py              # /track command
│               ├── my_parcels.py         # "My Parcels" callback
│               ├── payment.py            # "Pay Now" callback → Chapa URL
│               └── receipt.py            # "Confirm receipt" callback
│
│
├── mela-express-dashboard/               # Next.js operator/admin web dashboard
│   ├── .gitignore                        # Node: node_modules, .next, env files
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── public/
│   │   └── logo.svg
│   └── src/                             # TypeScript source root (Next.js convention = src/)
│       ├── app/                          # Next.js App Router
│       │   ├── layout.tsx
│       │   ├── page.tsx                  # Redirect to /dashboard
│       │   ├── login/
│       │   │   └── page.tsx
│       │   ├── dashboard/
│       │   │   └── page.tsx              # KPI snapshot
│       │   ├── parcels/
│       │   │   ├── page.tsx              # List + filters
│       │   │   ├── new/
│       │   │   │   └── page.tsx          # Intake form
│       │   │   └── [id]/
│       │   │       └── page.tsx          # Detail + status update + waybill
│       │   ├── manifests/
│       │   │   ├── page.tsx
│       │   │   ├── new/
│       │   │   │   └── page.tsx
│       │   │   └── [id]/
│       │   │       ├── page.tsx
│       │   │       └── receive/
│       │   │           └── page.tsx      # Bulk confirm arrival
│       │   ├── cash/
│       │   │   └── page.tsx              # Cash reconciliation
│       │   ├── reports/
│       │   │   └── page.tsx
│       │   └── admin/
│       │       ├── branches/
│       │       │   └── page.tsx
│       │       ├── staff/
│       │       │   └── page.tsx
│       │       └── overrides/
│       │           └── page.tsx
│       ├── components/
│       │   ├── ui/                       # Headless/Radix UI primitives (.gitkeep)
│       │   ├── parcels/
│       │   │   ├── ParcelTable.tsx
│       │   │   ├── ParcelForm.tsx
│       │   │   ├── StatusBadge.tsx
│       │   │   └── StatusTimeline.tsx
│       │   ├── manifests/
│       │   │   ├── ManifestTable.tsx
│       │   │   └── ManifestReceiveForm.tsx
│       │   └── layout/
│       │       ├── Sidebar.tsx
│       │       ├── TopBar.tsx
│       │       └── RoleGuard.tsx
│       ├── lib/
│       │   ├── api.ts                    # Axios instance with JWT interceptor
│       │   ├── auth.ts                   # Login, token storage, refresh logic
│       │   └── utils.ts
│       └── types/
│           └── index.ts                  # TypeScript types matching backend schemas
│
│
├── mela-express-public/                  # Public-facing tracking page
│   ├── .gitignore                        # Node: node_modules, .next, env files
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── src/                             # TypeScript source root
│       └── app/
│           ├── layout.tsx
│           ├── page.tsx                  # Redirects to /track/enter
│           └── track/
│               └── [code]/
│                   └── page.tsx          # melaexpress.com/track/MEX-HW-000482
│
│
├── docs/                                 # All project documentation (tracked by Git)
│   ├── architecture.md                   # Full HLD + LLD design document
│   ├── requirements.md                   # All 18 requirements with acceptance criteria
│   ├── tasks.md                          # Full implementation task list with dependency graph
│   ├── api-reference.md                  # Generated from FastAPI OpenAPI spec
│   ├── deployment.md                     # VPS setup, Docker Compose, Certbot steps
│   ├── operator-guide.md                 # How to use the dashboard (for training)
│   └── chapa-integration.md              # Chapa-specific notes, webhook verification
│
├── scripts/
│   ├── seed_branches.py                  # One-time: seed branch table from CSV
│   ├── seed_admin.py                     # One-time: create first admin account
│   └── backup_db.sh                      # Daily cron: pg_dump → offsite storage
│
├── ROADMAP.md                            # 5-phase development roadmap
├── FOLDER_STRUCTURE.md                   # This file
└── README.md                             # Project overview, quick start
```

---

## Key Architecture Decisions Encoded in This Structure

**`app/` vs `src/`**
The Python backend uses `app/` — the universal convention for FastAPI projects. The Next.js projects use `src/` — the standard Next.js App Router layout. These are different ecosystems with different conventions; both are correct.

**`app/core/`**
Pure Python modules with zero FastAPI or SQLAlchemy imports. The state machine, tracking code generator, and security primitives live here because they need to be unit-tested without spinning up a database or an ASGI server.

**`app/workers/`**
All Celery tasks in one place, separate from routers. Routers only call `.delay()` on tasks — they never `await` Telegram or SMS calls inline. This keeps the API request path fast regardless of downstream service latency.

**`app/bot/handlers/`**
Each Telegram command/callback in its own file. Every handler ends with an `await api_client.post(...)` call — zero business logic in the bot.

**`mela-express-dashboard/` and `mela-express-public/`**
Completely separate Next.js projects, each with their own Dockerfile and `.gitignore`. They talk to the backend API over HTTPS. No shared code with the Python backend.

**`docs/`**
All spec documents are copied here from `.kiro/` so they are committed to the Git repository and visible on GitHub. The `.kiro/` directory is for the Kiro IDE and is not pushed to GitHub.

**`.gitignore` at every level**
Root `.gitignore` covers the whole monorepo (env, macOS, Docker overrides). Each sub-project has its own `.gitignore` for language-specific artifacts (Python cache, Node modules, Next.js build output).

**`docker-compose.yml`**
Defines 8 services: `api`, `bot`, `worker`, `beat`, `db`, `redis`, `dashboard`, `nginx` (+ `certbot`). All share an internal Docker network; only `nginx` exposes ports 80/443 to the outside world.
