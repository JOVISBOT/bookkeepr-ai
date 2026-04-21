import axios from "axios";
import type {
  Transaction,
  TransactionListResponse,
  ReviewQueueResponse,
  Company,
  Account,
  AIMetrics,
  DashboardStats,
  BankStatement,
  ReconciliationSummary,
  BankStatementLinesResponse,
  CSVUploadResponse,
  MatchActionResponse,
  AutoMatchResponse,
} from "../types";

const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = "/auth/login";
    }
    return Promise.reject(error);
  }
);

// Companies
export async function getCompanies(): Promise<Company[]> {
  const response = await api.get("/companies");
  return response.data.companies;  // Return companies array
}

// Transactions
export async function getTransactions(
  companyId: number,
  page = 1,
  perPage = 25,
  needsReview?: boolean
): Promise<TransactionListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: perPage.toString(),
  });
  if (needsReview !== undefined) {
    params.append("needs_review", needsReview.toString());
  }
  const response = await api.get(
    `/companies/${companyId}/transactions?${params}`
  );
  return response.data;
}

export async function categorizeTransaction(
  transactionId: number,
  accountId: number
): Promise<{ success: boolean; transaction: Transaction }> {
  const response = await api.post(`/transactions/${transactionId}/categorize`, {
    account_id: accountId,
  });
  return response.data;
}

// Review Queue
export async function getReviewQueue(
  companyId: number,
  status = "pending",
  confidence?: string,
  page = 1,
  limit = 50
): Promise<ReviewQueueResponse> {
  const params = new URLSearchParams({
    status,
    page: page.toString(),
    limit: limit.toString(),
  });
  if (confidence) {
    params.append("confidence", confidence);
  }
  const response = await api.get(
    `/companies/${companyId}/review-queue?${params}`
  );
  return response.data;
}

export async function reviewTransaction(
  transactionId: number,
  action: "approve" | "reject" | "correct",
  accountId?: number,
  notes?: string
): Promise<{ success: boolean; message: string; transaction: Transaction }> {
  const response = await api.post(`/transactions/${transactionId}/review`, {
    action,
    account_id: accountId,
    notes,
  });
  return response.data;
}

export async function bulkReviewTransactions(
  transactionIds: number[],
  action: "approve" | "correct",
  accountId?: number
): Promise<{
  success: boolean;
  processed: number;
  errors: string[];
  message: string;
}> {
  const response = await api.post(`/transactions/bulk-review`, {
    transaction_ids: transactionIds,
    action,
    account_id: accountId,
  });
  return response.data;
}

// Accounts
export async function getAccounts(
  companyId: number,
  type?: string
): Promise<Account[]> {
  const params = new URLSearchParams();
  if (type) {
    params.append("type", type);
  }
  const response = await api.get(
    `/companies/${companyId}/accounts?${params}`
  );
  return response.data;
}

// AI Categorization
export async function runAICategorization(
  companyId: number,
  limit = 100,
  autoApprove = true
): Promise<{
  success: boolean;
  processed: number;
  summary: {
    total: number;
    high_confidence: number;
    medium_confidence: number;
    low_confidence: number;
    categorized: number;
    needs_review: number;
  };
  auto_approved: number;
}> {
  const response = await api.post(`/companies/${companyId}/ai-categorize`, {
    limit,
    auto_approve_high_confidence: autoApprove,
  });
  return response.data;
}

export async function getAIMetrics(
  companyId: number,
  days = 30
): Promise<AIMetrics> {
  const response = await api.get(
    `/companies/${companyId}/ai-metrics?days=${days}`
  );
  return response.data;
}

// Sync
export async function syncCompany(
  companyId: number,
  type: "full" | "accounts" | "transactions" = "full"
): Promise<{ success: boolean; message: string; [key: string]: any }> {
  const response = await api.post(`/companies/${companyId}/sync`, { type });
  return response.data;
}

// Dashboard Stats (computed from multiple endpoints)
export async function getDashboardStats(
  companyId: number
): Promise<DashboardStats> {
  const [metrics, reviewQueue] = await Promise.all([
    getAIMetrics(companyId, 30),
    getReviewQueue(companyId, "pending", undefined, 1, 1),
    getTransactions(companyId, 1, 1),
  ]);

  // Calculate monthly spending from transactions
  const recentTransactions = await getTransactions(companyId, 1, 100);
  const currentMonth = new Date().getMonth();
  const monthlySpending = recentTransactions.transactions
    .filter(
      (t) =>
        new Date(t.transaction_date).getMonth() === currentMonth &&
        t.amount < 0
    )
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  return {
    totalTransactions: metrics.metrics.total_transactions,
    pendingReview: reviewQueue.total,
    accuracyRate: metrics.metrics.accuracy_rate * 100,
    monthlySpending,
  };
}

