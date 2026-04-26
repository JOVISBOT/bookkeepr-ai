# BookKeepr AI - Technical Specification Summary
## From PDF Document Received 2026-04-24

---

## 1. PRODUCT OVERVIEW

**Multi-tenant, AI-powered bookkeeping SaaS** that autonomously classifies, reconciles, and reports financial transactions for multiple clients from a single operator dashboard.

**Replicates and extends QuickBooks functionality.**

---

## 2. SERVICE TIERS (What User Wants!)

| Tier | Name | AI Role | Human Involvement |
|------|------|---------|-------------------|
| **1** | Self-Serve AI | Client + AI fully autonomous | None (errors only) |
| **2** | Assisted AI + Operator | Auto-classify, flags edge cases | Operator reviews exceptions |
| **3** | Done-For-You | Drafts classifications | Operator reviews, approves, delivers |

**Current Implementation:** We have Tier 2 (Assisted) - AI categorizes, human reviews

---

## 3. TECH STACK (Their Recommendation vs Ours)

| Layer | Their Stack | Our Stack | Gap |
|-------|------------|-----------|-----|
| Backend | FastAPI | Flask | Minor |
| Frontend | React + Tailwind | HTML/CSS/JS | Medium |
| Database | PostgreSQL | SQLite | Major (multi-tenancy) |
| Cache/Queue | Redis + Celery | None | Major |
| AI | OpenAI/Claude API | scikit-learn | Major (LLM vs ML) |
| Bank | Plaid/MX/Finicity | Plaid | Minor |
| QuickBooks | QBO API | OAuth built | None |
| Auth | Auth0/Supabase | Flask-Login | Major |
| File Storage | AWS S3 | Local | Major |
| Email | SendGrid/Resend | None | Major |
| Hosting | AWS/Railway | Localhost | Major |

---

## 4. CORE MODULES WE NEED

### 4.1 Multi-Tenant Architecture
- [ ] Each client = isolated tenant
- [ ] Operator = superadmin across all tenants
- [ ] RBAC: operator/client/viewer
- [ ] Subdomain routing: client1.bookkeepr.app

### 4.2 Transaction Engine (PARTIALLY DONE)
- [x] Ingest from bank feeds (Plaid)
- [ ] CSV uploads with auto-mapping
- [ ] PDF uploads with OCR
- [x] Deduplicate on import
- [ ] Manual override with audit trail
- [ ] Reconciliation engine

### 4.3 AI Classification (MOSTLY DONE)
- [x] Auto-categorize by description/amount
- [x] Confidence scoring
- [ ] Low-confidence flagging for review
- [ ] Learn from corrections
- [ ] Custom rules per client

### 4.4 Bank & QuickBooks Integration (IN PROGRESS)
- [x] Plaid Link
- [ ] Nightly sync via Celery
- [ ] QuickBooks import/export
- [ ] Webhook support

### 4.5 CSV/PDF Import & Export (NEED TO BUILD)
- [ ] CSV upload with auto-detect columns
- [ ] PDF parsing with OCR (pdfplumber + Tesseract)
- [x] Export P&L as CSV
- [ ] Export as PDF
- [ ] Scheduled monthly reports via email

### 4.6 Reporting Engine (PARTIALLY DONE)
- [x] P&L report
- [x] Balance Sheet
- [ ] Cash Flow Statement
- [ ] A/R & A/P Aging
- [ ] Tax-ready summaries
- [ ] Custom date ranges

---

## 5. OPERATOR DASHBOARD (WHAT WE'RE BUILDING)

- [x] Client list with health status
- [x] Transaction ledger with AI classification
- [ ] Bulk classification actions
- [ ] Uncategorized queue
- [ ] Bank sync status panel
- [ ] Report generation panel
- [ ] Client tier management
- [ ] Notifications center
- [ ] Audit log
- [ ] Settings: Chart of Accounts, AI rules, email templates

