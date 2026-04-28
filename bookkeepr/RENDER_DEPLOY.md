# Render Deployment Guide — BookKeepr AI

## Quick Deploy Steps

### 1. Connect GitHub repo to Render
1. Push the `app/` directory to GitHub (or the whole bookkeepr repo)
2. In Render dashboard → **New Web Service** → Connect repo
3. **Root Directory:** `app/`
4. **Runtime:** Python 3
5. **Build Command:** `pip install -r requirements.txt`
6. **Start Command:** `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120`

### 2. Environment Variables (Render Dashboard)
Add these under **Environment**:

| Variable | Value |
|----------|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | *(generate a random string)* |
| `DATABASE_URL` | `sqlite:///bookkeepr.db` *(or Postgres URL from Render Postgres)* |
| `APP_URL` | `https://your-app.onrender.com` |
| `SUPPORT_EMAIL` | `support@bookkeepr.ai` |
| `LOG_LEVEL` | `INFO` |

**Optional (for AI categorization):**
| `ANTHROPIC_API_KEY` | *(your key)* |

### 3. Database
- **SQLite (default):** Works out of box but resets on deploy — fine for testing
- **PostgreSQL (recommended for production):** Create a Render Postgres DB, connect with `postgresql://user:pass@host:5432/bookkeepr`

### 4. Verify
- Visit `https://your-app.onrender.com`
- Login with test account (will need to sign up first on new DB)

---

## Files Already Configured

```text
app/
├── Procfile              ✅ Points to wsgi:application
├── wsgi.py               ✅ WSGI entry point for Gunicorn
├── runtime.txt           ✅ python-3.13.2
├── requirements.txt      ✅ Includes gunicorn + psycopg2-binary
└── .env                  ⚠️ Do NOT commit to git (already in .gitignore)
```

## Notes
- **No Redis needed** — Celery tasks not required for basic operation
- **Vercel frontend** already configured in `vercel.json` — proxies API to Render
- **SQLite resets on each deploy** — use Render Postgres for persistent data
