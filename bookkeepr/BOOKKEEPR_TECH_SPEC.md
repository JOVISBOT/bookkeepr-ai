# BookKeepr AI - Full Technical Specification
_From PDF: Boookkeepr_AI_Technical_Spec.pdf (4/24/2026)_

=== PAGE 1 ===
Boookkeepr AI
Full Technical Specification — Autonomous Bookkeeping Platform
1. PRODUCT OVERVIEW
Boookkeepr AI is a multi-tenant, AI-powered bookkeeping SaaS platform designed to autonomously classify, reconcile, and
report financial transactions for multiple clients from a single operator dashboard. It replicates and extends QuickBooks
functionality with autonomous AI transaction classification, bank feed integration, CSV/PDF import, and a full client-facing
portal — all accessible via web from any device.
2. SERVICE TIERS
TIER
NAME
WHO DOES THE WORK
AI ROLE
HUMAN INVOLVEMENT
1
Self-Serve AI
Client + AI fully autonomous
Full auto-classify, full automation
None (errors only)
2
Assisted
AI + Operator consults
Auto-classify, flags edge cases
Operator reviews exceptions & advises
3
Done-For-You
Operator does everything
Drafts classifications
Operator reviews, approves, delivers
3. RECOMMENDED TECH STACK
LAYER
TECHNOLOGY
PURPOSE
Backend API
Python / FastAPI
REST API, background jobs, AI orchestration
Frontend (Operator)
React + TailwindCSS
Operator dashboard — client management, reports
Frontend (Client)
React + TailwindCSS
Client portal — their own bookkeeping dashboard
Database
PostgreSQL
Core data: transactions, clients, classifications
Cache / Queue
Redis + Celery
Background jobs, bank sync, PDF generation
AI Classification
OpenAI / Claude API
Auto-categorize transactions by description/amount
Bank Integration
Plaid or MX API
Connect client bank accounts, pull transactions
QuickBooks Sync
QuickBooks Online API
Import/export client QBO data
Auth
Auth0 or Supabase Auth
Multi-tenant user auth with role-based access
File Storage
AWS S3 / Cloudflare R2
Store PDFs, CSV exports, receipts
Email/Notif
SendGrid / Resend
Client alerts, report delivery
Hosting
AWS / Railway / Render
Scalable cloud deployment

=== PAGE 2 ===
Local Dev / Self-Host
Docker + Docker Compose
Run full stack locally or on your own server
4. BACKEND — CORE MODULES
4.1 Multi-Tenant Architecture
 Each client is an isolated tenant with their own data partition
 Operator account has superadmin access across all tenants
 Role-Based Access Control (RBAC): operator / client / viewer roles
 Subdomain routing per client: client1.bookkeepr.app
4.2 Transaction Engine
 Ingest transactions from bank feeds (Plaid), CSV uploads, or QuickBooks API
 Deduplicate transactions automatically on import
 Store raw + classified versions of every transaction
 Support manual override of AI classification with audit trail
 Reconciliation engine to match bank vs. books
4.3 AI Classification Module
 Send transaction description + amount + merchant to LLM (Claude/OpenAI)
 Map to standard Chart of Accounts categories (income, expense, asset, liability)
 Confidence scoring — low-confidence txns flagged for human review
 Learn from operator corrections to improve accuracy over time (fine-tune or few-shot)
 Support for custom classification rules per client
4.4 Bank & QuickBooks Integration
 Plaid Link — client connects bank accounts via secure OAuth flow
 Automatic nightly bank feed sync via Celery scheduled task
 QuickBooks Online API — import Chart of Accounts, existing transactions, customers, vendors
 Export classified books back to QuickBooks or as QBO-compatible file
 Webhook support for real-time bank transaction alerts
4.5 CSV / PDF Import & Export
 Upload bank CSV statements — auto-detect column mapping (date, amount, description)
 Parse PDF bank statements using OCR (pdfplumber + Tesseract)
 Export: P&L; report, Balance Sheet, Transaction Ledger as PDF or CSV
 Schedule automated monthly report generation and email delivery
4.6 Reporting Engine
 Profit & Loss (P&L;) — monthly, quarterly, annual
 Balance Sheet — assets, liabilities, equity

=== PAGE 3 ===
 Cash Flow Statement
 Accounts Receivable / Payable Aging
 Tax-ready summary reports by category
 Custom date range filtering
5. OPERATOR DASHBOARD (Your Interface)
 Client list with health status — green/yellow/red based on sync status & uncategorized count
 Per-client transaction ledger with AI classification + ability to override any entry
 Bulk classification actions — approve all AI suggestions, reassign categories in bulk
 Uncategorized queue — items needing manual review surfaced at top
 Bank sync status panel — last synced, errors, pending imports per client
 Report generation panel — generate and send reports per client with one click
 Client tier management — assign, upgrade or downgrade service tiers
 Notifications center — alerts for sync failures, low-confidence txns, client activity
 Audit log — full history of every classification change with who changed it and when
 Settings: manage Chart of Accounts templates, AI classification rules, email templates
