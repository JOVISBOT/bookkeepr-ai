import { useState, useCallback, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, File, CheckCircle, AlertCircle, X } from "lucide-react";
import { uploadBankStatement } from "../../lib/api";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";

interface BankStatementUploadProps {
  companyId: number;
  onUploadSuccess?: (statementId: number) => void;
}

export function BankStatementUpload({
  companyId,
  onUploadSuccess,
}: BankStatementUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [metadata, setMetadata] = useState({
    statement_date: "",
    start_balance: "",
    end_balance: "",
  });
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("No file selected");
      return uploadBankStatement(companyId, file, {
        statement_date: metadata.statement_date || undefined,
        start_balance: metadata.start_balance
          ? parseFloat(metadata.start_balance)
          : undefined,
        end_balance: metadata.end_balance
          ? parseFloat(metadata.end_balance)
          : undefined,
      });
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["bank-statements"] });
      setFile(null);
      setMetadata({ statement_date: "", start_balance: "", end_balance: "" });
      if (onUploadSuccess) {
        onUploadSuccess(data.statement.id);
      }
    },
  });

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const droppedFile = files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  };

  const validateFile = (file: File): boolean => {
    const allowedTypes = [
      "text/csv",
      "application/vnd.ms-excel",
      "application/csv",
    ];
    const isCSV =
      allowedTypes.includes(file.type) || file.name.toLowerCase().endsWith(".csv");

    if (!isCSV) {
      uploadMutation.reset();
      return false;
    }
    return true;
  };

  const clearFile = () => {
    setFile(null);
    uploadMutation.reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleUpload = () => {
    if (file) {
      uploadMutation.mutate();
    }
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Upload Bank Statement</h3>

      {/* Drop Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200
          ${
            isDragging
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-gray-400"
          }
          ${file ? "bg-green-50 border-green-400" : ""}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="hidden"
        />

        {file ? (
          <div className="flex items-center justify-center gap-3">
            <File className="h-8 w-8 text-green-600" />
            <div className="text-left">
              <p className="font-medium text-green-700">{file.name}</p>
              <p className="text-sm text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearFile();
              }}
              className="p-1 hover:bg-gray-200 rounded-full transition-colors"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>
        ) : (
          <>
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600 font-medium">
              Drop your CSV file here, or click to browse
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Supports bank export CSV files
            </p>
          </>
        )}
      </div>

      {/* Metadata Form */}
      {file && (
        <div className="mt-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Statement Date
              </label>
              <Input
                type="date"
                value={metadata.statement_date}
                onChange={(e) =>
                  setMetadata({ ...metadata, statement_date: e.target.value })
                }
                placeholder="YYYY-MM-DD"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Balance
              </label>
              <Input
                type="number"
                step="0.01"
                value={metadata.start_balance}
                onChange={(e) =>
                  setMetadata({ ...metadata, start_balance: e.target.value })
                }
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Balance
              </label>
              <Input
                type="number"
                step="0.01"
                value={metadata.end_balance}
                onChange={(e) =>
                  setMetadata({ ...metadata, end_balance: e.target.value })
                }
                placeholder="0.00"
              />
            </div>
          </div>
        </div>
      )}

      {/* Upload Progress / Status */}
      {uploadMutation.isPending && (
        <div className="mt-4">
          <div className="flex items-center gap-2 text-blue-600">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span>Uploading and parsing CSV...</span>
          </div>
        </div>
      )}

      {uploadMutation.isSuccess && (
        <div className="mt-4 flex items-center gap-2 text-green-600">
          <CheckCircle className="h-5 w-5" />
          <span>
            Uploaded successfully! Created{" "}
            {uploadMutation.data.lines_created} lines.
          </span>
        </div>
      )}

      {uploadMutation.isError && (
        <div className="mt-4 flex items-center gap-2 text-red-600">
          <AlertCircle className="h-5 w-5" />
          <span>
            {uploadMutation.error instanceof Error
              ? uploadMutation.error.message
              : "Upload failed"}
          </span>
        </div>
      )}

      {/* Upload Button */}
      {file && (
        <div className="mt-6 flex justify-end">
          <Button
            onClick={handleUpload}
            disabled={uploadMutation.isPending}
            className="min-w-32"
          >
            {uploadMutation.isPending ? "Uploading..." : "Upload Statement"}
          </Button>
        </div>
      )}
    </Card>
  );
}
