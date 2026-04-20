# Phase 1: Setup Guide

## Step 1: Create Intuit Developer Account

### Instructions:

1. Go to: https://developer.intuit.com/
2. Click "Sign Up" (use your existing Intuit account or create new)
3. Complete developer profile
4. Verify email

### Create App:

1. Go to Dashboard → Create App
2. Select "QuickBooks Online"
3. App Name: "BookKeepr AI" (or your preferred name)
4. Select scopes:
   - `com.intuit.quickbooks.accounting` (read/write accounting data)
   - `openid` (user info)
   - `profile` (user profile)
   - `email` (user email)

### Get Credentials:

After creating app, you'll receive:
- **Client ID:** (copy this)
- **Client Secret:** (copy this - keep secure!)
- **Realm ID:** (test company ID from sandbox)

### Add Redirect URI:

1. Go to App Settings → Redirect URIs
2. Add: `http://localhost:5000/auth/callback`
3. For production later: `https://yourdomain.com/auth/callback`

---

## Step 2: Install Dependencies

```bash
# In bookkeepr/ directory
pip install intuit-oauth python-quickbooks flask sqlalchemy psycopg2-binary
```

Or add to requirements.txt:
```
intuit-oauth==1.2.4
python-quickbooks==0.9.10
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
psycopg2-binary==2.9.9
python-dotenv==1.0.1
```

---

## Step 3: Environment Configuration

Create `.env` file in `bookkeepr/`:

```bash
# Intuit OAuth
INTUIT_CLIENT_ID=your_client_id_here
INTUIT_CLIENT_SECRET=your_client_secret_here
INTUIT_REDIRECT_URI=http://localhost:5000/auth/callback
INTUIT_ENVIRONMENT=sandbox  # sandbox or production

# Database
DATABASE_URL=postgresql://user:password@localhost/bookkeepr

# Flask
FLASK_SECRET_KEY=your_random_secret_key_here
FLASK_ENV=development
```

---

## Step 4: Test OAuth Flow

After setup, run:

```bash
python run.py
```

Then visit: http://localhost:5000/auth/connect

Expected flow:
1. Redirect to Intuit login
2. User grants permissions
3. Redirect back to callback
4. Tokens saved to database

---

## Checkpoint Questions:

1. Did you create Intuit Developer account? [ ] Yes
2. Did you create an app? [ ] Yes
3. Do you have Client ID and Secret? [ ] Yes
4. Did you add redirect URI? [ ] Yes
5. Can you run Flask app? [ ] Yes

**Report back when checkpoint is complete.**
