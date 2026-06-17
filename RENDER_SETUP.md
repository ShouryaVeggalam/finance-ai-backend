# Render: connect your EXISTING database (required)

The API **cannot start** until `DATABASE_URL` is on the **web service**, not only on the Postgres service.

## Fix in 60 seconds

1. Open [Render Dashboard](https://dashboard.render.com)
2. Click your **Web Service** (`finance-ai-api` or similar) — **not** the database
3. Go to **Environment**
4. Click **Add Environment Variable**
5. Choose **Add from database** (or **Link database**)
6. Select your **existing Postgres**
7. Confirm the variable name is **`DATABASE_URL`**
8. If you don't see "Add from database":
   - Open your **Postgres** service → **Connect** → copy **Internal Database URL**
   - Back on the web service → **Environment** → add:
     - Key: `DATABASE_URL`
     - Value: paste the URL (`postgresql://...`)
9. Add **`SECRET_KEY`** = any long random string (if not already set)
10. **Save Changes** → **Manual Deploy**

## Verify

After deploy, logs should show:

```
Database URL: configured
Starting uvicorn...
```

Then open: `https://<your-service>.onrender.com/health`

## Common mistake

| Wrong | Right |
|-------|--------|
| DB URL only exists on Postgres service | Must be on **Web Service** environment |
| Using External URL for same-region services | Prefer **Internal Database URL** |
| Only set `FRONTEND_URL` | Must also set `DATABASE_URL` + `SECRET_KEY` |
