# Deployment: Backend + Vercel Frontend

## 1. Deploy backend (Render — recommended)

1. Go to [render.com](https://render.com) → **New** → **Blueprint**
2. Connect repo: `ShouryaVeggalam/finance-ai-backend`
3. Render reads `render.yaml` and provisions:
   - Web service (`finance-ai-api`)
   - PostgreSQL database
   - Redis
4. After deploy, copy the API URL (e.g. `https://finance-ai-api.onrender.com`)
5. Optional: add `OPENAI_API_KEY` in Render environment for AI CFO answers

Health check: `GET https://<your-api>/health`  
API docs: `https://<your-api>/docs`

## 2. Connect Vercel frontend

In [Vercel Dashboard](https://vercel.com) → project `finance-ai-frontend` → **Settings** → **Environment Variables**:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://finance-ai-api.onrender.com` (your Render URL) |

Redeploy the frontend after saving.

Live site: https://finance-ai--dun.vercel.app

## 3. Backend CORS

The backend already allows:

- `https://finance-ai--dun.vercel.app`
- `https://finance-ai-frontend.vercel.app`

Set on Render (auto via `render.yaml`):

```
FRONTEND_URL=https://finance-ai--dun.vercel.app
```

## 4. First use

1. Open https://finance-ai--dun.vercel.app/login
2. **Register** a company + founder account
3. Dashboard and CFO Agent load live data from the API
4. Without `NEXT_PUBLIC_API_URL`, the app runs in **demo mode** (mock data)

## 5. Local development

```bash
# Backend
cd backend && docker compose up -d
docker compose exec api python scripts/init_db.py

# Frontend
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## Repos

- Backend: https://github.com/ShouryaVeggalam/finance-ai-backend
- Frontend: https://github.com/ShouryaVeggalam/finance-ai-frontend
