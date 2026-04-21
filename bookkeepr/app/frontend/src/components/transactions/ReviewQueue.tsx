import { useState } from "react";
import { formatCurrency, formatDate, cn } from "../../lib/utils";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import type { Transaction } from "../../types";
import {
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Check,
} from "lucide-react";

interface ReviewQueueProps {
  transactions: Transaction[];
  total: number;
  pages: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  onApprove: (transactionId: number) => void;
  onReject: (transactionId: number) => void;
  onCorrect: (transactionId: number, accountId: number) => void;
  accounts: { id: number; name: string }[];
  isLoading?: boolean;
}

export function ReviewQueue({
  transactions,
  total,
  pages,
  currentPage,
  onPageChange,
  onApprove,
  onReject,
  onCorrect,
  accounts,
  isLoading,
}: ReviewQueueProps) {
  const [selectedAccounts, setSelectedAccounts] = useState<Record<number, number>>(
    {}
  );

  const getConfidenceBadge = (confidence: number | null) => {
    if (!confidence) return <Badge variant="secondary">Unknown</Badge>;
    if (confidence >= 0.85)
      return <Badge variant="success">{Math.round(confidence * 100)}%</Badge>;
    if (confidence >= 0.7)
      return <Badge variant="warning">{Math.round(confidence * 100)}%</Badge>;
    return <Badge variant="destructive">{Math.round(confidence * 100)}%</Badge>;
  };

  const selectedCount = Object.keys(selectedAccounts).length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Review Queue</CardTitle>
          <p className="text-sm text-slate-500 mt-1">
            {total} transactions need your attention
          </p>
        </div>
        {selectedCount > 0 && (
          <Button
            variant="default"
            size="sm"
            onClick={() => {
              // Bulk approve selected
              Object.entries(selectedAccounts).forEach(([txId, accId]) => {
                onCorrect(Number(txId), accId);
              });
              setSelectedAccounts({});
            }}
          >
            <Check className="h-4 w-4 mr-1" />
            Approve {selectedCount} Selected
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {isLoading ? (
            <div className="text-center py-8 text-slate-500">Loading...  </div>
          ) : transactions.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <p className="text-slate-600">All caught up! No transactions need review.</p>
            </div>
          ) : (
            transactions.map((tx) => (
              <div
                key={tx.id}
                className="border rounded-lg p-4 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium">
                        {tx.vendor_name || "Unknown Vendor"}
                      </span>
                      <span className="text-slate-500">•</span>
                      <span className="text-slate-600">
                        {formatDate(tx.transaction_date)}
                      </span>
                      <span
                        className={cn(
                          "font-medium",
                          tx.amount < 0 ? "text-red-600" : "text-green-600"
                        )}
                      >
                        {formatCurrency(tx.amount)}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 mt-1 truncate">
                      {tx.description || "No description"}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-slate-500">AI Suggested:</span>
                      <Badge variant="secondary">
                        {tx.suggested_category || "Uncategorized"}
                      </Badge>
                      {getConfidenceBadge(tx.suggested_confidence)}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <select
                      className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm"
                      value={selectedAccounts[tx.id] || ""}
                      onChange={(e) =>
                        setSelectedAccounts((prev) => ({
                          ...prev,
                          [tx.id]: Number(e.target.value),
                        }))
                      }
                    >
                      <option value="">Select category...</option>
                      {accounts.map((acc) => (
                        <option key={acc.id} value={acc.id}>
                          {acc.name}
                        </option>
                      ))}
                    </select>

                    <Button
                      variant="outline"
                      size="sm"
                      className="text-green-600 border-green-200 hover:bg-green-50"
                      onClick={() => onApprove(tx.id)}
                      disabled={isLoading}
                    >
                      <CheckCircle className="h-4 w-4" />
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 border-red-200 hover:bg-red-50"
                      onClick={() => onReject(tx.id)}
                      disabled={isLoading}
                    >
                      <XCircle className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Show suggestions if expanded */}
                {tx.suggestions && tx.suggestions.length > 0 && (
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-xs text-slate-500 mb-2">AI Suggestions:</p>
                    <div className="flex flex-wrap gap-2">
                      {tx.suggestions.slice(0, 3).map((sugg) => (
                        <Button
                          key={sugg.account_id}
                          variant="ghost"
                          size="sm"
                          className="text-xs h-7"
                          onClick={() => onCorrect(tx.id, sugg.account_id)}
                        >
                          {sugg.account_name} ({Math.round(sugg.confidence * 100)}%)
                        </Button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}

          {total > 0 && (
            <div className="flex items-center justify-between pt-4 border-t">
              <div className="text-sm text-slate-500">
                Showing {transactions.length} of {total}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-slate-500">
                  Page {currentPage} of {pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange(currentPage + 1)}
                  disabled={currentPage >= pages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
