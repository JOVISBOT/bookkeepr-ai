import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { 
  Upload, 
  FileSpreadsheet, 
  Database, 
  CreditCard,
  CheckCircle2,
  AlertCircle,
  Loader2
} from "lucide-react";

interface ImportSource {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  status: "available" | "coming_soon" | "connected";
  features: string[];
}

const importSources: ImportSource[] = [
  {
    id: "quickbooks",
    name: "QuickBooks Online",
    description: "Connect directly to QBO for real-time sync",
    icon: <Database className="h-6 w-6 text-green-600" />,
    status: "available",
    features: ["Auto-sync", "Real-time", "Multi-company"],
  },
  {
    id: "csv",
    name: "CSV Upload",
    description: "Import transactions from CSV files",
    icon: <FileSpreadsheet className="h-6 w-6 text-blue-600" />,
    status: "available",
    features: ["Bulk import", "Column mapping", "Validation"],
  },
  {
    id: "plaid",
    name: "Plaid (Bank Connect)",
    description: "Connect 12,000+ banks and credit cards",
    icon: <CreditCard className="h-6 w-6 text-purple-600" />,
    status: "coming_soon",
    features: ["12,000+ banks", "Real-time", "Secure"],
  },
  {
    id: "stripe",
    name: "Stripe",
    description: "Import payments and payouts",
    icon: <CreditCard className="h-6 w-6 text-indigo-600" />,
    status: "coming_soon",
    features: ["Payments", "Payouts", "Fees tracking"],
  },
];

export function DataImport() {
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [importStatus, setImportStatus] = useState<"idle" | "uploading" | "processing" | "complete" | "error">("idle");

  const handleImport = async () => {
    if (!selectedSource) return;

    setIsImporting(true);
    setImportStatus("uploading");
    setImportProgress(0);

    // Simulate import process
    for (let i = 0; i <= 100; i += 10) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      setImportProgress(i);
      if (i === 30) setImportStatus("processing");
      if (i === 80) setImportStatus("complete");
    }

    setIsImporting(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Data Import</h2>
        <p className="text-slate-500">Connect your accounts or upload files to import transactions</p>
      </div>

      {/* Import Sources Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {importSources.map((source) => (
          <Card
            key={source.id}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedSource === source.id
                ? "ring-2 ring-blue-500 border-blue-500"
                : "border-slate-200"
            } ${source.status === "coming_soon" ? "opacity-60" : ""}`}
            onClick={() =>
              source.status !== "coming_soon" && setSelectedSource(source.id)
            }
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-slate-50 rounded-lg">{source.icon}</div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{source.name}</h3>
                    <p className="text-sm text-slate-500">{source.description}</p>
                  </div>
                </div>
                <Badge
                  variant={
                    source.status === "available"
                      ? "success"
                      : source.status === "connected"
                      ? "default"
                      : "secondary"
                  }
                >
                  {source.status === "coming_soon" ? "Coming Soon" : "Available"}
                </Badge>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {source.features.map((feature) => (
                  <Badge key={feature} variant="outline" className="text-xs">
                    {feature}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Import Progress */}
      {isImporting && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              {importStatus === "complete" ? (
                <CheckCircle2 className="h-8 w-8 text-green-600" />
              ) : importStatus === "error" ? (
                <AlertCircle className="h-8 w-8 text-red-600" />
              ) : (
                <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
              )}
              <div className="flex-1">
                <p className="font-medium text-slate-900">
                  {importStatus === "uploading"
                    ? "Uploading transactions..."
                    : importStatus === "processing"
                    ? "Processing and categorizing..."
                    : importStatus === "complete"
                    ? "Import complete!"
                    : "Preparing import..."}
                </p>
                <div className="mt-2 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-300"
                    style={{ width: `${importProgress}%` }}
                  />
                </div>
              </div>
              <span className="text-sm font-medium text-slate-600">
                {importProgress}%
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Import Button */}
      {selectedSource && !isImporting && (
        <div className="flex justify-end">
          <Button onClick={handleImport} className="gap-2">
            <Upload className="h-4 w-4" />
            Start Import
          </Button>
        </div>
      )}

      {/* CSV Upload Section */}
      {selectedSource === "csv" && !isImporting && (
        <Card>
          <CardHeader>
            <CardTitle>CSV Import</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:bg-slate-50 transition-colors cursor-pointer">
              <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-600 font-medium">Drop CSV file here or click to browse</p>
              <p className="text-sm text-slate-400 mt-2">Supported formats: .csv, .xlsx, .xls</p>
            </div>

            <div className="bg-slate-50 p-4 rounded-lg">
              <p className="font-medium text-sm text-slate-700 mb-2">Expected CSV Columns:</p>
              <div className="flex flex-wrap gap-2">
                {["Date", "Description", "Amount", "Category", "Vendor"].map((col) => (
                  <Badge key={col} variant="outline" className="bg-white">
                    {col}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
