import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { getBankStatement, getCompanies } from "../lib/api";
import type { BankStatement, BankStatementLine, Company } from "../types";
import {
  BankStatementUpload,
  ReconciliationTable,
  MatchReviewModal,
  SummaryCards,
} from "../components/reconciliation";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";

export function Reconciliation() {
  const { statementId } = useParams<{ statementId?: string }>();
  const navigate = useNavigate();
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);
  const [showUpload, setShowUpload] = useState(true);
  const [reviewLine, setReviewLine] = useState<BankStatementLine | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Get companies
  const { data: companies } = useQuery<Company[]>({
    queryKey: ["companies"],
    queryFn: getCompanies,
  });

  // Get statement if ID provided
  const { data: statementData } = useQuery<{ statement: BankStatement }>({
    queryKey: ["bank-statement", statementId],
    queryFn: () => getBankStatement(parseInt(statementId!, 10)),
    enabled: !!statementId,
  });

  const statement = statementData?.statement;

  useEffect(() => {
    if (statement) {
      setShowUpload(false);
      setSelectedCompanyId(statement.company_id);
    }
  }, [statement]);

  const handleUploadComplete = (id: number) => {
    navigate(`/reconciliation/${id}`);
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Bank Reconciliation</h1>
          <p className="text-muted-foreground">
            Match bank statements with your transactions
          </p>
        </div>
        {statementId && (
          <Button variant="outline" onClick={() => navigate("/reconciliation")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Upload
          </Button>
        )}
      </div>

      {/* Company Selector */}
      {companies && companies.length > 1 && !statementId && (
        <Card className="p-6">
          <label className="text-sm font-medium mb-2 block">Select Company</label>
          <select
            value={selectedCompanyId || ""}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              setSelectedCompanyId(isNaN(val) ? null : val);
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
        </Card>
      )}

      {/* Upload Section - only show if we have a company selected */}
      {showUpload && !statementId && selectedCompanyId && (
        <BankStatementUpload
          companyId={selectedCompanyId}
          onUploadSuccess={handleUploadComplete}
        />
      )}

      {/* Upload placeholder when no company selected */}
      {showUpload && !statementId && !selectedCompanyId && (
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">Select a company above to upload a bank statement</p>
        </Card>
      )}

      {/* Statement Review */}
      {statementId && (
        <>
          <SummaryCards statementId={parseInt(statementId, 10)} />
          <ReconciliationTable
            statementId={parseInt(statementId, 10)}
            onReviewLine={handleReviewLine}
          />
        </>
      )}

      {/* Review Modal */}
      {reviewLine && statementId && selectedCompanyId && (
        <MatchReviewModal
          line={reviewLine}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          statementId={parseInt(statementId, 10)}
          companyId={selectedCompanyId}
        />
      )}
    </div>
  );
}
