# Mela Express — Deployment & Branching

## Branch model

| Branch | Purpose |
|--------|---------|
| `develop` | Integration — all feature PRs merge here |
| `staging` | **Vercel staging** — auto-deploys dashboard + public mini-app |
| `production` | **Vercel production** — promoted releases |
| `main` | Legacy stable tag; kept in sync with `production` on release |

### Flow

```
feature/*  →  develop  →  staging  →  production
   (PR ≤10 files)     (promote)    (promote)
```

## Vercel projects

Create **two** projects under [mih-nig-afes-projects](https://vercel.com/mih-nig-afes-projects):

| Project | Root directory | Production branch |
|---------|----------------|-------------------|
| `mela-dashboard` | `mela-express-dashboard` | `production` |
| `mela-public` | `mela-express-public` | `production` |

Connect the GitHub repo. Set **staging** branch deployments enabled for preview URLs.

### Environment variables (both frontends)

| Variable | Staging example | Production example |
|----------|-----------------|-------------------|
| `NEXT_PUBLIC_API_URL` | `https://api-staging.yourdomain.com/api` | `https://api.yourdomain.com/api` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Supabase anon key | Supabase anon key |

Public portal URL (for Telegram WebApp menu button) must be HTTPS:

```env
PUBLIC_PORTAL_URL=https://mela-public.vercel.app
```

Set on the **backend** (API), not Vercel.

### GitHub Actions secrets

For automated deploys:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID_DASHBOARD`
- `VERCEL_PROJECT_ID_PUBLIC`

Workflows: `.github/workflows/vercel-staging.yml` (on `staging`), `vercel-production.yml` (on `production`).

## Backend (API, bot, workers)

Not on Vercel. Deploy via Docker on VPS — `.github/workflows/deploy.yml` (triggered from `production`).
