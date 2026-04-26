import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { 
  DollarSign,
  Calendar,
  Filter,
  Download,
  FileText,
  BarChart3,
  PieChart,
  Activity,
  TrendingDown
} from "lucide-react";
import { formatCurrency } from "../../lib/utils";

interface FinancialStatementsProps {
  companyId: number;
}

export function FinancialStatements({ companyId }: FinancialStatementsProps) {
  const [dateRange, setDateRange] = useState("this_month");
  const [statementType, setStatementType] = useState("pnl");
  const [isLoading] = useState(false);

  // Use companyId for API calls
  console.log("Financial Statements for company:", companyId);
  const financialData = {
    pnl: {
      revenue: 125000,
      cogs: 45000,
      grossProfit: 80000,
      expenses: {
        "Rent": 5000,
        "Utilities": 1200,
        "Marketing": 3500,
        "Salaries": 25000,
        "Software": 800,
        "Insurance": 1200,
        "Meals & Entertainment": 450,
        "Office Supplies": 300,
        "Professional Services": 2000,
        "Travel": 800
      },
      totalExpenses: 40250,
      netIncome: 39750,
      margin: 31.8
    },
    balance: {
      assets: {
        "Cash & Bank": 85000,
        "Accounts Receivable": 15000,
        "Equipment": 25000,
        "Inventory": 5000
      },
      totalAssets: 130000,
      liabilities: {
        "Accounts Payable": 8000,
        "Credit Cards": 3500,
        "Loans": 15000
      },
      totalLiabilities: 26500,
      equity: {
        "Owner's Equity": 100000,
        "Retained Earnings": 3500
      },
      totalEquity: 103500
    },
    cashflow: {
      operating: 35000,
      investing: -5000,
      financing: -10000,
      netChange: 20000,
      beginningBalance: 65000,
      endingBalance: 85000
    }
  };

  const dateRanges = [
    { value: "this_month", label: "This Month" },
    { value: "last_month", label: "Last Month" },
    { value: "this_quarter", label: "This Quarter" },
    { value: "this_year", label: "This Year" },
    { value: "custom", label: "Custom Range" }
  ];

  const statementTypes = [
    { value: "pnl", label: "Profit & Loss", icon: BarChart3 },
    { value: "balance", label: "Balance Sheet", icon: PieChart },
    { value: "cashflow", label: "Cash Flow", icon: Activity }
  ];

  const renderPnL = () => {
    const data = financialData.pnl;
    return (
      <div className="space-y-6">
        {/* Revenue Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
            <span className="font-medium text-green-800">Revenue</span>
            <span className="font-bold text-green-700">{formatCurrency(data.revenue)}</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
            <span className="font-medium text-red-800">Cost of Goods Sold</span>
            <span className="font-bold text-red-700">-{formatCurrency(data.cogs)}</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border-2 border-blue-200">
            <span className="font-bold text-blue-800">Gross Profit</span>
            <span className="font-bold text-blue-700 text-lg">{formatCurrency(data.grossProfit)}</span>
          </div>
        </div>

        {/* Expenses Section */}
        <div className="space-y-2">
          <h4 className="font-medium text-slate-700 flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-red-500" />
            Expenses
          </h4>
          {Object.entries(data.expenses).map(([name, amount]) => (
            <div key={name} className="flex items-center justify-between p-2 hover:bg-slate-50 rounded">
              <span className="text-sm text-slate-600">{name}</span>
              <span className="text-sm font-medium text-slate-800">{formatCurrency(amount as number)}</span>
            </div>
          ))}
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg border-t-2 border-red-200">
            <span className="font-bold text-red-800">Total Expenses</span>
            <span className="font-bold text-red-700">-{formatCurrency(data.totalExpenses)}</span>
          </div>
        </div>

        {/* Net Income */}
        <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-lg border-2 border-emerald-200">
          <div>
            <span className="font-bold text-emerald-800 text-lg">Net Income</span>
            <Badge variant="success" className="ml-2">{data.margin}% margin</Badge>
          </div>
          <span className="font-bold text-emerald-700 text-xl">{formatCurrency(data.netIncome)}</span>
        </div>
      </div>
    );
  };

  const renderBalanceSheet = () => {
    const data = financialData.balance;
    return (
      <div className="space-y-6">
        {/* Assets */}
        <div className="space-y-2">
          <h4 className="font-medium text-slate-700 flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-green-500" />
            Assets
          </h4>
          {Object.entries(data.assets).map(([name, amount]) => (
            <div key={name} className="flex items-center justify-between p-2 hover:bg-slate-50 rounded">
              <span className="text-sm text-slate-600">{name}</span>
              <span className="text-sm font-medium text-slate-800">{formatCurrency(amount as number)}</span>
            </div>
          ))}
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border-t-2 border-green-200">
            <span className="font-bold text-green-800">Total Assets</span>
            <span className="font-bold text-green-700">{formatCurrency(data.totalAssets)}</span>
          </div>
        </div>

        {/* Liabilities */}
        <div className="space-y-2">
          <h4 className="font-medium text-slate-700 flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-red-500" />
            Liabilities
          </h4>
          {Object.entries(data.liabilities).map(([name, amount]) => (
            <div key={name} className="flex items-center justify-between p-2 hover:bg-slate-50 rounded">
              <span className="text-sm text-slate-600">{name}</span>
              <span className="text-sm font-medium text-slate-800">-{formatCurrency(amount as number)}</span>
            </div>
          ))}
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg border-t-2 border-red-200">
            <span className="font-bold text-red-800">Total Liabilities</span>
            <span className="font-bold text-red-700">-{formatCurrency(data.totalLiabilities)}</span>
          </div>
        </div>

        {/* Equity */}
        <div className="space-y-2">
          <h4 className="font-medium text-slate-700">Equity</h4>
          {Object.entries(data.equity).map(([name, amount]) => (
            <div key={name} className="flex items-center justify-between p-2 hover:bg-slate-50 rounded">
              <span className="text-sm text-slate-600">{name}</span>
              <span className="text-sm font-medium text-slate-800">{formatCurrency(amount as number)}</span>
            </div>
          ))}
        </div>

        {/* Total */}
        <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
          <span className="font-bold text-blue-800 text-lg">Total Equity</span>
          <span className="font-bold text-blue-700 text-xl">{formatCurrency(data.totalEquity)}</span>
        </div>
      </div>
    );
  };

  const renderCashFlow = () => {
    const data = financialData.cashflow;
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
            <span className="font-medium text-green-800">Operating Activities</span>
            <span className="font-bold text-green-700">+{formatCurrency(data.operating)}</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
            <span className="font-medium text-yellow-800">Investing Activities</span>
            <span className="font-bold text-yellow-700">{formatCurrency(data.investing)}</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
            <span className="font-medium text-red-800">Financing Activities</span>
            <span className="font-bold text-red-700">{formatCurrency(data.financing)}</span>
          </div>
        </div>

        <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
          <span className="font-bold text-blue-800 text-lg">Net Change in Cash</span>
          <span className="font-bold text-blue-700 text-xl">{formatCurrency(data.netChange)}</span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 text-slate-600">
            <span>Beginning Balance</span>
            <span>{formatCurrency(data.beginningBalance)}</span>
          </div>
          <div className="flex items-center justify-between p-2 text-slate-800 font-bold">
            <span>Ending Balance</span>
            <span>{formatCurrency(data.endingBalance)}</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <CardTitle className="text-xl flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Financial Statements
            </CardTitle>
            <p className="text-sm text-slate-500 mt-1">
              View your financial reports like QuickBooks
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="h-4 w-4" />
              Export PDF
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mt-4">
          {/* Statement Type */}
          <div className="flex items-center gap-2 bg-slate-100 rounded-lg p-1">
            {statementTypes.map((type) => (
              <Button
                key={type.value}
                variant={statementType === type.value ? "default" : "ghost"}
                size="sm"
                onClick={() => setStatementType(type.value)}
                className="gap-2"
              >
                <type.icon className="h-4 w-4" />
                {type.label}
              </Button>
            ))}
          </div>

          {/* Date Range */}
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-500" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-3 py-1.5 border rounded-md text-sm bg-white"
            >
              {dateRanges.map((range) => (
                <option key={range.value} value={range.value}>
                  {range.label}
                </option>
              ))}
            </select>
          </div>

          {/* Quick Filters */}
          <Button variant="outline" size="sm" className="gap-2">
            <Filter className="h-4 w-4" />
            More Filters
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
          </div>
        ) : (
          <>
            {statementType === "pnl" && renderPnL()}
            {statementType === "balance" && renderBalanceSheet()}
            {statementType === "cashflow" && renderCashFlow()}
          </>
        )}
      </CardContent>
    </Card>
  );
}
