import { cn } from "../../lib/utils";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular" | "rounded";
}

export function LoadingSkeleton({
  className,
  variant = "rectangular",
}: SkeletonProps) {
  const baseClasses = "shimmer";

  const variantClasses = {
    text: "h-4 rounded",
    circular: "rounded-full",
    rectangular: "rounded-lg",
    rounded: "rounded-xl",
  };

  return (
    <div
      className={cn(
        baseClasses,
        variantClasses[variant],
        className
      )}
    />
  );
}

interface StatCardSkeletonProps {
  className?: string;
}

export function StatCardSkeleton({ className }: StatCardSkeletonProps) {
  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-start justify-between mb-3">
        <div className="space-y-2">
          <LoadingSkeleton className="w-24 h-4" />
          <LoadingSkeleton className="w-16 h-8" />
        </div>
        <LoadingSkeleton variant="circular" className="w-10 h-10" />
      </div>
      <LoadingSkeleton className="w-32 h-5 mt-2" />
    </div>
  );
}

interface DashboardSkeletonProps {
  className?: string;
}

export function DashboardSkeleton({ className }: DashboardSkeletonProps) {
  return (
    <div className={cn("space-y-6", className)}>
      <div className="space-y-2">
        <LoadingSkeleton className="w-48 h-8" />
        <LoadingSkeleton className="w-64 h-5" />
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
      </div>
      
      <div className="grid gap-6 md:grid-cols-3">
        <div className="glass-card p-5 space-y-4">
          <LoadingSkeleton className="w-32 h-5" />
          <LoadingSkeleton className="w-full h-40" />
        </div>
        <div className="glass-card p-5 space-y-4">
          <LoadingSkeleton className="w-32 h-5" />
          <LoadingSkeleton className="w-full h-40" />
        </div>
      </div>
    </div>
  );
}

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  className?: string;
}

export function TableSkeleton({
  rows = 5,
  columns = 4,
  className,
}: TableSkeletonProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex gap-3">
        {Array.from({ length: columns }).map((_, i) => (
          <LoadingSkeleton key={`header-${i}`} className="flex-1 h-6" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div key={`row-${rowIdx}`} className="flex gap-3">
          {Array.from({ length: columns }).map((_, colIdx) => (
            <LoadingSkeleton
              key={`cell-${rowIdx}-${colIdx}`}
              className="flex-1 h-10"
            />
          ))}
        </div>
      ))}
    </div>
  );
}
