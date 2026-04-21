import { useState } from "react";
import { useCompanies, useAIMetrics, useReviewQueue } from "../hooks";
import { StatCard, SpendingChart, CategoryChart, AccuracyChart } from "../components/dashboard";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { formatCurrency, formatNumber, formatPercentage } from "../lib/utils";
import {
  DollarSign,
  Receipt,
  AlertCircle,
  TrendingUp,
  Activity,
  Brain,
  Loader2,
} from "lucide-react";

// Mock data for charts - will be replaced with real data from API
const mockMonthlyData = [
  { month: "Jan", amount: 45000, count: 234 },
  { month: "Feb", amount: 52000, count: 256 },
  { month: "Mar", amount: 48000, count: 245 },
  { month: "Apr", amount: 61000, count: 312 },
  { month: "May", amount: 55000, count: 278 },
  { month: "Jun", amount: 67000, count: 345 },
];

const mockCategoryData = [
  { category: "Office", amount: 15000, percentage: 25 },
  { category: "Travel", amount: 12000, percentage: 20 },
  { category: "Software", amount: 10000, percentage: 17 },
  { category: "Marketing", amount: 8000, percentage: 13 },
  { category: "Equipment", amount: 7500, percentage: 12 },
  { category: "Other", amount: 7500, percentage: 13 },
];

const mockAccuracyData = [
  { date: "W1", accuracy: 82, corrections: 5 },
  { date: "W2", accuracy: 85, corrections: 4 },
  { date: "W3", accuracy: 88, corrections: 3 },
  { date: "W4", accuracy: 91, corrections: 2 },
  { date: "W5", accuracy: 92, corrections: 2 },
  { date: "W6", accuracy: 94, corrections: 1 },
];

export function Dashboard() {
  const [selectedCompany, setSelectedCompany] = useState<number | null>(null);
  
  const { data: companies, isLoading: companiesLoading } = useCompanies();
  const { data: aiMetrics, isLoading: metricsLoading } = useAIMetrics(selectedCompany, 30);
  const { data: reviewQueue } = useReviewQueue(selectedCompany, "pending");

  // Auto-select first company if none selected
  if (companies && companies.length > 0 && !selectedCompany) {
    setSelectedCompany(companies[0].id);
  }

  const isLoading = companiesLoading || metricsLoading;

  const stats = {
    totalTransactions: aiMetrics?.metrics?.total_transactions || 0,
    pendingReview: reviewQueue?.total || 0,
    accuracyRate: (aiMetrics?.metrics?.accuracy_rate || 0) * 100,
    monthlySpending: mockMonthlyData[mockMonthlyData.length - 1].amount,
  };

  const confidenceDist = aiMetrics?.confidence_distribution || {};

  return (
    <div className="space-y-6">
      {/* Company Selector */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">Dashboard Overview</h2>
          <p className="text-slate-500">
            Track your transactions and AI categorization performance
          </p>
        </div>
        {companies && companies.length > 0 && (
          <select
            className="h-10 rounded-md border border-slate-200 bg-white px-3 text-sm"
            value={selectedCompany || ""}
            onChange={(e) => setSelectedCompany(Number(e.target.value))}
          >
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
        </div>
      ) : (
        <>
          {/* Stats Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Transactions"
              value={formatNumber(stats.totalTransactions)}
              description="All time transactions"
              icon={Receipt}
              trend={{ value: 12, label: "vs last month" }}
            />
            <StatCard
              title="Pending Review"
              value={formatNumber(stats.pendingReview)}
              description="Needs your attention"
              icon={AlertCircle}
              trend={{ value: -5, label: "vs last week" }}
            />
            <StatCard
              title="AI Accuracy"
              value={formatPercentage(stats.accuracyRate)}
              description="Last 30 days"
              icon={Brain}
              trend={{ value: 3, label: "improvement" }}
            />
            <StatCard
              title="Monthly Spending"
              value={formatCurrency(stats.monthlySpending)}
              description="This month"
              icon={DollarSign}
              trend={{ value: 8, label: "vs last month" }}
            />
          </div>

          {/* Charts Row 1 */}
          <div className="grid gap-4 lg:grid-cols-2">
            <SpendingChart data={mockMonthlyData} />
            <CategoryChart data={mockCategoryData} />
          </div>

          {/* Charts Row 2 */}
          <div className="grid gap-4 lg:grid-cols-3">
            <AccuracyChart data={mockAccuracyData} />
            
            {/* Confidence Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Confidence Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>High Confidence (≥85%)</span>
                      <span className="font-medium">{confidenceDist.high || 0}</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500 rounded-full"
                        style={{ 
                          width: `${Math.min(((confidenceDist.high || 0) / (stats.totalTransactions || 1)) * 100, 100)}%` 
                        }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Medium Confidence (70-85%)</span>
                      <span className="font-medium">{confidenceDist.medium || 0}</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-amber-500 rounded-full"
                        style={{ 
                          width: `${Math.min(((confidenceDist.medium || 0) / (stats.totalTransactions || 1)) * 100, 100)}%` 
                        }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Low Confidence (&lt;70%)</span>
                      <span className="font-medium">{confidenceDist.low || 0}</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-red-500 rounded-full"
                        style={{ 
                          width: `${Math.min(((confidenceDist.low || 0) / (stats.totalTransactions || 1)) * 100, 100)}%` 
                        }}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Button 
                    className="w-full justify-start" 
                    variant="outline"
                    onClick={() => window.location.href = "/review"}
                  >
                    <AlertCircle className="h-4 w-4 mr-2" />
                    Review {stats.pendingReview} Pending Items
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <Brain className="h-4 w-4 mr-2" />
                    Run AI Categorization
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <Activity className="h-4 w-4 mr-2" />
                    View Analytics Report
                  </Button>
                  <Button className="w-full justify-start" variant="outline">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Export Data
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
