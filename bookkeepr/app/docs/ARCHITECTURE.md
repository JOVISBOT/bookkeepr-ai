# BookKeepr AI - Technical Architecture

## Overview

BookKeepr AI is a premium autonomous bookkeeping application that integrates with QuickBooks Online (QBO) and QuickBooks Desktop (QBD). It uses AI to automatically categorize transactions, reconcile accounts, and save business owners 10+ hours per week.

## Architecture Principles

1. **Simplicity First** - Use proven libraries, avoid over-engineering
2. **Hybrid Integration** - Official libraries for auth/API, custom logic for business rules
3. **Scalable Foundation** - PostgreSQL + Celery for background processing
4. **Security-First** - OAuth 2.0, encrypted tokens, secure token storage

---

## Tech Stack

### Core Framework
| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Flask 3.x | Web framework |
| Database | PostgreSQL 15+ | Primary data store |
| ORM | SQLAlchemy 2.x | Database abstraction |
| Migrations | Flask-Migrate (Alembic) | Schema versioning |
| Task Queue | Celery + Redis | Background jobs |
| Auth | intuit-oauth | QBO OAuth 2.0 |
| API Client | python-quickbooks | QBO API wrapper |
| Environment | python-dotenv | Configuration |

### Additional Libraries
| Component | Technology | Purpose |
|-----------|------------|---------|
| Testing | pytest + pytest-flask | Unit/integration tests |
| Forms | Flask-WTF | Form handling |
| Security | Flask-Talisman | Security headers |
| Templating | Jinja2 | HTML rendering |
| CSS | Tailwind CSS | Styling |
| Charts | Chart.js | Data visualization |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser  │  Mobile Browser  │  QuickBooks Desktop (QBD)   │
└─────────────────┴──────────────────┴────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│                        Flask Application                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │   Routes    │ │  Services   │ │   Models    │ │  Tasks    │  │
│  │   (Blueprints)│ │  (Business) │ │  (SQLAlchemy)│ │ (Celery)  │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INTEGRATION LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  intuit-oauth    │  │ python-quickbooks│                    │
│  │  (QBO OAuth)     │  │ (QBO API)        │                    │
│  └──────────────────┘  └──────────────────┘                    │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  QBD SDK Agent   │  │   LLM API        │                    │
│  │  (Desktop)       │  │   (OpenAI)       │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  PostgreSQL │  │    Redis    │  │  QuickBooks (External)  │  │
│  │  (Primary)  │  │   (Queue)   │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
bookkeepr/app/
├── docs/
│   └── ARCHITECTURE.md           # This file
├── src/
│   ├── __init__.py               # Flask app factory
│   ├── config.py                 # Environment configuration
│   ├── extensions.py             # Flask extensions initialization
│   ├── models/                   # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py               # User account model
│   │   ├── company.py            # QBO/QBD company connection
│   │   ├── transaction.py        # Financial transactions
│   │   └── category.py           # AI learning categories
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── qb_service.py         # QuickBooks integration
│   │   ├── auth_service.py       # Authentication logic
│   │   └── categorization.py     # AI categorization engine
│   ├── routes/                   # Flask blueprints
│   │   ├── __init__.py
│   │   ├── auth.py               # OAuth routes
│   │   ├── dashboard.py          # Main UI
│   │   ├── transactions.py       # Transaction API
│   │   └── api.py                # REST API endpoints
│   ├── tasks/                    # Celery background tasks
│   │   ├── __init__.py
│   │   ├── sync.py               # QBO data sync
│   │   └── categorization.py     # Batch categorization
│   └── templates/                # Jinja2 templates
│       ├── base.html
│       ├── dashboard.html
│       ├── auth/
│       │   └── login.html
│       └── transactions/
│           └── list.html
├── migrations/                   # Alembic database migrations
├── tests/                        # Pytest test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_models.py
│   └── test_services.py
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .env                          # Local environment (gitignored)
├── config.py                     # Legacy config (optional)
└── run.py                        # Application entry point
```

---

## Data Models

### Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────────┐
│    User      │1     * │   Company    │1     * │   Transaction    │
├──────────────┤───────├──────────────┤───────├──────────────────┤
│ id (PK)      │       │ id (PK)      │       │ id (PK)          │
│ email        │       │ user_id (FK) │       │ company_id (FK)  │
│ password_hash│       │ realm_id     │       │ qbo_id           │
│ is_active    │       │ company_name │       │ date             │
│ created_at   │       │ access_token │       │ amount           │
│ updated_at   │       │ refresh_token│       │ description      │
└──────────────┘       │ token_expires│       │ vendor           │
                       │ is_active    │       │ category         │
                       │ created_at   │       │ account_id       │
                       │ updated_at   │       │ transaction_type │
                       └──────────────┘       │ status           │
                              │               │ created_at       │
                              │               │ updated_at       │
                              │               └──────────────────┘
                              │
                              │*     1┌──────────────┐
                              └────────│   Category   │
                                       ├──────────────┤
                                       │ id (PK)      │
                                       │ company_id(FK)│
                                       │ name         │
                                       │ account_id   │
                                       │ keywords     │
                                       │ created_at   │
                                       └──────────────┘
```

