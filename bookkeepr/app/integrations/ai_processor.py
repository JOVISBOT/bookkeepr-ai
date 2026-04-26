"""AI Processor for Transaction Categorization & Reconciliation"""
import os
import json
import requests
from typing import List, Dict

class AIProcessor:
    """AI-powered transaction processing"""
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.preferred_model = os.getenv('AI_MODEL', 'groq')
    
    def categorize_transaction(self, description: str, amount: float, vendor: str = None) -> Dict:
        """AI-categorize a transaction"""
        prompt = f"""Categorize this transaction:
Description: {description}
Amount: ${amount}
Vendor: {vendor or 'Unknown'}

Return JSON with:
- category (e.g., 'Software', 'Meals', 'Travel', 'Office Supplies')
- confidence (0-1)
- reason (why this category)
"""
        
        if self.preferred_model == 'groq' and self.groq_api_key:
            return self._groq_categorize(prompt)
        else:
            return self._ollama_categorize(prompt)
    
    def _groq_categorize(self, prompt):
        """Use Groq API for fast categorization"""
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {self.groq_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'mixtral-8x7b-32768',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3,
                'max_tokens': 200
            },
            timeout=5
        )
        
        result = response.json()['choices'][0]['message']['content']
        return self._parse_category_response(result)
    
    def _ollama_categorize(self, prompt):
        """Use local Ollama for categorization"""
        response = requests.post(
            f'{self.ollama_url}/api/generate',
            json={
                'model': 'llama3.2',
                'prompt': prompt,
                'stream': False
            },
            timeout=30
        )
        
        result = response.json().get('response', '')
        return self._parse_category_response(result)
    
    def _parse_category_response(self, response: str) -> Dict:
        """Parse AI response into structured data"""
        try:
            # Try to parse JSON directly
            if '{' in response and '}' in response:
                json_str = response[response.find('{'):response.rfind('}')+1]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback parsing
        lines = response.lower().split('\n')
        category = 'Uncategorized'
        confidence = 0.5
        reason = 'No clear match'
        
        for line in lines:
            if 'category' in line:
                category = line.split(':')[-1].strip().strip('"').title()
            elif 'confidence' in line:
                try:
                    confidence = float(line.split(':')[-1].strip())
                except:
                    pass
            elif 'reason' in line:
                reason = line.split(':')[-1].strip().strip('"')
        
        return {'category': category, 'confidence': confidence, 'reason': reason}
    
    def reconcile_transactions(self, bank_tx: List[Dict], qbo_tx: List[Dict]) -> List[Dict]:
        """AI-powered transaction reconciliation"""
        matches = []
        
        for bank in bank_tx:
            best_match = None
            best_score = 0
            
            for qbo in qbo_tx:
                score = self._calculate_match_score(bank, qbo)
                if score > best_score and score > 0.7:
                    best_score = score
                    best_match = qbo
            
            matches.append({
                'bank_transaction': bank,
                'qbo_transaction': best_match,
                'confidence': best_score,
                'matched': best_score > 0.85
            })
        
        return matches
    
    def _calculate_match_score(self, bank: Dict, qbo: Dict) -> float:
        """Calculate match confidence between bank and QBO transaction"""
        score = 0.0
        
        # Amount match (highest weight)
        bank_amount = abs(float(bank.get('amount', 0)))
        qbo_amount = abs(float(qbo.get('amount', 0)))
        if abs(bank_amount - qbo_amount) < 0.01:
            score += 0.4
        elif abs(bank_amount - qbo_amount) < 1.00:
            score += 0.2
        
        # Date proximity
        bank_date = bank.get('date', '')
        qbo_date = qbo.get('date', '')
        if bank_date == qbo_date:
            score += 0.3
        
        # Description similarity
        bank_desc = bank.get('description', '').lower()
        qbo_desc = qbo.get('description', '').lower()
        if any(word in qbo_desc for word in bank_desc.split() if len(word) > 3):
            score += 0.3
        
        return min(score, 1.0)
    
    def suggest_rules(self, transactions: List[Dict]) -> List[Dict]:
        """AI-suggests categorization rules from transaction patterns"""
        vendor_patterns = {}
        
        for tx in transactions:
            vendor = tx.get('vendor', 'Unknown')
            category = tx.get('category', 'Uncategorized')
            
            if vendor not in vendor_patterns:
                vendor_patterns[vendor] = {'categories': {}, 'count': 0}
            
            vendor_patterns[vendor]['categories'][category] = \
                vendor_patterns[vendor]['categories'].get(category, 0) + 1
            vendor_patterns[vendor]['count'] += 1
        
        # Generate rules for consistent patterns
        rules = []
        for vendor, data in vendor_patterns.items():
            if data['count'] >= 3:
                # Find most common category
                most_common = max(data['categories'].items(), key=lambda x: x[1])
                if most_common[1] / data['count'] > 0.8:
                    rules.append({
                        'vendor': vendor,
                        'category': most_common[0],
                        'confidence': most_common[1] / data['count'],
                        'auto_apply': most_common[1] / data['count'] > 0.95
                    })
        
        return rules
