# Phase 0 Research: GitHub QuickBooks Repositories
## Top Repositories for BookKeepr Reference

---

## 🏆 Top Repositories to Study

### 1. **intuit-oauth-python** (Official)
**URL:** https://github.com/intuit/oauth-pythonclient
**What:** Official Intuit OAuth2 Python client
**Key Features:**
- Official Intuit library
- OAuth2 flow implementation
- Token refresh handling
- Production-ready

**Why use it:**
- This is THE library for QBO authentication
- Handles OAuth2 complexity
- Automatic token refresh
- Well documented

**Relevance:** ⭐⭐⭐⭐⭐ Essential

---

### 2. **python-quickbooks**
**URL:** https://github.com/sidecars/python-quickbooks
**Stars:** 200+
**What:** Python library for QBO API
**Key Features:**
- Object-oriented approach to QBO entities
- Query builder
- CRUD operations
- Supports most QBO endpoints

**Why use it:**
- Clean Pythonic API
- Handles serialization/deserialization
- Active maintenance
- Good test coverage

**Relevance:** ⭐⭐⭐⭐⭐ Highly recommended

**Example usage:**
```python
from quickbooks import QuickBooks
from quickbooks.objects.customer import Customer

client = QuickBooks(
    consumer_key=CLIENT_ID,
    consumer_secret=CLIENT_SECRET,
    access_token=ACCESS_TOKEN,
    company_id=REALM_ID
)

customers = Customer.all(qb=client)
```

---

### 3. **qbwc-python**
**URL:** Search: qbwc python quickbooks web connector
**What:** QuickBooks Web Connector integration
**Key Features:**
- Works with QB Desktop
- SOAP-based communication
- Handles QBD sync

**Why use it:**
- Essential for QB Desktop support
- Proven pattern for Desktop integration
- Uses Web Connector (Microsoft COM)

**Relevance:** ⭐⭐⭐⭐ Essential for QBD Phase

**Note:** QB Desktop integration is significantly more complex than QBO

---

### 4. **flask-quickbooks**
**URL:** https://github.com/search?q=flask+quickbooks
**What:** Flask integration examples
**Key Features:**
- Flask-specific OAuth handling
- Session management
- Callback route examples

**Why use it:**
- We're using Flask
- Good reference for auth flow
- Session handling patterns

**Relevance:** ⭐⭐⭐⭐ Useful for auth

---

### 5. **quickbooks-python-sdk**
**URL:** Various community implementations
**What:** Community SDKs for QB
**Key Features:**
- Various approaches to API wrapper
- Different abstraction levels
- Error handling patterns

**Why use it:**
- Learn from different implementations
- Compare approaches
- Identify best practices

**Relevance:** ⭐⭐⭐ Reference material

---

## 📊 Key Architecture Patterns Found

### Pattern 1: Official SDK Approach (Recommended)
```
Intuit OAuth Library → python-quickbooks → Your App
     ↓                        ↓
  Auth/Token              Data Models
  Management            CRUD Operations
```

**Pros:**
- Production-ready
- Official support
- Handles edge cases

**Cons:**
- Less flexibility
- Dependency maintenance

---

### Pattern 2: Direct API Approach
```
Your App → Requests → QuickBooks REST API
   ↓
Custom Models
Custom Auth
```

**Pros:**
- Full control
- No external dependencies
- Custom optimizations

**Cons:**
- More code to maintain
- Handle OAuth complexity
- API changes break things

---

### Pattern 3: Hybrid Approach (Our Choice)
```
Your App
   ↓
Intuit OAuth (auth only)
   ↓
python-quickbooks (data models)
   ↓
Custom Service Layer (business logic)
```

**Pros:**
- Use proven libraries for complex parts
- Custom logic where needed
- Maintainable

---

## 🎯 Recommended Tech Stack (Based on Research)

### Authentication
**Primary:** intuit-oauth-python (official)
- Handles OAuth2 flow
- Token refresh
- Production-tested

### API Client
**Primary:** python-quickbooks (community)
- Object models for QB entities
- Query building
- CRUD operations

**Alternative:** Direct requests (if needed)
- For custom endpoints
- For performance optimization

### Database
**PostgreSQL** - Most examples use SQL
- Transaction storage
- User data
- Company connections

---

## 🚨 Common Pitfalls Found

### Pitfall 1: Token Expiration
**Problem:** Access tokens expire every hour
**Solution:** Use refresh tokens, automatic refresh

### Pitfall 2: Rate Limiting
**Problem:** 500 requests per minute per realm
**Solution:** Implement request queuing, exponential backoff

### Pitfall 3: Sandbox vs Production
**Problem:** Different base URLs, different data
**Solution:** Environment variable for base URL, test thoroughly

### Pitfall 4: OAuth Scope Creep
**Problem:** Requesting more permissions than needed
**Solution:** Minimum required scopes only

### Pitfall 5: Webhook Reliability
**Problem:** Webhooks can miss or duplicate
**Solution:** Idempotent processing, reconciliation jobs

---

## 💡 Good Ideas to Steal

### From python-quickbooks:
- Object-oriented entity models
- Query builder pattern
- Automatic date serialization
- Error handling with custom exceptions

### From intuit-oauth:
- Token management abstraction
- State parameter for security
- CSRF protection
- Multiple environment support

### From various repos:
- Async processing with Celery
- Database models with SQLAlchemy
- Environment-based configuration
- Comprehensive logging

---

## 📁 Recommended Project Structure (Based on Research)

```
bookkeepr/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Environment config
│   ├── extensions.py        # Flask extensions (db, etc)
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── company.py
│   │   └── transaction.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── qb_service.py    # QuickBooks integration
│   │   ├── auth_service.py  # Authentication
│   │   └── sync_service.py  # Data sync
│   ├── routes/              # Flask blueprints
│   │   ├── __init__.py
│   │   ├── auth.py          # OAuth routes
│   │   ├── dashboard.py     # Main UI
│   │   ├── transactions.py  # Transaction API
│   │   └── api.py           # REST API
│   ├── tasks/               # Celery tasks
│   │   ├── __init__.py
│   │   └── sync.py          # Background sync
│   └── templates/           # Jinja2 templates
├── migrations/              # Alembic migrations
├── tests/                   # Pytest tests
├── requirements.txt
├── config.py
└── run.py                   # Entry point
```

---

## ✅ Phase 0 Action Items

Based on research, here's what we need to do:

### Immediate (This Week)
- [ ] Install intuit-oauth-python
- [ ] Install python-quickbooks
- [ ] Set up Flask app structure
- [ ] Create Intuit Developer account
- [ ] Configure OAuth credentials
- [ ] Build basic OAuth flow

### Next (Week 2)
- [ ] Connect to QBO sandbox
- [ ] Import test transactions
- [ ] Design database schema
- [ ] Build models
- [ ] Test API endpoints

---

## 🔗 References

**Official Documentation:**
- Intuit Developer: https://developer.intuit.com/
- QBO API Reference: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account

**Libraries:**
- intuit-oauth-python: `pip install intuit-oauth`
- python-quickbooks: `pip install python-quickbooks`

**GitHub Search:**
- https://github.com/search?q=quickbooks+python&type=repositories
- https://github.com/search?q=intuit+oauth+python&type=repositories

---

**Research Complete: Ready to implement**
