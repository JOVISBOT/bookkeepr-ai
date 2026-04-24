"""AI Auto-Categorization Service for BookKeepr

Uses a lightweight TF-IDF + Logistic Regression model to categorize
financial transactions into standard chart-of-accounts buckets.
"""

import os
import json
import pickle
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

from extensions import db
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Training corpus — 50 demo transactions
# ---------------------------------------------------------------------------
TRAINING_DATA: List[Tuple[str, str]] = [
    # Operating Expenses (10)
    ("Office supplies purchase", "Operating Expenses"),
    ("Staples - printer paper", "Operating Expenses"),
    ("Postage and shipping fees", "Operating Expenses"),
    ("Office cleaning service", "Operating Expenses"),
    ("Coffee and snacks for office", "Operating Expenses"),
    ("Stationery and envelopes", "Operating Expenses"),
    ("Office maintenance repair", "Operating Expenses"),
    ("Break room supplies", "Operating Expenses"),
    ("Ink cartridges for printers", "Operating Expenses"),
    ("Office furniture small items", "Operating Expenses"),

    # Rent (8)
    ("Monthly office rent", "Rent"),
    ("Warehouse lease payment", "Rent"),
    ("Retail space rental", "Rent"),
    ("Parking garage lease", "Rent"),
    ("Equipment yard rental", "Rent"),
    ("Office building lease", "Rent"),
    ("Storage unit monthly fee", "Rent"),
    ("Co-working space membership", "Rent"),

    # Marketing (8)
    ("Facebook advertising campaign", "Marketing"),
    ("Google Ads spend", "Marketing"),
    ("Print brochure design", "Marketing"),
    ("Trade show booth fee", "Marketing"),
    ("Influencer sponsorship", "Marketing"),
    ("SEO consultant fee", "Marketing"),
    ("Email marketing platform", "Marketing"),
    ("Billboard advertisement", "Marketing"),

    # Sales (7)
    ("Client lunch meeting", "Sales"),
    ("Sales commission payout", "Sales"),
    ("CRM software subscription", "Sales"),
    ("Sales training seminar", "Sales"),
    ("Travel to client site", "Sales"),
    ("Demo equipment purchase", "Sales"),
    ("Sales team bonus", "Sales"),

    # Utilities (7)
    ("Electric bill payment", "Utilities"),
    ("Water and sewage", "Utilities"),
    ("Internet service provider", "Utilities"),
    ("Natural gas heating", "Utilities"),
    ("Phone service monthly", "Utilities"),
    ("Trash collection fee", "Utilities"),
    ("Sewer maintenance", "Utilities"),

    # Equipment (5)
    ("Laptop purchase Dell", "Equipment"),
    ("3D printer acquisition", "Equipment"),
    ("Company vehicle down payment", "Equipment"),
    ("Server rack installation", "Equipment"),
    ("Heavy machinery lease-to-own", "Equipment"),

    # Services (5)
    ("Legal consultation fee", "Services"),
    ("CPA audit services", "Services"),
    ("IT support contract", "Services"),
    ("Payroll processing", "Services"),
    ("Janitorial contract", "Services"),
]

