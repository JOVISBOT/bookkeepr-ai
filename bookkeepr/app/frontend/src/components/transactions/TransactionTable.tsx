import { useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { formatCurrency, formatDate } from "../../lib/utils";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import type { Transaction } from "../../types";
import { ChevronLeft, ChevronRight, Search, ArrowUpDown } from "lucide-react";

interface TransactionTableProps {
  data: Transaction[];
  total: number;
  pages: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  onReview?: (transaction: Transaction) => void;
}

export function TransactionTable({
  data,
  total,
  pages,
  currentPage,
  onPageChange,
  onReview,
}: TransactionTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");

  const columns: ColumnDef<Transaction>[] = [
    {
      accessorKey: "transaction_date",
      header: "Date",
      cell: ({ row }) => formatDate(row.getValue("transaction_date")),
    },
    {
      accessorKey: "vendor_name",
      header: "Vendor",
      cell: ({ row }) => row.getValue("vendor_name") || "N/A",
    },
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => (
        <div className="max-w-xs truncate" title={row.getValue("description")}>
          {row.getValue("description") || "N/A"}
        </div>
      ),
    },
    {
      accessorKey: "amount",
      header: "Amount",
      cell: ({ row }) => {
        const amount = row.getValue("amount") as number;
        const isNegative = amount < 0;
        return (
          <span className={isNegative ? "text-red-600" : "text-green-600"}>
            {formatCurrency(amount)}
          </span>
        );
      },
    },
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => row.getValue("category") || "Uncategorized",
    },
    {
      accessorKey: "categorization_status",
      header: "Status",
      cell: ({ row }) => {
        const status = row.getValue("categorization_status") as string;
        const variant =
          status === "categorized"
            ? "success"
            : status === "suggested"
            ? "warning"
            : "secondary";
        return <Badge variant={variant}>{status}</Badge>;
      },
    },
    {
      accessorKey: "suggested_confidence",
      header: "Confidence",
      cell: ({ row }) => {
        const confidence = row.getValue("suggested_confidence") as number;
        if (!confidence) return "-";
        return (
          <span
            className={
              confidence >= 0.85
                ? "text-green-600"
                : confidence >= 0.7
                ? "text-amber-600"
                : "text-red-600"
            }
          >
            {Math.round(confidence * 100)}%
          </span>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => {
        const transaction = row.original;
        const needsReview =
          transaction.categorization_status !== "categorized" ||
          (transaction.suggested_confidence || 0) < 0.85;

        return needsReview && onReview ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onReview(transaction)}
          >
            Review
          </Button>
        ) : null;
      },
    },
  ];

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      globalFilter,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search transactions..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <div className="rounded-md border">
        <table className="w-full text-sm">
          <thead className="border-b bg-slate-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="h-12 px-4 text-left align-middle font-medium text-slate-500"
                  >
                    {header.isPlaceholder ? null : (
                      <button
                        className="flex items-center gap-1 hover:text-slate-900"
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                        <ArrowUpDown className="h-4 w-4" />
                      </button>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="border-b hover:bg-slate-50"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="p-4">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={columns.length}
                  className="h-24 text-center text-slate-500"
                >
                  No transactions found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-500">
          Showing {data.length} of {total} transactions
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
    </div>
  );
}