6. CLIENT PORTAL (Their Interface)
 Dashboard: monthly P&L; summary, cash position, recent transactions
 Transaction feed — view all transactions, see AI category assigned
 Client can flag transactions or leave notes for operator review
 Report viewer — download PDF reports (only reports the operator has shared)
 Bank connection setup — Plaid Link widget for connecting accounts
 CSV upload — manual upload of bank statements if no direct feed
 Invoice & receipt upload (Tier 2 and 3)
 Messaging panel — direct communication with operator (Tier 2 and 3)
 Onboarding wizard — step-by-step setup: bank connect, QBO import, or CSV upload
 Mobile-responsive — full access from phone or tablet
 Cannot see other clients — fully isolated view
7. INTEGRATIONS CHECKLIST
Bank Feeds
Plaid (US banks), MX, or Finicity — OAuth, read-only transaction access
QuickBooks Online
OAuth 2.0 API — import/export Chart of Accounts, transactions, customers
QuickBooks Desktop
IIF or QBO file export for desktop users (no live API)
Stripe
Pull Stripe payouts and fees as income/expense transactions automatically
PayPal
Import PayPal transaction history via CSV or API
Square
Square Transactions API — pull sales, fees, refunds

=== PAGE 4 ===
Bank CSVs
Parser for major US bank statement CSV formats (Chase, BofA, Wells, etc.)
PDF Statements
OCR-based PDF parser for scanned or digital bank statements
Email Delivery
SendGrid / Resend for report delivery, alerts, client invites
Calendar / Deadlines
Google Calendar integration for tax deadline reminders (optional)
8. SECURITY & COMPLIANCE
 All data encrypted at rest (AES-256) and in transit (TLS 1.3)
 Bank credentials never stored — OAuth tokens only (read-only scope via Plaid)
 Multi-Factor Authentication (MFA) mandatory for operator account
 Session management with JWT access tokens (short-lived) + refresh tokens
 Row-level security in PostgreSQL — tenants cannot access each other's data
 SOC 2 readiness checklist — audit logs, access controls, incident response plan
 GDPR/CCPA compliance — data deletion on client offboarding
 Rate limiting and IP allowlisting for operator dashboard
 Regular automated backups — daily snapshots with 30-day retention
 Penetration testing before public launch
9. DATABASE SCHEMA (Core Tables)
TABLE
KEY COLUMNS
tenants
id, name, plan_tier, created_at, status
users
id, tenant_id, role (operator/client), email, mfa_enabled
accounts
id, tenant_id, name, type (asset/liability/income/expense/equity), parent_id
bank_connections
id, tenant_id, plaid_item_id, institution_name, last_sync_at, status
transactions
id, tenant_id, bank_connection_id, date, amount, description, raw_category
classifications
id, transaction_id, account_id, confidence, classified_by (ai/human), created_at
reports
id, tenant_id, report_type, period_start, period_end, file_url, created_at
audit_log
id, tenant_id, user_id, action, target_table, target_id, old_value, new_value, timestamp
10. BUILD PHASES — RECOMMENDED ROADMAP
Phase 1 — Foundation (Weeks 1–4)
✓ Set up monorepo: FastAPI backend + React frontend
✓ PostgreSQL schema: tenants, users, transactions, classifications
✓ Auth: login, RBAC (operator/client roles), MFA for operator
✓ Operator dashboard: client list, add client, basic transaction view

=== PAGE 5 ===
✓ CSV upload + parser (manual transaction import)
✓ Basic AI classification via OpenAI/Claude API
✓ Docker Compose setup for local development
Phase 2 — Bank & QBO Integration (Weeks 5–8)
✓ Plaid Link integration: client connects bank accounts
✓ Nightly bank sync job (Celery + Redis)
✓ QuickBooks Online OAuth import: Chart of Accounts + transactions
✓ Deduplication engine
✓ Client portal: dashboard, transaction feed, bank connect wizard
✓ PDF statement OCR parser
Phase 3 — Automation & Reporting (Weeks 9–12)
✓ Confidence scoring on AI classifications
✓ Uncategorized queue + bulk approval in operator dashboard
✓ Reporting engine: P&L;, Balance Sheet, Cash Flow
✓ Scheduled report generation + email delivery
✓ QBO export (classified transactions back to QuickBooks)
✓ Audit log
Phase 4 — Polish & Launch (Weeks 13–16)
✓ Tier billing integration (Stripe subscriptions)
✓ Mobile-responsive client portal
✓ Security hardening: rate limiting, pen test, backup automation
✓ Onboarding wizard for new clients
✓ Multi-client stress testing
✓ Production deployment (AWS or Railway)
11. DEPLOYMENT & SELF-HOSTING
 Docker Compose: run entire stack locally (API, frontend, Postgres, Redis) — great for dev and personal use
 Production: deploy backend to Railway, Render, or AWS ECS (Fargate)
 Frontend: deploy React app to Vercel or Cloudflare Pages
 Database: managed PostgreSQL via Railway, Supabase, or AWS RDS
 Custom domain + SSL certificate (Let's Encrypt via Caddy or AWS ACM)
 CI/CD pipeline: GitHub Actions — auto-deploy on push to main
 Environment variables managed via .env (local) and secrets manager (production)
 Monitoring: Sentry (errors), Uptime Robot (availability), Grafana (optional metrics)
 Access from anywhere via web browser — no local software required for operator
 Boookkeepr AI — Technical Specification v1.0 | Confidential | Built for autonomous multi-client bookkeeping
 