CATEGORIES = [
    "Operating Expenses",
    "Rent",
    "Marketing",
    "Sales",
    "Utilities",
    "Equipment",
    "Services",
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml_models", "category_model.pkl")


class CategorizationService:
    """Lightweight ML service for transaction auto-categorization."""

    def __init__(self):
        self._pipeline: Optional[Pipeline] = None
        self._is_trained = False
        self._load_or_train()

    # ------------------------------------------------------------------
    # Model persistence
    # ------------------------------------------------------------------
    def _load_or_train(self) -> None:
        """Load an existing pickled model or train a fresh one."""
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    self._pipeline = pickle.load(f)
                self._is_trained = True
                logger.info("Loaded existing categorization model.")
                return
            except Exception as exc:
                logger.warning(f"Could not load model: {exc}. Retraining …")

        self._train()
        self._save_model()

    def _train(self) -> None:
        """Train on the built-in 50-record corpus."""
        texts, labels = zip(*TRAINING_DATA)
        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=1000, C=10.0, class_weight="balanced")),
        ])
        self._pipeline.fit(texts, labels)
        self._is_trained = True
        logger.info("Trained categorization model on demo corpus.")

    def _save_model(self) -> None:
        """Persist the trained pipeline to disk."""
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self._pipeline, f)
        logger.info(f"Saved categorization model to {MODEL_PATH}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def categorize(self, description: str) -> Tuple[str, float]:
        """Return (category, confidence) for a single description."""
        if not self._is_trained or self._pipeline is None:
            raise RuntimeError("Model is not trained yet.")

        proba = self._pipeline.predict_proba([description])[0]
        idx = int(np.argmax(proba))
        category = self._pipeline.classes_[idx]
        confidence = round(float(proba[idx]) * 100, 2)
        return category, confidence

    def batch_categorize(self, descriptions: List[str]) -> List[Tuple[str, float]]:
        """Categorize many descriptions at once."""
        if not descriptions:
            return []
        proba_matrix = self._pipeline.predict_proba(descriptions)
        results = []
        for row in proba_matrix:
            idx = int(np.argmax(row))
            results.append((self._pipeline.classes_[idx], round(float(row[idx]) * 100, 2)))
        return results

    def retrain(self, transactions: List[Transaction]) -> Dict[str, any]:
        """Retrain with real user-labeled transactions and persist."""
        if not transactions:
            return {"success": False, "message": "No transactions provided"}

        texts, labels = [], []
        for txn in transactions:
            if txn.category and txn.description:
                texts.append(txn.description)
                labels.append(txn.category)

        if len(set(labels)) < 2:
            return {"success": False, "message": "Need at least 2 distinct categories"}

        self._pipeline.fit(texts, labels)
        self._is_trained = True
        self._save_model()

        return {
            "success": True,
            "message": f"Retrained on {len(texts)} transactions",
            "categories": list(set(labels)),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def build_training_text(transaction: Transaction) -> str:
        """Best-effort text extraction from a Transaction row."""
        parts = [transaction.description or ""]
        if transaction.memo:
            parts.append(transaction.memo)
        if transaction.vendor_name:
            parts.append(transaction.vendor_name)
        return " ".join(parts).strip() or "unknown"


# Singleton service instance
_categorization_service: Optional[CategorizationService] = None


def get_categorization_service() -> CategorizationService:
    global _categorization_service
    if _categorization_service is None:
        _categorization_service = CategorizationService()
    return _categorization_service


def categorize_transaction(transaction_id: int) -> Dict[str, any]:
    """High-level helper: categorize one DB transaction and write back."""
    service = get_categorization_service()
    txn = Transaction.query.get(transaction_id)
    if not txn:
        return {"success": False, "error": "Transaction not found"}

    text = service.build_training_text(txn)
    category, confidence = service.categorize(text)

    txn.suggested_category = category
    txn.suggested_confidence = confidence
    txn.categorization_status = "suggested"
    txn.categorized_by = "ai"
    txn.categorized_at = datetime.utcnow()
    db.session.commit()

    return {
        "success": True,
        "transaction_id": transaction_id,
        "category": category,
        "confidence": confidence,
        "status": "suggested",
    }


def categorize_all_pending(company_id: int) -> Dict[str, any]:
    """Batch-categorize every uncategorized transaction for a company."""
    service = get_categorization_service()
    pending = Transaction.query.filter_by(
        company_id=company_id,
        categorization_status="uncategorized",
    ).all()

    if not pending:
        return {"success": True, "categorized": 0, "message": "No pending transactions"}

    descriptions = [service.build_training_text(t) for t in pending]
    predictions = service.batch_categorize(descriptions)

    for txn, (cat, conf) in zip(pending, predictions):
        txn.suggested_category = cat
        txn.suggested_confidence = conf
        txn.categorization_status = "suggested"
        txn.categorized_by = "ai"
        txn.categorized_at = datetime.utcnow()

    db.session.commit()

    return {
        "success": True,
        "categorized": len(pending),
        "message": f"Categorized {len(pending)} transactions",
    }


def approve_suggestion(transaction_id: int, user_id: int) -> Dict[str, any]:
    """Promote an AI suggestion to the final category."""
    txn = Transaction.query.get(transaction_id)
    if not txn:
        return {"success": False, "error": "Transaction not found"}
    if txn.categorization_status != "suggested":
        return {"success": False, "error": "No suggestion to approve"}

    txn.category = txn.suggested_category
    txn.categorization_status = "categorized"
    txn.categorized_by = "user"
    txn.categorized_at = datetime.utcnow()
    txn.review_status = "approved"
    txn.reviewed_by_user_id = user_id
    txn.reviewed_at = datetime.utcnow()
    db.session.commit()

    return {"success": True, "transaction_id": transaction_id, "category": txn.category}


def evaluate_accuracy(test_data: List[Tuple[str, str]]) -> Dict[str, any]:
    """Run a quick accuracy report on held-out descriptions."""
    service = get_categorization_service()
    texts, labels = zip(*test_data)
    preds = [service.categorize(t)[0] for t in texts]
    acc = accuracy_score(labels, preds)
    return {
        "accuracy": round(float(acc) * 100, 2),
        "total": len(test_data),
        "report": classification_report(labels, preds, output_dict=True),
    }
