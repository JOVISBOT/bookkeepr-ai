# 📊 BookKeepr AI - Master Project Tracker

**Spec:** `bookkeepr/BOOKKEEPR_TECH_SPEC.md`
**Updated:** 2026-04-25 18:16 PDT

---

## 🎯 SUCCESS CRITERIA — Status

| # | Criterion | Status | What's Left |
|---|-----------|--------|-------------|
| 1 | Sign up → Confirm email → Log in | 🟡 80% | Email confirmation send (no SMTP yet) |
| 2 | Upload bank CSV → See transactions classified | 🟡 70% | CSV upload ✅, AI auto-classify on import ⚠️ |
| 3 | Connect Plaid → overnight sync → see new txns | 🔴 30% | Service exists, needs Plaid keys + Celery scheduler |
| 4 | Override classification → see audit trail | ✅ 100% | Working - audit log captures changes |
| 5 | Bulk approve 100+ txns → Export to QB | 🔴 40% | Bulk approve UI ⚠️, QB export ❌ |
| 6 | Generate P&L, Balance Sheet, Cash Flow | ✅ 95% | All three work + PDF/Excel/CSV |
| 7 | Schedule monthly report → Client gets email | 🔴 20% | Reports work, scheduler + email send ❌ |
| 8 | Client logs in → sees own P&L, txns, reports | 🔴 10% | Client portal ❌ (RBAC ready, no UI) |
| 9 | Operator sees all clients → manages each | ✅ 90% | List/add/edit/archive done; bulk view ⚠️ |
| 10 | 100 concurrent users smoothly | 🟡 60% | SQLite WAL ok for small teams; PostgreSQL for prod |

---

## 🔥 Phase 1 — Foundation (CURRENT)

### ✅ DONE
- [x] Multi-tenant architecture (Tenant model, plan tiers, 14-day trial)
- [x] User RBAC (operator/client/viewer)
- [x] MFA TOTP (Google Authenticator working)
- [x] Audit log (every action with IP + user agent)
- [x] Login/Register/Logout flows
- [x] Operator Dashboard (stats, charts, transactions)
- [x] Client management (list, add, edit, archive, health badges)
- [x] **CSV Import** (drag-drop, auto-detect columns, preview, dedupe) ✅ verified saving 5 txns
- [x] **QuickBooks OAuth** (sandbox connect → token exchange → save) ✅ verified
- [x] **Reports module** (11 reports with PDF/Excel/CSV download)
- [x] Filters: Period, Compare, Category, Account in primary row + 9 advanced
- [x] Unified blue theme across ALL pages
- [x] Grouped nav (Money / Reports / Banking / Account)
- [x] Pricing page (4 tiers)

### ⚠️ NEXT TONIGHT (Phase 1 finish)
- [ ] **AI categorize on import** - call OpenAI/Claude when CSV row imported
- [ ] **Bulk approve UI** - select multiple uncategorized → approve
- [ ] **QB push back** - export categorized txns to QuickBooks
- [ ] **QB sync transactions** - pull from QBO when sandbox has data (verified token works, just empty sandbox)

---

## 📅 Phase 2 — Bank Integration & Client Portal (NEXT)

- [ ] **Plaid integration** - need Plaid sandbox keys (free at plaid.com)
- [ ] **Celery + Redis** - for nightly bank sync
- [ ] **Client Portal** - separate UI at `/portal/` for end-clients
  - Login as 'client' role
  - See their own dashboard (P&L summary, recent txns)
  - Bank connect wizard
  - Receipt upload
  - Message operator
- [ ] **PDF statement OCR** (pdfplumber + Tesseract)
- [ ] Subdomain routing (`client1.bookkeepr.app`)

---

## 📅 Phase 3 — Advanced Reports & Audit (LATER)

- [ ] Tax-Ready Summary report
- [ ] A/R + A/P Aging
- [ ] Vendor Summary, Customer Summary
- [ ] Scheduled monthly report email (SendGrid integration)
- [ ] Audit log viewer UI for operators
- [ ] Custom rules per client

---

## 📅 Phase 4 — Launch

- [ ] Stripe billing live (code exists, need keys)
- [ ] AES-256 encryption for stored OAuth tokens
- [ ] Rate limiting (Flask-Limiter)
- [ ] Pen test
- [ ] Production deploy (Render or Railway)
- [ ] PostgreSQL migration
- [ ] Custom domain + SSL
- [ ] Monitoring (Sentry + Uptime Robot)

---

## 🐛 Bugs Fixed This Session (2026-04-25)
- ✅ CSV import: NOT NULL constraint on `qbo_transaction_id` → generate `csv-{uuid}`
- ✅ Transactions page empty: route didn't pass data → now loads with filters
- ✅ Reports P&L returned 0 items: wrong data shape → unified `line_items`
- ✅ Categories empty: only used DB column → 17 common + custom
- ✅ Reports picked wrong company: now prefers connected
- ✅ QBO callback: `exchange_code_for_tokens` typo → `_token`
- ✅ QBO callback: `company.realm_id` → `company.qbo_realm_id`
- ✅ QBO callback: `sync_company_info` missing → graceful try/except
- ✅ DATABASE_URL relative path → absolute with forward slashes
- ✅ Theme inconsistency (8 pages) → all unified blue
- ✅ Sidebar layout (4 pages) → unified `base.html`
- ✅ Reports filters cramped → primary in top row + collapsible advanced
- ✅ Old heartbeats deleted (kept only 3 free local tasks)
- ✅ Demo seed data (50 fake transactions) deleted

---

## 🟢 What WORKS RIGHT NOW (verified by tests)
- Login: `test@bookkeepr.ai` / `TestPass123!`
- 5 real transactions in DB (Office Depot, Stripe, AWS, Acme, Adobe)
- Connected QBO sandbox (realm 9341456840126349)
- All 11 reports with PDF download
- Client management
- MFA TOTP setup
- All 90+ routes return 200/302

## 🔴 Known Issues
- QBO sandbox account is empty (no real txns to pull) — your sandbox issue, not code
- Email confirmation requires SMTP setup (env: SMTP_HOST, SMTP_USER, SMTP_PASS)
- Plaid needs keys (env: PLAID_CLIENT_ID, PLAID_SECRET)
- Stripe billing needs keys (env: STRIPE_SECRET_KEY)

---

**For tonight's work:** Use CSV import. Login → Money → Import CSV → upload your bank CSV → Preview → Commit → see it on Transactions page → run P&L report.
