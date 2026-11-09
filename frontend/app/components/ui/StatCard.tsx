import React from "react";

const COLUMNS = {
  1: "grid-cols-1",
  2: "grid-cols-1 sm:grid-cols-2",
  3: "grid-cols-1 sm:grid-cols-3",
  4: "grid-cols-2 xl:grid-cols-4",
};

/** Agrupa indicadores en una sola superficie, separados por líneas finas. */
export function StatGrid({ columns, children }: { columns: keyof typeof COLUMNS; children: React.ReactNode }) {
  return (
    <div className={`grid gap-px rounded-lg overflow-hidden bg-border-primary border border-border-primary ${COLUMNS[columns]}`}>
      {children}
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
}

export function StatCard({ title, value, subtitle, icon }: StatCardProps) {
  return (
    <div className="bg-bg-surface p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-text-secondary">{title}</p>
        {icon && <span className="text-text-muted shrink-0">{icon}</span>}
      </div>
      <p className="mt-2.5 text-3xl leading-none font-semibold text-text-primary tabular-nums tracking-tight">{value}</p>
      {subtitle && <p className="mt-3 text-xs text-text-muted">{subtitle}</p>}
    </div>
  );
}
