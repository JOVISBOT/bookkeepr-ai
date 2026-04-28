# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Starting the Server

**Always run from `app/` directory:**
```bash
cd app
flask run             # uses FLASK_APP from app/.env
# OR
python run.py         # directly starts on port 5000 with debug=True
```

The `restart_server.bat` at root level uses the broken outer `__init__.py` — **do not use it**. Always work from `app/`.

## Running Tests

```bash
cd app
pytest tests/                        # all tests
pytest tests/test_auth.py            # single file
pytest tests/test_models.py -k "test_user"  # single test by name
```

## Critical Architecture: Two-Layer App Structure

This repo has two Flask app layers. **Only the inner layer matters:**

```
bookkeepr/
├── run.py               # BROKEN outer entry (imports fail — do not use)
├── app/                 # outer package (legacy wrapper — mostly ignore)
│   ├── __init__.py      # BROKEN factory — do not edit
│   ├── run.py           # correct inner entry point
│   ├── extensions.py    # Flask extensions (db, login_manager)
│   ├── config.py        # DevelopmentConfig / ProductionConfig / TestingConfig
│   └── app/             # ← THE REAL APPLICATION — all edits go here
│       ├── __init__.py  # real create_app() — registers all 19 blueprints
│       ├── decorators.py
│       ├── models/
│       ├── routes/
│       ├── services/
│       └── templates/
```

**Rule:** Every file edit goes inside `app/app/`. The outer `bookkeepr/app/__init__.py` is a broken legacy file — never edit it.

## Blueprint Organization (app/app/routes/)

| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| `main` | `/` | Landing page |
| `auth` | `/auth` | Login, register, logout |
| `dashboard` | `/dashboard` | Operator dashboard (Jinja2 UI) |
| `api` | `/api/v1` | REST API for React frontend |
| `quickbooks` | `/quickbooks` | QBO OAuth callback + sync trigger |
| `portal` | `/portal` | Client-facing portal (Jinja2) |
| `clients` | `/clients` | Operator manages client accounts |
| `reports` | (multiple) | Financial reports + PDF/CSV download |
| `ai` | `/api/v1/ai` | AI categorization endpoints |
| `ai_enhanced` | `/api/v1/ai` | Anomalies, cashflow forecast, breakdowns |
| `reconciliation` | `/api/v1` | Bank reconciliation |
| `billing` | — | Stripe subscriptions |
| `pricing` | `/pricing` | Pricing page |
| `review` | — | Transaction review queue |
| `admin` | — | Superadmin panel |
| `banks` | — | Plaid bank connections |
| `imports` | — | CSV/OFX import |
| `mfa` | — | TOTP multi-factor auth |

Both `ai` and `ai_enhanced` register at `/api/v1/ai` — their routes don't overlap so this works.

## Data Model Relationships

Two FKs exist from `Company` → `User`: `user_id` (owner) and `client_user_id` (portal client). Both must specify `foreign_keys` to avoid SQLAlchemy `AmbiguousForeignKeysError`:

```python
# user.py
companies = db.relationship('Company', foreign_keys='[Company.user_id]', backref='owner', ...)

# company.py
client_user = db.relationship('User', foreign_keys=[client_user_id], backref='client_companies')
```

**Never add a new FK from Company to User without specifying `foreign_keys` on both sides.**

Key model fields:
- `Transaction.categorization_status`: `uncategorized` | `suggested` | `categorized`
- `Transaction.review_status`: `pending` | `approved` | `flagged`
- `Transaction.transaction_date` (not `date`), `Transaction.vendor_name` (not `payee`)
- `Company.qbo_company_name` (not `company_name`), `Company.client_user_id` (portal access)
- `Company.qbo_realm_id`: unique QuickBooks company identifier; placeholder format `pending-<hex>` for manually added clients

## RBAC Decorators

```python
@operator_required      # firm owner only
@client_required        # client/viewer only (use require_client in portal.py)
@role_required('admin') # specific role
@tenant_isolated        # auto-injects tenant_id filter
```

Portal routes use a local `require_client` decorator (not imported from decorators.py) that redirects clients vs operators differently.

## Dual Frontend

- **Jinja2 templates** (`app/app/templates/`) serve `/dashboard/*`, `/portal/*`, `/clients/*`, etc. These use Tailwind CDN + Lucide icons. Always call `lucide.createIcons()` at end of template.
- **React SPA** (`app/frontend/src/`) served at `/app/*`. API calls go to `/api/v1/*`. The build output lands in `app/static/`.

`base.html` loads: Tailwind CDN (script, not link), theme.css (`/static/css/theme.css`), Inter font, Lucide icons.

## GAAP Categorization Service

`app/app/services/gaap_coa.py` contains the GAAP/AICPA chart of accounts. Use it for AI categorization:

```python
from app.services.gaap_coa import categorize_by_gaap, seed_gaap_accounts

result = categorize_by_gaap(description, vendor, amount)
# returns: {account_number, account_name, account_type, classification, confidence}
# confidence: base 60% + 8% per keyword match, cap 96%
# HIGH ≥80% → auto-approve, MEDIUM 50-79% → suggest+review, LOW <30% → manual
```

Account numbers follow GAAP: 1000-1999 Assets, 2000-2999 Liabilities, 3000-3999 Equity, 4000-4999 Revenue, 5000-5999 COGS, 6000-6999 Operating Expenses, 7000-7999 Other.

## Client Portal Flow

1. Operator creates Company (manually or via QBO OAuth)
2. Operator visits `/clients/<id>/invite` → creates `User(role='client')` + temp password → sets `company.client_user_id`
3. Client logs in at `/auth/login` → `require_client` redirects to `/portal/`
4. `_get_client_company()` in portal.py finds company via `db.or_(Company.user_id == current_user.id, Company.client_user_id == current_user.id)`

## Database

SQLite in development (`app/instance/bookkeepr.db`), PostgreSQL in production. WAL mode is enabled for SQLite concurrency.

`db.create_all()` does **not** add columns to existing tables. Use raw `ALTER TABLE` for schema changes on existing tables:
```python
with db.engine.connect() as conn:
    conn.execute(text('ALTER TABLE companies ADD COLUMN new_col TYPE'))
    conn.commit()
```

Flask-Migrate (`flask db migrate / flask db upgrade`) is available but migrations are in `app/migrations/`.

## Environment Variables

Required in `app/.env`:
```
FLASK_APP=run.py
DATABASE_URL=sqlite:///absolute/path/to/bookkeepr.db
INTUIT_CLIENT_ID=...
INTUIT_CLIENT_SECRET=...
INTUIT_REDIRECT_URI=http://localhost:5000/quickbooks/callback
INTUIT_SANDBOX_MODE=true
SECRET_KEY=...
```
