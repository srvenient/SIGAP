import React from "react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  badge?: string;
}

export function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  badge,
}: StatCardProps) {
  return (
    <div className="relative overflow-hidden rounded-xl bg-bg-surface border border-border-primary p-4 sm:p-5 shadow-xs transition-colors duration-150 hover:border-border-strong">
      <div className="flex items-start justify-between gap-3 relative z-10">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-[11px] font-semibold text-text-muted tracking-wider uppercase font-sans">
              {title}
            </p>
            {badge && (
              <span className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-bg-app border border-border-secondary text-text-muted">
                {badge}
              </span>
            )}
          </div>

          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight font-special tabular-nums">
              {value}
            </span>
          </div>

          {subtitle && (
            <p className="mt-1 text-xs text-text-secondary truncate font-sans">
              {subtitle}
            </p>
          )}

          {trend && (
            <div className="mt-2.5 flex items-center gap-1.5 text-xs font-mono">
              <span
                className={`font-semibold ${
                  trend.isPositive ? "text-status-success" : "text-status-warning"
                }`}
              >
                {trend.value}
              </span>
              <span className="text-text-muted">{trend.label || "vs turno anterior"}</span>
            </div>
          )}
        </div>

        <div className="w-10 h-10 rounded-lg bg-bg-accent/80 border border-border-secondary flex items-center justify-center text-text-primary shrink-0">
          {icon}
        </div>
      </div>
    </div>
  );
}