---

## 6. CLIENT PORTAL (NEED TO BUILD)

- [ ] Dashboard: P&L summary, cash position
- [ ] Transaction feed with AI categories
- [ ] Flag transactions for review
- [ ] Report viewer (PDF downloads)
- [ ] Bank connection setup
- [ ] CSV upload
- [ ] Invoice/receipt upload
- [ ] Messaging with operator
- [ ] Onboarding wizard
- [ ] Mobile-responsive
- [ ] Isolated view (can't see other clients)

---

## 7. INTEGRATIONS NEEDED

- [x] Plaid (bank feeds)
- [ ] MX or Finicity (alternative banks)
- [x] QuickBooks Online (OAuth)
- [ ] QuickBooks Desktop (file export)
- [ ] Stripe (payouts & fees)
- [ ] PayPal (CSV/API)
- [ ] Square (transactions)
- [ ] Bank CSVs (Chase, BofA, Wells, etc.)
- [ ] PDF OCR (Tesseract)
- [ ] Email delivery (SendGrid/Resend)

---

## 8. SECURITY & COMPLIANCE (NEED TO BUILD)

- [ ] AES-256 encryption at rest
- [ ] TLS 1.3 in transit
- [ ] OAuth tokens only (no bank credentials stored)
- [ ] MFA mandatory for operator
- [ ] JWT tokens (short-lived)
- [ ] Row-level security in PostgreSQL
- [ ] SOC 2 readiness
- [ ] GDPR/CCPA compliance
- [ ] Rate limiting & IP allowlisting
- [ ] Daily backups with 30-day retention
- [ ] Penetration testing

---

## 9. DATABASE SCHEMA (NEED TO MIGRATE)

| Table | Status |
|-------|--------|
| tenants | ❌ Missing (need multi-tenancy) |
| users | ✅ Partial (need roles) |
| accounts | ✅ Basic (need Chart of Accounts) |
| bank_connections | ✅ Created today |
| transactions | ✅ Created |
| classifications | ❌ Missing |
| reports | ❌ Missing |
| audit_log | ❌ Missing |

---

## 10. BUILD PHASES

### Phase 1 — Foundation (Weeks 1-4)
- [x] Monorepo setup
- [x] PostgreSQL schema (we have SQLite)
- [ ] Auth with RBAC (we have basic auth)
- [ ] Operator dashboard (partially done)

### Phase 2 — AI & Import (Weeks 5-8)
- [x] AI classification (done!)
- [ ] CSV upload with auto-mapping
- [ ] PDF OCR parsing
- [ ] Learn from corrections

### Phase 3 — Bank & QuickBooks (Weeks 9-12)
- [x] Plaid integration (done!)
- [ ] QuickBooks sync
- [ ] Nightly bank sync
- [ ] Webhook alerts

### Phase 4 — Client Portal & Polish (Weeks 13-16)
- [ ] Client portal
- [ ] Report generation
- [ ] Email delivery
- [ ] Mobile responsive

---

## PRIORITY GAPS TO FILL NOW:

1. **Multi-tenancy** - Isolate clients
2. **Client portal** - Their own dashboard
3. **PDF reports** - Not just CSV
4. **Email delivery** - Automated reports
5. **Advanced reporting** - Cash flow, A/R, A/P
6. **Security** - MFA, encryption
7. **Database migration** - SQLite → PostgreSQL

---

## WHAT WE HAVE vs WHAT WE NEED:

**HAVE (✅):**
- Basic dashboard
- AI categorization (95%)
- Plaid bank integration
- QuickBooks OAuth
- CSV export
- Basic reports

**NEED (🔄):**
- Multi-tenant architecture
- Client portal
- PDF generation
- Email automation
- Advanced security
- PostgreSQL database
- Redis queue
- OCR for receipts
- Mobile app

---

**Recommendation:** Migrate to PostgreSQL + add client portal + PDF reports + email
