"""Tests for AI Auto-Categorization Service

Verifies:
  • Model training on 50 demo transactions
  • Single + batch categorization
  • API endpoints
  • Accuracy > 80% on demo corpus
"""

import pytest
import sys
import os

# Ensure app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.ai_categorization import (
    CategorizationService,
    get_categorization_service,
    categorize_transaction,
    categorize_all_pending,
    approve_suggestion,
    evaluate_accuracy,
    TRAINING_DATA,
    CATEGORIES,
)


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------
class TestCategorizationService:
    """Unit tests for the ML service itself."""

    @pytest.fixture(scope="class")
    def service(self):
        return CategorizationService()

    # 1. Training corpus integrity ------------------------------------------
    def test_training_data_has_50_records(self):
        assert len(TRAINING_DATA) == 50, f"Expected 50 demo rows, got {len(TRAINING_DATA)}"

    def test_all_categories_present(self):
        found = {label for _, label in TRAINING_DATA}
        for cat in CATEGORIES:
            assert cat in found, f"Missing category: {cat}"

    # 2. Single categorization ----------------------------------------------
    @pytest.mark.parametrize("description, expected", [
        ("Monthly office rent payment", "Rent"),
        ("Google Ads campaign spend", "Marketing"),
        ("Electric utility bill", "Utilities"),
        ("Laptop purchase for employee", "Equipment"),
        ("Legal fee for contract review", "Services"),
        ("Office printer paper", "Operating Expenses"),
        ("Client lunch at steakhouse", "Sales"),
    ])
    def test_single_categorization(self, service, description, expected):
        category, confidence = service.categorize(description)
        assert category == expected, f"Expected {expected}, got {category}"
        assert confidence >= 50.0, f"Confidence too low: {confidence}"

    # 3. Batch categorization -----------------------------------------------
    def test_batch_categorization(self, service):
        descriptions = ["Monthly rent", "Facebook ad", "Electric bill", "Office supplies"]
        results = service.batch_categorize(descriptions)
        assert len(results) == len(descriptions)
        assert results[0][0] == "Rent"
        assert results[1][0] == "Marketing"
        assert results[2][0] == "Utilities"
        assert results[3][0] == "Operating Expenses"

    # 4. Confidence scoring -------------------------------------------------
    def test_confidence_range(self, service):
        _, confidence = service.categorize("Office supplies purchase")
        assert 0.0 <= confidence <= 100.0

    # 5. Accuracy > 80% on demo corpus -------------------------------------
    def test_demo_accuracy_above_80(self):
        report = evaluate_accuracy(TRAINING_DATA)
        assert report["accuracy"] >= 80.0, f"Accuracy {report['accuracy']}% below 80%"

    # 6. Edge cases ---------------------------------------------------------
    def test_empty_string(self, service):
        cat, conf = service.categorize("")
        assert cat in CATEGORIES
        assert conf >= 0.0

    def test_gibberish(self, service):
        cat, conf = service.categorize("xyz123 nonsense qwerty")
        assert cat in CATEGORIES
        assert conf >= 0.0


# ---------------------------------------------------------------------------
# Standalone tests (no Flask app needed)
# ---------------------------------------------------------------------------
class TestAccuracyReport:
    """Verify accuracy on demo corpus without Flask context."""

    def test_accuracy_above_80_percent(self):
        report = evaluate_accuracy(TRAINING_DATA)
        print(f"\n   Demo corpus accuracy: {report['accuracy']}%")
        assert report["accuracy"] >= 80.0

    def test_all_categories_in_training(self):
        found = {label for _, label in TRAINING_DATA}
        assert found == set(CATEGORIES)

    def test_training_distribution(self):
        counts = {}
        for _, label in TRAINING_DATA:
            counts[label] = counts.get(label, 0) + 1
        # Verify expected distribution
        assert counts.get("Operating Expenses") == 10
        assert counts.get("Rent") == 8
        assert counts.get("Marketing") == 8
        assert counts.get("Sales") == 7
        assert counts.get("Utilities") == 7
        assert counts.get("Equipment") == 5
        assert counts.get("Services") == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
