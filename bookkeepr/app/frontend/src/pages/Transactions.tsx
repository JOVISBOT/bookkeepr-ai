import { useState } from "react";
import { useCompanies, useTransactions } from "../hooks";
import { TransactionTable } from "../components/transactions";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Loader2, Brain } from "lucide-react";
import { useAICategorize } from "../hooks/useTransactions";

export function Transactions() {
  const [selectedCompany, setSelectedCompany] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [isCategorizing, setIsCategorizing] = useState(false);

  const { data: companies, isLoading: companiesLoading } = useCompanies();
  const { data: transactionsResponse, isLoading: transactionsLoading } = useTransactions(
    selectedCompany,
    currentPage,
    25
  );

  const aiCategorize = useAICategorize();

  const handleAICategorize = async () => {
    if (!selectedCompany) return;
    setIsCategorizing(true);
    try {
      await aiCategorize.mutateAsync({ companyId: selectedCompany });
    } finally {
      setIsCategorizing(false);
    }
  };

  const isLoading = companiesLoading || transactionsLoading;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Transactions</h1>
          <p className="text-muted-foreground">
            View and manage your transactions
          </p>
        </div>
        <Button
          onClick={handleAICategorize}
          disabled={isCategorizing || !selectedCompany}
          className="flex items-center gap-2"
        >
          {isCategorizing ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Categorizing...
            </>
          ) : (
            <>
              <Brain className="h-4 w-4" />
              AI Categorize
            </>
          )}
        </Button>
      </div>

      {/* Company Selector */}
      {companies && companies.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Select Company</CardTitle>
          </CardHeader>
          <CardContent>
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
        <TransactionTable
          data={transactionsResponse?.transactions || []}
          total={transactionsResponse?.total || 0}
          pages={transactionsResponse?.pages || 0}
          currentPage={currentPage}
          onPageChange={setCurrentPage}
        />
      )}
    </div>
  );
}
