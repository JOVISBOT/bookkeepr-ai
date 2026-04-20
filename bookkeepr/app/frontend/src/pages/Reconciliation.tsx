import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, ArrowLeft } from "lucide-react";
import { getBankStatement, getCompanies } from "../lib/api";
import type { BankStatementLine } from "../types";
import {
  BankStatementUpload,
  ReconciliationTable,
  MatchReviewModal,
  SummaryCards,
} from "../components/reconciliation";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Select } from "../components/ui/Select";

export function Reconciliation() {
  const { statementId } = useParams<{ statementId?: string }>();
  const navigate = useNavigate();
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);
  const [showUpload, setShowUpload] = useState(true);
  const [reviewLine, setReviewLine] = useState<BankStatementLine | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Get companies
  const { data: companiesData } = useQuery({
    queryKey: ["companies"],
    queryFn: getCompanies,
  });

  // Get current statement details
  const { data: statementData } = useQuery({
    queryKey: ["bank-statement", statementId],
    queryFn: () => getBankStatement(parseInt(statementId!)),
    enabled: !!statementId,
  });

  const companies = companiesData || [];
  const currentStatement = statementData?.statement;

  // Auto-select company from statement or default to first
  useEffect(() => {
    if (currentStatement) {
      setSelectedCompanyId(currentStatement.company_id);
      setShowUpload(false);
    } else if (companies.length > 0 && !selectedCompanyId) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [currentStatement, companies, selectedCompanyId]);

  const handleUploadSuccess = (newStatementId: number) => {
    navigate(`/reconciliation/${newStatementId}`);
  };

  const handleReviewLine = (line: BankStatementLine) => {
    setReviewLine(line);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setReviewLine(null);
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bank Reconciliation</h1>
          <p className="text-gray-500 mt-1">
            Match bank statement lines with QuickBooks transactions
          </p>
        </div>

        {/* Company Selector */}
        <div className="w-64">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Company
          </label>
          <Select
            value={selectedCompanyId?.toString() || ""}
            onChange={(e) => setSelectedCompanyId(parseInt(e.target.value))}
            disabled={companies.length === 0 || !!statementId}
          >
            {companies.map((company) => (
              <option key={company.id} value={company.id}>
                {company.name}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {/* Upload Section (Collapsible) */}
      {selectedCompanyId && (
        <div>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-3"
          >
            {showUpload ? (
              <>
                <ChevronUp className="h-4 w-4" />
                Hide Upload
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4" />
                Upload New Statement
              </>
            )}
          </button>

          {showUpload && (
            <BankStatementUpload
              companyId={selectedCompanyId}
              onUploadSuccess={handleUploadSuccess}
            />
          )}
        </div>
      )}

      {/* Current Statement View */}
      {statementId && currentStatement ? (
        <div className="space-y-6">
          {/* Statement Header */}
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate("/reconciliation")}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back
                </Button>
                <div>
                  <h2 className="text-lg font-semibold">
                    {currentStatement.file_name}
                  </h2>
                  <p className="text-sm text-gray-500">
                    Uploaded{" "}
                    {new Date(currentStatement.upload_date).toLocaleDateString()} ·{" "}
                    {currentStatement.line_count} lines ·{" "}
                    Status:{" "}
                    <span
                      className={`font-medium ${
                        currentStatement.status === "reconciled"
                          ? "text-green-600"
                          : "text-yellow-600"
                      }`}
                    >
                      {currentStatement.status}
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Summary Cards */}
          <SummaryCards statementId={parseInt(statementId)} />

          {/* Reconciliation Table */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Statement Lines</h3>
            <ReconciliationTable
              statementId={parseInt(statementId)}
              onReviewLine={handleReviewLine}
            />
          </Card>
        </div>
      ) : statementId ? (
        // Loading or invalid statement
        <Card className="p-8 text-center">
          <p className="text-gray-500">Loading statement...</p>
        </Card>
      ) : (
        // No statement selected - show instructions
        <Card className="p-8 text-center">
          <p className="text-gray-600 mb-2">
            Upload a bank statement CSV to begin reconciliation
          </p>
          <p className="text-sm text-gray-500">
            Or select a previously uploaded statement from your statement history
          </p>
        </Card>
      )}

      {/* Match Review Modal */}
      <MatchReviewModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        line={reviewLine}
        companyId={currentStatement?.company_id || selectedCompanyId || 0}
        statementId={parseInt(statementId || "0")}
      />
    </div>
  );
}
