import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, CheckCircle, HelpCircle, FileText } from "lucide-react";
import { getReconciliationSummary, runAutoMatch } from "../../lib/api";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import type { ReconciliationSummary } from "../../types";

interface SummaryCardsProps {
  statementId: number;
}

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  color: "blue" | "green" | "yellow" | "red";
}) {
  const colorClasses = {
    blue: "bg-blue-50 border-blue-200 text-blue-900",
    green: "bg-green-50 border-green-200 text-green-900",
    yellow: "bg-yellow-50 border-yellow-200 text-yellow-900",
    red: "bg-red-50 border-red-200 text-red-900",
  };

  const iconColors = {
    blue: "text-blue-600",
    green: "text-green-600",
    yellow: "text-yellow-600",
    red: "text-red-600",
  };

  return (
    <Card className={`p-4 ${colorClasses[color]}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium opacity-80">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {subtitle && (
            <p className="text-sm mt-1 opacity-70">{subtitle}</p>
          )}
        </div>
        <Icon className={`h-8 w-8 ${iconColors[color]} opacity-80`} />
      </div>
    </Card>
  );
}

export function SummaryCards({ statementId }: SummaryCardsProps) {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["reconciliation-summary", statementId],
    queryFn: () => getReconciliationSummary(statementId),
    enabled: !!statementId,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const autoMatchMutation = useMutation({
    mutationFn: () => runAutoMatch(statementId, 0.85),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["reconciliation-summary", statementId],
      });
      queryClient.invalidateQueries({
        queryKey: ["bank-statement-lines", statementId],
      });
    },
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="p-4 h-28 animate-pulse bg-gray-100" />
        ))}
      </div>
    );
  }

  const summary: ReconciliationSummary = data?.summary || {
    total_lines: 0,
    matched: 0,
    approved: 0,
    rejected: 0,
    unmatched: 0,
    total_in: 0,
    total_out: 0,
    match_rate: 0,
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      signDisplay: "never",
    }).format(Math.abs(amount));
  };

  const approvedRate =
    summary.total_lines > 0
      ? Math.round((summary.approved / summary.total_lines) * 100)
      : 0;

  const matchedRate =
    summary.total_lines > 0
      ? Math.round((summary.matched / summary.total_lines) * 100)
      : 0;

  return (
    <div className="space-y-4">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Lines"
          value={summary.total_lines}
          subtitle={`${formatCurrency(summary.total_in)} in / ${formatCurrency(
            summary.total_out
          )} out`}
          icon={FileText}
          color="blue"
        />

        <StatCard
          title="Matched"
          value={`${matchedRate}%`}
          subtitle={`${summary.matched} of ${summary.total_lines} lines`}
          icon={CheckCircle}
          color="green"
        />

        <StatCard
          title="Approved"
          value={`${approvedRate}%`}
          subtitle={`${summary.approved} approved`}
          icon={CheckCircle}
          color="yellow"
        />

        <StatCard
          title="Remaining"
          value={summary.unmatched}
          subtitle={`${summary.rejected} rejected`}
          icon={HelpCircle}
          color="red"
        />
      </div>

      {/* Progress Bars */}
      <Card className="p-4">
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">
                Overall Match Rate
              </span>
              <span className="text-sm font-medium text-gray-700">
                {Math.round(summary.match_rate * 100)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${summary.match_rate * 100}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">
                Approved Rate
              </span>
              <span className="text-sm font-medium text-gray-700">
                {approvedRate}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-green-600 h-2.5 rounded-full transition-all duration-500"
                style={{
                  width: `${
                    summary.total_lines > 0
                      ? (summary.approved / summary.total_lines) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              onClick={() => autoMatchMutation.mutate()}
              disabled={autoMatchMutation.isPending}
              variant="outline"
            >
              <RefreshCw
                className={`h-4 w-4 mr-2 ${
                  autoMatchMutation.isPending ? "animate-spin" : ""
                }`}
              />
              {autoMatchMutation.isPending
                ? "Running Auto-Match..."
                : "Run Auto-Match"}
            </Button>
          </div>

          {autoMatchMutation.isSuccess && (
            <div className="text-sm text-green-600 bg-green-50 p-2 rounded">
              Created {autoMatchMutation.data.matches_created} new matches
            </div>
          )}

          {autoMatchMutation.isError && (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
              Failed to run auto-match. Please try again.
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
