# BookKeepr AI - Phase 1: QBO Core Integration
## Project Architecture Document

---

## Overview
**Phase:** 1 - QBO Core Integration  
**Goal:** Establish working QBO connection with OAuth, company sync, and transaction import  
**Timeline:** 2-3 weeks  
**Status:** IN PROGRESS

---

## Tech Stack (Based on Phase 0 Research)

### Backend
- **Framework:** Flask (Python)
- **Auth:** intuit-oauth-python (official Intuit library)
- **API Client:** python-quickbooks (community library)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy

### Frontend
- **Framework:** React (with Tailwind CSS)
- **State:** React Query / Zustand
- **Charts:** Recharts

### Infrastructure
- **Hosting:** Railway / Render (TBD)
- **Queue:** Celery + Redis (for background sync)
- **Storage:** AWS S3 (for exports)

---

## Project Structure

```
bookkeepr/
├── app/                        # Flask application
│   ├── __init__.py            # App factory
│   ├── config.py              # Configuration
│   ├── models/                # Database models
│   │   ├── __init__.py
│   │   ├── user.py           # User model
│   │   ├── company.py        # QBO Company
│   │   ├── account.py        # Chart of accounts
│   │   ├── transaction.py    # Bank transactions
│   │   └── connection.py     # QBO connection
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py   # OAuth flow
│   │   ├── qbo_service.py    # QBO API wrapper
│   │   ├── sync_service.py   # Data synchronization
│   │   └── webhook_service.py  # Webhook handlers
│   ├── routes/                # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py           # OAuth routes
│   │   ├── company.py        # Company info
│   │   ├── transactions.py     # Transaction CRUD
│   │   └── dashboard.py       # Dashboard data
│   ├── static/                # Frontend build
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/             # HTML templates
│       └── index.html
├── migrations/                # Alembic migrations
├── tests/                     # Test suite
├── requirements.txt           # Python deps
└── README.md
```

---

## Database Schema

### Tables

**users**
- id (PK)
- email (unique)
- password_hash
- created_at
- updated_at

**companies**
- id (PK)
- user_id (FK)
- qbo_company_id (unique)
- company_name
- realm_id
- country
- fiscal_year_start
- created_at
- updated_at

**qbo_connections**
- id (PK)
- company_id (FK)
- access_token (encrypted)
- refresh_token (encrypted)
- expires_at
- is_active
- created_at
- updated_at

**accounts**
- id (PK)
- company_id (FK)
- qbo_account_id
- name
- account_type
- account_sub_type
- current_balance
- created_at
- updated_at

**transactions**
- id (PK)
- company_id (FK)
- qbo_transaction_id
- account_id (FK)
- date
- amount
- description
- payee
- category_id
- is_categorized
- created_at
- updated_at

---

## API Integration Plan

### Phase 1.1: OAuth Flow
1. User clicks "Connect QuickBooks"
2. Redirect to Intuit OAuth2 authorization URL
3. User grants permissions
4. Callback receives authorization code
5. Exchange code for access_token + refresh_token
6. Store tokens securely
7. Fetch company info (realm_id, company_name)

### Phase 1.2: Chart of Accounts Sync
1. Query QBO for accounts
2. Store in local database
3. Map account types (assets, liabilities, equity, revenue, expenses)

### Phase 1.3: Transaction Import
1. Query QBO for transactions (last 90 days)
2. Handle pagination
3. Store transactions with account references
4. Queue for AI categorization (Phase 2)

---

## Security Considerations

- OAuth tokens encrypted at rest (AES-256)
- HTTPS only
- Rate limiting on API endpoints
- Token refresh automation
- Webhook signature verification

---

## Deliverables Checklist

### Week 1: Foundation
- [ ] Project structure setup
- [ ] Database models created
- [ ] Flask app initialized
- [ ] Config management

### Week 2: OAuth & Connection
- [ ] OAuth flow implemented
- [ ] Company connection working
- [ ] Token storage/refresh
- [ ] Error handling

### Week 3: Data Sync
- [ ] Chart of accounts sync
- [ ] Transaction import
- [ ] Basic dashboard UI
- [ ] Tests written

---

## Next Phase Preview
**Phase 2: AI Categorization**
- OpenAI/GPT integration
- Smart transaction categorization
- Learning from user corrections
- Category confidence scores

---

## Status
**Current:** Setting up project structure  
**Next:** Database models → OAuth implementation