export default api;

// ============ Bank Reconciliation API ============

// Upload bank statement CSV
export async function uploadBankStatement(
  companyId: number,
  file: File,
  metadata?: {
    statement_date?: string;
    start_balance?: number;
    end_balance?: number;
  }
): Promise<CSVUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("company_id", companyId.toString());
  if (metadata?.statement_date) {
    formData.append("statement_date", metadata.statement_date);
  }
  if (metadata?.start_balance !== undefined) {
    formData.append("start_balance", metadata.start_balance.toString());
  }
  if (metadata?.end_balance !== undefined) {
    formData.append("end_balance", metadata.end_balance.toString());
  }

  const response = await api.post("/bank-statements", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

// Get bank statement details
export async function getBankStatement(
  statementId: number
): Promise<{ statement: BankStatement }> {
  const response = await api.get(`/bank-statements/${statementId}`);
  return response.data;
}

// Get bank statement lines with pagination and status filter
export async function getBankStatementLines(
  statementId: number,
  page = 1,
  perPage = 50,
  status?: string
): Promise<BankStatementLinesResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: perPage.toString(),
  });
  if (status) {
    params.append("status", status);
  }
  const response = await api.get(
    `/bank-statements/${statementId}/lines?${params}`
  );
  return response.data;
}

// Run auto-matching on a statement
export async function runAutoMatch(
  statementId: number,
  confidenceThreshold = 0.85
): Promise<AutoMatchResponse> {
  const response = await api.post(
    `/bank-statements/${statementId}/auto-match`,
    { confidence_threshold: confidenceThreshold }
  );
  return response.data;
}

// Get reconciliation summary
export async function getReconciliationSummary(
  statementId: number
): Promise<{ summary: ReconciliationSummary }> {
  const response = await api.get(`/bank-statements/${statementId}/summary`);
  return response.data;
}

// Approve a reconciliation match
export async function approveMatch(
  matchId: number
): Promise<MatchActionResponse> {
  const response = await api.post(
    `/reconciliation-matches/${matchId}/approve`
  );
  return response.data;
}

// Reject a reconciliation match
export async function rejectMatch(
  matchId: number
): Promise<MatchActionResponse> {
  const response = await api.post(
    `/reconciliation-matches/${matchId}/reject`
  );
  return response.data;
}

// Create manual match
export async function createManualMatch(
  bankLineId: number,
  transactionId: number,
  companyId: number
): Promise<MatchActionResponse> {
  const response = await api.post("/reconciliation/manual-match", {
    bank_line_id: bankLineId,
    transaction_id: transactionId,
    company_id: companyId,
  });
  return response.data;
}

// Get transactions for manual matching
export async function getTransactionsForMatching(
  companyId: number,
  filters?: {
    query?: string;
    date_from?: string;
    date_to?: string;
    amount_min?: number;
    amount_max?: number;
    limit?: number;
  }
): Promise<{ transactions: Transaction[]; total: number }> {
  const params = new URLSearchParams();
  if (filters?.query) params.append("query", filters.query);
  if (filters?.date_from) params.append("date_from", filters.date_from);
  if (filters?.date_to) params.append("date_to", filters.date_to);
  if (filters?.amount_min !== undefined)
    params.append("amount_min", filters.amount_min.toString());
  if (filters?.amount_max !== undefined)
    params.append("amount_max", filters.amount_max.toString());
  if (filters?.limit) params.append("limit", filters.limit.toString());

  const response = await api.get(
    `/companies/${companyId}/transactions-for-matching?${params}`
  );
  return response.data;
}

// Billing
export async function getPlans(): Promise<{ success: boolean; plans: Record<string, any> }> {
  const response = await api.get("/billing/plans");
  return response.data;
}

export async function getSubscription(): Promise<{ success: boolean; subscription: any | null; has_active_subscription: boolean }> {
  const response = await api.get("/billing/subscription");
  return response.data;
}

export async function createCheckout(planType: string): Promise<{ success: boolean; checkout_url: string; session_id: string }> {
  const response = await api.post("/billing/create-checkout", { plan_type: planType });
  return response.data;
}
