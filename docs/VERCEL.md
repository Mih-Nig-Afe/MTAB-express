# Vercel setup (mih-nig-afes-projects)

One-time setup in [Vercel Dashboard](https://vercel.com/mih-nig-afes-projects):

## 1. Import GitHub repo

Import `Mih-Nig-Afe/Mela-express` twice (two projects):

| Project name | Root Directory | Git branch (Production) |
|--------------|----------------|-------------------------|
| `mela-dashboard` | `mela-express-dashboard` | `staging` |
| `mela-public` | `mela-express-public` | `staging` |

> **Staging deploys from the `staging` branch.** Promote to `production` branch when ready for live URLs.

## 2. Environment variables

Set for **both** projects (Production + Preview):

```
NEXT_PUBLIC_API_URL=https://YOUR-API-HOST/api
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=eyJ...
```

For Telegram Mini App, backend also needs:

```
PUBLIC_PORTAL_URL=https://mela-public.vercel.app
```

(use the actual `mela-public` Vercel URL)

## 3. GitHub Actions (optional CI deploy)

Add repository secrets:

- `VERCEL_TOKEN` — from https://vercel.com/account/tokens
- `VERCEL_ORG_ID` — team settings → General
- `VERCEL_PROJECT_ID_DASHBOARD` — dashboard project settings
- `VERCEL_PROJECT_ID_PUBLIC` — public project settings

Pushes to `staging` run `.github/workflows/vercel-staging.yml`.

## 4. Telegram bot menu button

After `mela-public` is live on HTTPS, set `PUBLIC_PORTAL_URL` on the API so the bot WebApp menu opens `/mini-app`.

## Branch flow

```
feature/* (≤10 files/PR) → develop → staging → production
                              ↑ Vercel      ↑ Vercel prod
                              deploy        deploy
```
