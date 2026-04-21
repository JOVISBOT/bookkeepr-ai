import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import {
  useCompanies,
  useReviewQueue,
  useReviewTransaction,
  useAccounts,
} from "../hooks";
import { ReviewQueue } from "../components/transactions";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Loader2 } from "lucide-react";

export function ReviewPage() {
  const [searchParams] = useSearchParams();
  const [selectedCompany, setSelectedCompany] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedConfidence, setSelectedConfidence] = useState<string | undefined>(
    undefined
  );

  const { data: companies, isLoading: companiesLoading } = useCompanies();
  const { data: accounts, isLoading: accountsLoading } = useAccounts(selectedCompany);

  const {
    data: reviewQueue,
    isLoading: queueLoading,
    refetch: refetchQueue,
  } = useReviewQueue(selectedCompany, "pending", selectedConfidence, currentPage);

  const reviewMutation = useReviewTransaction();

  // Get initial company from URL
  useEffect(() => {
    const companyId = searchParams.get("company");
    if (companyId) {
      setSelectedCompany(parseInt(companyId, 10));
    } else if (companies && companies.length > 0 && !selectedCompany) {
      setSelectedCompany(companies[0].id);
    }
  }, [searchParams, companies, selectedCompany]);

  const handleApprove = async (transactionId: number) => {
    await reviewMutation.mutateAsync({
      transactionId,
      action: "approve",
    });
    refetchQueue();
  };

  const handleReject = async (transactionId: number) => {
    await reviewMutation.mutateAsync({
      transactionId,
      action: "reject",
    });
    refetchQueue();
  };

  const handleCorrect = async (transactionId: number, accountId: number) => {
    await reviewMutation.mutateAsync({
      transactionId,
      action: "correct",
      accountId,
    });
    refetchQueue();
  };

  const isLoading = companiesLoading || queueLoading || accountsLoading;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Review Queue</h1>
          <p className="text-muted-foreground">
            Review and approve AI-categorized transactions
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={selectedConfidence}
            onChange={(e) => setSelectedConfidence(e.target.value || undefined)}
            className="px-3 py-2 border rounded-md text-sm"
          >
            <option value="">All Confidence</option>
            <option value="low">Low (&lt;70%)</option>
            <option value="medium">Medium (70-85%)</option>
            <option value="high">High (&gt;85%)</option>
          </select>
          <Button
            variant="outline"
            onClick={() => refetchQueue()}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Refresh"
            )}
          </Button>
        </div>
      </div>

      {/* Company Selector */}
      {companies && companies.length > 1 && (
        <Card>
          <CardContent className="pt-6">
            <label className="text-sm font-medium mb-2 block">Select Company</label>
            <select
              value={selectedCompany || ""}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                setSelectedCompany(isNaN(val) ? null : val);
                setCurrentPage(1);
              }}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="">Select a company...</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <ReviewQueue
          transactions={reviewQueue?.transactions || []}
          total={reviewQueue?.total || 0}
          pages={reviewQueue?.pages || 0}
          currentPage={currentPage}
          onPageChange={setCurrentPage}
          onApprove={handleApprove}
          onReject={handleReject}
          onCorrect={handleCorrect}
          accounts={accounts || []}
        />
      )}
    </div>
  );
}
