"""
Common vendor → GAAP category seeds.

These are pre-approved mappings for well-known vendors so the classifier
works accurately from day one, before any user-approved transactions exist.

Stored as synthetic Transaction rows (categorized_by='seed', review_status='approved')
so the local_classifier's vendor_history tier picks them up immediately.
"""
from __future__ import annotations
import logging
from datetime import date

logger = logging.getLogger(__name__)

# (vendor_name, category, transaction_type)
# category is the friendly GAAP name — no number prefix shown to users
VENDOR_SEEDS = [
    # ── Software & Subscriptions ─────────────────────────────────────────────
    ("Google Workspace",        "Software & Technology",        "Purchase"),
    ("Microsoft 365",           "Software & Technology",        "Purchase"),
    ("Microsoft Office",        "Software & Technology",        "Purchase"),
    ("Adobe Creative Cloud",    "Software & Technology",        "Purchase"),
    ("Slack",                   "Software & Technology",        "Purchase"),
    ("Zoom",                    "Software & Technology",        "Purchase"),
    ("Dropbox",                 "Software & Technology",        "Purchase"),
    ("GitHub",                  "Software & Technology",        "Purchase"),
    ("AWS",                     "Software & Technology",        "Purchase"),
    ("Amazon Web Services",     "Software & Technology",        "Purchase"),
    ("Google Cloud",            "Software & Technology",        "Purchase"),
    ("Cloudflare",              "Software & Technology",        "Purchase"),
    ("Notion",                  "Software & Technology",        "Purchase"),
    ("Asana",                   "Software & Technology",        "Purchase"),
    ("HubSpot",                 "Advertising & Marketing",      "Purchase"),
    ("Salesforce",              "Software & Technology",        "Purchase"),
    ("QuickBooks",              "Accounting & Bookkeeping Fees","Purchase"),
    ("Gusto",                   "Payroll - Salaries & Wages",   "Purchase"),
    ("ADP",                     "Payroll - Salaries & Wages",   "Purchase"),
    ("Paychex",                 "Payroll - Salaries & Wages",   "Purchase"),
    ("Stripe",                  "Bank Charges & Fees",          "Purchase"),
    ("PayPal",                  "Bank Charges & Fees",          "Purchase"),
    ("Square",                  "Bank Charges & Fees",          "Purchase"),
    ("Shopify",                 "Software & Technology",        "Purchase"),
    ("Mailchimp",               "Advertising & Marketing",      "Purchase"),
    ("Canva",                   "Advertising & Marketing",      "Purchase"),
    ("ChatGPT",                 "Software & Technology",        "Purchase"),
    ("OpenAI",                  "Software & Technology",        "Purchase"),
    ("Anthropic",               "Software & Technology",        "Purchase"),
    ("Figma",                   "Software & Technology",        "Purchase"),

    # ── Advertising ──────────────────────────────────────────────────────────
    ("Google Ads",              "Advertising & Marketing",      "Purchase"),
    ("Facebook Ads",            "Advertising & Marketing",      "Purchase"),
    ("Meta",                    "Advertising & Marketing",      "Purchase"),
    ("LinkedIn",                "Advertising & Marketing",      "Purchase"),
    ("Twitter",                 "Advertising & Marketing",      "Purchase"),
    ("TikTok",                  "Advertising & Marketing",      "Purchase"),

    # ── Travel ───────────────────────────────────────────────────────────────
    ("Delta Airlines",          "Travel Expense",               "Purchase"),
    ("United Airlines",         "Travel Expense",               "Purchase"),
    ("American Airlines",       "Travel Expense",               "Purchase"),
    ("Southwest Airlines",      "Travel Expense",               "Purchase"),
    ("Marriott",                "Travel Expense",               "Purchase"),
    ("Hilton",                  "Travel Expense",               "Purchase"),
    ("Airbnb",                  "Travel Expense",               "Purchase"),
    ("Uber",                    "Travel Expense",               "Purchase"),
    ("Lyft",                    "Travel Expense",               "Purchase"),
    ("Hertz",                   "Travel Expense",               "Purchase"),
    ("Enterprise",              "Travel Expense",               "Purchase"),

    # ── Meals ────────────────────────────────────────────────────────────────
    ("DoorDash",                "Meals & Entertainment",        "Purchase"),
    ("Uber Eats",               "Meals & Entertainment",        "Purchase"),
    ("Grubhub",                 "Meals & Entertainment",        "Purchase"),
    ("Starbucks",               "Meals & Entertainment",        "Purchase"),
    ("Chipotle",                "Meals & Entertainment",        "Purchase"),
    ("Panera",                  "Meals & Entertainment",        "Purchase"),

    # ── Office & Shipping ────────────────────────────────────────────────────
    ("Amazon",                  "Office Supplies & Expenses",   "Purchase"),
    ("Staples",                 "Office Supplies & Expenses",   "Purchase"),
    ("Office Depot",            "Office Supplies & Expenses",   "Purchase"),
    ("FedEx",                   "Office Supplies & Expenses",   "Purchase"),
    ("UPS",                     "Office Supplies & Expenses",   "Purchase"),
    ("USPS",                    "Office Supplies & Expenses",   "Purchase"),

    # ── Utilities & Phone ────────────────────────────────────────────────────
    ("AT&T",                    "Telephone & Internet",         "Purchase"),
    ("Verizon",                 "Telephone & Internet",         "Purchase"),
    ("T-Mobile",                "Telephone & Internet",         "Purchase"),
    ("Comcast",                 "Telephone & Internet",         "Purchase"),
    ("Spectrum",                "Telephone & Internet",         "Purchase"),

    # ── Insurance ────────────────────────────────────────────────────────────
    ("Geico",                   "Insurance Expense",            "Purchase"),
    ("State Farm",              "Insurance Expense",            "Purchase"),
    ("Progressive",             "Insurance Expense",            "Purchase"),
    ("Allstate",                "Insurance Expense",            "Purchase"),
    ("Hiscox",                  "Insurance Expense",            "Purchase"),
    ("Next Insurance",          "Insurance Expense",            "Purchase"),

    # ── Vehicle ──────────────────────────────────────────────────────────────
    ("Shell",                   "Vehicle Expense",              "Purchase"),
    ("Chevron",                 "Vehicle Expense",              "Purchase"),
    ("Exxon",                   "Vehicle Expense",              "Purchase"),
    ("BP",                      "Vehicle Expense",              "Purchase"),
    ("Jiffy Lube",              "Vehicle Expense",              "Purchase"),

    # ── Legal & Professional ─────────────────────────────────────────────────
    ("LegalZoom",               "Legal Fees",                   "Purchase"),
    ("Upwork",                  "Consulting Fees",              "Purchase"),
    ("Fiverr",                  "Consulting Fees",              "Purchase"),
]