### Model Details

#### User Model
- Stores application users (business owners/accountants)
- Email/password authentication
- One-to-many relationship with companies

#### Company Model
- Represents a connected QuickBooks company
- Stores OAuth tokens (encrypted at rest)
- Links to QBO via realm_id
- One-to-many relationship with transactions

#### Transaction Model
- Stores imported transactions from QBO
- Tracks categorization status
- Supports AI learning and review queue
- Indexes on: company_id, date, status, vendor

#### Category Model
- Custom categories per company
- AI learning keywords (JSON)
- Links to QBO account_id for posting

---

## QuickBooks Integration

### QBO (QuickBooks Online) Flow

```
1. User clicks "Connect to QuickBooks"
2. Redirect to Intuit OAuth authorization
3. User grants permissions
4. OAuth callback receives authorization code
5. Exchange code for access_token + refresh_token
6. Store tokens encrypted in Company record
7. Use tokens with python-quickbooks library
8. Automatic token refresh before expiration
```

### QBD (QuickBooks Desktop) Flow

```
1. User installs local agent on Windows PC
2. Agent communicates via QBSDK/QBXML
3. Syncs data to cloud database
4. AI processing in cloud
5. Pushes categorizations back to Desktop
```

### Token Management

| Token Type | Lifetime | Storage | Usage |
|------------|----------|---------|-------|
| access_token | 1 hour | Encrypted DB | API calls |
| refresh_token | 100 days | Encrypted DB | Get new access_token |
| authorization | 10 minutes | Session | Initial OAuth only |

---

## Security Considerations

### Authentication & Authorization
- OAuth 2.0 for QBO integration
- Password hashing with bcrypt (via Flask-Bcrypt)
- Session management with Flask-Login
- CSRF protection on all forms

### Data Protection
- OAuth tokens encrypted at rest (Fernet encryption)
- PostgreSQL SSL connections
- Environment variables for secrets
- No hardcoded credentials

### API Security
- Rate limiting (500 req/min per realm - QBO limit)
- Request signing where required
- Webhook signature verification

---

## Background Processing

### Celery Tasks

| Task | Frequency | Purpose |
|------|-----------|---------|
| sync_transactions | Hourly | Import new QBO transactions |
| auto_categorize | On demand | AI categorization batch |
| token_refresh | Before expiry | Keep OAuth tokens valid |
| reconciliation | Daily | Match transactions to bank feeds |
| cleanup | Weekly | Remove old logs/tmp files |

### Task Queue Flow

```
[Scheduled Trigger] → [Redis Queue] → [Celery Worker] → [PostgreSQL]
     Hourly/Cron              Broker         Processing         Results
```

---

## AI Categorization Engine

### Architecture

```
Incoming Transaction
       │
       ▼
┌─────────────────┐
│  Rule Engine    │ ──→ Exact match (vendor rules) → Category
│  (First Pass)   │
└─────────────────┘
       │
       ▼ (no rule match)
┌─────────────────┐
│  LLM Categorizer│ ──→ AI prediction → Category + Confidence
│  (OpenAI API)   │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Confidence Gate │ ──→ High (>80%): Auto-apply
│                 │ ──→ Medium (50-80%): Suggest
│                 │ ──→ Low (<50%): Review queue
└─────────────────┘
       │
       ▼ (user correction)
┌─────────────────┐
│  Learning Store │ ──→ Update keywords → Better future predictions
│                 │
└─────────────────┘
```

