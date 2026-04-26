import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Clock, CheckCircle2, AlertCircle, ArrowUpRight } from "lucide-react";
import { formatDate } from "../../lib/utils";

interface Activity {
  id: number;
  type: "categorized" | "reviewed" | "imported" | "synced";
  description: string;
  timestamp: string;
  amount?: number;
}

const recentActivities: Activity[] = [
  {
    id: 1,
    type: "categorized",
    description: "Google Ads categorized as Marketing",
    timestamp: "2026-04-23T14:30:00",
    amount: 1276,
  },
  {
    id: 2,
    type: "reviewed",
    description: "Client Payment approved",
    timestamp: "2026-04-23T13:15:00",
    amount: 6291,
  },
  {
    id: 3,
    type: "imported",
    description: "12 transactions imported from QuickBooks",
    timestamp: "2026-04-23T10:00:00",
  },
  {
    id: 4,
    type: "synced",
    description: "Account synced successfully",
    timestamp: "2026-04-23T09:00:00",
  },
  {
    id: 5,
    type: "categorized",
    description: "Office Supplies categorized",
    timestamp: "2026-04-22T16:45:00",
    amount: 150,
  },
];

const activityConfig = {
  categorized: {
    icon: CheckCircle2,
    color: "bg-green-100 text-green-700",
    label: "Categorized",
  },
  reviewed: {
    icon: ArrowUpRight,
    color: "bg-blue-100 text-blue-700",
    label: "Reviewed",
  },
  imported: {
    icon: AlertCircle,
    color: "bg-amber-100 text-amber-700",
    label: "Imported",
  },
  synced: {
    icon: Clock,
    color: "bg-purple-100 text-purple-700",
    label: "Synced",
  },
};

export function RecentActivity() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-slate-600" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {recentActivities.map((activity) => {
            const config = activityConfig[activity.type];
            const Icon = config.icon;

            return (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50 transition-colors"
              >
                <div className={`p-2 rounded-lg ${config.color}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {activity.description}
                    </p>
                    <Badge variant="secondary" className="text-xs shrink-0">
                      {config.label}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-500">
                      {formatDate(activity.timestamp)}
                    </span>
                    {activity.amount && (
                      <span className="text-xs font-medium text-slate-700">
                        ${activity.amount.toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
