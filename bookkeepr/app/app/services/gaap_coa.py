"""
GAAP/AICPA Standard Chart of Accounts

Provides a full chart of accounts following GAAP numbering conventions:
  1000-1999  Assets
  2000-2999  Liabilities
  3000-3999  Equity
  4000-4999  Revenue
  5000-5999  Cost of Goods Sold
  6000-6999  Operating Expenses
  7000-7999  Other Income / Expense
  8000-8999  Tax Expense

Used to seed new companies and drive AI categorization lookups.
"""

GAAP_ACCOUNTS = [
    # ── ASSETS ──────────────────────────────────────────────────────────────
    {"number": "1000", "name": "Cash & Cash Equivalents",        "type": "Bank",                           "classification": "Asset",     "keywords": ["cash deposit", "cash withdrawal", "atm", "bank transfer", "online transfer", "online banking transfer", "wire transfer", "zelle", "venmo transfer", "cash app", "outgoing transfer", "incoming transfer", "transfer to", "transfer from", "internal transfer", "account transfer", "external transfer", "schoolsfirst", "credit union transfer", "savings transfer", "checking transfer"]},
    {"number": "1010", "name": "Petty Cash",                     "type": "Bank",                           "classification": "Asset",     "keywords": ["petty cash", "cash on hand"]},
    {"number": "1100", "name": "Accounts Receivable",            "type": "Accounts Receivable",            "classification": "Asset",     "keywords": ["accounts receivable", "a/r", "invoice outstanding"]},
    {"number": "1200", "name": "Inventory",                      "type": "Other Current Asset",            "classification": "Asset",     "keywords": ["inventory", "stock", "merchandise purchased"]},
    {"number": "1300", "name": "Prepaid Expenses",               "type": "Other Current Asset",            "classification": "Asset",     "keywords": ["prepaid", "prepayment", "deposit paid"]},
    {"number": "1400", "name": "Short-term Investments",         "type": "Other Current Asset",            "classification": "Asset",     "keywords": ["short-term investment", "treasury", "money market", "coinbase", "bitcoin", "ethereum", "crypto", "cryptocurrency", "robinhood", "webull", "td ameritrade", "etrade", "fidelity transfer", "schwab", "vanguard", "brokerage"]},
    {"number": "1500", "name": "Property, Plant & Equipment",    "type": "Fixed Asset",                    "classification": "Asset",     "keywords": []},
    {"number": "1510", "name": "Buildings",                      "type": "Fixed Asset",                    "classification": "Asset",     "keywords": ["building purchase", "property purchase", "real estate"]},
    {"number": "1520", "name": "Equipment",                      "type": "Fixed Asset",                    "classification": "Asset",     "keywords": ["equipment purchase", "machinery", "heavy equipment"]},
    {"number": "1530", "name": "Vehicles",                       "type": "Fixed Asset",                    "classification": "Asset",     "keywords": ["vehicle purchase", "truck", "car purchase", "auto purchase"]},
    {"number": "1540", "name": "Furniture & Fixtures",           "type": "Fixed Asset",                    "classification": "Asset",     "keywords": ["furniture", "desk", "chair", "shelving", "fixture"]},
    {"number": "1590", "name": "Accumulated Depreciation",       "type": "Fixed Asset",                    "classification": "Asset",     "keywords": ["depreciation"]},
    {"number": "1700", "name": "Intangible Assets",              "type": "Other Asset",                    "classification": "Asset",     "keywords": ["patent", "trademark", "copyright", "goodwill", "intangible"]},

    # ── LIABILITIES ─────────────────────────────────────────────────────────
    {"number": "2000", "name": "Accounts Payable",               "type": "Accounts Payable",               "classification": "Liability", "keywords": ["accounts payable", "a/p", "vendor payment", "bill payment", "bill pay"]},
    {"number": "2100", "name": "Accrued Liabilities",            "type": "Other Current Liability",        "classification": "Liability", "keywords": ["accrued expense", "accrued liability"]},
    {"number": "2200", "name": "Payroll Liabilities",            "type": "Other Current Liability",        "classification": "Liability", "keywords": ["payroll liability", "payroll tax payable", "employee withholding"]},
    {"number": "2300", "name": "Sales Tax Payable",              "type": "Other Current Liability",        "classification": "Liability", "keywords": ["sales tax payable", "sales tax collected", "vat payable"]},
    {"number": "2400", "name": "Credit Card Payable",            "type": "Credit Card",                    "classification": "Liability", "keywords": ["credit card payment", "visa payment", "mastercard payment", "amex payment", "capital one mobile pmt", "capital one payment", "capital one", "credit one bank", "chase credit card", "citi payment", "discover payment", "synchrony bank", "barclays payment", "bank of america card", "wells fargo card", "credit card pmt", "card payment", "cc payment", "buy now pay later", "klarna", "afterpay", "affirm", "sezzle", "zip pay", "bnpl"]},
    {"number": "2500", "name": "Short-term Notes Payable",       "type": "Other Current Liability",        "classification": "Liability", "keywords": ["short-term loan", "line of credit", "revolving credit", "note payable", "personal loan payment", "consumer loan"]},
    {"number": "2600", "name": "Long-term Debt",                 "type": "Long Term Liability",            "classification": "Liability", "keywords": ["long-term loan", "mortgage", "sba loan", "term loan payment", "bank loan", "student ln", "student loan", "dept education", "dept of education", "navient", "fedloan", "sallie mae", "nelnet", "great lakes loan", "loan payment", "edu loan", "education loan"]},
    {"number": "2700", "name": "Deferred Revenue",               "type": "Other Current Liability",        "classification": "Liability", "keywords": ["deferred revenue", "unearned revenue", "advance payment received"]},

    # ── EQUITY ──────────────────────────────────────────────────────────────
    {"number": "3000", "name": "Owner's Equity",                 "type": "Equity",                         "classification": "Equity",    "keywords": []},
    {"number": "3100", "name": "Common Stock / Paid-in Capital", "type": "Equity",                         "classification": "Equity",    "keywords": ["stock issuance", "capital contribution", "paid-in capital"]},
    {"number": "3200", "name": "Retained Earnings",              "type": "Retained Earnings",              "classification": "Equity",    "keywords": ["retained earnings"]},
    {"number": "3300", "name": "Owner's Draw / Distributions",   "type": "Equity",                         "classification": "Equity",    "keywords": ["owner draw", "owner distribution", "shareholder distribution", "dividend paid"]},

    # ── REVENUE ─────────────────────────────────────────────────────────────
    {"number": "4000", "name": "Service Revenue",                "type": "Service/Fee Income",             "classification": "Revenue",   "keywords": ["service fee", "consulting fee", "retainer", "professional services income", "fee income", "service income", "client payment", "invoice payment", "payment received", "contract payment", "direct deposit", "payroll income", "paycheck", "employer deposit", "salary deposit", "ach deposit", "direct dep", "payroll deposit"]},
    {"number": "4100", "name": "Product Sales Revenue",          "type": "Sales of Product Income",        "classification": "Revenue",   "keywords": ["product sale", "merchandise sale", "goods sold", "shopify", "square", "stripe payment", "retail sale", "online sale", "ecommerce"]},
    {"number": "4200", "name": "Interest Income",                "type": "Other Income",                   "classification": "Revenue",   "keywords": ["interest earned", "interest income", "dividend received", "investment income", "savings interest"]},
    {"number": "4300", "name": "Other Income",                   "type": "Other Income",                   "classification": "Revenue",   "keywords": ["miscellaneous income", "other income", "refund received", "rebate received", "grant income"]},
    {"number": "4400", "name": "Rental Income",                  "type": "Other Income",                   "classification": "Revenue",   "keywords": ["rental income", "rent received", "sublease income", "airbnb income", "lease income"]},

    # ── COST OF GOODS SOLD ───────────────────────────────────────────────────
    {"number": "5000", "name": "Cost of Goods Sold",             "type": "Cost of Goods Sold",             "classification": "Expense",   "keywords": ["cost of goods", "cogs", "product cost", "inventory cost", "wholesale purchase", "raw material"]},
    {"number": "5100", "name": "Direct Labor - COGS",            "type": "Cost of Labor",                  "classification": "Expense",   "keywords": ["direct labor", "production labor", "manufacturing labor"]},
    {"number": "5200", "name": "Freight & Shipping - COGS",      "type": "Cost of Goods Sold",             "classification": "Expense",   "keywords": ["freight in", "shipping in", "import cost", "customs duty"]},

    # ── OPERATING EXPENSES ───────────────────────────────────────────────────
    {"number": "6000", "name": "Advertising & Marketing",        "type": "Advertising/Promotional",        "classification": "Expense",   "keywords": ["google ads", "facebook ads", "meta ads", "instagram ads", "twitter ads", "linkedin ads", "tiktok ads", "advertising", "marketing", "mailchimp", "constant contact", "hubspot", "hootsuite", "canva", "sprout social", "semrush", "ahrefs", "promotion", "campaign", "billboard", "radio ad", "print ad", "marketing agency", "pr firm"]},
    {"number": "6100", "name": "Bank Charges & Fees",            "type": "Bank Charges",                   "classification": "Expense",   "keywords": ["bank fee", "service charge", "wire fee", "ach fee", "overdraft fee", "monthly maintenance fee", "account fee", "transfer fee", "stripe fee", "paypal fee", "square fee", "processing fee", "merchant fee", "transaction fee", "payment processing"]},
    {"number": "6200", "name": "Depreciation Expense",           "type": "Depreciation",                   "classification": "Expense",   "keywords": ["depreciation expense", "amortization expense"]},
    {"number": "6300", "name": "Insurance Expense",              "type": "Insurance",                      "classification": "Expense",   "keywords": ["insurance", "geico", "allstate", "state farm", "progressive", "nationwide", "farmers insurance", "liability insurance", "general liability", "workers compensation", "workers comp", "health insurance", "dental insurance", "vision insurance", "aetna", "cigna", "united health", "blue cross", "humana", "property insurance", "auto insurance premium", "commercial insurance", "e&o insurance", "professional liability"]},
    {"number": "6400", "name": "Meals & Entertainment",          "type": "Entertainment Meals",            "classification": "Expense",   "keywords": ["restaurant", "starbucks", "coffee", "doordash", "uber eats", "grubhub", "door dash", "seamless", "chipotle", "mcdonald", "wendys", "subway", "chick-fil-a", "panera", "catering", "client lunch", "client dinner", "business meal", "entertainment", "team lunch", "team dinner", "dine", "bar tab"]},
    {"number": "6500", "name": "Office Supplies & Expenses",     "type": "Office/General Administrative",  "classification": "Expense",   "keywords": ["staples", "office depot", "officemax", "office supply", "paper", "printer ink", "toner", "pens", "notebooks", "folders", "binders", "postage", "stamps", "fedex", "ups", "usps", "mailing", "shipping supplies", "amazon office"]},
    {"number": "6600", "name": "Payroll - Salaries & Wages",     "type": "Payroll Expenses",               "classification": "Expense",   "keywords": ["payroll", "adp payroll", "gusto payroll", "paychex", "salary", "wages", "direct deposit payroll", "biweekly payroll", "weekly payroll", "employee payroll", "w-2 payment", "payroll processing", "payroll service", "payroll tax serv", "tax serv payroll", "alvarez tax"]},
    {"number": "6610", "name": "Payroll - Employer Taxes",       "type": "Payroll Expenses",               "classification": "Expense",   "keywords": ["payroll tax", "fica", "employer fica", "social security tax", "medicare tax", "federal unemployment", "futa", "state unemployment", "suta", "941 payment"]},
    {"number": "6620", "name": "Employee Benefits",              "type": "Payroll Expenses",               "classification": "Expense",   "keywords": ["health benefit", "employee benefit", "401k contribution", "retirement contribution", "profit sharing", "fsa contribution", "hsa contribution", "cobra payment", "group life insurance", "employee life insurance"]},
    {"number": "6700", "name": "Legal Fees",                     "type": "Legal & Professional Fees",      "classification": "Expense",   "keywords": ["attorney", "law firm", "lawyer", "legal fee", "court filing", "notary", "litigation", "contract review", "legalzoom", "rocket lawyer"]},
    {"number": "6710", "name": "Accounting & Bookkeeping Fees",  "type": "Legal & Professional Fees",      "classification": "Expense",   "keywords": ["accountant fee", "cpa fee", "bookkeeper fee", "tax preparation", "tax prep fee", "accounting service", "bookkeeping service", "audit fee", "tax return", "tax filing"]},
    {"number": "6720", "name": "Consulting Fees",                "type": "Legal & Professional Fees",      "classification": "Expense",   "keywords": ["consultant fee", "consulting fee", "advisor fee", "freelancer", "independent contractor payment", "1099 contractor", "upwork", "fiverr", "toptal", "contract labor"]},
    {"number": "6800", "name": "Rent & Lease Expense",           "type": "Rent or Lease",                  "classification": "Expense",   "keywords": ["rent payment", "office rent", "building lease", "lease payment", "property management", "landlord payment", "coworking space", "wework", "regus", "iwork", "shared office", "studio rent", "storage unit"]},
    {"number": "6900", "name": "Repairs & Maintenance",          "type": "Repairs & Maintenance",          "classification": "Expense",   "keywords": ["repair", "maintenance", "plumber", "electrician", "hvac repair", "cleaning service", "janitorial", "pest control", "handyman", "service contract", "building maintenance", "equipment repair", "it support"]},
    {"number": "6950", "name": "Software & Technology",          "type": "Computer and Internet Expenses", "classification": "Expense",   "keywords": ["aws", "amazon web services", "azure", "google cloud", "google workspace", "github", "slack", "zoom", "microsoft 365", "office 365", "adobe creative", "salesforce", "hubspot crm", "quickbooks subscription", "xero", "software license", "app subscription", "saas", "digital ocean", "heroku", "netlify", "cloudflare", "godaddy"]},
    {"number": "6960", "name": "Subscriptions & Dues",           "type": "Other Business Expenses",        "classification": "Expense",   "keywords": ["subscription", "annual membership", "dues", "trade association", "professional membership", "chamber of commerce", "linkedin premium", "netflix business", "spotify business", "recurring payment", "recurring charge", "autopay", "auto-pay", "monthly charge", "auto payment", "recurring authorized", "authorized recurring"]},
    {"number": "6970", "name": "Telephone & Internet",           "type": "Utilities",                      "classification": "Expense",   "keywords": ["at&t", "verizon", "t-mobile", "sprint", "comcast", "xfinity", "spectrum", "cox", "century link", "phone bill", "cell phone bill", "internet service", "broadband", "business phone", "voip"]},
    {"number": "6980", "name": "Travel Expense",                 "type": "Travel",                         "classification": "Expense",   "keywords": ["airline", "delta airlines", "united airlines", "american airlines", "southwest airlines", "jetblue", "spirit airlines", "hotel", "marriott", "hilton", "hyatt", "sheraton", "westin", "airbnb", "booking.com", "expedia", "hotels.com", "flight", "train ticket", "amtrak", "parking fee", "taxi", "lyft", "uber trip", "car rental", "hertz", "enterprise car", "avis", "budget rent"]},
    {"number": "6990", "name": "Utilities",                      "type": "Utilities",                      "classification": "Expense",   "keywords": ["electric bill", "electricity", "gas utility", "natural gas", "water bill", "sewage", "pacific gas", "con edison", "pge", "duke energy", "dominion energy", "sce", "utility payment", "trash service"]},
    {"number": "6995", "name": "Vehicle Expense",                "type": "Vehicle",                        "classification": "Expense",   "keywords": ["gas station", "fuel", "shell", "chevron", "bp", "exxon", "mobil", "speedway", "auto insurance", "car wash", "auto repair", "oil change", "jiffy lube", "midas", "muffler", "tires", "goodyear", "firestone", "vehicle registration", "dmv", "toll"]},
    {"number": "6998", "name": "Taxes & Licenses",               "type": "Taxes & Licenses",               "classification": "Expense",   "keywords": ["business license", "permit fee", "vehicle registration tax", "franchise tax", "excise tax", "property tax payment", "city tax", "county tax", "state tax payment", "tax deposit", "941 deposit", "irs payment"]},
    {"number": "6999", "name": "Miscellaneous Expense",          "type": "Other Miscellaneous Service Cost","classification": "Expense",   "keywords": ["miscellaneous", "misc expense", "petty cash expense", "charitable donation", "nonprofit donation", "gift card", "employee gift", "flowers", "holiday party"]},

    # ── OTHER INCOME / EXPENSE ───────────────────────────────────────────────
    {"number": "7000", "name": "Interest Expense",               "type": "Interest Paid",                  "classification": "Expense",   "keywords": ["interest payment", "loan interest", "credit card interest", "finance charge", "interest charged", "mortgage interest"]},
    {"number": "7100", "name": "Loss on Sale of Assets",         "type": "Other Expense",                  "classification": "Expense",   "keywords": ["loss on sale", "asset disposal", "write-off"]},
    {"number": "7200", "name": "Foreign Exchange Loss/Gain",     "type": "Other Expense",                  "classification": "Expense",   "keywords": ["foreign exchange", "fx loss", "currency conversion", "exchange rate"]},

    # ── TAX EXPENSE ─────────────────────────────────────────────────────────
    {"number": "8000", "name": "Federal Income Tax Expense",     "type": "Income Tax Expense",             "classification": "Expense",   "keywords": ["federal income tax", "irs tax payment", "estimated tax", "quarterly tax", "corporate income tax"]},
    {"number": "8100", "name": "State Income Tax Expense",       "type": "Income Tax Expense",             "classification": "Expense",   "keywords": ["state income tax", "state tax payment", "state estimated tax"]},
]


