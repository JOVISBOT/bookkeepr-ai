import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { formatPercentage } from "../../lib/utils";

interface AccuracyData {
  date: string;
  accuracy: number;
  corrections: number;
}

interface AccuracyChartProps {
  data: AccuracyData[];
}

export function AccuracyChart({ data }: AccuracyChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Accuracy Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200" />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                className="text-slate-500 text-xs"
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                className="text-slate-500 text-xs"
                tickFormatter={(value) => `${value}%`}
                domain={[0, 100]}
              />
              <Tooltip
                formatter={(value) => [
                  formatPercentage(value as number),
                  "Accuracy",
                ]}
                contentStyle={{
                  backgroundColor: "white",
                  border: "1px solid #e2e8f0",
                  borderRadius: "6px",
                }}
              />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: "#10b981", r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
