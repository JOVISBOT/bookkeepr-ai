import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
// import type { Transaction } from "../types";
import {
  getTransactions,
  getReviewQueue,
  categorizeTransaction,
  reviewTransaction,
  bulkReviewTransactions,
  runAICategorization,
  getAIMetrics,
  syncCompany,
} from "../lib/api";

// Get transactions
export function useTransactions(
  companyId: number | null,
  page = 1,
  perPage = 25,
  needsReview?: boolean
) {
  return useQuery({
    queryKey: ["transactions", companyId, page, perPage, needsReview],
    queryFn: () => {
      if (!companyId) throw new Error("Company ID required");
      return getTransactions(companyId, page, perPage, needsReview);
    },
    enabled: !!companyId,
  });
}

// Get review queue
export function useReviewQueue(
  companyId: number | null,
  status = "pending",
  confidence?: string,
  page = 1,
  limit = 50
) {
  return useQuery({
    queryKey: ["review-queue", companyId, status, confidence, page, limit],
    queryFn: () => {
      if (!companyId) throw new Error("Company ID required");
      return getReviewQueue(companyId, status, confidence, page, limit);
    },
    enabled: !!companyId,
  });
}

// Categorize transaction mutation
export function useCategorizeTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      transactionId,
      accountId,
    }: {
      transactionId: number;
      accountId: number;
    }) => categorizeTransaction(transactionId, accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    },
  });
}

// Review transaction mutation
export function useReviewTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      transactionId,
      action,
      accountId,
      notes,
    }: {
      transactionId: number;
      action: "approve" | "reject" | "correct";
      accountId?: number;
      notes?: string;
    }) => reviewTransaction(transactionId, action, accountId, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      queryClient.invalidateQueries({ queryKey: ["ai-metrics"] });
    },
  });
}

// Bulk review mutation
export function useBulkReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      transactionIds,
      action,
      accountId,
    }: {
      transactionIds: number[];
      action: "approve" | "correct";
      accountId?: number;
    }) => bulkReviewTransactions(transactionIds, action, accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      queryClient.invalidateQueries({ queryKey: ["ai-metrics"] });
    },
  });
}

// AI Categorization mutation
export function useAICategorize() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      companyId,
      limit,
      autoApprove,
    }: {
      companyId: number;
      limit?: number;
      autoApprove?: boolean;
    }) => runAICategorization(companyId, limit, autoApprove),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      queryClient.invalidateQueries({ queryKey: ["ai-metrics"] });
    },
  });
}

// AI Metrics
export function useAIMetrics(companyId: number | null, days = 30) {
  return useQuery({
    queryKey: ["ai-metrics", companyId, days],
    queryFn: () => {
      if (!companyId) throw new Error("Company ID required");
      return getAIMetrics(companyId, days);
    },
    enabled: !!companyId,
  });
}

// Sync mutation
export function useSyncCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      companyId,
      type,
    }: {
      companyId: number;
      type: "full" | "accounts" | "transactions";
    }) => syncCompany(companyId, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    },
  });
}
