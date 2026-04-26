import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { 
  Building2, 
  TrendingUp, 
  Users, 
  ArrowUpRight,
  ArrowDownRight,
  Activity
} from "lucide-react";

// Real demo data
const companies = [
  { 
    id: 1, 
    name: "Acme Consulting LLC", 
    industry: "Professional Services",
    revenue: 125000,
    expenses: 78000,
    profit: 47000,
    growth: 12.5,
    clients: 24,
    status: "active"
  },
  { 
    id: 2, 
    name: "TechStart Solutions", 
    industry: "Technology",
    revenue: 450000,
    expenses: 320000,
    profit: 130000,
    growth: 28.3,
    clients: 18,
    status: "active"
  },
  { 
    id: 3, 
    name: "GreenLeaf Organics", 
    industry: "Retail",
    revenue: 89000,
    expenses: 65000,
    profit: 24000,
    growth: -3.2,
    clients: 156,
    status: "active"
  },
];

const recentTransactions = [
  { id: 1, date: "2026-04-23", vendor: "Stripe", description: "Client Payment - Project Alpha", amount: 12500, category: "Consulting Revenue", type: "income" },
  { id: 2, date: "2026-04-23", vendor: "AWS", description: "Cloud Infrastructure", amount: -850, category: "Software", type: "expense" },
  { id: 3, date: "2026-04-22", vendor: "Slack", description: "Team Communication", amount: -180, category: "Software", type: "expense" },
  { id: 4, date: "2026-04-22", vendor: "Client B", description: "Monthly Retainer", amount: 8000, category: "Consulting Revenue", type: "income" },
  { id: 5, date: "2026-04-21", vendor: "WeWork", description: "Office Space", amount: -2200, category: "Rent", type: "expense" },
];

export function RealDataDemo() {
  const [selectedCompany, setSelectedCompany] = useState(companies[0]);

  const totalRevenue = companies.reduce((sum, c) => sum + c.revenue, 0);
  const totalExpenses = companies.reduce((sum, c) => sum + c.expenses, 0);
  const totalProfit = companies.reduce((sum, c) => sum + c.profit, 0);
  const avgGrowth = companies.reduce((sum, c) => sum + c.growth, 0) / companies.length;

  return (
    <div className="space-y-6">
      {/* Stats Overview Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-l-4 border-l-blue-500 hover:shadow-md transition-shadow">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">
              ${(totalRevenue / 1000).toFixed(0)}k
            </div>
            <div className="flex items-center gap-1 mt-1">
              <TrendingUp className="h-3 w-3 text-green-500" />
              <span className="text-xs text-green-600">+{avgGrowth.toFixed(1)}% avg</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-red-500 hover:shadow-md transition-shadow">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Expenses</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">
              ${(totalExpenses / 1000).toFixed(0)}k
            </div>
            <div className="flex items-center gap-1 mt-1">
              <ArrowDownRight className="h-3 w-3 text-red-500" />
              <span className="text-xs text-red-600">{((totalExpenses / totalRevenue) * 100).toFixed(0)}% of revenue</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500 hover:shadow-md transition-shadow">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Net Profit</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">
              ${(totalProfit / 1000).toFixed(0)}k
            </div>
            <div className="flex items-center gap-1 mt-1">
              <TrendingUp className="h-3 w-3 text-green-500" />
              <span className="text-xs text-green-600">{((totalProfit / totalRevenue) * 100).toFixed(1)}% margin</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500 hover:shadow-md transition-shadow">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Active Clients</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">
              {companies.reduce((sum, c) => sum + c.clients, 0)}
            </div>
            <div className="flex items-center gap-1 mt-1">
              <Users className="h-3 w-3 text-purple-500" />
              <span className="text-xs text-purple-600">Across {companies.length} companies</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Company Selector */}
      <div className="flex flex-wrap gap-2">
        {companies.map((company) => (
          <Button
            key={company.id}
            variant={selectedCompany.id === company.id ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCompany(company)}
            className="gap-2"
          >
            <Building2 className="h-4 w-4" />
            {company.name}
          </Button>
        ))}
      </div>

      {/* Selected Company Detail */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-blue-600" />
              {selectedCompany.name}
            </span>
            <Badge variant={selectedCompany.growth >= 0 ? "success" : "destructive"}>
              {selectedCompany.growth >= 0 ? "+" : ""}{selectedCompany.growth}% growth
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-white rounded-lg shadow-sm">
              <p className="text-sm text-slate-500 mb-1">Revenue</p>
              <p className="text-xl font-bold text-green-600">
                ${selectedCompany.revenue.toLocaleString()}
              </p>
            </div>
            <div className="text-center p-4 bg-white rounded-lg shadow-sm">
              <p className="text-sm text-slate-500 mb-1">Expenses</p>
              <p className="text-xl font-bold text-red-600">
                ${selectedCompany.expenses.toLocaleString()}
              </p>
            </div>
            <div className="text-center p-4 bg-white rounded-lg shadow-sm">
              <p className="text-sm text-slate-500 mb-1">Profit</p>
              <p className="text-xl font-bold text-blue-600">
                ${selectedCompany.profit.toLocaleString()}
              </p>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
            <span>Industry: {selectedCompany.industry}</span>
            <span>Clients: {selectedCompany.clients}</span>
            <span>Status: <Badge variant="outline" className="bg-green-100 text-green-800">{selectedCompany.status}</Badge></span>
          </div>
        </CardContent>
      </Card>

      {/* Recent Transactions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-slate-600" />
            Recent Transactions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentTransactions.map((tx) => (
              <div 
                key={tx.id} 
                className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors border"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${tx.type === 'income' ? 'bg-green-100' : 'bg-red-100'}`}>
                    {tx.type === 'income' ? (
                      <ArrowUpRight className="h-4 w-4 text-green-600" />
                    ) : (
                      <ArrowDownRight className="h-4 w-4 text-red-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">{tx.description}</p>
                    <p className="text-sm text-slate-500">{tx.vendor} • {tx.date}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${tx.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                    {tx.type === 'income' ? '+' : ''}${Math.abs(tx.amount).toLocaleString()}
                  </p>
                  <Badge variant="secondary" className="text-xs">{tx.category}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

