# Mela Express — Railway backend deployment

## Services (one Railway project)

| Service | Start command |
|---------|---------------|
| **api** | `sh scripts/start-api.sh` |
| **bot** | `python -m app.bot.bot` |
| **worker** | `celery -A app.workers.celery_app worker --loglevel=info --concurrency=2` |
| **beat** | `celery -A app.workers.celery_app beat --loglevel=info` |

Add **PostgreSQL** and **Redis** plugins. Root directory for every service: `mela-express-backend`.

## Required variables (api, bot, worker, beat)

| Variable | Example |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://…` (convert Railway Postgres URL) |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `CELERY_BROKER_URL` | same as Redis |
| `CELERY_RESULT_BACKEND` | Redis DB 1 |
| `TELEGRAM_BOT_TOKEN` | BotFather token |
| `APP_BASE_URL` | `https://<api-service>.up.railway.app` |
| `INTERNAL_API_URL` | `http://api.railway.internal:8000` (bot only) |
| `PUBLIC_PORTAL_URL` | `https://mela-public.vercel.app` |
| `JWT_SECRET_KEY` | `openssl rand -hex 32` |
| `ENVIRONMENT` | `production` |
| `CORS_ORIGINS` | `["https://mela-public.vercel.app","https://mela-dashboard-sigma.vercel.app"]` |

After first deploy, run seeds:

```bash
railway run python scripts/seed_branches.py
railway run python scripts/seed_admin.py
railway run python scripts/seed_staff.py
```
