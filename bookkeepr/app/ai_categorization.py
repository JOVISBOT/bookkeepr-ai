"""
AI Auto-Categorization System for BookKeepr
Uses simple rule-based ML to categorize transactions
"""
import re
from datetime import datetime

class TransactionCategorizer:
    """AI-powered transaction categorization"""
    
    def __init__(self):
        self.categories = {
            'Operating Expenses': [
                'office', 'supplies', 'software', 'subscription', 'service',
                'consulting', 'legal', 'accounting', 'insurance'
            ],
            'Rent': [
                'rent', 'lease', 'property', 'building', 'office space'
            ],
            'Marketing': [
                'advertising', 'marketing', 'promotion', 'ad spend', 
                'campaign', 'social media', 'seo', 'google ads'
            ],
            'Sales': [
                'sales', 'revenue', 'income', 'payment received', 'client payment'
            ],
            'Utilities': [
                'electric', 'gas', 'water', 'internet', 'phone', 'utility'
            ],
            'Equipment': [
                'computer', 'laptop', 'printer', 'hardware', 'equipment',
                'furniture', 'desk', 'chair'
            ],
            'Services': [
                'cleaning', 'maintenance', 'repair', 'shipping', 'delivery'
            ]
        }
    
    def categorize(self, description, amount):
        """
        Categorize a transaction based on description and amount
        
        Args:
            description: Transaction description
            amount: Transaction amount (positive = income, negative = expense)
        
        Returns:
            category_name or None
        """
        description_lower = description.lower()
        
        # Check for income indicators
        if amount > 0:
            if any(word in description_lower for word in ['payment', 'invoice', 'sale', 'revenue', 'income']):
                return 'Sales'
        
        # Check each category
        for category, keywords in self.categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        # Default categorization based on amount
        if amount > 1000:
            return 'Operating Expenses'
        elif amount < -500:
            return 'Operating Expenses'
        
        return 'Uncategorized'
    
    def categorize_transactions(self, transactions):
        """Categorize multiple transactions"""
        results = []
        for transaction in transactions:
            category = self.categorize(
                transaction.get('description', ''),
                transaction.get('amount', 0)
            )
            results.append({
                'id': transaction.get('id'),
                'description': transaction.get('description'),
                'amount': transaction.get('amount'),
                'category': category,
                'confidence': 0.85 if category != 'Uncategorized' else 0.3
            })
        return results
    
    def get_category_stats(self, categorized_transactions):
        """Get statistics by category"""
        stats = {}
        for transaction in categorized_transactions:
            category = transaction['category']
            if category not in stats:
                stats[category] = {'count': 0, 'total': 0}
            stats[category]['count'] += 1
            stats[category]['total'] += transaction['amount']
        return stats

# Create instance
categorizer = TransactionCategorizer()

if __name__ == "__main__":
    # Test with sample transactions
    test_transactions = [
        {'id': 1, 'description': 'Office supplies from Staples', 'amount': -150.00},
        {'id': 2, 'description': 'Monthly rent payment', 'amount': -2500.00},
        {'id': 3, 'description': 'Google Ads campaign', 'amount': -500.00},
        {'id': 4, 'description': 'Client payment - Invoice #1234', 'amount': 3500.00},
        {'id': 5, 'description': 'Electric bill', 'amount': -180.00},
    ]
    
    results = categorizer.categorize_transactions(test_transactions)
    
    print("AI Categorization Results:")
    print("-" * 60)
    for result in results:
        print(f"{result['description'][:30]:30} | ${result['amount']:>8.2f} | {result['category']}")
    
    print("\nCategory Statistics:")
    print("-" * 60)
    stats = categorizer.get_category_stats(results)
    for category, data in stats.items():
        print(f"{category:20} | {data['count']:3} transactions | ${data['total']:>8.2f}")
