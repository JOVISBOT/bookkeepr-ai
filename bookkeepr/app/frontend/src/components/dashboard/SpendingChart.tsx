import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { formatCurrency } from "../../lib/utils";

interface SpendingData {
  month: string;
  amount: number;
  count: number;
}

interface SpendingChartProps {
  data: SpendingData[];
}

export function SpendingChart({ data }: SpendingChartProps) {
  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle>Monthly Spending</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200" />
              <XAxis
                dataKey="month"
                tickLine={false}
                axisLine={false}
                className="text-slate-500 text-xs"
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                className="text-slate-500 text-xs"
                tickFormatter={(value) => `$${value / 1000}k`}
              />
              <Tooltip
                formatter={(value) => [formatCurrency(value as number), "Amount"]}
                contentStyle={{
                  backgroundColor: "white",
                  border: "1px solid #e2e8f0",
                  borderRadius: "6px",
                }}
              />
              <Bar
                dataKey="amount"
                fill="#3b82f6"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