def seed_vendor_knowledge(company_id: int) -> dict:
    """
    Insert pre-approved synthetic transactions so the classifier's
    vendor_history tier works from day one.

    Safe to call multiple times — skips vendors that already have
    approved transactions for this company.
    """
    from extensions import db
    from app.models.transaction import Transaction

    created = 0
    skipped = 0

    for vendor_name, category, txn_type in VENDOR_SEEDS:
        # Check if this vendor already has approved transactions
        existing = Transaction.query.filter_by(
            company_id=company_id,
            vendor_name=vendor_name,
            review_status='approved',
        ).first()
        if existing:
            skipped += 1
            continue

        # Create 3 synthetic approved transactions (enough for 82% classifier confidence)
        for i in range(3):
            txn = Transaction(
                company_id=company_id,
                qbo_transaction_id=f'seed-{vendor_name.lower().replace(" ", "-")}-{i}',
                transaction_type=txn_type,
                description=f'{vendor_name} charge',
                vendor_name=vendor_name,
                amount=-99.00,
                transaction_date=date(2025, 1, i + 1),
                category=category,
                suggested_category=category,
                suggested_confidence=90,
                categorization_status='categorized',
                categorized_by='seed',
                review_status='approved',
                raw_data={'seed': True, 'source': 'vendor_seeds'},
            )
            db.session.add(txn)
        created += 1

    db.session.commit()
    logger.info(f'Vendor seeds: {created} vendors seeded, {skipped} already present for company {company_id}')
    return {'seeded': created, 'skipped': skipped}
