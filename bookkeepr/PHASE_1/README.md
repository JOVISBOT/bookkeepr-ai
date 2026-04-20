# Phase 1: QuickBooks Online Integration

## Overview
Build OAuth 2.0 authentication and connect to QuickBooks Online sandbox.

## Duration
**2-3 weeks**

## Objectives
- [ ] OAuth 2.0 authentication flow
- [ ] Company info retrieval
- [ ] Chart of accounts import
- [ ] Transaction data import (bank feeds, credit cards)
- [ ] Basic CRUD operations

## Key Deliverables
1. Intuit Developer account created
2. OAuth app registered
3. Working OAuth flow (connect/disconnect)
4. Company data sync working
5. Transaction import pipeline

## Technical Stack
- **Auth:** intuit-oauth-python
- **API:** python-quickbooks
- **Database:** PostgreSQL (SQLAlchemy)
- **Framework:** Flask

## Reference
- [Intuit Developer Portal](https://developer.intuit.com/)
- [QBO API Reference](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account)
- [GitHub Repos](https://github.com/search?q=quickbooks&type=repositories)

## Phase Gate Criteria
Before moving to Phase 2, must have:
- [ ] QBO connection working
- [ ] Can import transactions
- [ ] Data persistence tested

---

**Status:** 🟡 In Progress
**Started:** 2026-04-18
