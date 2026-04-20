# BookKeepr AI

**Premium Autonomous Bookkeeping for QuickBooks**

AI-powered bookkeeping automation that saves business owners 10+ hours/week by intelligently categorizing transactions, automating reconciliation, and syncing seamlessly with QuickBooks Online and Desktop.

---

## 🎯 Mission

Build the world's best AI-powered bookkeeping automation for QuickBooks Online and Desktop, targeting business owners doing $500K-$5M revenue.

**Target Launch:** $199/$299/$399 monthly tiers  
**Exit Goal:** $1M ARR → $50-100M acquisition (5-10x ARR)

---

## 📋 Phase Overview

| Phase | Focus | Status |
|-------|-------|--------|
| **0** | Foundation & Research | ✅ Complete |
| **1** | QBO Core Integration | ✅ **Complete** |
| **2** | AI Categorization | 🔄 Next Up |
| **3** | Dashboard & UX | ⏳ Planned |
| **4** | Reconciliation | ⏳ Planned |
| **5** | QBD Integration | ⏳ Planned |
| **6** | Billing & Launch | ⏳ Planned |
| **7** | Scale & Growth | ⏳ Planned |
| **8** | Exit Preparation | ⏳ Planned |

---

## 🚀 Current Status: Phase 1 Complete

### What's Built

- ✅ **Flask Application** with modular structure
- ✅ **Database Models** (User, Company, Account, Transaction)
- ✅ **QuickBooks OAuth 2.0** integration
- ✅ **Company & Chart of Accounts sync**
- ✅ **Transaction import** (Purchases, Deposits, Journal Entries, Invoices, Sales Receipts)
- ✅ **Dashboard UI** with Tailwind CSS
- ✅ **Authentication system** (login/register)
- ✅ **REST API endpoints** for transactions, accounts, sync

### Tech Stack

- **Backend:** Python 3.11+, Flask
- **Database:** PostgreSQL + SQLAlchemy
- **QBO Libraries:** intuit-oauth, python-quickbooks
- **Frontend:** Tailwind CSS, Jinja2, Lucide icons
- **Auth:** Flask-Login

---

## 🏗️ Architecture

```
bookkeepr/
├── app/                      # Main Flask application
│   ├── app/                  # Application package
│   │   ├── models/           # Database models
│   │   ├── routes/           # Flask blueprints
│   │   ├── services/         # Business logic
│   │   └── templates/        # Jinja2 templates
│   ├── config.py             # Configuration
│   ├── extensions.py         # Flask extensions
│   ├── requirements.txt      # Dependencies
│   └── run.py                # Entry point
├── PHASE_0/                  # Phase 0 documentation
├── PHASE_1/                  # Phase 1 documentation
├── MASTER_PLAN.md            # Full project roadmap
└── README.md                 # This file
```

---

## 🛠️ Setup

See [app/README.md](app/README.md) for detailed setup instructions.

Quick start:

```bash
cd app
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python run.py
```

---

## 📚 Documentation

- [Master Plan](MASTER_PLAN.md) - Complete roadmap through Phase 8
- [Phase 1 Details](app/README.md) - Current phase technical documentation
- [Phase 0 Research](PHASE_0/) - Initial research and architecture

---

## 🎯 Next Phase: AI Categorization

Phase 2 will focus on:
- Rule-based categorization system
- AI-powered transaction categorization (OpenAI/Anthropic)
- Learning from user corrections
- Confidence scoring
- Review queue for uncertain items

Target: 80% auto-categorization accuracy

---

## 🔒 Security Notes

- OAuth tokens are securely stored and automatically refreshed
- Environment variables manage sensitive configuration
- See `.env.example` for required variables

---

## 📄 License

Private - All rights reserved
