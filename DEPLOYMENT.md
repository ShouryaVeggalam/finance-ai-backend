# Deployment: Backend + Vercel Frontend

## 1. Deploy backend on Render (use your existing database)

**Do not use Blueprint** if you already have Postgres — Blueprint would try to create new resources.

### Option A — New Web Service (recommended if you have a DB)

1. Render → **New** → **Web Service**
2. Connect repo: `ShouryaVeggalam/finance-ai-backend`
3. Runtime: **Docker**
### Connect your existing Postgres (required)

In your **Web Service** → **Environment**:

**Easiest:** Click **Add Environment Variable** → **Add from database** → select your existing Postgres.  
Render injects `DATABASE_URL` automatically — you do **not** need `DATABASE_URL_SYNC` separately.

**Or set manually:**

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql://user:pass@host/dbname` (from Postgres → Connect) |
| `SECRET_KEY` | any long random string |
| `FRONTEND_URL` | `https://finance-ai--dun.vercel.app` |

Also required: `SECRET_KEY` (random string). Without it the deploy will fail in production.

5. Deploy. On first boot the API auto-creates tables (`APP_ENV=production`).

### Option B — Blueprint (only if you want Render to create NEW Postgres + Redis)

Use **New → Blueprint** only when you want a fresh database. The repo `render.yaml` is now **web-only** and will not create a database.

### Celery / background jobs

Optional. The API runs without Redis. Background jobs (hourly sync, reports) need Redis — point `REDIS_URL` / `CELERY_*` at an existing Redis instance, or skip for now.

Health: `GET https://<your-api>/health`  
Docs: `https://<your-api>/docs`

## 2. Connect Vercel frontend

Vercel → `finance-ai-frontend` → **Settings** → **Environment Variables**:

```
NEXT_PUBLIC_API_URL=https://your-render-api.onrender.com
```

Redeploy. Live site: https://finance-ai--dun.vercel.app

## 3. First use

1. https://finance-ai--dun.vercel.app/login → Register
2. Dashboard loads live data from your existing DB

## Repos

- Backend: https://github.com/ShouryaVeggalam/finance-ai-backend
- Frontend: https://github.com/ShouryaVeggalam/finance-ai-frontend