def get_gaap_accounts():
    """Return the full GAAP chart of accounts list."""
    return GAAP_ACCOUNTS


def seed_gaap_accounts(company_id: int) -> dict:
    """
    Seed GAAP-compliant chart of accounts into the given company.
    Skips accounts that already exist (idempotent).
    Returns counts of created vs skipped.
    """
    from extensions import db
    from app.models.account import Account

    created = 0
    skipped = 0

    for acct in GAAP_ACCOUNTS:
        exists = Account.query.filter_by(
            company_id=company_id,
            account_number=acct["number"]
        ).first()
        if exists:
            skipped += 1
            continue

        new_account = Account(
            company_id=company_id,
            qbo_account_id=f"gaap-{acct['number']}",
            name=acct["name"],
            account_type=acct["type"],
            account_sub_type=acct["type"],
            classification=acct["classification"],
            account_number=acct["number"],
            description=f"GAAP standard account {acct['number']}",
            is_active=True,
            current_balance=0,
        )
        db.session.add(new_account)
        created += 1

    db.session.commit()
    return {"created": created, "skipped": skipped, "total": len(GAAP_ACCOUNTS)}


def categorize_by_gaap(description: str, vendor: str, amount: float) -> dict:
    """
    Rule-based GAAP categorization using keyword matching.
    Returns best matching account with confidence score.

    Confidence tiers:
      >= 80  → HIGH   (auto-approve)
      50-79  → MEDIUM (suggest, human review)
      < 50   → LOW    (flag for manual entry)
    """
    combined = f"{description} {vendor}".lower()
    best_match = None
    best_score = 0
    best_hits = 0

    for acct in GAAP_ACCOUNTS:
        if not acct["keywords"]:
            continue
        hits = 0
        for kw in acct["keywords"]:
            if kw in combined:
                # Multi-word phrases score higher than single words
                word_count = len(kw.split())
                hits += word_count
        if hits == 0:
            continue
        # Score: base 60 + 5 per word hit, cap at 96
        score = min(96, 60 + (hits - 1) * 5)
        if score > best_score:
            best_score = score
            best_match = acct
            best_hits = hits

    if best_match:
        # Build a human-readable explanation of why this category was chosen
        matched_kws = [kw for kw in best_match["keywords"] if kw in combined]
        if matched_kws:
            kw_sample = '", "'.join(matched_kws[:3])
            explanation = f'Matched "{kw_sample}" → {best_match["name"]} (GAAP {best_match["number"]})'
        else:
            explanation = f'Categorized as {best_match["name"]} (GAAP {best_match["number"]})'
        return {
            "account_number": best_match["number"],
            "account_name": best_match["name"],
            "account_type": best_match["type"],
            "classification": best_match["classification"],
            "confidence": best_score,
            "keyword_hits": best_hits,
            "explanation": explanation,
        }

    # Fallback: classify by amount sign
    if amount and float(amount) > 0:
        fallback = next(a for a in GAAP_ACCOUNTS if a["number"] == "4000")
        return {
            "account_number": "4000",
            "account_name": fallback["name"],
            "account_type": fallback["type"],
            "classification": "Revenue",
            "confidence": 35,
            "keyword_hits": 0,
        }
    else:
        fallback = next(a for a in GAAP_ACCOUNTS if a["number"] == "6999")
        return {
            "account_number": "6999",
            "account_name": fallback["name"],
            "account_type": fallback["type"],
            "classification": "Expense",
            "confidence": 30,
            "keyword_hits": 0,
        }
