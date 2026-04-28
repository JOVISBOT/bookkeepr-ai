# BOOKKEEPR AI — Claude Code Briefing
## PM: JOVIS | Do the work, I'll review

---

## Current State

BookKeepr is a Flask app at `C:\Users\jovis\.openclaw\workspace\bookkeepr\`
- **Runs locally** on port 5000 — 2 instances running
- **DB:** SQLite (local dev only) 
- **Frontend:** Jinja2 templates + Tailwind CSS + Chart.js + Lucide icons
- **Auth:** Flask-Login based, API at `/api/v1/login`
- **Routes:** 20+ blueprints (auth, api, dashboard, quickbooks, reconciliation, billing, etc.)
- **User:** `test@bookkeepr.ai` / `password123` (admin, tenant_id=1)
- **Has sandbox data:** accounts, transactions, QuickBooks connected
- **Dashboard works** but has a "JSON parse error" somewhere (need to find & fix)

## Issues to Tackle (Priority Order)

### P0: JSON Parse Error on Dashboard
Screenshots show "JSON parse error" on the dashboard. Probable cause: `/api/v1/user` returns HTML (login redirect) instead of JSON for unauthenticated API calls, or a malformed response somewhere. 
- Check all `/api/v1/*` endpoints return proper JSON
- Check dashboard JS fetch calls handle errors gracefully
- Check response Content-Type headers

### P0: AI Categorization for CSV Imports
The app has OpenAI/Anthropic dependencies but AI categorization isn't wired to CSV import flow.
- Check `app/routes/imports.py` and `app/routes/ai.py`
- Wire up categorization when user imports transactions
- Can use the existing Anthropic/OpenAI keys (check .env)

### P1: Production Deployment Prep (Render)
Missing files needed for Render:
- ❌ `runtime.txt` — Python version spec (Python 3.12.x)
- ❌ `Dockerfile` — optional but helpful
- ❌ Root-level `Procfile` — current one is in `app/` subdirectory, Render needs it at root
- ⚠️ `requirements.txt` conflicts — one at root, one in `app/`. Need to consolidate properly
- ⚠️ PostgreSQL switch — SQLite won't work on Render (ephemeral fs). Need config for DATABASE_URL env var with PostgreSQL
- ⚠️ .env.example — document all env vars needed for Render

### P2: Frontend Polish
- Charts loading correctly?
- "JSON parse error" could be in chart data fetching
- Check Chart.js data endpoints in `app/routes/charts.py`

## How to Proceed

1. Start by finding & fixing the JSON parse error (scrape the page or check JS console)
2. Then wire up AI categorization 
3. Then prep deployment

**Project directory:** `C:\Users\jovis\.openclaw\workspace\bookkeepr\`
**App entry:** `bookkeepr/app/run.py`
**Check .env:** `C:\Users\jovis\.openclaw\workspace\bookkeepr\app\.env`

**Testing:** Server is live on port 5000. Login via POST to `/api/v1/login` with `{"email":"test@bookkeepr.ai","password":"password123"}`.

**Don't break the working app.** Make backup copies before changes. Test every change with the running server.

Report summary when done. JOVIS reviews.