---

## Deployment Architecture

### Production Stack

| Component | Service | Purpose |
|-----------|---------|---------|
| App Server | Gunicorn + Flask | HTTP requests |
| Web Server | Nginx | Static files, SSL termination |
| Database | PostgreSQL 15+ | Data persistence |
| Queue | Redis | Celery broker |
| Workers | Celery | Background tasks |
| Monitoring | Sentry | Error tracking |
| Hosting | Railway/Render/Digital Ocean | Infrastructure |

### Environment Strategy

| Environment | Purpose | Data |
|-------------|---------|------|
| local | Development | Local Postgres, sandbox QBO |
| staging | Testing | Staging DB, sandbox QBO |
| production | Live | Production DB, production QBO |

---

## API Endpoints (Planned)

### Authentication
- `GET /auth/login` - Login page
- `GET /auth/qbo/connect` - Start QBO OAuth
- `GET /auth/qbo/callback` - OAuth callback
- `POST /auth/logout` - Logout

### Dashboard
- `GET /dashboard` - Main dashboard
- `GET /dashboard/stats` - Stats API

### Transactions
- `GET /transactions` - List transactions
- `GET /transactions/<id>` - Transaction detail
- `POST /transactions/<id>/categorize` - Categorize transaction
- `GET /transactions/review` - Review queue

### API (REST)
- `GET /api/v1/companies` - List companies
- `GET /api/v1/companies/<id>/transactions` - Company transactions
- `POST /api/v1/webhooks/qbo` - QBO webhook receiver

---

## Scaling Considerations

### Database
- Connection pooling (SQLAlchemy pool)
- Read replicas for heavy reporting
- Archival strategy for old transactions

### Application
- Horizontal scaling with multiple workers
- Stateless design (sessions in Redis)
- CDN for static assets

### Background Jobs
- Multiple Celery workers
- Task prioritization queues
- Dead letter queue for failures

---

## Monitoring & Observability

### Metrics to Track
- Transaction sync success rate
- Categorization accuracy
- OAuth token refresh failures
- API response times
- Background task queue depth

### Logging Strategy
- Structured JSON logging
- Request ID correlation
- Sensitive data redaction
- Log rotation

---

## Development Guidelines

### Code Organization
- Fat models, thin views, service layer for business logic
- Blueprints for route organization
- Services for external integrations
- Tasks for background work

### Testing Strategy
- Unit tests for models and services
- Integration tests for API endpoints
- Mock external services (QBO API)
- Test database per test run

### Git Workflow
- Feature branches
- PR reviews required
- CI/CD via GitHub Actions
- Automated testing on PR

---

## References

### Libraries
- [intuit-oauth](https://github.com/intuit/oauth-pythonclient) - Official Intuit OAuth
- [python-quickbooks](https://github.com/sidecars/python-quickbooks) - QBO API wrapper
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Celery](https://docs.celeryproject.org/) - Task queue

### Documentation
- [Intuit Developer](https://developer.intuit.com/)
- [QBO API Reference](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account)
- [QBD SDK](https://developer.intuit.com/app/developer/qbdocs/docs/get-started)

---

## Decision Log

| Date | Decision | Reasoning |
|------|----------|-----------|
| 2026-04-19 | Flask over FastAPI | Familiarity, mature ecosystem, simpler for HTML rendering |
| 2026-04-19 | python-quickbooks over direct API | Proven library, handles models, reduces maintenance |
| 2026-04-19 | PostgreSQL over MySQL | JSON support for keywords, better SQLAlchemy support |
| 2026-04-19 | Celery over RQ | More mature, better monitoring, proven at scale |
| 2026-04-19 | Tailwind CSS over Bootstrap | Modern, utility-first, smaller bundle |

---

**Version:** 1.0  
**Last Updated:** 2026-04-19  
**Status:** Foundation Phase - In Progress
