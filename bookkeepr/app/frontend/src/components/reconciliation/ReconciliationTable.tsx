import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type SortingState,
  type ColumnDef,
} from "@tanstack/react-table";
import { Check, X, Search, MoreHorizontal } from "lucide-react";
import { getBankStatementLines, approveMatch, rejectMatch } from "../../lib/api";
import type { BankStatementLine } from "../../types";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

interface ReconciliationTableProps {
  statementId: number;
  onReviewLine?: (line: BankStatementLine) => void;
}

export function ReconciliationTable({
  statementId,
  onReviewLine,
}: ReconciliationTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["bank-statement-lines", statementId, statusFilter],
    queryFn: () => getBankStatementLines(statementId, 1, 100, statusFilter || undefined),
    enabled: !!statementId,
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
    },
  });

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      unmatched: { variant: "secondary", label: "Unmatched" },
      matched: { variant: "default", label: "Matched" },
      approved: { variant: "outline", label: "Approved" },
      rejected: { variant: "destructive", label: "Rejected" },
    };
    const config = variants[status] || variants.unmatched;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.85)
      return <Badge variant="default">{Math.round(confidence * 100)}%</Badge>;
    if (confidence >= 0.6)
      return <Badge variant="secondary">{Math.round(confidence * 100)}%</Badge>;
    return <Badge variant="outline">{Math.round(confidence * 100)}%</Badge>;
  };

  const formatAmount = (amount: string) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      signDisplay: "auto",
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

  const columns: ColumnDef<BankStatementLine>[] = [
    {
      accessorKey: "line_date",
      header: "Date",
      cell: ({ row }) => formatDate(row.original.line_date),
    },
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => (
        <div className="max-w-xs truncate" title={row.original.description || ""}>
          {row.original.description || "-"}
        </div>
      ),
    },
    {
      accessorKey: "amount",
      header: "Amount",
      cell: ({ row }) => (
        <span
          className={
            parseFloat(row.original.amount) < 0
              ? "text-red-600"
              : "text-green-600"
          }
        >
          {formatAmount(row.original.amount)}
        </span>
      ),
    },
    {
      accessorKey: "match_status",
      header: "Status",
      cell: ({ row }) => getStatusBadge(row.original.match_status),
    },
    {
      accessorKey: "match_confidence",
      header: "Confidence",
      cell: ({ row }) =>
        row.original.match_status !== "unmatched"
          ? getConfidenceBadge(row.original.match_confidence)
          : "-",
    },
    {
      id: "matched_transaction",
      header: "Matched Transaction",
      cell: ({ row }) => {
        const matched = row.original.matched_transaction;
        if (!matched) return <span className="text-gray-400">-</span>;
        return (
          <div className="text-sm">
            <div className="font-medium truncate max-w-xs">
              {matched.description || matched.vendor_name || "-"}
            </div>
            <div className="text-gray-500">
              {formatDate(matched.transaction_date)} ·{" "}
              {formatAmount(matched.amount)}
            </div>
          </div>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => {
        const line = row.original;
        if (line.match_status === "approved") {
          return <span className="text-green-600 flex items-center gap-1"><Check className="h-4 w-4" /> Approved</span>;
        }
        if (line.match_status === "rejected") {
          return <span className="text-red-600 flex items-center gap-1"><X className="h-4 w-4" /> Rejected</span>;
        }
        return (
          <div className="flex items-center gap-2">
            {line.proposed_matches && line.proposed_matches.length > 0 && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    line.proposed_matches?.[0]?.id &&
                    approveMutation.mutate(line.proposed_matches[0].id)
                  }
                  disabled={approveMutation.isPending}
                >
                  <Check className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    line.proposed_matches?.[0]?.id &&
                    rejectMutation.mutate(line.proposed_matches[0].id)
                  }
                  disabled={rejectMutation.isPending}
                >
                  <X className="h-4 w-4" />
                </Button>
              </>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onReviewLine?.(line)}
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </div>
        );
      },
    },
  ];

  const table = useReactTable({
    data: data?.lines || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    state: {
      sorting,
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded-md px-3 py-2 text-sm"
          >
            <option value="">All Status</option>
            <option value="unmatched">Unmatched</option>
            <option value="matched">Matched</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        <div className="text-sm text-gray-500">
          {data?.total || 0} lines total
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                    {header.column.getIsSorted() && (
                      <span className="ml-1">
                        {header.column.getIsSorted() === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y">
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="hover:bg-gray-50 transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
            {table.getRowModel().rows.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-gray-500"
                >
                  No bank statement lines found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
