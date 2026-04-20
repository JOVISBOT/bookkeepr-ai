export interface Transaction {
  id: number;
  qbo_transaction_id: string;
  transaction_type: string;
  transaction_date: string;
  amount: number;
  description: string | null;
  memo: string | null;
  vendor_name: string | null;
  customer_name: string | null;
  category: string | null;
  categorization_status: "uncategorized" | "suggested" | "categorized";
  suggested_category: string | null;
  suggested_confidence: number | null;
  review_status: "pending" | "approved" | "flagged";
  has_attachment: boolean;
  created_at: string;
  categorized_at: string | null;
  suggestions?: Array<{
    account_id: number;
    account_name: string;
    confidence: number;
  }>;
}

export interface TransactionListResponse {
  transactions: Transaction[];
  total: number;
  pages: number;
  current_page: number;
}

export interface ReviewQueueResponse {
  transactions: Transaction[];
  total: number;
  pages: number;
  current_page: number;
}

export interface Company {
  id: number;
  name: string;
  qbo_realm_id: string | null;
  created_at: string;
}

export interface Account {
  id: number;
  name: string;
  account_type: string;
  account_number: string | null;
}

export interface AIMetrics {
  metrics: {
    accuracy_rate: number;
    total_transactions: number;
    correct_categorizations: number;
    corrections_made: number;
  };
  confidence_distribution: {
    high?: number;
    medium?: number;
    low?: number;
  };
  recent_corrections: Correction[];
  period_days: number;
}

export interface Correction {
  id: number;
  transaction_id: number;
  original_account_id: number;
  corrected_account_id: number;
  user_id: number;
  created_at: string;
  original_account?: string;
  corrected_account?: string;
}

export interface DashboardStats {
  totalTransactions: number;
  pendingReview: number;
  accuracyRate: number;
  monthlySpending: number;
}

export interface SpendingData {
  month: string;
  amount: number;
  count: number;
}

export interface CategorySpending {
  category: string;
  amount: number;
  percentage: number;
}
