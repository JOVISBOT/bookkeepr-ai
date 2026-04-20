# Phase 0: Foundation & Research
## Week 1-2: Getting Started

**Goal:** Set up development environment, research existing solutions, define architecture

---

## 📋 Task Checklist

### Day 1-2: Research Existing Solutions
- [ ] Review top 10 GitHub QuickBooks repositories
- [ ] Document architecture patterns found
- [ ] Note integration approaches (OAuth, SDK, etc.)
- [ ] Identify common pitfalls and solutions

**Key Repositories to Study:**
Search: https://github.com/search?q=quickbooks&type=repositories

Look for:
- Python integrations with QBO
- OAuth 2.0 implementations
- Database schema designs
- Error handling patterns

### Day 3-4: Intuit Developer Setup
- [ ] Create Intuit Developer account: https://developer.intuit.com/
- [ ] Create new app for BookKeepr
- [ ] Get Client ID and Client Secret
- [ ] Configure OAuth redirect URLs
- [ ] Review API documentation
- [ ] Test API explorer

### Day 5-7: Project Setup
- [ ] Initialize Git repository
- [ ] Set up Python virtual environment
- [ ] Create project structure
- [ ] Install initial dependencies
- [ ] Set up PostgreSQL database
- [ ] Configure environment variables
- [ ] Create first "Hello World" endpoint

---

## 🔍 Research Template

For each GitHub repository reviewed, document:

```
Repository: [name]
URL: [link]
Stars: [count]
Last Updated: [date]

What it does:
- [description]

Architecture:
- Language: [python/js/etc]
- Framework: [flask/django/etc]
- Database: [postgres/mysql/etc]

Good ideas to steal:
- [list]

Problems/Concerns:
- [list]

Relevance to BookKeepr:
- [how we can use this]
```

---

## 🛠️ Technical Requirements

### Python Environment
```bash
# Python 3.11+
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
```

### Initial Dependencies
```
flask==3.0.0
sqlalchemy==2.0.0
psycopg2-binary==2.9.9
intuit-oauth==1.2.4
requests==2.31.0
python-dotenv==1.0.0
celery==5.3.0
redis==5.0.0
openai==1.0.0
pytest==7.4.0
```

### Database Schema (Draft)

```sql
-- Companies (QB connections)
companies:
  - id (PK)
  - user_id (FK)
  - qb_realm_id
  - qb_company_name
  - access_token (encrypted)
  - refresh_token (encrypted)
  - token_expires_at
  - is_qbo (boolean)
  - is_qbd (boolean)
  - created_at
  - updated_at

-- Transactions (imported from QB)
transactions:
  - id (PK)
  - company_id (FK)
  - qb_transaction_id
  - date
  - amount
  - description
  - vendor
  - account_id
  - category (AI assigned)
  - confidence_score
  - status (auto_categorized / needs_review / approved)
  - created_at

-- Categories (Chart of Accounts mapping)
categories:
  - id (PK)
  - company_id (FK)
  - qb_account_id
  - name
  - account_type
  - is_active

-- Rules (user-defined categorization rules)
rules:
  - id (PK)
  - company_id (FK)
  - pattern (vendor/description match)
  - category_id (FK)
  - conditions (JSON)
  - priority
  - is_active

-- Users (BookKeepr users)
users:
  - id (PK)
  - email
  - password_hash
  - subscription_tier (standard/silver/gold)
  - subscription_status
  - stripe_customer_id
  - created_at
```

---

## 🏗️ Project Structure (Draft)

```
bookkeepr/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── transaction.py
│   │   └── category.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── transactions.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── qbo_service.py
│   │   ├── categorizer.py
│   │   └── reconciler.py
│   └── templates/
│       └── (HTML templates)
├── migrations/
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── run.py
```

---

## 🔐 Environment Variables (.env.example)

```
# Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost/bookkeepr

# Intuit / QuickBooks
INTUIT_CLIENT_ID=your-client-id
INTUIT_CLIENT_SECRET=your-client-secret
INTUIT_REDIRECT_URI=http://localhost:5000/callback
INTUIT_ENVIRONMENT=sandbox  # or production

# OpenAI (for categorization)
OPENAI_API_KEY=your-openai-key

# Stripe (for billing)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

---

## 📊 Success Criteria

Phase 0 is complete when:

- [ ] At least 5 GitHub repos reviewed and documented
- [ ] Intuit Developer account created
- [ ] App registered with Intuit
- [ ] OAuth credentials obtained
- [ ] Local development environment running
- [ ] Database schema defined
- [ ] Project structure created
- [ ] First Flask endpoint responds

---

## 🚀 Ready to Start

**Next Actions:**
1. Create GitHub repo for BookKeepr
2. Start reviewing QuickBooks repositories
3. Set up local environment
4. Create Intuit Developer account

**Estimated Time:** 3-5 hours over 1 week

**Let's begin!**
