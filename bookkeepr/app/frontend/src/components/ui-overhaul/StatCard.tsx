import { cn } from "../../lib/utils";
import { AnimatedNumber } from "./AnimatedNumber";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
    label: string;
  };
  variant?: "blue" | "green" | "amber" | "purple";
  formatter?: (value: number) => string;
}

const variantStyles = {
  blue: {
    bg: "bg-primary-50 dark:bg-primary-950/30",
    icon: "text-primary-600 dark:text-primary-400",
    iconBg: "bg-primary-100 dark:bg-primary-900/40",
    border: "border-l-primary-500",
  },
  green: {
    bg: "bg-success-50 dark:bg-success-950/30",
    icon: "text-success-600 dark:text-success-400",
    iconBg: "bg-success-100 dark:bg-success-900/40",
    border: "border-l-success-500",
  },
  amber: {
    bg: "bg-warning-50 dark:bg-warning-950/30",
    icon: "text-warning-600 dark:text-warning-400",
    iconBg: "bg-warning-100 dark:bg-warning-900/40",
    border: "border-l-warning-500",
  },
  purple: {
    bg: "bg-purple-50 dark:bg-purple-950/30",
    icon: "text-purple-600 dark:text-purple-400",
    iconBg: "bg-purple-100 dark:bg-purple-900/40",
    border: "border-l-purple-500",
  },
};

export function StatCard({
  title,
  value,
  prefix = "",
  suffix = "",
  decimals = 0,
  icon: Icon,
  trend,
  variant = "blue",
  formatter,
}: StatCardProps) {
  const styles = variantStyles[variant];

  return (
    <div
      className={cn(
        "glass-card hover-lift border-l-4",
        styles.border,
        "p-5"
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <div className="mt-1">
            <span className="text-2xl font-bold text-foreground">
              <AnimatedNumber
                value={value}
                prefix={prefix}
                suffix={suffix}
                decimals={decimals}
                formatter={formatter}
              />
            </span>
          </div>
        </div>
        <div className={cn("p-2.5 rounded-xl", styles.iconBg)}>
          <Icon className={cn("h-5 w-5", styles.icon)} />
        </div>
      </div>
      
      {trend && (
        <div className="flex items-center gap-1.5 mt-2">
          <span
            className={cn(
              "inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full",
              trend.isPositive
                ? "text-success-700 bg-success-100 dark:text-success-300 dark:bg-success-900/40"
                : "text-danger-700 bg-danger-100 dark:text-danger-300 dark:bg-danger-900/40"
            )}
          >
            {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}%
          </span>
          <span className="text-xs text-muted-foreground">{trend.label}</span>
        </div>
      )}
    </div>
  );
}
