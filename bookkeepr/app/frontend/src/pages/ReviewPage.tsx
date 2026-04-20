import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import {
  useCompanies,
  useReviewQueue,
  useReviewTransaction,
  useAICategorize,
  useAccounts,
} from "../hooks";
import { ReviewQueue } from "../components/transactions";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";
import { Loader2, Brain, Filter } from "lucide-react";
import { cn } from "../lib/utils";

export function ReviewPage() {
  const [searchParams] = useSearchParams();
  const [selectedCompany, setSelectedCompany] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedConfidence, setSelectedConfidence] = useState<string | undefined>(
    undefined
  );
  const [isProcessing, setIsProcessing] = useState(false);

  const { data: companies, isLoading: companiesLoading } = useCompanies();
  const { data: accounts } = useAccounts(selectedCompany);
  const {
    data: reviewQueue,
    isLoading: queueLoading,
  } = useReviewQueue(
    selectedCompany,
    "pending",
    selectedConfidence,
    currentPage,
    10
  );
  const reviewMutation = useReviewTransaction();
  const aiCategorize = useAICategorize();

  // Auto-select first company
  if (companies && companies.length > 0 && !selectedCompany) {
    setSelectedCompany(companies[0].id);
  }

  // Handle single transaction review from query param
  useEffect(() => {
    const txId = searchParams.get("tx");
    if (txId) {
      // Could scroll to or highlight specific transaction
      console.log("Reviewing transaction:", txId);
    }
  }, [searchParams]);

  const handleApprove = async (transactionId: number) => {
    setIsProcessing(true);
    try {
      await reviewMutation.mutateAsync({
        transactionId,
        action: "approve",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async (transactionId: number) => {
    setIsProcessing(true);
    try {
      await reviewMutation.mutateAsync({
        transactionId,
        action: "reject",
        notes: "Rejected by user",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCorrect = async (transactionId: number, accountId: number) => {
    setIsProcessing(true);
    try {
      await reviewMutation.mutateAsync({
        transactionId,
        action: "correct",
        accountId,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRunAI = async () => {
    if (!selectedCompany) return;
    setIsProcessing(true);
    try {
      await aiCategorize.mutateAsync({
        companyId: selectedCompany,
        limit: 50,
        autoApprove: false,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const isLoading = companiesLoading || queueLoading;

  // Calculate stats
  const pendingCount = reviewQueue?.total || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">Review Queue</h2>
          <p className="text-slate-500">
            Approve or correct AI categorization suggestions
          </p>
        </div>
        <div className="flex items-center gap-2">
          {companies && companies.length > 0 && (
            <select
              className="h-10 rounded-md border border-slate-200 bg-white px-3 text-sm"
              value={selectedCompany || ""}
              onChange={(e) => {
                setSelectedCompany(Number(e.target.value));
                setCurrentPage(1);
              }}
            >
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}
          <Button onClick={handleRunAI} disabled={isProcessing || !selectedCompany}>
            {isProcessing ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Brain className="h-4 w-4 mr-2" />
            )}
            Run AI
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-amber-600">
              {pendingCount}
            </div>
            <p className="text-sm text-slate-500">Pending Review</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">
              {reviewQueue?.transactions?.filter(
                (t) => (t.suggested_confidence || 0) >= 0.85
              ).length || 0}
            </div>
            <p className="text-sm text-slate-500">High Confidence</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-amber-600">
              {reviewQueue?.transactions?.filter(
                (t) => {
                  const conf = t.suggested_confidence || 0;
                  return conf >= 0.7 && conf < 0.85;
                }
              ).length || 0}
            </div>
            <p className="text-sm text-slate-500">Medium Confidence</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-red-600">
              {reviewQueue?.transactions?.filter(
                (t) => (t.suggested_confidence || 0) < 0.7
              ).length || 0}
            </div>
            <p className="text-sm text-slate-500">Low Confidence</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-slate-500" />
        <span className="text-sm text-slate-500">Filter by confidence:</span>
        <div className="flex gap-2">
          {["all", "high", "medium", "low"].map((level) => (
            <button
              key={level}
              onClick={() => {
                setSelectedConfidence(level === "all" ? undefined : level);
                setCurrentPage(1);
              }}
              className={cn(
                "px-3 py-1 rounded-full text-sm font-medium transition-colors",
                (selectedConfidence || "all") === level
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}
            >
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Review Queue */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
        </div>
      ) : reviewQueue ? (
        <ReviewQueue
          transactions={reviewQueue.transactions}
          total={reviewQueue.total}
          pages={reviewQueue.pages}
          currentPage={currentPage}
          onPageChange={setCurrentPage}
          onApprove={handleApprove}
          onReject={handleReject}
          onCorrect={handleCorrect}
          accounts={accounts?.map((a) => ({ id: a.id, name: a.name })) || []}
          isLoading={isProcessing}
        />
      ) : (
        <div className="text-center py-8 text-slate-500">
          Select a company to view review queue
        </div>
      )}
    </div>
  );
}
