import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { X, Check, Search, AlertCircle } from "lucide-react";
import {
  approveMatch,
  rejectMatch,
  createManualMatch,
  getTransactionsForMatching,
} from "../../lib/api";
import type { BankStatementLine, Transaction } from "../../types";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";

interface MatchReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  line: BankStatementLine | null;
  companyId: number;
  statementId: number;
}

export function MatchReviewModal({
  isOpen,
  onClose,
  line,
  companyId,
  statementId,
}: MatchReviewModalProps) {
  const [activeTab, setActiveTab] = useState<"review" | "search">("review");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFilters, setSearchFilters] = useState({
    date_from: "",
    date_to: "",
    amount_min: "",
    amount_max: "",
  });
  const [selectedTransaction, setSelectedTransaction] =
    useState<Transaction | null>(null);
  const queryClient = useQueryClient();

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setActiveTab("review");
      setSearchQuery("");
      setSearchFilters({
        date_from: "",
        date_to: "",
        amount_min: "",
        amount_max: "",
      });
      setSelectedTransaction(null);
    }
  }, [isOpen]);

  const { data: searchResults, isLoading: isSearching } = useQuery<{
    transactions: Transaction[];
    total: number;
  }>({
    queryKey: [
      "transactions-for-matching",
      companyId,
      searchQuery,
      searchFilters,
    ],
    queryFn: () =>
      getTransactionsForMatching(companyId, {
        query: searchQuery || undefined,
        date_from: searchFilters.date_from || undefined,
        date_to: searchFilters.date_to || undefined,
        amount_min: searchFilters.amount_min
          ? parseFloat(searchFilters.amount_min)
          : undefined,
        amount_max: searchFilters.amount_max
          ? parseFloat(searchFilters.amount_max)
          : undefined,
        limit: 20,
      }),
    enabled: activeTab === "search" && !!(searchQuery || searchFilters.date_from),
  });

  const approveMutation = useMutation({
    mutationFn: approveMatch,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["bank-statement-lines", statementId],
      });
      queryClient.invalidateQueries({
        queryKey: ["reconciliation-summary", statementId],
      });
      onClose();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: rejectMatch,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["bank-statement-lines", statementId],
      });
      queryClient.invalidateQueries({
        queryKey: ["reconciliation-summary", statementId],
      });
      onClose();
    },
  });

  const manualMatchMutation = useMutation({
    mutationFn: (transactionId: number) =>
      createManualMatch(line!.id, transactionId, companyId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["bank-statement-lines", statementId],
      });
      queryClient.invalidateQueries({
        queryKey: ["reconciliation-summary", statementId],
      });
      onClose();
    },
  });

  if (!isOpen || !line) return null;

  const formatAmount = (amount: string | number) => {
    const num = typeof amount === "string" ? parseFloat(amount) : amount;
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(num);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const handleApprove = () => {
    const matchId = line.proposed_matches?.[0]?.id;
    if (matchId) {
      approveMutation.mutate(matchId);
    }
  };

  const handleReject = () => {
    const matchId = line.proposed_matches?.[0]?.id;
    if (matchId) {
      rejectMutation.mutate(matchId);
    }
  };

  const handleManualMatch = () => {
    if (selectedTransaction) {
      manualMatchMutation.mutate(selectedTransaction.id);
    }
  };

  const hasProposedMatch =
    line.proposed_matches && line.proposed_matches.length > 0;
  const proposedMatch = line.proposed_matches?.[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold">Review Match</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="px-6 border-b">
          <div className="flex gap-6">
            <button
              onClick={() => setActiveTab("review")}
              className={`py-3 border-b-2 transition-colors ${
                activeTab === "review"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent hover:text-gray-700"
              }`}
            >
              Review Match
            </button>
            <button
              onClick={() => setActiveTab("search")}
              className={`py-3 border-b-2 transition-colors ${
                activeTab === "search"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent hover:text-gray-700"
              }`}
            >
              Find Different Match
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === "review" ? (
            <div className="space-y-6">
              {/* Bank Line Details */}
              <Card className="p-4 bg-blue-50 border-blue-200">
                <h3 className="font-semibold text-blue-900 mb-3">
                  Bank Statement Line
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Date:</span>{" "}
                    <span className="font-medium">
                      {formatDate(line.line_date)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Amount:</span>{" "}
                    <span
                      className={`font-medium ${
                        parseFloat(line.amount) < 0
                          ? "text-red-600"
                          : "text-green-600"
                      }`}
                    >
                      {formatAmount(line.amount)}
                    </span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-600">Description:</span>{" "}
                    <span className="font-medium">
                      {line.description || "-"}
                    </span>
                  </div>
                  {line.reference_number && (
                    <div>
                      <span className="text-gray-600">Reference:</span>{" "}
                      <span className="font-medium">
                        {line.reference_number}
                      </span>
                    </div>
                  )}
                </div>
              </Card>

              {/* Proposed Match */}
              {hasProposedMatch ? (
                <Card className="p-4 bg-green-50 border-green-200">
                  <h3 className="font-semibold text-green-900 mb-3">
                    Proposed Match
                    {proposedMatch?.is_auto_matched && (
                      <span className="ml-2 text-xs bg-green-200 text-green-800 px-2 py-1 rounded">
                        Auto-matched
                      </span>
                    )}
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Confidence Score:</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              proposedMatch!.confidence >= 0.85
                                ? "bg-green-500"
                                : proposedMatch!.confidence >= 0.6
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                            }`}
                            style={{
                              width: `${proposedMatch!.confidence * 100}%`,
                            }}
                          />
                        </div>
                        <span className="font-semibold">
                          {Math.round(proposedMatch!.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                    {line.matched_transaction && (
                      <div className="grid grid-cols-2 gap-4 text-sm mt-4">
                        <div>
                          <span className="text-gray-600">QBO Date:</span>{" "}
                          <span className="font-medium">
                            {formatDate(line.matched_transaction.transaction_date)}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">QBO Amount:</span>{" "}
                          <span className="font-medium">
                            {formatAmount(line.matched_transaction.amount)}
                          </span>
                        </div>
                        <div className="col-span-2">
                          <span className="text-gray-600">Description:</span>{" "}
                          <span className="font-medium">
                            {line.matched_transaction.description ||
                              line.matched_transaction.vendor_name ||
                              "-"}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              ) : (
                <Card className="p-4 bg-yellow-50 border-yellow-200">
                  <div className="flex items-center gap-2 text-yellow-800">
                    <AlertCircle className="h-5 w-5" />
                    <span>No proposed match found for this line.</span>
                  </div>
                  <p className="text-sm text-yellow-700 mt-2">
                    Switch to "Find Different Match" to search for transactions.
                  </p>
                </Card>
              )}

              {/* Action Buttons */}
              {hasProposedMatch && (
                <div className="flex gap-3 justify-end">
                  <Button
                    variant="outline"
                    onClick={handleReject}
                    disabled={rejectMutation.isPending}
                  >
                    Reject Match
                  </Button>
                  <Button
                    onClick={handleApprove}
                    disabled={approveMutation.isPending}
                  >
                    <Check className="h-4 w-4 mr-2" />
                    Approve Match
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Search Filters */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <div className="relative">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date From
                  </label>
                  <Input
                    type="date"
                    value={searchFilters.date_from}
                    onChange={(e) =>
                      setSearchFilters({
                        ...searchFilters,
                        date_from: e.target.value,
                      })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date To
                  </label>
                  <Input
                    type="date"
                    value={searchFilters.date_to}
                    onChange={(e) =>
                      setSearchFilters({ ...searchFilters, date_to: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Amount Range
                  </label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      placeholder="Min"
                      value={searchFilters.amount_min}
                      onChange={(e) =>
                        setSearchFilters({
                          ...searchFilters,
                          amount_min: e.target.value,
                        })
                      }
                    />
                    <Input
                      type="number"
                      placeholder="Max"
                      value={searchFilters.amount_max}
                      onChange={(e) =>
                        setSearchFilters({
                          ...searchFilters,
                          amount_max: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>
              </div>

              {/* Search Results */}
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium">Date</th>
                      <th className="px-4 py-3 text-left font-medium">
                        Description
                      </th>
                      <th className="px-4 py-3 text-left font-medium">Amount</th>
                      <th className="px-4 py-3 text-left font-medium">Type</th>
                      <th className="px-4 py-3 text-left font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {isSearching ? (
                      <tr>
                        <td
                          colSpan={5}
                          className="px-4 py-8 text-center text-gray-500"
                        >
                          Searching...
                        </td>
                      </tr>
                    ) : searchResults?.transactions?.length ? (
                      searchResults.transactions.map((txn) => (
                        <tr
                          key={txn.id}
                          className={`hover:bg-gray-50 ${
                            selectedTransaction?.id === txn.id
                              ? "bg-blue-50"
                              : ""
                          }`}
                        >
                          <td className="px-4 py-3">
                            {formatDate(txn.transaction_date)}
                          </td>
                          <td className="px-4 py-3">
                            {txn.description || txn.vendor_name || "-"}
                          </td>
                          <td
                            className={`px-4 py-3 ${
                              txn.amount < 0 ? "text-red-600" : "text-green-600"
                            }`}
                          >
                            {formatAmount(txn.amount)}
                          </td>
                          <td className="px-4 py-3">{txn.transaction_type}</td>
                          <td className="px-4 py-3">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedTransaction(txn)}
                            >
                              Select
                            </Button>
                          </td>
                        </tr>
                      ))
                    ) : searchQuery || searchFilters.date_from ? (
                      <tr>
                        <td
                          colSpan={5}
                          className="px-4 py-8 text-center text-gray-500"
                        >
                          No transactions found
                        </td>
                      </tr>
                    ) : (
                      <tr>
                        <td
                          colSpan={5}
                          className="px-4 py-8 text-center text-gray-400"
                        >
                          Enter search criteria above
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Selected Transaction */}
              {selectedTransaction && (
                <Card className="p-4 bg-blue-50 border-blue-200">
                  <h4 className="font-semibold mb-2">Selected Transaction</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Date:</span>{" "}
                      <span className="font-medium">
                        {formatDate(selectedTransaction.transaction_date)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Amount:</span>{" "}
                      <span className="font-medium">
                        {formatAmount(selectedTransaction.amount)}
                      </span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-600">Description:</span>{" "}
                      <span className="font-medium">
                        {selectedTransaction.description ||
                          selectedTransaction.vendor_name ||
                          "-"}
                      </span>
                    </div>
                  </div>
                </Card>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 justify-end">
                <Button variant="outline" onClick={() => onClose()}>
                  Cancel
                </Button>
                <Button
                  onClick={handleManualMatch}
                  disabled={!selectedTransaction || manualMatchMutation.isPending}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Create Manual Match
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
