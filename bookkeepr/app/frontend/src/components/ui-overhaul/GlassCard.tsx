import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

export function GlassCard({
  children,
  className,
  hover = true,
  padding = "md",
}: GlassCardProps) {
  const paddingClasses = {
    none: "",
    sm: "p-3",
    md: "p-5",
    lg: "p-6",
  };

  return (
    <div
      className={cn(
        "glass-card",
        paddingClasses[padding],
        hover && "hover-lift",
        className
      )}
    >
      {children}
    </div>
  );
}
