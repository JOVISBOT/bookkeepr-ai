"""
AI Categorization Service - GPT-4 powered transaction categorization

Phase 2.1: AI-Powered Categorization Engine
- OpenAI GPT-4 integration for transaction classification
- Context enrichment with account chart of accounts
- Confidence scoring system
- Batch processing with rate limits
- Learning from user corrections

Features:
- Automatic categorization with 90%+ accuracy target
- Confidence thresholds (high/medium/low)
- Rule integration for hybrid categorization
- Pattern learning from user corrections
- Historical transaction context
"""

import json
import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from flask import current_app

from extensions import db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category_rule import CategoryRule

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Categorization confidence levels"""
    HIGH = "high"      # >= 0.85 - Auto-approved
    MEDIUM = "medium"  # 0.70-0.84 - Needs review
    LOW = "low"        # < 0.70 - Requires manual categorization


@dataclass
class CategorizationResult:
    """Result of AI categorization"""
    transaction_id: int
    account_id: Optional[int]
    account_name: Optional[str]
    confidence: float
    confidence_level: ConfidenceLevel
    reason: str
    suggestions: List[Dict] = field(default_factory=list)
    matched_rules: List[int] = field(default_factory=list)
    ai_raw_response: Optional[str] = None
    processed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransactionContext:
    """Context for categorizing a transaction"""
    transaction: Transaction
    chart_of_accounts: List[Account]
    similar_transactions: List[Dict] = field(default_factory=list)
    user_rules: List[CategoryRule] = field(default_factory=list)
    historical_patterns: Dict = field(default_factory=dict)


class AICategorizationService:
    """
    AI-powered transaction categorization service
    
    Uses GPT-4 to categorize transactions with high accuracy.
    Integrates with user rules and learns from corrections.
    """
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = 500  # OpenAI tier limits
    MAX_BATCH_SIZE = 100
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.70
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI categorization service
        
        Args:
            api_key: OpenAI API key (defaults to env var)
        """
        import os
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required for AI categorization")
        import anthropic
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.request_times: List[datetime] = []
        self._executor = ThreadPoolExecutor(max_workers=5)
    
    def categorize_transaction(
        self,
        transaction: Transaction,
        company_id: int,
        use_rules: bool = True
    ) -> CategorizationResult:
        """
        Categorize a single transaction
        
        Args:
            transaction: Transaction to categorize
            company_id: Company ID for context
            use_rules: Whether to apply user rules first
            
        Returns:
            CategorizationResult with account assignment
        """
        # Check rules first if enabled
        if use_rules:
            rule_result = self._check_category_rules(transaction, company_id)
            if rule_result:
                return rule_result
        
        # Get context for AI
        context = self._build_transaction_context(transaction, company_id)
        
        # Generate categorization via GPT-4
        result = self._ai_categorize(context)
        
        # Apply post-processing
        result = self._post_process_result(result, context)
        
        return result
    
    def categorize_batch(
        self,
        transactions: List[Transaction],
        company_id: int,
        batch_size: int = 50
    ) -> List[CategorizationResult]:
        """
        Categorize multiple transactions with rate limiting
        
        Args:
            transactions: List of transactions to categorize
            company_id: Company ID for context
            batch_size: Max transactions per batch
            
        Returns:
            List of CategorizationResults
        """
        results = []
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            batch_results = self._categorize_batch(batch, company_id)
            results.extend(batch_results)
            
            # Rate limit pause between batches
            if i + batch_size < len(transactions):
                time.sleep(1)  # 1 second between batches
        
        return results
    
    def _categorize_batch(
        self,
        transactions: List[Transaction],
        company_id: int
    ) -> List[CategorizationResult]:
        """Process a batch of transactions"""
        results = []
        
        for transaction in transactions:
            try:
                result = self.categorize_transaction(transaction, company_id)
                results.append(result)
                
                # Update transaction with results
                self._apply_categorization(transaction, result)
                
            except Exception as e:
                logger.error(f"Categorization failed for transaction {transaction.id}: {e}")
                results.append(CategorizationResult(
                    transaction_id=transaction.id,
                    account_id=None,
                    account_name=None,
                    confidence=0.0,
                    confidence_level=ConfidenceLevel.LOW,
                    reason=f"Error: {str(e)}"
                ))
        
        return results
    
    def _check_category_rules(
        self,
        transaction: Transaction,
        company_id: int
    ) -> Optional[CategorizationResult]:
        """
        Check if any user rules match this transaction
        
        Rules take precedence over AI when confidence is high
        """
        user_id = self._get_user_id_for_company(company_id)
        rules = CategoryRule.get_active_rules(user_id, company_id)
        
        matched_rules = []
        for rule in rules:
            if rule.matches_transaction(transaction):
                matched_rules.append(rule)
                rule.record_match()
        
        # If we have matching rules, use the highest priority one
        if matched_rules:
            # Sort by priority (descending)
            matched_rules.sort(key=lambda r: r.priority, reverse=True)
            best_rule = matched_rules[0]
            
            # Calculate confidence with rule boost
            base_confidence = 0.75  # Rules start with medium confidence
            confidence = min(1.0, base_confidence + best_rule.confidence_boost)
            
            # Get account name
            account = Account.query.get(best_rule.target_account_id)
            
            return CategorizationResult(
                transaction_id=transaction.id,
                account_id=best_rule.target_account_id,
                account_name=account.name if account else None,
                confidence=confidence,
                confidence_level=self._get_confidence_level(confidence),
                reason=f"Matched rule: {best_rule.name}",
                matched_rules=[r.id for r in matched_rules],
                suggestions=[]
            )
        
        return None
    
    def _build_transaction_context(
        self,
        transaction: Transaction,
        company_id: int
    ) -> TransactionContext:
        """Build rich context for AI categorization"""
        
        # Get chart of accounts
        chart_of_accounts = Account.get_expense_accounts(company_id)
        
        # Get user rules
        user_id = self._get_user_id_for_company(company_id)
        user_rules = CategoryRule.get_active_rules(user_id, company_id)
        
        # Find similar transactions (same payee/pattern)
        similar = self._find_similar_transactions(transaction, company_id)
        
        # Build historical patterns
        patterns = self._build_historical_patterns(transaction.payee_name, company_id)
        
        return TransactionContext(
            transaction=transaction,
            chart_of_accounts=chart_of_accounts,
            similar_transactions=similar,
            user_rules=user_rules,
            historical_patterns=patterns
        )
    
    def _find_similar_transactions(
        self,
        transaction: Transaction,
        company_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """Find similar historical transactions"""
        
        # Search by payee name
        if transaction.payee_name:
            similar = Transaction.query.filter(
                Transaction.company_id == company_id,
                Transaction.payee_name.ilike(f"%{transaction.payee_name}%"),
                Transaction.category_id.isnot(None)
            ).order_by(Transaction.transaction_date.desc()).limit(limit).all()
            
            return [
                {
                    'category_id': t.category_id,
                    'payee_name': t.payee_name,
                    'description': t.description,
                    'amount': float(t.amount),
                    'date': t.transaction_date.isoformat() if t.transaction_date else None
                }
                for t in similar
            ]
        
        return []
    
    def _build_historical_patterns(
        self,
        payee_name: Optional[str],
        company_id: int
    ) -> Dict:
        """Build patterns from historical categorizations"""
        if not payee_name:
            return {}
        
        # Find most common category for this payee
        from sqlalchemy import func
        
        patterns = db.session.query(
            Transaction.category_id,
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.company_id == company_id,
            Transaction.payee_name.ilike(f"%{payee_name}%"),
            Transaction.category_id.isnot(None)
        ).group_by(Transaction.category_id).order_by(func.count(Transaction.id).desc()).limit(3).all()
        
        return {
            'most_common_categories': [
                {'category_id': p[0], 'count': p[1]}
                for p in patterns
            ]
        }
    
    def _ai_categorize(self, context: TransactionContext) -> CategorizationResult:
        """
        Use GPT-4 to categorize transaction
        
        Returns best matching account with confidence score
        """
        # Build the prompt
        prompt = self._build_categorization_prompt(context)
        
        # Call Anthropic Claude API
        try:
            system_prompt = self._get_system_prompt()
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )

            self._track_request()

            content = response.content[0].text
            # Extract JSON from response
            import re as _re
            m = _re.search(r'\{.*\}', content, _re.DOTALL)
            result = json.loads(m.group() if m else content)

            return self._parse_ai_response(result, context)

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """System prompt for GPT-4"""
        return """You are an expert financial categorization AI for small business accounting.

Your task: Categorize financial transactions into the correct expense/income account based on:
1. Transaction description and payee name
2. Transaction amount
3. Historical patterns (if provided)
4. Account descriptions

Return a JSON object with:
- account_id: The ID of the best matching account (integer)
- confidence: Confidence score 0.0-1.0 (float)
- reason: Brief explanation of why this category was chosen (string)
- suggestions: Array of top 3 alternative categories with scores [{account_id, account_name, confidence}]

Be conservative: Only assign high confidence (>=0.85) when you are very certain.
For medium confidence (0.70-0.84), suggest similar alternatives.
For low confidence (<0.70), suggest multiple options.

Consider:
- Vendor/payee patterns (same vendor usually uses same category)
- Amount ranges (e.g., large purchases vs small expenses)
- Description keywords
- Account descriptions for context"""
    
    def _build_categorization_prompt(self, context: TransactionContext) -> str:
        """Build detailed prompt for transaction categorization"""
        
        tx = context.transaction
        
        prompt_parts = [
            "## Transaction to Categorize",
            f"Description: {tx.description or 'N/A'}",
            f"Payee: {tx.payee_name or 'N/A'}",
            f"Amount: ${float(tx.amount):,.2f}",
            f"Type: {tx.transaction_type}",
            f"Date: {tx.transaction_date}",
            "",
            "## Available Accounts",
        ]
        
        # Add accounts in a structured format
        for account in context.chart_of_accounts:
            prompt_parts.append(
                f"ID: {account.id} | {account.name} ({account.account_sub_type or account.account_type})"
            )
            if account.description:
                prompt_parts.append(f"   Description: {account.description}")
            # common_keywords not stored on Account model — skip
        
        # Add similar transactions for context
        if context.similar_transactions:
            prompt_parts.extend([
                "",
                "## Similar Past Transactions",
            ])
            for sim in context.similar_transactions[:3]:
                prompt_parts.append(
                    f"- {sim['payee_name']}: ${sim['amount']:,.2f} → Category ID: {sim['category_id']}"
                )
        
        # Add historical patterns
        if context.historical_patterns.get('most_common_categories'):
            prompt_parts.extend([
                "",
                "## Historical Patterns for this Payee",
            ])
            for cat in context.historical_patterns['most_common_categories'][:3]:
                account = next(
                    (a for a in context.chart_of_accounts if a.id == cat['category_id']),
                    None
                )
                if account:
                    prompt_parts.append(f"- Previously categorized to: {account.name} ({cat['count']} times)")
        
        prompt_parts.extend([
            "",
            "Respond with a JSON object containing: account_id, confidence, reason, suggestions",
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_ai_response(
        self,
        response: Dict,
        context: TransactionContext
    ) -> CategorizationResult:
        """Parse and validate AI response"""
        
        tx = context.transaction
        
        account_id = response.get('account_id')
        confidence = response.get('confidence', 0.0)
        reason = response.get('reason', 'No reason provided')
        suggestions_raw = response.get('suggestions', [])
        
        # Validate account_id exists
        account = None
        if account_id:
            account = next(
                (a for a in context.chart_of_accounts if a.id == account_id),
                None
            )
        
        # Build suggestions list
        suggestions = []
        for sug in suggestions_raw[:3]:
            sug_account = next(
                (a for a in context.chart_of_accounts if a.id == sug.get('account_id')),
                None
            )
            if sug_account:
                suggestions.append({
                    'account_id': sug.get('account_id'),
                    'account_name': sug_account.name,
                    'confidence': sug.get('confidence', 0.0)
                })
        
        # If account not found, reduce confidence
        if account is None:
            confidence = 0.0
            reason = f"AI suggested invalid account ID {account_id}"
            account_id = None
        
        return CategorizationResult(
            transaction_id=tx.id,
            account_id=account_id,
            account_name=account.name if account else None,
            confidence=confidence,
            confidence_level=self._get_confidence_level(confidence),
            reason=reason,
            suggestions=suggestions,
            ai_raw_response=json.dumps(response)
        )
    
    def _post_process_result(
        self,
        result: CategorizationResult,
        context: TransactionContext
    ) -> CategorizationResult:
        """Apply post-processing to AI result"""
        
        # Adjust confidence based on historical patterns
        if context.historical_patterns.get('most_common_categories'):
            top_pattern = context.historical_patterns['most_common_categories'][0]
            
            # If AI matches historical pattern, boost confidence
            if result.account_id == top_pattern['category_id']:
                result.confidence = min(1.0, result.confidence + 0.1)
                result.reason += " (confirmed by historical pattern)"
            # If AI contradicts strong pattern (>5 previous), reduce confidence
            elif top_pattern['count'] > 5:
                result.confidence = max(0.0, result.confidence - 0.15)
                result.reason += " (contradicts historical pattern)"
        
        # Recalculate confidence level
        result.confidence_level = self._get_confidence_level(result.confidence)
        
        return result
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Convert confidence score to level"""
        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW
    
    def _apply_categorization(
        self,
        transaction: Transaction,
        result: CategorizationResult
    ):
        """Apply categorization result to transaction record"""
        
        transaction.category_id = result.account_id
        transaction.category_confidence = result.confidence
        transaction.category_suggestions = [
            {'account_id': s['account_id'], 'confidence': s['confidence']}
            for s in result.suggestions
        ]
        transaction.ai_processed = True
        transaction.ai_rules_matched = result.matched_rules
        
        # Set review status based on confidence
        if result.confidence_level == ConfidenceLevel.HIGH and result.account_id:
            transaction.needs_review = False
            transaction.status = 'categorized'
        else:
            transaction.needs_review = True
            transaction.review_reason = result.reason
            transaction.status = 'pending'
        
        db.session.commit()
    
    def _track_request(self):
        """Track API request time for rate limiting"""
        now = datetime.utcnow()
        self.request_times.append(now)
        
        # Remove requests older than 1 minute
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]
    
    def _check_rate_limit(self):
        """Check if we're approaching rate limits"""
        if len(self.request_times) >= self.MAX_REQUESTS_PER_MINUTE:
            raise RateLimitError("Rate limit reached", response=None, body=None)
    
    def _get_user_id_for_company(self, company_id: int) -> int:
        """Get user ID associated with company"""
        from app.models.company import Company
        company = Company.query.get(company_id)
        return company.user_id if company else 0


class LearningSystem:
    """
    Learning System - Store and learn from user corrections
    
    Phase 2.4: Learning from corrections
    - Store user corrections as training data
    - Build pattern matching from corrections
    - Auto-generate rules from patterns
    """
    
    MIN_CORRECTIONS_FOR_RULE = 3  # Need 3+ same pattern to auto-create rule
    CONFIDENCE_DECAY = 0.95  # Reduce old pattern confidence over time
    
    def __init__(self):
        self.ai_service = AICategorizationService()
    
    def record_correction(
        self,
        transaction: Transaction,
        original_account_id: Optional[int],
        corrected_account_id: int,
        user_id: int
    ):
        """
        Record a user correction for learning
        
        Args:
            transaction: The corrected transaction
            original_account_id: What AI/user rules suggested
            corrected_account_id: What user manually selected
            user_id: User who made the correction
        """
        from app.models.correction_log import CorrectionLog
        
        # Log the correction
        correction = CorrectionLog(
            user_id=user_id,
            company_id=transaction.company_id,
            transaction_id=transaction.id,
            original_account_id=original_account_id,
            corrected_account_id=corrected_account_id,
            payee_name=transaction.payee_name,
            description=transaction.description,
            amount=transaction.amount,
            ai_confidence=transaction.category_confidence
        )
        
        db.session.add(correction)
        db.session.commit()
        
        # Update AI model with this correction
        self._learn_from_correction(correction)
        
        # Check if we should auto-generate a rule
        self._evaluate_rule_creation(correction, user_id)
    
    def _learn_from_correction(self, correction):
        """Update internal patterns based on correction"""
        
        # common_keywords not on Account model — learning handled via CategoryRule only
        pass
    
    def _evaluate_rule_creation(self, correction, user_id: int):
        """Check if we should auto-create a rule from corrections"""
        from app.models.correction_log import CorrectionLog
        from sqlalchemy import func
        
        # Look for patterns in past corrections
        if correction.payee_name:
            # Count corrections for this payee → account combination
            count = CorrectionLog.query.filter(
                CorrectionLog.user_id == user_id,
                CorrectionLog.payee_name.ilike(f"%{correction.payee_name}%"),
                CorrectionLog.corrected_account_id == correction.corrected_account_id
            ).count()
            
            # If we've seen this pattern enough times, create a rule
            if count >= self.MIN_CORRECTIONS_FOR_RULE:
                self._create_auto_rule(correction, user_id, count)
    
    def _create_auto_rule(self, correction, user_id: int, match_count: int):
        """Auto-generate a rule from learned pattern"""
        
        account = Account.query.get(correction.corrected_account_id)
        if not account:
            return
        
        # Check if rule already exists
        existing = CategoryRule.query.filter_by(
            user_id=user_id,
            vendor_name=correction.payee_name,
            target_account_id=correction.corrected_account_id
        ).first()
        
        if existing:
            # Update existing rule
            existing.match_count = match_count
            db.session.commit()
            return
        
        # Create new AI-learned rule
        rule = CategoryRule(
            user_id=user_id,
            company_id=correction.company_id,
            name=f"Auto: {correction.payee_name} → {account.name}",
            rule_type='vendor',
            vendor_name=correction.payee_name,
            target_account_id=correction.corrected_account_id,
            priority=50,  # Medium priority
            is_ai_learned=True,
            match_count=match_count
        )
        
        db.session.add(rule)
        db.session.commit()
        
        logger.info(f"Created AI-learned rule: {rule.name}")
    
    def get_accuracy_metrics(self, company_id: int, days: int = 30) -> Dict:
        """Get AI categorization accuracy metrics"""
        from app.models.correction_log import CorrectionLog
        
        since = datetime.utcnow() - timedelta(days=days)
        
        # Count AI categorizations
        ai_categorized = Transaction.query.filter(
            Transaction.company_id == company_id,
            Transaction.ai_processed == True,
            Transaction.created_at >= since
        ).count()
        
        # Count corrections
        corrections = CorrectionLog.query.filter(
            CorrectionLog.company_id == company_id,
            CorrectionLog.created_at >= since
        ).count()
        
        # Calculate accuracy
        if ai_categorized > 0:
            accuracy = (ai_categorized - corrections) / ai_categorized
        else:
            accuracy = 0.0
        
        # Confidence distribution
        confidence_dist = db.session.query(
            Transaction.category_confidence,
            func.count(Transaction.id)
        ).filter(
            Transaction.company_id == company_id,
            Transaction.ai_processed == True
        ).group_by(Transaction.category_confidence).all()
        
        return {
            'total_categorized': ai_categorized,
            'corrections': corrections,
            'accuracy': round(accuracy * 100, 2),
            'correction_rate': round(corrections / ai_categorized * 100, 2) if ai_categorized else 0,
            'target_accuracy': 90,
            'meets_target': accuracy >= 0.90
        }


# Initialize service
def get_ai_categorization_service() -> AICategorizationService:
    """Get AI categorization service instance"""
    return AICategorizationService()


def get_learning_system() -> LearningSystem:
    """Get learning system instance"""
    return LearningSystem()
