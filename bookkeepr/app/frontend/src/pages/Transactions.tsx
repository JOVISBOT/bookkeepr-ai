import { useState } from "react";
import { useCompanies, useTransactions } from "../hooks";
import { TransactionTable } from "../components/transactions";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Loader2, Brain } from "lucide-react";
import type { Transaction } from "../types";
import { useAICategorize } from "../hooks/useTransactions";

export function Transactions() {
  const [selectedCompany, setSelectedCompany] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [isCategorizing, setIsCategorizing] = useState(false);

  const { data: companies, isLoading: companiesLoading } = useCompanies();
  const { data: transactions, isLoading: transactionsLoading } = useTransactions(
    selectedCompany,
    currentPage,
    25
  );
  const aiCategorize = useAICategorize();

  // Auto-select first company
  if (companies && companies.length > 0 && !selectedCompany) {
    setSelectedCompany(companies[0].id);
  }

  const handleReview = (transaction: Transaction) => {
    // Navigate to review page with this transaction
    window.location.href = `/review?tx=${transaction.id}`;
  };

  const handleAICategorize = async () => {
    if (!selectedCompany) return;
    setIsCategorizing(true);
    try {
      await aiCategorize.mutateAsync({
        companyId: selectedCompany,
        limit: 100,
        autoApprove: true,
      });
    } finally {
      setIsCategorizing(false);
    }
  };

  const isLoading = companiesLoading || transactionsLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">All Transactions</h2>
          <p className="text-slate-500">
            View and manage your transaction history
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
          <Button 
            onClick={handleAICategorize} 
            disabled={isCategorizing || !selectedCompany}
          >
            {isCategorizing ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Brain className="h-4 w-4 mr-2" />
            )}
            Run AI Categorize
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">
              {transactions?.total?.toLocaleString() || "0"}
            </div>
            <p className="text-sm text-slate-500">Total Transactions</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">
              {transactions?.transactions?.filter(
                (t) => t.categorization_status === "categorized"
              ).length || 0}
            </div>
            <p className="text-sm text-slate-500">Categorized</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-amber-600">
              {transactions?.transactions?.filter(
                (t) => t.categorization_status === "suggested"
              ).length || 0}
            </div>
            <p className="text-sm text-slate-500">Suggested</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-slate-600">
              {transactions?.transactions?.filter(
                (t) => t.categorization_status === "uncategorized"
              ).length || 0}
            </div>
            <p className="text-sm text-slate-500">Uncategorized</p>
          </CardContent>
        </Card>
      </div>

      {/* Transaction Table */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction List</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
            </div>
          ) : transactions ? (
            <TransactionTable
              data={transactions.transactions}
              total={transactions.total}
              pages={transactions.pages}
              currentPage={currentPage}
              onPageChange={setCurrentPage}
              onReview={handleReview}
            />
          ) : (
            <div className="text-center py-8 text-slate-500">
              Select a company to view transactions
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
